CREATE EXTERNAL TABLE IF NOT EXISTS daily_pollutant_agg (
    zone_id STRING,
    zone_name STRING,
    city STRING,
    `date` STRING,
    avg_aqi DOUBLE,
    avg_pm25 DOUBLE,
    avg_pm10 DOUBLE,
    avg_no2 DOUBLE,
    avg_so2 DOUBLE,
    avg_co DOUBLE,
    avg_o3 DOUBLE
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LOCATION '/data/processed/daily_pollutant_agg';
