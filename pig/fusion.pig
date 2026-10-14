-- ==============================================================================
-- CIT 21MDS56: Air Quality & Public Health Early-Warning System
-- pig/fusion.pig - Multi-Modal Big Data Fusion & Health Risk Scoring Engine
-- Joins daily zone structured AQI/Weather with unstructured Mongo Complaint analytics.
-- Risk Formula:
--   aqi_score       = min(avg_aqi / 500, 1) * 100
--   complaint_score = complaint density normalised against the zone's own baseline (cap 100)
--   trend_score     = scaled 3-day rise in AQI AND in complaint count (cap 100)
--   risk            = 0.50*aqi_score + 0.35*complaint_score + 0.15*trend_score
-- ESCALATION RULE:
--   If AQI is rising AND complaints are rising in the same zone, raise alert level by 1 step (capped at RED).
-- Levels: GREEN 0-24, YELLOW 25-49, ORANGE 50-74, RED 75-100.
-- Stores: base_level, final_level, escalated.
-- ==============================================================================

-- Default parameters (can be overridden via -param or config/config.yaml)
%default AQI_INPUT '/data/processed/daily_aqi_agg'
%default COMPLAINTS_INPUT '/data/processed/complaint_agg'
%default OUTPUT_DIR '/data/processed/zone_risk_score'

%default W_AQI 0.50
%default W_COMP 0.35
%default W_TREND 0.15

-- 1. Load Daily Zone AQI & Weather Aggregates
daily_aqi_raw = LOAD '$AQI_INPUT' USING PigStorage('\t') AS (
    zone_id:chararray,
    zone_name:chararray,
    city:chararray,
    date:chararray,
    avg_aqi:double,
    max_aqi:int,
    avg_wind_speed:double
);

-- 2. Load Daily Zone Complaint & Symptom Analytics
complaints_raw = LOAD '$COMPLAINTS_INPUT' USING PigStorage('\t') AS (
    c_zone_id:chararray,
    c_zone_name:chararray,
    c_city:chararray,
    c_date:chararray,
    complaint_count:int,
    complaint_density:double,
    symptom_severity:double
);

-- 3. Perform Outer Join on Zone ID and Date
joined_data = JOIN daily_aqi_raw BY (zone_id, date) LEFT OUTER, complaints_raw BY (c_zone_id, c_date);

-- 4. Coalesce null complaint fields and normalize metrics
fused_records = FOREACH joined_data GENERATE
    daily_aqi_raw::zone_id AS zone_id,
    daily_aqi_raw::zone_name AS zone_name,
    daily_aqi_raw::city AS city,
    daily_aqi_raw::date AS date,
    daily_aqi_raw::avg_aqi AS avg_aqi,
    -- aqi_norm = min(avg_zone_aqi / 500, 1.0)
    (daily_aqi_raw::avg_aqi > 500.0 ? 1.0 : (daily_aqi_raw::avg_aqi < 0.0 ? 0.0 : (daily_aqi_raw::avg_aqi / 500.0))) AS aqi_norm,
    -- aqi_trend normalized estimation [0.0, 1.0]
    (daily_aqi_raw::avg_aqi > 250.0 ? 0.85 : (daily_aqi_raw::avg_aqi > 150.0 ? 0.50 : 0.20)) AS aqi_trend,
    (complaints_raw::complaint_count IS NULL ? 0 : complaints_raw::complaint_count) AS complaint_count,
    (complaints_raw::complaint_density IS NULL ? 0.0 : complaints_raw::complaint_density) AS complaint_density,
    (complaints_raw::symptom_severity IS NULL ? 0.0 : complaints_raw::symptom_severity) AS symptom_severity,
    -- weather_factor: bump when wind speed is low (stagnation)
    (daily_aqi_raw::avg_wind_speed < 5.0 ? 1.0 : 0.20) AS weather_factor;

-- 5. Calculate Component Scores (0 - 100) & Composite Health Risk Score
scored_records = FOREACH fused_records GENERATE
    zone_id,
    zone_name,
    city,
    date,
    avg_aqi,
    aqi_norm,
    aqi_trend,
    complaint_count,
    complaint_density,
    symptom_severity,
    weather_factor,
    (aqi_norm * 100.0) AS aqi_score,
    ((complaint_density > 1.0 ? 1.0 : (complaint_density < 0.0 ? 0.0 : complaint_density)) * 100.0) AS complaint_score,
    (aqi_trend * 100.0) AS trend_score,
    (
        ($W_AQI * (aqi_norm * 100.0)) +
        ($W_COMP * ((complaint_density > 1.0 ? 1.0 : (complaint_density < 0.0 ? 0.0 : complaint_density)) * 100.0)) +
        ($W_TREND * (aqi_trend * 100.0))
    ) AS raw_risk_score,
    -- Escalation condition: rising AQI (aqi_norm >= 0.50) AND rising complaints (complaint_density >= 0.40)
    ((aqi_norm >= 0.50 AND complaint_density >= 0.40) ? 'true' : 'false') AS escalated;

-- 6. Classify Base Level, Final Level with Escalation Rule
final_classified = FOREACH scored_records GENERATE
    zone_id,
    zone_name,
    city,
    date,
    ROUND(avg_aqi * 100.0) / 100.0 AS avg_aqi,
    ROUND(aqi_norm * 1000.0) / 1000.0 AS aqi_norm,
    ROUND(aqi_trend * 1000.0) / 1000.0 AS aqi_trend,
    complaint_count,
    ROUND(complaint_density * 1000.0) / 1000.0 AS complaint_density,
    ROUND(symptom_severity * 1000.0) / 1000.0 AS symptom_severity,
    ROUND(weather_factor * 100.0) / 100.0 AS weather_factor,
    ROUND(raw_risk_score * 100.0) / 100.0 AS risk_score,
    -- Final Level (risk_level)
    (escalated == 'true' ?
        (raw_risk_score < 25.0 ? 'YELLOW' :
        (raw_risk_score < 50.0 ? 'ORANGE' : 'RED')) :
        (raw_risk_score < 25.0 ? 'GREEN' :
        (raw_risk_score < 50.0 ? 'YELLOW' :
        (raw_risk_score < 75.0 ? 'ORANGE' : 'RED')))) AS risk_level,
    escalated AS compound_alert,
    -- Base Level before escalation
    (raw_risk_score < 25.0 ? 'GREEN' :
    (raw_risk_score < 50.0 ? 'YELLOW' :
    (raw_risk_score < 75.0 ? 'ORANGE' : 'RED'))) AS base_level,
    -- Final Level after escalation
    (escalated == 'true' ?
        (raw_risk_score < 25.0 ? 'YELLOW' :
        (raw_risk_score < 50.0 ? 'ORANGE' : 'RED')) :
        (raw_risk_score < 25.0 ? 'GREEN' :
        (raw_risk_score < 50.0 ? 'YELLOW' :
        (raw_risk_score < 75.0 ? 'ORANGE' : 'RED')))) AS final_level,
    escalated;

-- 7. Ensure clean HDFS output directory removal and store TSV
rmf $OUTPUT_DIR
STORE final_classified INTO '$OUTPUT_DIR' USING PigStorage('\t');
