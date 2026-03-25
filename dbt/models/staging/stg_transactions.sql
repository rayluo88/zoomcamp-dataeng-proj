{{ config(materialized='view') }}

-- Staging view: light cleanup on top of the raw external table
-- No business logic here — just type safety and column renaming

SELECT
  TransactionID                                       AS transaction_id,
  CAST(isFraud AS BOOL)                               AS is_fraud,
  transaction_ts,
  transaction_date,
  CAST(TransactionAmt AS FLOAT64)                     AS transaction_amt,
  UPPER(TRIM(ProductCD))                              AS product_cd,
  CAST(card1 AS INT64)                                AS card1,
  CAST(card2 AS FLOAT64)                              AS card2,
  CAST(card3 AS FLOAT64)                              AS card3,
  LOWER(TRIM(card4))                                  AS card_type,     -- visa, mastercard, etc.
  CAST(card5 AS FLOAT64)                              AS card5,
  LOWER(TRIM(card6))                                  AS card_category, -- debit, credit, etc.
  CAST(addr1 AS FLOAT64)                              AS billing_zip,
  CAST(addr2 AS FLOAT64)                              AS billing_country,
  LOWER(TRIM(P_emaildomain))                          AS purchaser_email_domain,
  LOWER(TRIM(R_emaildomain))                          AS recipient_email_domain,
  M1, M2, M3, M4, M5, M6, M7, M8, M9                -- match flags (T/F/unknown)
FROM {{ source('raw_data', 'transactions') }}
