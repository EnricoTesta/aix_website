# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python38_render_template]
# [START gae_python3_render_template]
import datetime
from flask import Flask, render_template, request, Response
from google.auth.transport import requests
from json import loads
import google.oauth2.id_token

import utils
from utils import *

from globals import CHALLENGES


app = Flask(__name__)

flask_logger = getLogger('flask_logger')

USER_STARTING_CREDITS = 10
BACKEND_PROJECT = 'aix-backend-prod'
BACKEND_SAMPLE_DATA_DATASET = 'sample_data'
firebase_request_adapter = requests.Request()

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/')
def root():
    return render_template('home.html')

@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')

@app.route('/video')
def video():
    return render_template('video.html')

@app.route('/challenges')
def challenges():
    return render_template('challenges.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/buy_credits')
def buy_credits():
    return render_template('buy_credits.html')

@app.route('/forgot_password')
def forgot():
    return render_template('forgot_password.html')

@app.route('/resend_verification_email')
def resend_verification_email():
    return render_template('resend_verification_email.html')

@app.route('/profile')
def profile():
    # Verify Firebase auth.
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None

    if id_token:
        try:
            # Verify the token against the Firebase Auth API. This example
            # verifies the token on each page load. For improved performance,
            # some applications may wish to cache results in an encrypted
            # session store (see for instance
            # http://flask.pocoo.org/docs/1.0/quickstart/#sessions).
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)
        except ValueError as exc:
            # This will be raised if the token is expired or any other
            # verification checks fail.
            error_message = str(exc)

        # Record and fetch the recent times a logged-in user has accessed
        # the site. This is currently shared amongst all users, but will be
        # individualized in a following step.

        #store_time(datetime.datetime.now())
        #times = fetch_times(10)
        return render_template('profile.html', user_data=claims, error_message=error_message)
    else:
        return Response(response='Access Denied: you must be logged in to access the Profile page.', status=400, mimetype='application/json')
    #return render_template(
    #    'profile.html',
    #    user_data=claims, error_message=error_message, times=times)

@app.route('/backend_get_leaderboard', methods=['POST'])
def backend_get_leaderboard():
    challenge = request.form['challenge'].replace("\'", "")
    try:
        l = get_user_leaderboard(CHALLENGES[challenge]['name'])
        return Response(response=dumps(l), status=200, mimetype='application/json')
    except:
        return Response(response=dumps({}), status=400, mimetype='application/json')
@app.route('/backend_get_user_displayname', methods=['POST'])
def backend_get_user_displayname():
    try:
        user = request.form['user'].replace("\'", "")
        display_name = get_user_displayname(user)
        return Response(response=dumps({'display_name': str(display_name)}), status=200, mimetype='application/json')
    except:
        Response(response='Failure', status=400, mimetype='application/json')


