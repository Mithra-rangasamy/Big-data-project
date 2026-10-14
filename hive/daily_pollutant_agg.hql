SET hive.query.results.cache.enabled=false;
SET hive.auto.convert.join=false;
SET hive.exec.mode.local.auto=false;
SET hive.exec.compress.output=false;

INSERT OVERWRITE DIRECTORY 'hdfs://localhost:9000/data/processed/daily_pollutant_agg'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
SELECT 
    zone_id,
    zone_name,
    city,
    `date`,
    ROUND(AVG(aqi), 2) AS avg_aqi,
    ROUND(AVG(pm25), 2) AS avg_pm25,
    ROUND(AVG(pm10), 2) AS avg_pm10,
    ROUND(AVG(no2), 2) AS avg_no2,
    ROUND(AVG(so2), 2) AS avg_so2,
    ROUND(AVG(co), 2) AS avg_co,
    ROUND(AVG(o3), 2) AS avg_o3
FROM aqi_readings
GROUP BY zone_id, zone_name, city, `date`;
