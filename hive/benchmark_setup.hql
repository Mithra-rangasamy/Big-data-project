-- ==============================================================================
-- CIT 21MDS56: Big Data Computing Laboratory
-- hive/benchmark.hql - Partitioned vs Non-Partitioned Hive Analytical Benchmark
-- ==============================================================================

-- 1. Create Non-Partitioned Table
CREATE TABLE IF NOT EXISTS aqi_readings_unpartitioned (
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
    o3 DOUBLE,
    city STRING,
    `date` STRING
)
STORED AS TEXTFILE;

-- 2. Populate Non-Partitioned Table from Partitioned Table
INSERT OVERWRITE TABLE aqi_readings_unpartitioned
SELECT record_id, city_name, zone_id, zone_name, ts, aqi, pm25, pm10, no2, so2, co, o3, city, `date`
FROM aqi_readings;
