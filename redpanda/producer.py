"""
IEEE-CIS Fraud Detection — Redpanda producer.

Replays train_transaction.csv row-by-row as JSON messages to topic
`ieee_cis_transactions`, preserving relative transaction timing.

Usage:
    uv run python redpanda/producer.py [--speed FACTOR] [--limit N]

Options:
    --speed FACTOR   Time compression (default 3600 = 1 real second = 1 simulated hour)
    --limit N        Only send the first N rows (0 = all rows)
    --broker HOST    Kafka broker address (default localhost:9092)
    --dry-run        Print messages without sending
"""

import argparse
import json
import time
import sys
from pathlib import Path

import pandas as pd
from kafka import KafkaProducer

TOPIC = "ieee_cis_transactions"
# TransactionDT is seconds since 2017-12-01 — treat as relative ordering
REFERENCE_DATE = pd.Timestamp("2017-12-01")
DATA_FILE = Path(__file__).parent.parent / "data" / "train_transaction.csv"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--speed", type=float, default=3600,
                   help="Time compression factor (default 3600: 1s real = 1h simulated)")
    p.add_argument("--limit", type=int, default=0,
                   help="Row limit (0 = all)")
    p.add_argument("--broker", default="localhost:9092",
                   help="Kafka broker (default localhost:9092)")
    p.add_argument("--dry-run", action="store_true",
                   help="Print without sending")
    return p.parse_args()


def load_transactions(limit: int) -> pd.DataFrame:
    print(f"Loading {DATA_FILE} ...", flush=True)
    df = pd.read_csv(DATA_FILE, nrows=limit if limit else None)
    df = df.sort_values("TransactionDT").reset_index(drop=True)
    # Replace NaN with None for JSON serialisation
    df = df.where(pd.notna(df), None)
    print(f"Loaded {len(df):,} rows", flush=True)
    return df


def make_producer(broker: str) -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=[broker],
        value_serializer=lambda v: json.dumps(
            v, default=lambda x: None if isinstance(x, float) and (x != x) else str(x)
        ).encode("utf-8"),
        acks="all",
        retries=3,
    )


def run(args):
    df = load_transactions(args.limit)
    producer = None if args.dry_run else make_producer(args.broker)

    prev_dt = None
    total_sent = 0

    import math

    for _, row in df.iterrows():
        # Replace float NaN with None for valid JSON
        record = {k: (None if isinstance(v, float) and math.isnan(v) else v)
                  for k, v in row.to_dict().items()}
        # Derive ISO timestamp from TransactionDT offset
        tx_ts = REFERENCE_DATE + pd.Timedelta(seconds=int(record["TransactionDT"]))
        record["transaction_ts"] = tx_ts.isoformat()

        # Pace replay according to simulated time gap
        if prev_dt is not None and not args.dry_run:
            gap_seconds = (record["TransactionDT"] - prev_dt) / args.speed
            if gap_seconds > 0:
                time.sleep(min(gap_seconds, 5))  # cap sleep to 5s for usability

        prev_dt = record["TransactionDT"]

        if args.dry_run:
            print(json.dumps(record, default=lambda x: None if isinstance(x, float) and (x != x) else str(x))[:200])
        else:
            producer.send(TOPIC, value=record)
            total_sent += 1
            if total_sent % 1000 == 0:
                producer.flush()
                print(f"  Sent {total_sent:,} messages ...", flush=True)

    if producer:
        producer.flush()
        producer.close()
        print(f"Done. Sent {total_sent:,} messages to topic '{TOPIC}'.")
    else:
        print(f"Dry-run complete — {len(df):,} rows would be sent.")


if __name__ == "__main__":
    args = parse_args()
    run(args)
