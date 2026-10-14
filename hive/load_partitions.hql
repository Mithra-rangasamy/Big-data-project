-- ==============================================================================
-- CIT 21MDS56: Air Quality & Public Health Early-Warning System
-- hive/load_partitions.hql - Registers all HDFS partitions into Hive Metastore
-- ==============================================================================

MSCK REPAIR TABLE aqi_readings;
MSCK REPAIR TABLE weather_data;
