from googleapiclient.discovery import build
from google.cloud import storage, bigquery, pubsub_v1
from yaml import safe_load
from logging import getLogger
import psycopg2
import pathlib
import string
import datetime
from json import dumps
from random import choice, choices
import os
from globals import CHALLENGES


USER_STARTING_CREDITS = 10
BACKEND_PROJECT = 'aix-backend-prod'

utils_logger = getLogger('utils_logger')

with open(os.path.join(pathlib.Path(__file__).parent.resolve(), 'db.yaml'), 'r') as f:
    db = safe_load(f)

def get_db_conn():
    if os.environ.get("GAE_ENV") == "standard":
        host = f"/cloudsql/{db['connection_name']}"
    else:
        host = db['host']
    return psycopg2.connect(host=host, database=db['database'], user=db['user'], password=db['password'])

def run_query(query):
    conn=get_db_conn()
    cur=conn.cursor()
    cur.execute(query)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def run_insert_statement(insert_statement):
    conn=get_db_conn()
    cur=conn.cursor()
    cur.execute(insert_statement)
    conn.commit()
    cur.close()
    conn.close()

def get_policy(project_id, version=1):
    """Gets IAM policy for a project."""

    service = build("cloudresourcemanager", "v1")
    policy = (
        service.projects()
            .getIamPolicy(
            resource=project_id,
            body={"options": {"requestedPolicyVersion": version}},
        )
            .execute()
    )
    print(policy)
    return policy

def set_policy(project_id, policy):
    """Sets IAM policy for a project."""

    service = build("cloudresourcemanager", "v1")

    policy = (
        service.projects()
            .setIamPolicy(resource=project_id, body={"policy": policy})
            .execute()
    )
    print(policy)
    return policy

def modify_policy_add_member(policy, role, member):
    """Adds a new member to a role binding."""

    binding = next(b for b in policy["bindings"] if b["role"] == role)
    binding["members"].append(member)
    print(binding)
    return policy

def modify_policy_remove_member(policy, role, member):
    """Removes a  member from a role binding."""
    binding = next(b for b in policy["bindings"] if b["role"] == role)
    if "members" in binding and member in binding["members"]:
        binding["members"].remove(member)
    print(binding)
    return policy

def modify_policy_add_role(project_id, role, member):
    """Adds a new role binding to a policy."""

    policy = get_policy(project_id)

    binding = None
    for b in policy["bindings"]:
        if b["role"] == role:
            binding = b
            break
    if binding is not None:
        binding["members"].append(member)
    else:
        binding = {"role": role, "members": [member]}
        policy["bindings"].append(binding)

    set_policy(project_id, policy)

def modify_policy_remove_role(project_id, role, member):
    """Removes a role"""

    policy = get_policy(project_id)

    binding = next(b for b in policy["bindings"] if b["role"] == role)
    if "members" in binding and member in binding["members"]:
        binding["members"].remove(member)

    set_policy(project_id, policy)

def choose_compute_zone():

    AVAILABLE_ZONE_LIST = ['europe-west4-a', 'europe-west4-b', 'europe-west4-c',
                           'europe-west3-a', 'europe-west3-b', 'europe-west3-c',
                           'europe-west2-a', 'europe-west2-b', 'europe-west2-c',
                           'europe-west1-d', 'europe-west1-b', 'europe-west1-c',
                           'europe-north1-a', 'europe-north1-b', 'europe-north1-c',
                           'europe-central2-a', 'europe-central2-b', 'europe-central2-c']

    return choice(AVAILABLE_ZONE_LIST)

