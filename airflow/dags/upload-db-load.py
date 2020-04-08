from airflow import DAG
from datetime import datetime, timedelta
import os

from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
# Helper Imports
from lib.configuration import get_config, get_backup_command, get_loader_command
from updater.callbacks import airflow_task_success, airflow_task_failure
from updater.create_databases.rename_db import begin_rename

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime.now(),
    'email': ['contact@patentsview.org'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 10,
    'retry_delay': timedelta(minutes=5),
    'concurrency': 4
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
}

upload_dag = DAG(
    'upload_db_creation',
    description='Upload CSV files to database',
    start_date=datetime(2020, 1, 1, 0, 0, 0),
    catchup=True,
    schedule_interval=None)
project_home = os.environ['PACKAGE_HOME']
config = get_config()

backup_old_db = BashOperator(dag=upload_dag, task_id='backup_olddb',
                             bash_command=get_backup_command(config, project_home),
                             on_success_callback=airflow_task_success,
                             on_failure_callback=airflow_task_failure)

rename_old_operator = PythonOperator(task_id='rename_db', python_callable=begin_rename, op_kwargs={'config': config},
                                     dag=upload_dag, on_success_callback=airflow_task_success,
                                     on_failure_callback=airflow_task_failure
                                     )

restore_old_db = BashOperator(dag=upload_dag, task_id='restore_olddb',
                              bash_command=get_loader_command(config, project_home),
                              on_success_callback=airflow_task_success,
                              on_failure_callback=airflow_task_failure)
rename_old_operator.set_upstream(backup_old_db)
restore_old_db.set_upstream(rename_old_operator)
