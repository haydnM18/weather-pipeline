from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/home/koopa/weather-pipeline')

from ingestion.ingest_weather import main as ingest
from ingestion.transform import transform

default_args = {
    'owner': 'intern',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='weather_pipeline',
    default_args=default_args,
    schedule='@hourly',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['portfolio', 'weather'],
) as dag:

    t1 = PythonOperator(
        task_id='ingest_weather_api',
        python_callable=ingest,
    )

    t2 = PythonOperator(
        task_id='transform_to_star_schema',
        python_callable=transform,
    )

    t1 >> t2
