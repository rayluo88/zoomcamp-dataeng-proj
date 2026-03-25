{{ config(materialized='view') }}

SELECT
  TransactionID       AS transaction_id,
  LOWER(TRIM(DeviceType))   AS device_type,
  TRIM(DeviceInfo)          AS device_info,
  id_12, id_13, id_14, id_15, id_16, id_17, id_18,
  id_19, id_20, id_28, id_29,
  TRIM(id_30)         AS os,
  TRIM(id_31)         AS browser,
  id_32, id_33, id_34, id_35, id_36, id_37, id_38
FROM {{ source('raw_data', 'identity') }}
