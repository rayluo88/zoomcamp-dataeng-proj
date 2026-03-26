"""
LLM Narration — Post-dbt intelligence layer

Queries pre-aggregated mart tables from BigQuery, generates natural language
summaries using any OpenAI-compatible LLM API, and writes structured output
to the Evidence.dev sources directory for dashboard rendering.

Architecture principle: LLM narrates facts from verified data.
It has NO role in fraud detection — only presentation.

Provider-agnostic design: configure via env vars, default is DeepSeek.
To switch providers:
  - OpenAI:  LLM_BASE_URL=https://api.openai.com/v1  LLM_MODEL=gpt-4o-mini
  - Groq:    LLM_BASE_URL=https://api.groq.com/openai/v1  LLM_MODEL=llama-3.3-70b-versatile
  - Ollama:  LLM_BASE_URL=http://localhost:11434/v1  LLM_API_KEY=ollama  LLM_MODEL=llama3.2

Usage:
  uv run python scripts/generate_narration.py            # full run
  uv run python scripts/generate_narration.py --dry-run  # print prompt/response, no file write
  uv run python scripts/generate_narration.py --mock     # skip BigQuery + API, write sample output
"""

import argparse
import csv
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "financial-risk-control-system")
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials/pipeline-sa-key.json")
OUTPUT_FILE = Path("dashboard/sources/narration/summary.csv")

# LLM provider config — defaults to DeepSeek (OpenAI-compatible)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

MAX_SECTION_LEN = 500

SYSTEM_PROMPT = """You are a financial analytics narrator for a fraud detection system.
Your job is to write clear, factual summaries of fraud detection metrics.

Rules you must follow:
1. ONLY state facts that appear in the provided data. Do not add external context.
2. Never infer causation — do not say "caused by" or "because of".
3. Never recommend actions or make predictions about the future.
4. Never fabricate or extrapolate numbers. Only use values from the input data.
5. Use hedging language for observations: "the data shows", "the dataset indicates".
6. Each section must be 2-4 sentences maximum.
7. Write in plain business English. No bullet points within prose sections."""


# ── Data Fetching ───────────────────────────────────────────────────────────────

def fetch_mart_data() -> dict:
    """Query pre-aggregated mart tables. Returns structured dict — no raw data."""
    from google.cloud import bigquery
    from google.oauth2 import service_account

    credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
    bq = bigquery.Client(project=PROJECT_ID, credentials=credentials)

    kpi_query = f"""
    SELECT
      SUM(total_txns)                                            AS total_txns,
      SUM(fraud_txns)                                            AS fraud_txns,
      ROUND(SUM(fraud_txns) * 100.0 / SUM(total_txns), 2)       AS fraud_rate_pct,
      ROUND(SUM(fraud_amt) / 1000000, 2)                         AS fraud_amt_m,
      ROUND(SUM(total_amt) / 1000000, 2)                         AS total_amt_m,
      MIN(dimension_value)                                       AS period_start,
      MAX(dimension_value)                                       AS period_end
    FROM `{PROJECT_ID}.production.mart_risk_summary`
    WHERE summary_type = 'daily'
    """

    segment_query = f"""
    SELECT summary_type, dimension_value, total_txns, fraud_txns, fraud_rate_pct
    FROM `{PROJECT_ID}.production.mart_risk_summary`
    WHERE summary_type IN ('product_cd', 'card_type', 'device_type')
    ORDER BY summary_type, fraud_rate_pct DESC
    """

    bucket_query = f"""
    SELECT
      amount_bucket,
      COUNT(*)                                        AS total_txns,
      SUM(CAST(is_fraud AS INT64))                    AS fraud_txns,
      ROUND(AVG(IF(is_fraud, 1.0, 0.0)), 6)             AS fraud_rate_pct
    FROM `{PROJECT_ID}.production.fct_transactions`
    GROUP BY amount_bucket
    ORDER BY fraud_rate_pct DESC
    """

    log.info("Querying BigQuery mart tables...")

    kpi_row = list(bq.query(kpi_query).result())[0]
    kpi = dict(kpi_row)

    segments: dict[str, list] = {"product_cd": [], "card_type": [], "device_type": []}
    for row in bq.query(segment_query).result():
        d = dict(row)
        segments[d["summary_type"]].append({
            "dimension": d["dimension_value"],
            "total_txns": int(d["total_txns"]),
            "fraud_txns": int(d["fraud_txns"]),
            "fraud_rate_pct": float(d["fraud_rate_pct"]),
        })

    buckets = [
        {
            "bucket": dict(row)["amount_bucket"],
            "total_txns": int(dict(row)["total_txns"]),
            "fraud_txns": int(dict(row)["fraud_txns"]),
            "fraud_rate_pct": float(dict(row)["fraud_rate_pct"]),
        }
        for row in bq.query(bucket_query).result()
    ]

    return {
        "overall": {
            "total_txns": int(kpi["total_txns"]),
            "fraud_txns": int(kpi["fraud_txns"]),
            "fraud_rate_pct": float(kpi["fraud_rate_pct"]),
            "fraud_amt_m": float(kpi["fraud_amt_m"]),
            "total_amt_m": float(kpi["total_amt_m"]),
            "period_start": kpi["period_start"],
            "period_end": kpi["period_end"],
        },
        "by_product": segments["product_cd"],
        "by_card_type": segments["card_type"],
        "by_device": segments["device_type"],
        "by_amount": buckets,
    }


