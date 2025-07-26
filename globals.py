from yaml import safe_load
from pathlib import Path
import os


DEPLOYMENT_TYPE = os.getenv('AIRFLOW_ENV')

CHALLENGES = {}
dirs = [dir.name for dir in os.scandir(os.path.join(Path(__file__).parent.resolve(), 'challenges'))]
for dir_name in dirs:
    with open(os.path.join(Path(__file__).parent.resolve(), f'challenges/{dir_name}/{dir_name}.yaml'), 'r') as f:
        CHALLENGES[dir_name] = safe_load(f)

    if DEPLOYMENT_TYPE is None:
        path_to_file = os.path.join(Path(__file__).parent.resolve(),
                                    f'challenges/{dir_name}/environment/prod/cloud.yaml')
    elif DEPLOYMENT_TYPE == 'DEV':
        path_to_file = os.path.join(Path(__file__).parent.resolve(),
                                    f'challenges/{dir_name}/environment/dev/cloud.yaml')
    else:
        raise ValueError(f"Unknown deployment {DEPLOYMENT_TYPE}")

    with open(path_to_file, 'r') as f:
        CLOUD = safe_load(f)

    CHALLENGES[dir_name] = {**CHALLENGES[dir_name], **CLOUD}
