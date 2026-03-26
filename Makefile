.PHONY: help setup infra infra-destroy ingest dbt-run dbt-test \
        stream-up stream-down stream-topic stream-produce stream-consume \
        airflow-up airflow-down airflow-logs \
        narrate narrate-dry narrate-mock \
        dashboard-sources dashboard-dev dashboard-build dashboard-full \
        clean

# ─── Default ─────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "Intelligent Financial Risk Control System — Make targets"
	@echo ""
	@echo "  setup             Install Python (uv) + dashboard (npm) dependencies"
	@echo "  infra             Terraform init + apply (creates all GCP resources)"
	@echo "  infra-destroy     Terraform destroy (tears down all GCP resources)"
	@echo ""
	@echo "  ingest            Run batch ingestion: Kaggle → Parquet → GCS → BigQuery"
	@echo "  dbt-run           Run all dbt models (staging + production)"
	@echo "  dbt-test          Run dbt data quality tests"
	@echo ""
	@echo "  stream-up         Start Redpanda broker + Console UI"
	@echo "  stream-down       Stop Redpanda"
	@echo "  stream-topic      Create ieee_cis_transactions topic (first-time only)"
	@echo "  stream-produce    Replay 1000 transactions into Redpanda (fast mode)"
	@echo "  stream-consume    Consume from Redpanda → GCS + BigQuery"
	@echo ""
	@echo "  airflow-up        Start Airflow (webserver + scheduler)"
	@echo "  airflow-down      Stop Airflow"
	@echo "  airflow-logs      Tail Airflow logs"
	@echo ""
	@echo "  narrate           Generate AI narration from mart data (requires LLM_API_KEY)"
	@echo "  narrate-dry       Preview narration prompt without calling API"
	@echo "  narrate-mock      Write sample narration (no BigQuery or API needed)"
	@echo ""
	@echo "  dashboard-sources Pull latest data from BigQuery"
	@echo "  dashboard-dev     Start Evidence.dev dev server (http://localhost:3000)"
	@echo "  dashboard-build   Build static dashboard for deployment"
	@echo "  dashboard-full    Narrate + pull sources + build"
	@echo ""
	@echo "  clean             Stop all Docker services"
	@echo ""

# ─── Setup ───────────────────────────────────────────────────────────────────
setup:
	uv sync
	cd dashboard && npm install

# ─── Infrastructure ──────────────────────────────────────────────────────────
infra:
	cd terraform && terraform init && terraform apply -auto-approve

infra-destroy:
	cd terraform && terraform destroy -auto-approve

# ─── Batch Ingestion ─────────────────────────────────────────────────────────
ingest:
	uv run python scripts/ingest_to_gcs.py

# ─── dbt Transformations ─────────────────────────────────────────────────────
dbt-run:
	cd dbt && uv run dbt run

dbt-test:
	cd dbt && uv run dbt test

# ─── Streaming (Redpanda) ────────────────────────────────────────────────────
stream-up:
	cd redpanda && docker compose up -d

stream-down:
	cd redpanda && docker compose down

stream-topic:
	docker exec redpanda rpk topic create ieee_cis_transactions --partitions 3

stream-produce:
	uv run python redpanda/producer.py --limit 1000 --speed 999999

stream-consume:
	uv run python redpanda/consumer.py

# ─── Airflow ─────────────────────────────────────────────────────────────────
airflow-up:
	cd airflow && docker compose up -d

airflow-down:
	cd airflow && docker compose down

airflow-logs:
	cd airflow && docker compose logs -f

# ─── LLM Narration ───────────────────────────────────────────────────────────
narrate:
	uv run python scripts/generate_narration.py

narrate-dry:
	uv run python scripts/generate_narration.py --dry-run

narrate-mock:
	uv run python scripts/generate_narration.py --mock

# ─── Dashboard ───────────────────────────────────────────────────────────────
dashboard-sources:
	cd dashboard && npm run sources

dashboard-dev: dashboard-sources
	cd dashboard && npm run dev

dashboard-build: dashboard-sources
	cd dashboard && npm run build

dashboard-full: narrate dashboard-sources
	cd dashboard && npm run build

# ─── Cleanup ─────────────────────────────────────────────────────────────────
clean:
	cd airflow && docker compose down 2>/dev/null || true
	cd redpanda && docker compose down 2>/dev/null || true
