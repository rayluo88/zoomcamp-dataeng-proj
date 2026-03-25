"""
Phase 2 — Batch Ingestion: IEEE-CIS Fraud Detection → GCS → BigQuery

Flow:
  1. Download dataset from Kaggle (if not already present)
  2. Convert CSVs to Parquet (faster BigQuery loads, ~3x smaller)
  3. Upload Parquet files to GCS raw/ layer
  4. Create external BigQuery tables pointing to GCS files
"""

import os
import zipfile
import logging
from pathlib import Path

import pandas as pd
from google.cloud import storage, bigquery
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "financial-risk-control-system")
BUCKET_NAME = os.getenv("GCS_BUCKET", "financial-risk-control-system-datalake")
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials/pipeline-sa-key.json")
KAGGLE_COMPETITION = "ieee-fraud-detection"

DATA_DIR = Path("data")
RAW_GCS_PREFIX = "raw/ieee_cis"

# Tables to ingest: (csv_name, bq_table_name)
TABLES = [
    ("train_transaction.csv", "train_transaction"),
    ("train_identity.csv", "train_identity"),
]

# ── Step 1: Download from Kaggle ───────────────────────────────────────────────

def download_dataset():
    zip_path = DATA_DIR / f"{KAGGLE_COMPETITION}.zip"
    if zip_path.exists():
        log.info("Zip already downloaded, skipping.")
    else:
        log.info("Downloading dataset from Kaggle...")
        DATA_DIR.mkdir(exist_ok=True)
        os.system(f"kaggle competitions download -c {KAGGLE_COMPETITION} -p {DATA_DIR}")

    log.info("Extracting zip...")
    with zipfile.ZipFile(zip_path, "r") as z:
        for csv_name, _ in TABLES:
            if not (DATA_DIR / csv_name).exists():
                z.extract(csv_name, DATA_DIR)
                log.info(f"Extracted {csv_name}")

# ── Step 2: Convert CSV → Parquet ─────────────────────────────────────────────

def to_parquet(csv_name: str) -> Path:
    csv_path = DATA_DIR / csv_name
    parquet_path = DATA_DIR / csv_name.replace(".csv", ".parquet")

    if parquet_path.exists():
        log.info(f"{parquet_path} already exists, skipping conversion.")
        return parquet_path

    log.info(f"Converting {csv_name} → parquet...")
    df = pd.read_csv(csv_path)
    df.to_parquet(parquet_path, index=False, engine="pyarrow")
    log.info(f"Saved {parquet_path} ({parquet_path.stat().st_size / 1e6:.1f} MB)")
    return parquet_path

# ── Step 3: Upload to GCS ─────────────────────────────────────────────────────

def upload_to_gcs(local_path: Path, gcs_prefix: str):
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)
    blob_name = f"{gcs_prefix}/{local_path.name}"
    blob = bucket.blob(blob_name)

    if blob.exists():
        log.info(f"gs://{BUCKET_NAME}/{blob_name} already exists, skipping upload.")
        return f"gs://{BUCKET_NAME}/{blob_name}"

    log.info(f"Uploading {local_path} → gs://{BUCKET_NAME}/{blob_name} ...")
    blob.upload_from_filename(str(local_path))
    log.info("Upload complete.")
    return f"gs://{BUCKET_NAME}/{blob_name}"

# ── Step 4: Create BigQuery external table ────────────────────────────────────

def create_bq_external_table(gcs_uri: str, table_name: str):
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.raw.{table_name}"

    external_config = bigquery.ExternalConfig("PARQUET")
    external_config.source_uris = [gcs_uri]
    external_config.autodetect = True

    table = bigquery.Table(table_ref)
    table.external_data_configuration = external_config

    client.delete_table(table_ref, not_found_ok=True)
    client.create_table(table)
    log.info(f"Created external table {table_ref} → {gcs_uri}")

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH

    download_dataset()

    for csv_name, bq_table in TABLES:
        parquet_path = to_parquet(csv_name)
        gcs_uri = upload_to_gcs(parquet_path, RAW_GCS_PREFIX)
        create_bq_external_table(gcs_uri, bq_table)

    log.info("Ingestion complete. Run: bq query 'SELECT COUNT(*) FROM raw.train_transaction'")

if __name__ == "__main__":
    main()
