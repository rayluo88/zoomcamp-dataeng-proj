"""
IEEE-CIS Fraud Detection — Redpanda consumer.

Reads messages from topic `ieee_cis_transactions`, batches them, and writes:
  - GCS:       gs://<bucket>/raw/stream/YYYY/MM/DD/HH/batch_<ts>.json.gz
  - BigQuery:  raw.stream_transactions (streaming insert)

Usage:
    uv run python redpanda/consumer.py [--broker HOST] [--batch-size N]

Options:
    --broker HOST        Kafka broker (default localhost:9092)
    --batch-size N       Messages per GCS file / BQ insert batch (default 500)
    --gcs-bucket BUCKET  GCS bucket name (default financial-risk-control-system-datalake)
    --bq-project PROJECT BigQuery project (default financial-risk-control-system)
    --bq-dataset DATASET BigQuery dataset (default raw)
    --bq-table TABLE     BigQuery table (default stream_transactions)
    --no-gcs             Skip GCS writes
    --no-bq              Skip BigQuery writes
"""

import argparse
import gzip
import json
import os
import sys
from datetime import datetime, timezone
from io import BytesIO

from google.cloud import bigquery, storage
from kafka import KafkaConsumer

TOPIC = "ieee_cis_transactions"
DEFAULT_BUCKET = "financial-risk-control-system-datalake"
DEFAULT_PROJECT = "financial-risk-control-system"
DEFAULT_DATASET = "raw"
DEFAULT_TABLE = "stream_transactions"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--broker", default="localhost:9092")
    p.add_argument("--batch-size", type=int, default=500)
    p.add_argument("--gcs-bucket", default=DEFAULT_BUCKET)
    p.add_argument("--bq-project", default=DEFAULT_PROJECT)
    p.add_argument("--bq-dataset", default=DEFAULT_DATASET)
    p.add_argument("--bq-table", default=DEFAULT_TABLE)
    p.add_argument("--no-gcs", action="store_true")
    p.add_argument("--no-bq", action="store_true")
    return p.parse_args()


def make_consumer(broker: str) -> KafkaConsumer:
    return KafkaConsumer(
        TOPIC,
        bootstrap_servers=[broker],
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="risk-stream-consumer",
        consumer_timeout_ms=30_000,  # exit after 30s of silence
    )


def gcs_path(now: datetime) -> str:
    ts = now.strftime("%Y%m%dT%H%M%SZ")
    return f"raw/stream/{now.strftime('%Y/%m/%d/%H')}/batch_{ts}.json.gz"


def write_to_gcs(client: storage.Client, bucket_name: str, records: list[dict]):
    now = datetime.now(tz=timezone.utc)
    blob_path = gcs_path(now)

    buf = BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
        for r in records:
            gz.write((json.dumps(r, default=str) + "\n").encode("utf-8"))

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.upload_from_string(buf.getvalue(), content_type="application/gzip")
    print(f"  GCS: gs://{bucket_name}/{blob_path} ({len(records)} records)", flush=True)


def write_to_bq(client: bigquery.Client, project: str, dataset: str, table: str,
                records: list[dict]):
    table_ref = f"{project}.{dataset}.{table}"
    errors = client.insert_rows_json(table_ref, records)
    if errors:
        print(f"  BQ insert errors: {errors}", file=sys.stderr)
    else:
        print(f"  BQ: inserted {len(records)} rows into {table_ref}", flush=True)


def ensure_bq_table(bq_client: bigquery.Client, project: str, dataset: str, table: str):
    """Create the streaming table if it doesn't exist (minimal schema)."""
    table_id = f"{project}.{dataset}.{table}"
    schema = [
        bigquery.SchemaField("TransactionID", "INTEGER"),
        bigquery.SchemaField("isFraud", "INTEGER"),
        bigquery.SchemaField("TransactionDT", "INTEGER"),
        bigquery.SchemaField("transaction_ts", "STRING"),
        bigquery.SchemaField("TransactionAmt", "FLOAT"),
        bigquery.SchemaField("ProductCD", "STRING"),
        bigquery.SchemaField("card4", "STRING"),
        bigquery.SchemaField("card6", "STRING"),
        bigquery.SchemaField("P_emaildomain", "STRING"),
        bigquery.SchemaField("R_emaildomain", "STRING"),
        bigquery.SchemaField("_ingested_at", "TIMESTAMP"),
    ]
    tbl = bigquery.Table(table_id, schema=schema)
    tbl.time_partitioning = bigquery.TimePartitioning(field="_ingested_at")
    try:
        bq_client.create_table(tbl, exists_ok=True)
        print(f"BQ table ready: {table_id}", flush=True)
    except Exception as e:
        print(f"Warning: could not create BQ table: {e}", file=sys.stderr)


def run(args):
    gcs_client = None if args.no_gcs else storage.Client(project=args.bq_project)
    bq_client = None if args.no_bq else bigquery.Client(project=args.bq_project)

    if bq_client:
        ensure_bq_table(bq_client, args.bq_project, args.bq_dataset, args.bq_table)

    consumer = make_consumer(args.broker)
    batch: list[dict] = []
    total = 0

    print(f"Listening on topic '{TOPIC}' (batch size {args.batch_size}) ...", flush=True)

    try:
        for message in consumer:
            record = message.value
            record["_ingested_at"] = datetime.now(tz=timezone.utc).isoformat()
            batch.append(record)

            if len(batch) >= args.batch_size:
                if gcs_client:
                    write_to_gcs(gcs_client, args.gcs_bucket, batch)
                if bq_client:
                    write_to_bq(bq_client, args.bq_project, args.bq_dataset,
                                args.bq_table, batch)
                total += len(batch)
                batch = []

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        # Flush remaining
        if batch:
            if gcs_client:
                write_to_gcs(gcs_client, args.gcs_bucket, batch)
            if bq_client:
                write_to_bq(bq_client, args.bq_project, args.bq_dataset,
                            args.bq_table, batch)
            total += len(batch)
        consumer.close()

    print(f"\nConsumer finished. Total records processed: {total:,}")


if __name__ == "__main__":
    args = parse_args()
    run(args)