def build_dag_conf(user, challenge):
    user_bucket = get_user_bucket(user)
    return {
        "user_id": user,
        "resource_suffix": f"{user.lower()}-{''.join(choices(string.ascii_lowercase + string.digits, k=5))}",
        "project": CHALLENGES[challenge]['project_name'],
        "zone": choose_compute_zone(),
        "repo_gcs_path": "gs://aix_pypi_repo/",
        "code_gcs_path": f"gs://{user_bucket}/{challenge}/code/",
        "logs_gcs_path": f"gs://{user_bucket}/{challenge}/logs/",
        "data_gcs_path": f"gs://{CHALLENGES[challenge]['bucket']}/tmp/{user}/",
        "user_dataset": get_user_dataset(user),
        "artifacts_gcs_path": f"gs://{CHALLENGES[challenge]['bucket']}/artifacts/{user}/",
        "evaluation_gcs_path": f"gs://{CHALLENGES[challenge]['bucket']}/evaluation/{user}/",
        "dag_retries": 0,
        "challenge": CHALLENGES[challenge]['name']
    }


def write_dag_run_request(dag=None, run_id=None, conf=None, bucket_name=None):
    client = storage.Client(project=conf['project'])
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(f'user_requests/{dag}/{run_id}')
    blob.upload_from_string(dumps(conf))


def create_user_dataset(user_email, project, dataset_name=None,
                        sandbox=False, expiration_ms=1000 * 60 * 60 * 24 * 7):
    client = bigquery.Client(project=project, location='EU')
    user_dataset = bigquery.Dataset(f'{project}.{dataset_name}')
    if sandbox:
        user_dataset.default_table_expiration_ms = expiration_ms
        user_dataset.default_partition_expiration_ms = expiration_ms

        # Set Editor access to user for his/her sandbox dataset
        entries = list(user_dataset.access_entries)
        entries.append(bigquery.AccessEntry(role='roles/bigquery.dataEditor',
                                            entity_type=bigquery.enums.EntityTypes.USER_BY_EMAIL,
                                            entity_id=user_email)
                       )
        user_dataset.access_entries = entries

    try:
        client.create_dataset(user_dataset)
    except Exception as e:
        utils_logger.error(f"Failed to create dataset {user_dataset} with exception {e}")
        raise Exception


def setup_user_iam(user_email):
    # Grant custom role to run queries (project-level bigquery.externaluser - bigquery.jobs.create permission)
    # roles/bigquery.jobUser --> this grants the bigquery.config.get permission that allows users to see project history (!!!)
    try:
        modify_policy_add_role(project_id=BACKEND_PROJECT,
                               role='projects/aix-backend-prod/roles/bigquery.externaluser',
                               member=f'user:{user_email}')
    except Exception as e:
        utils_logger.error(f"Failed to add role bigquery.externaluser to {user_email} with exception {e}")
        raise Exception
    utils_logger.info(f"Added role bigquery.externaluser to {user_email}")


def share_sample_dataset(sample_dataset, user_email, share_flag=True):
    # Useful BQ page address
    # https://console.cloud.google.com/bigquery?authuser=0&project=<PROJECT_ID>&p=<PROJECT_ID>&d=<DATASET_ID>&page=dataset
    # Set Viewer access to user for backend-shared dataset
    client = bigquery.Client(project=BACKEND_PROJECT, location='EU')
    shared_dataset = client.get_dataset(f'{BACKEND_PROJECT}.{sample_dataset}')
    shared_entries = list(shared_dataset.access_entries)
    if share_flag:
        shared_entries.append(bigquery.AccessEntry(role='roles/bigquery.dataViewer',
                                                   entity_type=bigquery.enums.EntityTypes.USER_BY_EMAIL,
                                                   entity_id=user_email)
                              )
    else:
        user_idx = None
        for idx, entry in enumerate(shared_entries):
            if entry.user_by_email == user_email:
                user_idx = idx
                break
        if user_idx:
            shared_entries.pop(user_idx)

    shared_dataset.access_entries = shared_entries
    try:
        client.update_dataset(shared_dataset, ['access_entries'])
        utils_logger.info(f"Updated shared dataset for {user_email}")
    except Exception as e:
        utils_logger.error(f"Failed to update shared dataset "
                           f"for {user_email} with exception: {e}")
        raise Exception


