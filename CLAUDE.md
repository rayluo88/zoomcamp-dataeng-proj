# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Intelligent Financial Risk Control System** — a Data Engineering Zoomcamp capstone project that ingests synthetic financial transaction data (PaySim), detects fraud patterns, and serves a risk analytics dashboard.

**Course**: [DataTalksClub Data Engineering Zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp)
**Project requirements**: https://github.com/DataTalksClub/data-engineering-zoomcamp/tree/main/projects

## Technology Stack

| Layer | Tool |
|---|---|
| Cloud | GCP (BigQuery, GCS, Compute Engine) |
| IaC | Terraform |
| Orchestration | Apache Airflow |
| Data Lake | Google Cloud Storage |
| Data Warehouse | BigQuery (partitioned + clustered tables) |
| Batch Processing | Apache Spark (PySpark) |
| Stream Processing | Apache Kafka |
| Transformations | dbt |
| Dashboard | Looker Studio or Streamlit |
| Dataset | [PaySim](https://www.kaggle.com/datasets/ealaxi/paysim1) synthetic financial transactions |

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
- Kafka producer: replay PaySim transactions as a stream
- Kafka consumer: write to GCS/BigQuery in near-real-time
- Airflow DAG or Kafka Connect for orchestration

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

## Project Conventions

- **GCS structure**: `gs://<bucket>/raw/`, `/staged/`, `/curated/`
- **BigQuery datasets**: `raw`, `staging`, `production`
- **Airflow DAGs**: prefixed `risk_` (e.g., `risk_batch_ingest`)
- **dbt models**: follow staging → intermediate → mart layering
- **Terraform**: all resources in `terraform/` directory, variables in `terraform/variables.tf`
- **Secrets**: use GCP Secret Manager or environment variables; never commit credentials

## Key Files (once created)

- `terraform/` — all GCP infrastructure
- `airflow/dags/` — Airflow DAG definitions
- `airflow/plugins/` — custom operators/hooks
- `dbt/` — dbt project (models, tests, macros)
- `kafka/` — producer/consumer scripts
- `spark/` — PySpark batch jobs
- `dashboard/` — Streamlit app (if not using Looker Studio)
