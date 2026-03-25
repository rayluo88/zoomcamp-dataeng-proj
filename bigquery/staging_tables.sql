-- Phase 3: Promote raw → staging with typed schema
-- Run once to create staging tables from the raw external tables

CREATE OR REPLACE TABLE `financial-risk-control-system.staging.transactions`
AS
SELECT
  TransactionID,
  isFraud,
  TransactionDT,
  -- Convert timedelta (seconds) to actual timestamp
  -- Reference date: 2017-12-01 (inferred from competition data)
  TIMESTAMP_ADD(TIMESTAMP '2017-12-01 00:00:00', INTERVAL TransactionDT SECOND) AS transaction_ts,
  DATE(TIMESTAMP_ADD(TIMESTAMP '2017-12-01 00:00:00', INTERVAL TransactionDT SECOND)) AS transaction_date,
  TransactionAmt,
  ProductCD,
  card1, card2, card3, card4, card5, card6,
  addr1, addr2,
  dist1, dist2,
  P_emaildomain,
  R_emaildomain,
  C1, C2, C3, C4, C5, C6, C7, C8, C9, C10, C11, C12, C13, C14,
  D1, D2, D3, D4, D5, D6, D7, D8, D9, D10, D11, D12, D13, D14, D15,
  M1, M2, M3, M4, M5, M6, M7, M8, M9,
  V1, V2, V3, V4, V5, V6, V7, V8, V9, V10,
  V11, V12, V13, V14, V15, V16, V17, V18, V19, V20,
  V21, V22, V23, V24, V25, V26, V27, V28, V29, V30,
  V31, V32, V33, V34, V35, V36, V37, V38, V39, V40,
  V41, V42, V43, V44, V45, V46, V47, V48, V49, V50
FROM `financial-risk-control-system.raw.train_transaction`;

CREATE OR REPLACE TABLE `financial-risk-control-system.staging.identity`
AS
SELECT * FROM `financial-risk-control-system.raw.train_identity`;
