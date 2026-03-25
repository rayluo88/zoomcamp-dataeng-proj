# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Intelligent Financial Risk Control System** — a Data Engineering Zoomcamp capstone project that ingests synthetic financial transaction data (PaySim), detects fraud patterns, and serves a risk analytics dashboard.

**Course**: [DataTalksClub Data Engineering Zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp)
**Project requirements**: https://github.com/DataTalksClub/data-engineering-zoomcamp/tree/main/projects
**Dataset**: [IEEE-CIS Fraud Detection](https://www.kaggle.com/competitions/ieee-fraud-detection) — real anonymized e-commerce transaction data from Vesta Corporation (590K transactions, 400+ features, fraud labels)

## Technology Stack

| Layer | Tool |
|---|---|
| Cloud | GCP (BigQuery, GCS, Compute Engine) |
| IaC | Terraform |
| Orchestration | Apache Airflow |
| Data Lake | Google Cloud Storage |
| Data Warehouse | BigQuery (partitioned + clustered tables) |
| Batch Processing | Apache Spark (PySpark) |
| Stream Processing | Redpanda |
| Transformations | dbt |
| Dashboard | Looker Studio or Streamlit |
| Dataset | [IEEE-CIS Fraud Detection](https://www.kaggle.com/competitions/ieee-fraud-detection) — real Vesta Corp e-commerce transactions |

## Build Sequence

Follow these phases in order — each builds on the previous:

### Phase 1: Infrastructure (Terraform + GCP)
- GCS bucket for data lake (raw/staged/curated layers)
- BigQuery datasets
- GCP service account with IAM roles
- Terraform state in GCS backend

### Phase 2: Data Ingestion — Batch
- Download PaySim CSV from Kaggle
- Airflow DAG: upload raw data to GCS → load to BigQuery staging table
- Schedule: daily or one-time historical load

### Phase 3: Data Warehouse Setup
- BigQuery external tables pointing to GCS
- Partitioned by transaction date, clustered by transaction type
- Staging → production table promotion via DAG

### Phase 4: dbt Transformations
- `stg_transactions` — clean and type-cast raw data
- `dim_` models — customer, transaction type, merchant
- `fct_transactions` — fact table with fraud flag
- `mart_risk_summary` — aggregated risk metrics for dashboard

### Phase 5: Streaming Pipeline
- Redpanda producer: replay PaySim transactions as a stream
- Redpanda consumer: write to GCS/BigQuery in near-real-time
- Airflow DAG or Redpanda Connect (Kafka-compatible API) for orchestration

### Phase 6: Dashboard
- Two required tiles: categorical distribution (fraud by type) + temporal distribution (fraud trend over time)
- Host publicly for peer review

### Phase 7: Reproducibility
- `README.md` with full setup instructions
- `.env.example` with all required variables documented
- One-command setup via Makefile or setup script

## Evaluation Rubric (max 28 points)

| Category | 4 pts (max) requires |
|---|---|
| Problem Description | Well-articulated in README |
| Cloud | GCP deployed + Terraform IaC |
| Data Ingestion (Batch) | End-to-end Airflow DAG |
| Data Ingestion (Stream) | Full Kafka pipeline |
| Data Warehouse | Partitioned + clustered BigQuery tables |
| Transformations | dbt models |
| Dashboard | 2+ tiles (categorical + temporal) |
| Reproducibility | Clear, working setup instructions |

## Development Environment

- **`uv`** — Python package manager for local dev tools (dbt, kaggle CLI, scripts, PySpark)
  - Dependencies defined in `pyproject.toml`, locked in `uv.lock`
  - Run any tool: `uv run <command>` (auto-activates venv)
- **Docker** — Airflow runs in Docker Compose (isolated, matches production)
  - Start: `cd airflow && docker compose up -d`
  - UI: http://localhost:8080 (admin/admin)
  - Airflow 2.11.2 (latest 2.x — Airflow 3 has breaking changes incompatible with course material)

## Common Commands

```bash
# dbt (via uv — no manual venv activation needed)
cd dbt && uv run dbt run              # run all models
cd dbt && uv run dbt run -s model_name  # run single model
cd dbt && uv run dbt test               # run data tests

# Airflow (Docker)
cd airflow && docker compose up -d    # start
cd airflow && docker compose down     # stop
cd airflow && docker compose logs -f  # tail logs

# Batch ingestion
uv run python scripts/ingest_to_gcs.py  # full pipeline: Kaggle → Parquet → GCS → BigQuery

# Add a new dependency
uv add <package-name>

# Terraform
cd terraform && terraform plan       # preview changes
cd terraform && terraform apply      # apply changes
```

## Project Conventions

- **GCS structure**: `gs://<bucket>/raw/`, `/staged/`, `/curated/`
- **BigQuery datasets**: `raw`, `staging`, `production`
- **Airflow DAGs**: prefixed `risk_` (e.g., `risk_batch_ingest`)
- **dbt models**: follow staging → intermediate → mart layering
- **GCP region**: `asia-southeast1` (Singapore) for all resources — GCS bucket, BigQuery dataset, Compute Engine. Keep everything in the same region; cross-region data transfer is what drives costs.
- **Terraform**: all resources in `terraform/` directory, variables in `terraform/variables.tf`
- **Secrets**: use GCP Secret Manager or environment variables; never commit credentials

## Key Files (once created)

- `terraform/` — all GCP infrastructure
- `airflow/dags/` — Airflow DAG definitions
- `airflow/plugins/` — custom operators/hooks
- `dbt/` — dbt project (models, tests, macros)
- `redpanda/` — producer/consumer scripts
- `spark/` — PySpark batch jobs
- `dashboard/` — Streamlit app (if not using Looker Studio)
