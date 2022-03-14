
import airflow
import os
import psycopg2
from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python_operator import PythonOperator
from airflow.hooks.postgres_hook import PostgresHook
from datetime import timedelta
from datetime import datetime
import pandas as pd
from google.cloud import storage
import fsspec as fs





#TODO make everything dynamic, like passing in the filename, the bucket, others...


def csv2postgres():
    uri = r"gs://landing_bucket_wizeline_project/user_purchase.csv"#TODO should be passed as Pub/Sub message


#    pg_hook=PostgresHook(postgres_conn_id='dd-database')
    get_postgres_conn=PostgresHook(postgres_conn_id='dd-database').get_conn()
    curr=get_postgres_conn.cursor()
   
    of = fs.open(uri, "rt")

    # client = storage.Client(credentials='google_cloud_storage_default')
    # # https://console.cloud.google.com/storage/browser/[bucket-id]/
    # bucket = client.get_bucket('landing_bucket_wizeline_project')
    # # Then do other things...
    # blob = bucket.blob(file)

    # with of as f:
    #     next(f)
    #     curr.copy_from(f,'datadriven_raw.user_purchase',sep=",")
    #     get_postgres_conn.commit()

    with of as f:
     curr.copy_expert("COPY datadriven_raw.user_purchase FROM STDIN WITH CSV HEADER", f)
     get_postgres_conn.commit()    



one_day_ago = datetime.combine(
    datetime.today() - timedelta(1),
    datetime.min.time()
)




default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': one_day_ago,
    'email': ['fjcristanchov@unal.edu.co'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'catchup': False,
    'retry_delay': timedelta(minutes=1),
  
}

#tasks
dag = DAG('postgres_write',
          default_args=default_args,
          schedule_interval=None,
          catchup=False
          )


task1=PostgresOperator(
    task_id='create_table'
    ,sql= 
        """
        CREATE SCHEMA IF NOT EXISTS datadriven_raw;
        CREATE TABLE IF NOT EXISTS datadriven_raw.user_purchase(
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
    ,postgres_conn_id='dd-database'
    ,autocommit=True
    ,dag=dag
    )

task2=PythonOperator(task_id='csv2database'
            ,provide_context=True
            ,python_callable=csv2postgres
            ,dag=dag
            )

task1>>task2