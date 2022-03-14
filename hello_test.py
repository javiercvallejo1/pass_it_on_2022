from datetime import datetime, timedelta
from airflow.models import DAG
from airflow.operators.python_operator import PythonOperator
one_day_ago = datetime.combine(
    datetime.today() - timedelta(1),
    datetime.min.time()
)
def say_hello():
    print("Hello GCPower")
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': one_day_ago,
    'email': ['cmadrigal@videoamp.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 0,
    'catchup': False,
    'retry_delay': timedelta(minutes=5),
    'provide_context': True
}
dag = DAG('GREETING_TEST',
          default_args=default_args,
          schedule_interval=None,
          catchup=False,
          max_active_runs=1
          )
with dag:
    greeting = PythonOperator(
        task_id="say_hello",
        python_callable=say_hello
    )
    greeting