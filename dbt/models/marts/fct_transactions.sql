{{ config(
    materialized='table',
    partition_by={
      "field": "transaction_date",
      "data_type": "date",
      "granularity": "day"
    },
    cluster_by=["product_cd", "card_type", "is_fraud"]
) }}

-- Fact table: one row per transaction, enriched with identity features
-- Partitioned + clustered to mirror the production.transactions table

SELECT
  t.transaction_id,
  t.is_fraud,
  t.transaction_ts,
  t.transaction_date,
  t.transaction_amt,
  t.product_cd,
  t.card_type,
  t.card_category,
  t.billing_zip,
  t.billing_country,
  t.purchaser_email_domain,
  t.recipient_email_domain,
  t.M1, t.M2, t.M3, t.M4, t.M5, t.M6, t.M7, t.M8, t.M9,
  -- Identity enrichment (nullable — not all transactions have identity)
  i.device_type,
  i.device_info,
  i.os,
  i.browser,
  -- Derived risk signals
  CASE
    WHEN t.purchaser_email_domain IN ('gmail.com','yahoo.com','hotmail.com','outlook.com') THEN 'personal'
    WHEN t.purchaser_email_domain IS NULL THEN 'unknown'
    ELSE 'other'
  END AS email_domain_type,
  CASE
    WHEN t.transaction_amt < 50   THEN 'low'
    WHEN t.transaction_amt < 500  THEN 'medium'
    WHEN t.transaction_amt < 5000 THEN 'high'
    ELSE 'very_high'
  END AS amount_bucket
FROM {{ ref('stg_transactions') }} t
LEFT JOIN {{ ref('stg_identity') }} i USING (transaction_id)
