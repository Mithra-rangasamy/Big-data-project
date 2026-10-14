CREATE EXTERNAL TABLE IF NOT EXISTS aqi_complaint_correlation (
    zone_id STRING,
    zone_name STRING,
    city STRING,
    lag_0 DOUBLE,
    lag_1 DOUBLE,
    lag_2 DOUBLE,
    lag_3 DOUBLE,
    optimal_lag INT,
    max_correlation DOUBLE
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LOCATION '/data/processed/aqi_complaint_correlation';
