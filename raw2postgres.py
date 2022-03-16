
import airflow
import os
import psycopg2
from airflow import DAG
from airflow.providers.google.cloud.transfers.gcs_to_gcs import GCSToGCSOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from airflow.hooks.postgres_hook import PostgresHook
from datetime import timedelta
from datetime import datetime
import pandas as pd
from google.cloud import storage
import fsspec as fs





#TODO make everything dynamic, like passing in the filename, the bucket, others...


def csv2postgres():
    uri = r"gs://raw_med_pass_it_on/raw_user_purchase.csv"#TODO should be passed as Pub/Sub message


#    pg_hook=PostgresHook(postgres_conn_id='dd-database')
    get_postgres_conn=PostgresHook(postgres_conn_id='pass-it-on').get_conn()
    curr=get_postgres_conn.cursor()
   
    of = fs.open(uri, "rt")

    with of as f:
     curr.copy_expert("COPY passiton_raw.user_purchase FROM STDIN WITH CSV HEADER", f)
     get_postgres_conn.commit()    



one_day_ago = datetime.combine(
    datetime.today() - timedelta(1),
    datetime.min.time()
)




default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': one_day_ago,
    'email': ['javiercvallejo1@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'catchup': False,
    'retry_delay': timedelta(minutes=1),
  
}


#tasks
dag = DAG('postgres_write',
          default_args=default_args,
          schedule_interval='0 8 * * *',
          catchup=False
          )

begin = DummyOperator(
    task_id='Begin',
    dag=dag)

end = DummyOperator(
    task_id='End',
    trigger_rule='none_failed',
    dag=dag)



move_file = GCSToGCSOperator(
    task_id="copy_single_gcs_file",
    source_bucket='ldn-med-pass-it-on',
    source_object='user_purchase.csv',
    destination_bucket='raw-med-pass-it-on',  # If not supplied the source_bucket value will be used
    destination_object="raw_" + 'user_purchase.csv',  # If not supplied the source_object value will be used
    dag=dag
)

task1=PostgresOperator(
    task_id='create_table'
    ,sql= 
        """
        CREATE SCHEMA IF NOT EXISTS passiton_raw;
        CREATE TABLE IF NOT EXISTS passiton_raw.user_purchase(
            invoice_number VARCHAR(10)
            ,stock_code VARCHAR(20)
            ,detail VARCHAR(1000)
            ,quantity INT
            ,invoice_date TIMESTAMP
            ,unit_price NUMERIC(8,3)
            ,customer_id INT
            ,country VARCHAR(20)

            );
        """
    ,postgres_conn_id='pass-it-on'
    ,autocommit=True
    ,dag=dag
    )

task2=PythonOperator(task_id='csv2database'
            ,provide_context=True
            ,python_callable=csv2postgres
            ,dag=dag
            )

begin>>move_file>>task1>>task2>>end