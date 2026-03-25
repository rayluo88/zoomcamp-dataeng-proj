-- Phase 3: Create partitioned + clustered production tables
-- Partitioning on transaction_date → queries scan only relevant date ranges
-- Clustering on ProductCD, card4 → fast filtering on fraud analysis dimensions

CREATE OR REPLACE TABLE `financial-risk-control-system.production.transactions`
PARTITION BY transaction_date
CLUSTER BY ProductCD, card4, isFraud
OPTIONS (
  description = "Main transaction fact table. Partitioned by date, clustered for fraud analysis queries.",
  require_partition_filter = false
)
AS
SELECT
  t.TransactionID,
  t.isFraud,
  t.transaction_ts,
  t.transaction_date,
  t.TransactionAmt,
  t.ProductCD,
  t.card1, t.card2, t.card3, t.card4, t.card5, t.card6,
  t.addr1, t.addr2,
  t.P_emaildomain,
  t.R_emaildomain,
  t.M1, t.M2, t.M3, t.M4, t.M5, t.M6, t.M7, t.M8, t.M9,
  -- Identity features (left join — not all transactions have identity)
  i.DeviceType,
  i.DeviceInfo,
  i.id_12, i.id_13, i.id_14, i.id_15, i.id_16, i.id_17, i.id_18,
  i.id_19, i.id_20, i.id_28, i.id_29, i.id_30, i.id_31, i.id_32,
  i.id_33, i.id_34, i.id_35, i.id_36, i.id_37, i.id_38
FROM `financial-risk-control-system.staging.transactions` t
LEFT JOIN `financial-risk-control-system.staging.identity` i
  USING (TransactionID);
