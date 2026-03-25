SELECT
  summary_type,
  dimension_value,
  total_txns,
  fraud_txns,
  fraud_rate_pct,
  total_amt,
  fraud_amt,
  avg_txn_amt
FROM `financial-risk-control-system.production.mart_risk_summary`
ORDER BY summary_type, dimension_value
