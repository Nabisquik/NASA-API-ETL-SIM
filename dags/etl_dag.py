import os
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount
from datetime import datetime

from insert_records import main # sys.path appened using docker.yaml PYTHONPATH

default_args = {
    'description': 'A DAG to orchestrate data',
    'start_date': datetime(2025, 12, 10),
    'catchup':False,
    'schedule_interval': '@once',
}

dag = DAG(
    dag_id = "NASA-API-dbt-Orchestrator",
    default_args = default_args
)

PROJECT_ROOT = os.getenv('PROJECT_ROOT') 
DBT_NETWORK = os.getenv('DBT_NETWORK')

with dag:
    # Task 1: API pull and store in Postgres
    fetch_and_store = PythonOperator(
        task_id="API_Ingest_Store",
        python_callable=main
    )

    # Task 2: Transform - Load w/ dbt
    task2 = DockerOperator(
        task_id='transform_data_task',
        image = 'ghcr.io/dbt-labs/dbt-postgres:1.9.latest',
        command='run',
        working_dir = '/usr/app',
        mounts = [
           Mount(source = os.path.join(PROJECT_ROOT, 'dbt', 'my_project'),
                 target = '/usr/app',
                 type = 'bind'),
            Mount(source = os.path.join(PROJECT_ROOT, 'dbt', 'profiles.yml'),
                  target = '/root/.dbt/profiles.yml',
                  type = 'bind'),     
        ],
        network_mode = DBT_NETWORK,
        docker_url = 'unix://var/run/docker.sock',
        auto_remove = 'success',
        environment={
            # Explicitly pass Postgres credentials and dbt env
            'POSTGRES_DB': os.getenv('POSTGRES_DB'),
            'POSTGRES_USER': os.getenv('POSTGRES_USER'),
            'POSTGRES_PASSWORD': os.getenv('POSTGRES_PASSWORD'),
            'POSTGRES_HOST': os.getenv('POSTGRES_HOST', 'db'),
            'DBT_PROFILES_DIR': '/root/.dbt'
        }
    )

    fetch_and_store >> task2