@app.route('/backend_user_setup', methods=['POST'])
def backend_user_setup():
    flask_logger.info("Starting user setup...")
    try:
        data = request.get_json()
        dataset_name = setup_user_bigquery(user_email=data['user_email'])
        bucket_name = setup_user_bucket(data['user'])
        setup_user_registry(user_uid=data['user'], user_email=data['user_email'],
                            user_name=data['user_name'], bucket_name=bucket_name, dataset_name=dataset_name)
        user_top_up(transaction_id=None, user_uid=data['user'],
                    amount=USER_STARTING_CREDITS, currency='USD',
                    timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H%M%S'))  # each new user starts with 10 credits
        update_user_credits_and_wallet()
        publish_on_pub_sub(event='new_user', user_email=data['user_email'])
        return Response(response='Success', status=200, mimetype='application/json')
    except Exception as e:
        return Response(response='Failure' + str(e), status=400, mimetype='application/json')

@app.route('/backend_delete_user', methods=['POST'])
def backend_delete_user():
    user = request.form['user'].replace("\'", "")
    try:
        delete_user_account(user)
        return Response(response='Success', status=200, mimetype='application/json')
    except Exception as e:
        return Response(response='Failure' + str(e), status=400, mimetype='application/json')

@app.route('/backend_get_job_running_status', methods=['POST'])
def backend_get_job_running_status():
    try:
        user = request.form['user'].replace("\'", "")
        challenge = request.form['challenge'].replace("\'", "")
        destination_bucket_name = get_user_bucket(user)
        storage_client = storage.Client()
        blob_list = list(storage_client.list_blobs(destination_bucket_name, prefix=f'{challenge}/running_job/'))
        if blob_list:
            return Response(response='Yes', status=200, mimetype='application/json')
        return Response(response='No', status=200, mimetype='application/json')
    except:
        return Response(response='Failure', status=400, mimetype='application/json')

@app.route('/backend_update_db', methods=['POST'])
def backend_update_db():
    try:
        user = request.form['user'].replace("\'", "")
        order_data = loads(request.form['order_data'])
        if order_data['status'] == 'COMPLETED':
            amount = 0
            for item in order_data['purchase_units']: # always 1 element
                amount += float(item['amount']['value'])
            user_top_up(order_data['id'], user, amount, item['amount']['currency_code'], order_data['create_time'])
            update_user_credits_and_wallet()
            return Response(response='Success', status=200, mimetype='application/json')
        #TODO: setup a table for order data and send replicate all order data 1:1
        return Response(response='Success-No Top up', status=200, mimetype='application/json')
    except:
        Response(response='Failure', status=400, mimetype='application/json')

@app.route('/backend_get_user_credits_and_wallet', methods=['POST'])
def backend_get_user_credits_and_wallet():
    try:
        user = request.form['user'].replace("\'", "")
        credits, wallet = get_user_credits_and_wallet(user)
        return Response(response=dumps({'credits': str(credits), 'wallet': str(wallet)}), status=200, mimetype='application/json')
    except:
        Response(response='Failure', status=400, mimetype='application/json')

@app.route('/backend_activate_submission', methods=['POST'])
def backend_activate_submission():
    try:
        user = request.form['user'].replace("\'", "")
        challenge = request.form['challenge'].replace("\'", "")

        # Check credit availability
        credits_check_query = f"select credits from t_web_user_current_credits_and_wallet where user_id = \'{user}\'"
        user_credits = run_query(credits_check_query)[0][0]
        if user_credits <= 0:
            return Response(response='Failure - Insufficient Credits', status=401, mimetype='application/json')

        destination_bucket_name = get_user_bucket(user)
        storage_client = storage.Client()

        # Check code presence
        code_blobs = list(storage_client.list_blobs(bucket_or_name=destination_bucket_name, prefix=f'{challenge}/code/'))
        if not code_blobs:
            return Response(response='Failure - No code found. You must upload code to join current round.',
                            status=402, mimetype='application/json')

        # Check artifact quality
        quality_blobs = list(storage_client.list_blobs(bucket_or_name=destination_bucket_name, prefix=f'{challenge}/quality/'))
        if not quality_blobs:
            return Response(response='Failure - Quality certificate not found. Please review requirements.',
                            status=403, mimetype='application/json')

        # Check there are no quality issues (this should be redundant but it's not. There are some cases in which
        # even if there are quality issues a quality certificate is issued)
        issues_blobs = list(storage_client.list_blobs(bucket_or_name=destination_bucket_name,
                                                      prefix=f'{challenge}/quality_issues/'))
        if issues_blobs:
            return Response(response='Failure - Code quality issues found. Please review requirements.',
                            status=403, mimetype='application/json')

        bucket = storage_client.get_bucket(destination_bucket_name)
        blob = bucket.blob(f'{challenge}/active/active.txt')
        with blob.open(mode='w') as mf:
            mf.write("")
        return Response(response='Success', status=200, mimetype='application/json')
    except:
        return Response(response='Failure', status=400, mimetype='application/json')

@app.route('/backend_get_submission_status', methods=['POST'])
def backend_get_submission_status():
    try:
        user = request.form['user'].replace("\'", "")
        challenge = request.form['challenge'].replace("\'", "")
        destination_bucket_name = get_user_bucket(user)
        storage_client = storage.Client()
        blob_list = list(storage_client.list_blobs(destination_bucket_name, prefix=f'{challenge}/active/'))
        if blob_list:
            return Response(response='Yes', status=200, mimetype='application/json')
        return Response(response='No', status=200, mimetype='application/json')
    except:
        return Response(response='Failure', status=400, mimetype='application/json')

@app.route('/backend_deactivate_submission', methods=['POST'])
def backend_deactivate_submission():
    try:
        user = request.form['user'].replace("\'", "")
        challenge = request.form['challenge'].replace("\'", "")
        destination_bucket_name = get_user_bucket(user)
        storage_client = storage.Client()
        full_blob_list = list(storage_client.list_blobs(destination_bucket_name, prefix=f'{challenge}/active/'))
        for blob in full_blob_list:
            blob.delete()
        return Response(response='Success', status=200, mimetype='application/json')
    except:
        return Response(response='Failure', status=400, mimetype='application/json')

@app.route('/backend_get_metrics', methods=['POST'])
def backend_get_metrics():
    try:
        user = request.form['user'].replace("\'", "")
        challenge = request.form['challenge'].replace("\'", "")
        destination_bucket_name = get_user_bucket(user)
        storage_client = storage.Client()
        bucket = storage_client.bucket(destination_bucket_name)
        try:
            blob = bucket.blob(f'{challenge}/model_evaluations/eval_metrics.json')
            response_dict = loads(blob.download_as_text())
            for k, v in response_dict.items():
                response_dict[k] = str(round(float(response_dict[k]), 5))
            return Response(response=dumps(response_dict), status=200, mimetype='application/json')
        except:
            return Response(response=dumps({'N/A': ''}), status=200, mimetype='application/json')
    except:
        return Response(response='Failure', status=400, mimetype='application/json')

@app.route('/backend_get_code_quality', methods=['POST'])
def backend_get_code_quality():
    try:
        user = request.form['user'].replace("\'", "")
        challenge = request.form['challenge'].replace("\'", "")
        destination_bucket_name = get_user_bucket(user)
        storage_client = storage.Client()
        issues_list = list(storage_client.list_blobs(destination_bucket_name, prefix=f'{challenge}/quality_issues/'))
        quality_list = list(storage_client.list_blobs(destination_bucket_name, prefix=f'{challenge}/quality/'))
        if issues_list:
            for item in issues_list:
                if item.name.endswith(".json"):
                    response_dict = loads(item.download_as_text())
                    response_dict['Quality'] = 'KO'
                    return Response(response=dumps(response_dict), status=200, mimetype='application/json')
        elif quality_list:
            return Response(response=dumps({'Quality': 'OK'}), status=200, mimetype='application/json')
        else:
            # No code runs
            return Response(response=dumps({'Quality': 'N/A'}), status=200, mimetype='application/json')
    except:
        return Response(response='Failure', status=400, mimetype='application/json')

@app.route('/backend_get_logs', methods=['POST'])
def backend_get_logs():
    try:
        user = request.form['user'].replace("\'", "")
        challenge = request.form['challenge'].replace("\'", "")
        destination_bucket_name = get_user_bucket(user)
        storage_client = storage.Client()
        full_blob_list = list(storage_client.list_blobs(destination_bucket_name, prefix=f'{challenge}'))
        relevant_blobs = [b for b in full_blob_list if b.name.endswith('.log')]
        string_response = ''
        for item in relevant_blobs:
            string_response += item.download_as_text()
            string_response += '\n'
        return Response(response=string_response, status=200, mimetype='application/json')
    except:
        return Response(response='Failure', status=400, mimetype='application/json')

@app.route('/backend_upload_file', methods=['POST'])
def backend_upload_file():
    try:
        file_to_upload = request.files['file']
        user = request.form['user'].replace("\'", "")
        challenge = request.form['challenge'].replace("\'", "")

        # Check upload window
        eligible, starting_from = check_upload_time_window_eligible(challenge)
        if not eligible:
            return Response(response=f'Failure - Out of upload window. You may upload again starting from {starting_from}',
                            status=402, mimetype='application/json')

        # Check running user_job
        if check_running_user_job(user, challenge):
            return Response(response='Failure - Job running. You may upload again after your current job is done.',
                            status=403, mimetype='application/json')

        #TODO: check file suffix + file size

        # Check credits
        credits_check_query = f"select credits from t_web_user_current_credits_and_wallet where user_id = \'{user}\'"
        user_credits = run_query(credits_check_query)[0][0]
        if user_credits <= 0:
            return Response(response='Failure - Insufficient Credits', status=401, mimetype='application/json')

        # Get user's bucket
        destination_bucket_name = get_user_bucket(user)
        storage_client = storage.Client(project='aix-website-prod')
        bucket = storage_client.bucket(destination_bucket_name)

        # Erase any existing content (ensure at most 1 file at any given time)
        bucket.delete_blobs([b for b in bucket.list_blobs(prefix=challenge)])

        # Upload file to bucket
        blob = bucket.blob(f'{challenge}/code/{file_to_upload.filename}')
        blob.upload_from_file(file_to_upload)

        # Erase from data bucket (artifacts and evaluations)
        data_bucket_name = CHALLENGES[challenge]['bucket']
        storage_client = storage.Client(project=CHALLENGES[challenge]['project_name'])
        bucket = storage_client.bucket(data_bucket_name)
        bucket.delete_blobs([b for b in bucket.list_blobs(prefix=f'{challenge}/artifacts/{user}/')])
        bucket.delete_blobs([b for b in bucket.list_blobs(prefix=f'{challenge}/evaluation/{user}/')])

        # Write DAG request User_Job_Dag
        dag_conf = build_dag_conf(user, challenge)
        run_id = user + '-' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        write_dag_run_request(dag=f'{challenge}_user_job', run_id=run_id, conf=dag_conf, bucket_name=data_bucket_name)

        # Publish event on Pub/Sub
        publish_on_pub_sub(event='code_submission', user_id=user)

        return Response(response='Success', status=200, mimetype='application/json')
    except:
        return Response(response='Failure', status=400, mimetype='application/json')

@app.route('/backend_get_prize_round_number', methods=['POST'])
def get_prize_round_number():
    challenge = request.form['challenge'].replace("\'", "")
    query_statement = f"select distinct ref_date from t_web_user_leaderboard where challenge=\'{challenge}\'"
    try:
        result = utils.run_query(query_statement)[0][0]
        if CHALLENGES[challenge]['frequency'] == 'weekly':
            result = result.isocalendar()
            d = {'round_number': str(result[0]) + '/' + str(result[1])}
        elif CHALLENGES[challenge]['frequency'] == 'monthly':
            d = {'round_number': str(result.year) + '/' + str(result.month)}
        else:
            raise ValueError(f"Challenge frequency can be 'weekly' or 'monthly',"
                             f" got {CHALLENGES[challenge]['frequency']}")
        return Response(response=dumps(d), status=200, mimetype='application/json')
    except Exception:
        return Response(response=dumps({'round_number': 'N/A'}), status=200, mimetype='application/json')

@app.route('/backend_get_user_dataset', methods=['POST'])
def backend_get_user_dataset():
    user = request.form['user'].replace("\'", "")
    try:
        dataset = get_user_dataset(user)
        return Response(response=dataset, status=200, mimetype='application/json')
    except:
        return Response(response='Failure', status=400, mimetype='application/json')


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    debug_flag = True
    if os.environ.get("GAE_ENV") == "standard":
        debug_flag = False
    app.run(host='0.0.0.0', port=8080, debug=debug_flag)  # default is 127.0.0.1, however it's not open to the network
# [END gae_python3_render_template]
# [END gae_python38_render_template]
