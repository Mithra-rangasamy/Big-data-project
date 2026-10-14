-- ==============================================================================
-- CIT 21MDS56: Air Quality & Public Health Early-Warning System
-- hive/output_table.hql - External table mapping Apache Pig fused output
-- ==============================================================================

USE air_quality_ews;

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
    compound_alert BOOLEAN,
    base_level STRING,
    final_level STRING,
    escalated BOOLEAN
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/data/processed/zone_risk_score';