def setup_user_bigquery(user_email):
    try:
        dataset_name = f"ud_{''.join([choice(string.ascii_lowercase + string.digits) for _ in range(10)])}"
        create_user_dataset(user_email, 'aix-backend-prod', dataset_name=dataset_name, sandbox=True)
        utils_logger.info(f"Created dataset {dataset_name} in aix-backend-prod...")
        for _, challenge in CHALLENGES.items():
            create_user_dataset(user_email, challenge['project_name'], dataset_name=dataset_name, sandbox=False)
            utils_logger.info(f"Created dataset {dataset_name} in {challenge['project_name']}...")
            share_sample_dataset(challenge['backend_sample_dataset'], user_email)
            utils_logger.info(f"Shared dataset {challenge['backend_sample_dataset']}...")
        setup_user_iam(user_email)
        return dataset_name
    except Exception as e:
        utils_logger.error(f"Failed to create datasets with exception {e}")
        raise Exception

def setup_user_bucket(user_uid):
    try:
        storage_client = storage.Client(project='aix-website-prod')
    except Exception as e:
        utils_logger.error(f"Failed to get storage client for aix-website-prod with exception {e}")
        raise Exception
    bucket_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '_' + user_uid.lower()
    bucket = storage_client.bucket(bucket_name)
    bucket.storage_class = "STANDARD"
    storage_client.create_bucket(bucket, location="eu") # TODO: add security checks
    utils_logger.info(f"Created bucket {bucket_name}...")
    return bucket_name

def setup_user_registry(user_uid, user_email, user_name, bucket_name, dataset_name):
    insert_statement = "insert into public.user_registry values (\'" + user_uid + "\', \'" + \
                       user_email + "\', \'" + user_name + "\', \'" + str(datetime.datetime.now()) + "\', " + 'NULL' + ", \'" + \
                       bucket_name + "\', \'" + dataset_name + "\')"
    try:
        run_insert_statement(insert_statement)
        utils_logger.info(f"User registry setup successful for email {user_email}")
    except Exception as e:
        utils_logger.error(f"Failed to setup user registry for email {user_email} with exception {e}")
        raise Exception


def publish_on_pub_sub(event=None, user_email=None, user_id=None):
    publisher = pubsub_v1.PublisherClient()
    if event == 'new_user':
        topic_path = publisher.topic_path('aix-backend-prod', 'new-users')
    elif event == 'code_submission':
        topic_path = publisher.topic_path('aix-backend-prod', 'code-submissions')
    else:
        raise NotImplementedError
    data = str({"event": f'{str(event)}', "email": f'{str(user_email)}', "user": f'{str(user_id)}'}).encode("utf-8")
    future = publisher.publish(topic_path, data)
    utils_logger.info(f"Published message on event {event}: {future.result()}")


def update_user_credits_and_wallet():
    procedure_statement = "call user_current_credits_and_wallet()"
    run_insert_statement(procedure_statement)

def get_user_credits_and_wallet(user_uid):
    query_statement = "select credits, wallet from public.t_web_user_current_credits_and_wallet where user_id = \'" + user_uid + "\'"
    results = run_query(query_statement)
    return results[0][0], results[0][1]

def get_user_dataset(user_uid):
    query_statement = "select dataset_id from public.user_registry where user_id = \'" + user_uid + "\'"
    results = run_query(query_statement)
    return results[0][0]

def get_user_displayname(user_uid):
    query_statement = "select username from public.user_registry where user_id = \'" + user_uid + "\'"
    results = run_query(query_statement)
    return results[0][0]

def get_user_leaderboard(challenge):
    query_statement = f"select * from public.t_web_user_leaderboard where challenge=\'{challenge}\'"
    results = run_query(query_statement)
    leaderboard = {'user': [], 'weight': [], 'prize': []}
    for row in results:
        leaderboard['user'].append(row[0])
        leaderboard['weight'].append(str(round(float(row[3]), 4)))
        leaderboard['prize'].append(str(round(float(row[4]), 2)))
    return leaderboard

def get_user_bucket(user_uid):
    query_statement = "select bucket_id from public.user_registry where user_id = \'" + user_uid + "\'"
    results = run_query(query_statement)
    if len(results) > 1:
        raise ValueError("There is more than one bucket linked to the user.")
    return results[0][0]

