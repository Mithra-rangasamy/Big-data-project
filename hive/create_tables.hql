-- ==============================================================================
-- CIT 21MDS56: Air Quality & Public Health Early-Warning System
-- hive/create_tables.hql - Creates external partitioned tables for raw ingestion
-- ==============================================================================

-- 1. Structured AQI Telemetry
CREATE EXTERNAL TABLE IF NOT EXISTS aqi_readings (
    record_id STRING,
    city_name STRING,
    zone_id STRING,
    zone_name STRING,
    ts STRING,
    aqi INT,
    pm25 DOUBLE,
    pm10 DOUBLE,
    no2 DOUBLE,
    so2 DOUBLE,
    co DOUBLE,
    o3 DOUBLE
)
PARTITIONED BY (city STRING, `date` STRING)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/data/raw/aqi';

-- 2. Structured Weather / Meteorological Telemetry
CREATE EXTERNAL TABLE IF NOT EXISTS weather_data (
    record_id STRING,
    city_name STRING,
    zone_id STRING,
    ts STRING,
    temp DOUBLE,
    humidity DOUBLE,
    wind_speed DOUBLE,
    wind_direction DOUBLE
)
PARTITIONED BY (city STRING, `date` STRING)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/data/raw/weather';

-- 3. Output Fused Table (Computed by Apache Pig, queried by Hive and Flask)
CREATE EXTERNAL TABLE IF NOT EXISTS zone_risk_score (
    zone_id STRING,
    zone_name STRING,
    city STRING,
    `date` STRING,
    avg_aqi DOUBLE,
    aqi_norm DOUBLE,
    aqi_trend DOUBLE,
    complaint_count INT,
    complaint_density DOUBLE,
    symptom_severity DOUBLE,
    weather_factor DOUBLE,
    risk_score DOUBLE,
    risk_level STRING,
    compound_alert BOOLEAN
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/data/processed/zone_risk_score';
