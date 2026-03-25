"""
Airflow DAG: risk_batch_ingest
Orchestrates the full batch ingestion pipeline for IEEE-CIS fraud data.

Tasks:
  1. download_dataset  — pull from Kaggle if not cached
  2. convert_to_parquet — CSV → Parquet
  3. upload_to_gcs     — push Parquet files to GCS raw/ layer
  4. create_bq_tables  — create/refresh BigQuery external tables
"""

from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
import sys, os

sys.path.insert(0, "/opt/airflow/scripts")
from ingest_to_gcs import download_dataset, to_parquet, upload_to_gcs, create_bq_external_table
from pathlib import Path

RAW_GCS_PREFIX = "raw/ieee_cis"
TABLES = [
    ("train_transaction.csv", "train_transaction"),
    ("train_identity.csv", "train_identity"),
]

with DAG(
    dag_id="risk_batch_ingest",
    description="IEEE-CIS fraud data: Kaggle → GCS → BigQuery",
    schedule_interval="@once",   # change to @daily for incremental datasets
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["risk", "ingestion", "batch"],
) as dag:

    download = PythonOperator(
        task_id="download_dataset",
        python_callable=download_dataset,
    )

    def _convert_all():
        for csv_name, _ in TABLES:
            to_parquet(csv_name)

    convert = PythonOperator(
        task_id="convert_to_parquet",
        python_callable=_convert_all,
    )

    def _upload_all():
        uris = {}
        for csv_name, bq_table in TABLES:
            parquet_path = Path("data") / csv_name.replace(".csv", ".parquet")
            uri = upload_to_gcs(parquet_path, RAW_GCS_PREFIX)
            uris[bq_table] = uri
        return uris

    upload = PythonOperator(
        task_id="upload_to_gcs",
        python_callable=_upload_all,
    )

    def _create_tables(**context):
        uris = context["ti"].xcom_pull(task_ids="upload_to_gcs")
        for _, bq_table in TABLES:
            gcs_uri = uris[bq_table]
            create_bq_external_table(gcs_uri, bq_table)

    create_tables = PythonOperator(
        task_id="create_bq_tables",
        python_callable=_create_tables,
        provide_context=True,
    )

    download >> convert >> upload >> create_tables
