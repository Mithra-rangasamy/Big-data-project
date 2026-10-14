SET hive.query.results.cache.enabled=false;
SET hive.auto.convert.join=false;
SET hive.exec.mode.local.auto=false;
SET hive.exec.compress.output=false;

INSERT OVERWRITE DIRECTORY 'hdfs://localhost:9000/data/processed/daily_aqi_agg'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
SELECT 
    a.zone_id,
    a.zone_name,
    a.city,
    a.`date`,
    ROUND(AVG(a.aqi), 2) AS avg_aqi,
    MAX(a.aqi) AS max_aqi,
    ROUND(AVG(COALESCE(w.wind_speed, 8.0)), 2) AS avg_wind_speed
FROM aqi_readings a
LEFT JOIN weather_data w
  ON a.zone_id = w.zone_id AND a.city = w.city AND a.`date` = w.`date` AND a.ts = w.ts
GROUP BY a.zone_id, a.zone_name, a.city, a.`date`;
