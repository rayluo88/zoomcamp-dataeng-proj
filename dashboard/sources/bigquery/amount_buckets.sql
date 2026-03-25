SELECT
  amount_bucket,
  COUNT(*) AS total_txns,
  SUM(CAST(is_fraud AS INT64)) AS fraud_txns,
  ROUND(SUM(CAST(is_fraud AS INT64)) * 100.0 / COUNT(*), 2) AS fraud_rate_pct,
  ROUND(AVG(transaction_amt), 2) AS avg_amt
FROM `financial-risk-control-system.production.fct_transactions`
GROUP BY amount_bucket
ORDER BY
  CASE amount_bucket
    WHEN 'low' THEN 1
    WHEN 'medium' THEN 2
    WHEN 'high' THEN 3
    WHEN 'very_high' THEN 4
    ELSE 5
  END