def user_top_up(transaction_id, user_uid, amount, currency, timestamp):
    if transaction_id is None:
        sql_transaction_id = 'NULL'
    else:
        sql_transaction_id = f"\'{transaction_id}\'"
    procedure_statement = f"call user_top_up({sql_transaction_id}, \'{user_uid}\', {amount}, \'{currency}\', \'{timestamp}\')"
    try:
        run_insert_statement(procedure_statement)
        utils_logger.info(f"User top up successful for user_uid {user_uid}")
    except:
        utils_logger.error(f"User top up failed for user_uid {user_uid}")
        raise Exception

def delete_user_account(user_uid):

    user_email = get_user_email(user_uid)

    # Delete BQ datasets (both sample and full)
    from google.cloud import bigquery
    user_dataset = get_user_dataset(user_uid)
    bigquery.Client(project='aix-backend-prod', location='EU').delete_dataset(dataset=user_dataset,
                                                                              delete_contents=True)
    utils_logger.info(f"Deleted dataset {user_dataset} in aix-backend-prod")
    for _, challenge in CHALLENGES.items():
        bigquery.Client(project=challenge['project_name'], location='EU')\
            .delete_dataset(dataset=get_user_dataset(user_uid), delete_contents=True)
        utils_logger.info(f"Deleted dataset {user_dataset} in {challenge['project_name']}")
        share_sample_dataset(challenge['backend_sample_dataset'], user_email, share_flag=False)

    # Delete IAM permissions
    try:
        modify_policy_remove_role(project_id=BACKEND_PROJECT,
                                  role='projects/aix-backend-prod/roles/bigquery.externaluser',
                                  member=f'user:{user_email}')
    except Exception as e:
        utils_logger.error(f"Failed to remove role bigquery.externaluser to {user_email} with exception {e}")
        raise Exception
    utils_logger.info(f"Removed role bigquery.externaluser to {user_email}")

    # Delete bucket
    from google.cloud import storage
    storage_client = storage.Client(project='aix-website-prod')
    bucket_name = get_user_bucket(user_uid)
    bucket = storage_client.get_bucket(bucket_name)
    blob_list = list(bucket.list_blobs())
    for blob in blob_list:
        blob.delete()
    bucket.delete()

    # Update user registry with deletion date
    # Connect to your postgres DB
    user_query_statement = f"update public.user_registry set deleted_on = \'{str(datetime.datetime.now())}\' where user_id = \'{user_uid}\'"
    run_insert_statement(user_query_statement)

def check_upload_time_window_eligible(challenge):
    current_timestamp = datetime.datetime.utcnow()
    eligibility_interval = CHALLENGES[challenge]['upload_window']

    # Extract info from current timestamp
    current_weekday = current_timestamp.isoweekday()
    current_hour = current_timestamp.hour

    # Check eligibility (should be between start and end)
    if (eligibility_interval['start']['weekday'] < current_weekday < eligibility_interval['end']['weekday']) or \
       (current_weekday == eligibility_interval['start']['weekday'] and eligibility_interval['start']['hour'] <= current_hour) or \
       (current_weekday == eligibility_interval['end']['weekday'] and current_hour < eligibility_interval['end']['hour']):
        return True, None
    else:
        next_interval_start = current_timestamp.replace(hour=0, minute=0, second=0, microsecond=0) + \
                              datetime.timedelta(days=abs(current_weekday - eligibility_interval['start']['weekday'])) + \
                              datetime.timedelta(hours=eligibility_interval['start']['hour'])
        return False, next_interval_start.strftime("%Y-%m-%d %H:%M") + " UTC"

def check_running_user_job(user_uid=None, challenge=None):
    user_bucket = get_user_bucket(user_uid)
    storage_client = storage.Client(project='aix-website-prod')
    blobs = list(storage_client.list_blobs(bucket_or_name=user_bucket, prefix=f'{challenge}/running_job'))
    if blobs:
        return True
    return False

def get_user_email(user_uid):
    query_statement = "select user_email from public.user_registry where user_id = \'" + user_uid + "\'"
    results = run_query(query_statement)
    return results[0][0]
