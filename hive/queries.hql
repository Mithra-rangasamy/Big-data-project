-- ==============================================================================
-- CIT 21MDS56: Air Quality & Public Health Early-Warning System
-- hive/queries.hql - Historical Analytical Trend & Comparison Queries
-- All 5 required analytical queries:
--   1. 7-day moving average AQI per city
--   2. Worst-performing zones this month
--   3. Daily AQI by zone
--   4. Days exceeding an AQI threshold per city
--   5. Weekday vs Weekend air quality comparison
-- ==============================================================================

USE default;

-- ------------------------------------------------------------------------------
-- QUERY 1: 7-Day Moving Average AQI per City
-- Demonstrates window functions over partitioned time-series
-- ------------------------------------------------------------------------------
SELECT 
    city,
    `date`,
    ROUND(AVG(daily_avg_aqi) OVER (
        PARTITION BY city 
        ORDER BY `date` 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2) AS aqi_7day_moving_avg
FROM (
    SELECT city, `date`, AVG(aqi) as daily_avg_aqi
    FROM aqi_readings
    GROUP BY city, `date`
) daily_city
ORDER BY city, `date` DESC
LIMIT 25;

-- ------------------------------------------------------------------------------
-- QUERY 2: Worst-Performing Zones This Month
-- Identifies persistent hot-spots across all metropolitan zones
-- ------------------------------------------------------------------------------
SELECT 
    city,
    zone_id,
    zone_name,
    ROUND(AVG(aqi), 1) AS monthly_avg_aqi,
    MAX(aqi) AS peak_aqi,
    ROUND(AVG(pm25), 1) AS avg_pm25,
    ROUND(AVG(pm10), 1) AS avg_pm10
FROM aqi_readings
GROUP BY city, zone_id, zone_name
ORDER BY monthly_avg_aqi DESC
LIMIT 10;

-- ------------------------------------------------------------------------------
-- QUERY 3: Daily AQI by Zone
-- Zone-level daily time-series aggregation for trend inspection
-- ------------------------------------------------------------------------------
SELECT 
    city,
    zone_id,
    zone_name,
    `date`,
    ROUND(AVG(aqi), 1) AS daily_avg_aqi,
    MAX(aqi) AS peak_aqi,
    ROUND(AVG(pm25), 1) AS daily_avg_pm25
FROM aqi_readings
GROUP BY city, zone_id, zone_name, `date`
ORDER BY `date` DESC, daily_avg_aqi DESC
LIMIT 25;

-- ------------------------------------------------------------------------------
-- QUERY 4: Days Exceeding an AQI Threshold (AQI > 200: Poor/Severe) per City
-- Identifies municipal vulnerability and violation counts of CPCB standards
-- ------------------------------------------------------------------------------
SELECT 
    city,
    COUNT(DISTINCT `date`) AS total_monitored_days,
    COUNT(DISTINCT CASE WHEN daily_city_aqi > 200 THEN `date` END) AS days_exceeding_200,
    COUNT(DISTINCT CASE WHEN daily_city_aqi > 300 THEN `date` END) AS days_severe_above_300,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN daily_city_aqi > 200 THEN `date` END) / COUNT(DISTINCT `date`), 1) AS violation_percentage
FROM (
    SELECT city, `date`, AVG(aqi) AS daily_city_aqi
    FROM aqi_readings
    GROUP BY city, `date`
) city_daily_summary
GROUP BY city
ORDER BY days_exceeding_200 DESC;

-- ------------------------------------------------------------------------------
-- QUERY 5: Weekday vs Weekend Comparison
-- Evaluates vehicular and commercial emission differences
-- ------------------------------------------------------------------------------
SELECT 
    city,
    day_type,
    ROUND(AVG(aqi), 1) AS avg_aqi,
    ROUND(AVG(pm25), 1) AS avg_pm25,
    ROUND(AVG(no2), 1) AS avg_no2,
    COUNT(*) AS total_hourly_readings
FROM (
    SELECT 
        city,
        aqi,
        pm25,
        no2,
        CASE 
            WHEN from_unixtime(unix_timestamp(`date`, 'yyyy-MM-dd'), 'u') IN ('6', '7') THEN 'WEEKEND'
            ELSE 'WEEKDAY'
        END AS day_type
    FROM aqi_readings
) labeled_readings
GROUP BY city, day_type
ORDER BY city, day_type;
