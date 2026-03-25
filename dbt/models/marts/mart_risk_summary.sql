{{ config(materialized='table') }}

-- Risk summary mart: pre-aggregated metrics for the dashboard
-- Two tiles required: categorical (fraud by product/card type) + temporal (fraud trend)

-- Temporal: daily fraud metrics
WITH daily AS (
  SELECT
    transaction_date,
    COUNT(*)                                          AS total_txns,
    COUNTIF(is_fraud)                                 AS fraud_txns,
    ROUND(COUNTIF(is_fraud) / COUNT(*) * 100, 4)      AS fraud_rate_pct,
    ROUND(SUM(transaction_amt), 2)                    AS total_amt,
    ROUND(SUM(IF(is_fraud, transaction_amt, 0)), 2)   AS fraud_amt
  FROM {{ ref('fct_transactions') }}
  GROUP BY 1
),

-- Categorical: fraud by product code
by_product AS (
  SELECT
    product_cd,
    COUNT(*)                                          AS total_txns,
    COUNTIF(is_fraud)                                 AS fraud_txns,
    ROUND(COUNTIF(is_fraud) / COUNT(*) * 100, 4)      AS fraud_rate_pct,
    ROUND(AVG(transaction_amt), 2)                    AS avg_txn_amt
  FROM {{ ref('fct_transactions') }}
  GROUP BY 1
),

-- Categorical: fraud by card type
by_card_type AS (
  SELECT
    COALESCE(card_type, 'unknown')                    AS card_type,
    COUNT(*)                                          AS total_txns,
    COUNTIF(is_fraud)                                 AS fraud_txns,
    ROUND(COUNTIF(is_fraud) / COUNT(*) * 100, 4)      AS fraud_rate_pct
  FROM {{ ref('fct_transactions') }}
  GROUP BY 1
),

-- Categorical: fraud by device type
by_device AS (
  SELECT
    COALESCE(device_type, 'unknown')                  AS device_type,
    COUNT(*)                                          AS total_txns,
    COUNTIF(is_fraud)                                 AS fraud_txns,
    ROUND(COUNTIF(is_fraud) / COUNT(*) * 100, 4)      AS fraud_rate_pct
  FROM {{ ref('fct_transactions') }}
  GROUP BY 1
)

-- Return all summary dimensions as separate tables via dbt's multi-table pattern
-- Dashboard queries each CTE independently via views

SELECT
  'daily'                                             AS summary_type,
  CAST(transaction_date AS STRING)                    AS dimension_value,
  total_txns,
  fraud_txns,
  fraud_rate_pct,
  total_amt,
  fraud_amt,
  NULL AS avg_txn_amt
FROM daily

UNION ALL

SELECT
  'product_cd',
  product_cd,
  total_txns,
  fraud_txns,
  fraud_rate_pct,
  NULL,
  NULL,
  avg_txn_amt
FROM by_product

UNION ALL

SELECT
  'card_type',
  card_type,
  total_txns,
  fraud_txns,
  fraud_rate_pct,
  NULL,
  NULL,
  NULL
FROM by_card_type

UNION ALL

SELECT
  'device_type',
  device_type,
  total_txns,
  fraud_txns,
  fraud_rate_pct,
  NULL,
  NULL,
  NULL
FROM by_device