# ── LLM Call ────────────────────────────────────────────────────────────────────

def generate_narration(data: dict, dry_run: bool = False) -> dict | None:
    """
    Call configured LLM provider with grounded, constrained prompt.
    Uses OpenAI-compatible API — works with DeepSeek, OpenAI, Groq, Ollama, etc.
    Returns parsed JSON dict or None on failure.
    """
    user_prompt = f"""Below is a summary of fraud detection metrics from the IEEE-CIS dataset.

DATA:
{json.dumps(data, indent=2)}

Write a brief narrative summary based ONLY on the numbers in DATA above.

Return your response as a JSON object with exactly these keys:
- "executive_summary": Overall fraud posture — total transactions, fraud rate, and financial exposure. (2-3 sentences)
- "risk_highlights": Which segments show the highest fraud rates and what the data shows about them. (2-3 sentences)
- "segment_analysis": Patterns across product codes, card types, and device types. (2-3 sentences)
- "data_period": State the data period covered using the period_start and period_end from the data. (1 sentence)

Return only the JSON object. No markdown fences, no preamble."""

    if dry_run:
        print("\n" + "=" * 60)
        print(f"PROVIDER: {LLM_BASE_URL}")
        print(f"MODEL:    {LLM_MODEL}")
        print("\nSYSTEM PROMPT:")
        print(SYSTEM_PROMPT)
        print("\nUSER PROMPT:")
        print(user_prompt)
        print("=" * 60 + "\n")
        return None

    if not LLM_API_KEY:
        log.error("LLM_API_KEY not set — skipping narration")
        return None

    client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

    log.info(f"Calling LLM (provider={LLM_BASE_URL}, model={LLM_MODEL})...")
    response = client.chat.completions.create(
        model=LLM_MODEL,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = response.choices[0].message.content or ""
    log.info(f"Received response ({len(raw)} chars)")

    # Strip markdown fences if the model added them despite instructions
    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse LLM response as JSON: {e}")
        log.debug(f"Raw response: {raw}")
        return None


# ── Validation ─────────────────────────────────────────────────────────────────

def _collect_numbers(obj) -> set[str]:
    """Recursively collect all numeric values from a data structure as strings."""
    nums: set[str] = set()
    if isinstance(obj, (int, float)):
        nums.add(str(round(float(obj), 2)))
        if float(obj) == int(float(obj)):
            nums.add(str(int(obj)))
    elif isinstance(obj, dict):
        for v in obj.values():
            nums |= _collect_numbers(v)
    elif isinstance(obj, list):
        for item in obj:
            nums |= _collect_numbers(item)
    return nums


def validate_output(narration: dict, source_data: dict) -> dict:
    """
    Validate LLM output:
    1. Required keys present (fill empty string if missing)
    2. Each section within length limit (truncate if over)
    3. Log warning if numbers appear that weren't in source data
    """
    required_keys = {"executive_summary", "risk_highlights", "segment_analysis", "data_period"}
    source_numbers = _collect_numbers(source_data)
    result = {}

    for key in required_keys:
        if key not in narration:
            log.warning(f"Missing key '{key}' in narration — leaving blank")
            result[key] = ""
            continue

        text = str(narration[key])

        if len(text) > MAX_SECTION_LEN:
            log.warning(f"Section '{key}' too long ({len(text)} chars) — truncating")
            text = text[:MAX_SECTION_LEN].rsplit(" ", 1)[0] + "..."

        # Warn on numbers that don't appear in source data (hallucination signal)
        if source_data:
            found = re.findall(r"\b\d+\.?\d*\b", text)
            unverified = [n for n in found if n not in source_numbers and len(n) > 2]
            if unverified:
                log.warning(f"Section '{key}' contains unverified numbers: {unverified}")

        result[key] = text

    return result


# ── Mock Output ─────────────────────────────────────────────────────────────────

MOCK_NARRATION = {
    "executive_summary": (
        "The dataset contains 590,540 e-commerce transactions with an overall fraud rate of 3.49%, "
        "representing approximately 20,600 fraudulent transactions. The total transaction volume "
        "amounts to approximately $3,544.9M, of which around $170.1M is attributed to fraudulent activity."
    ),
    "risk_highlights": (
        "Product code W exhibits the highest fraud rate among all product segments in the data. "
        "The data shows that very high-value transactions (above $5,000) carry a substantially "
        "elevated fraud rate compared to lower amount buckets."
    ),
    "segment_analysis": (
        "Across card types, the data indicates variation in fraud exposure, with certain categories "
        "showing higher rates than the overall average. Device type analysis shows that the dataset "
        "includes mobile, desktop, and unknown device classifications with differing fraud profiles."
    ),
    "data_period": (
        "The dataset covers transactions from the observation period recorded in the IEEE-CIS "
        "fraud detection dataset."
    ),
}


# ── Write Output ────────────────────────────────────────────────────────────────

def write_csv(narration: dict) -> None:
    """Write narration to CSV for Evidence.dev CSV connector consumption."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["executive_summary", "risk_highlights", "segment_analysis", "data_period", "generated_at"]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({
            **{k: narration.get(k, "") for k in fieldnames[:-1]},
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        })

    log.info(f"Narration written to {OUTPUT_FILE}")


# ── Main ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate LLM narration for the financial risk dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Provider config via environment variables (defaults to DeepSeek):
  LLM_API_KEY   API key for the LLM provider
  LLM_BASE_URL  API base URL (default: https://api.deepseek.com)
  LLM_MODEL     Model name  (default: deepseek-chat)
""",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print prompt without calling API or writing file")
    parser.add_argument("--mock", action="store_true", help="Use hardcoded sample output (skips BigQuery and API)")
    args = parser.parse_args()

    if args.mock:
        log.info("Mock mode — using hardcoded sample narration")
        validated = validate_output(MOCK_NARRATION, {})
        write_csv(validated)
        return

    data = fetch_mart_data()

    if data["overall"]["total_txns"] == 0:
        log.error("No data found in mart tables — skipping narration")
        return

    narration = generate_narration(data, dry_run=args.dry_run)

    if args.dry_run:
        return

    if narration is None:
        log.warning("Narration generation failed — no output written (dashboard unaffected)")
        return

    validated = validate_output(narration, data)
    write_csv(validated)


if __name__ == "__main__":
    main()
