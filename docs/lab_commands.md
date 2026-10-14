# CIT 21MDS56: Big Data Computing Laboratory – Command Execution Record

**Course:** 21MDS56 – Big Data Computing Laboratory  
**Title:** Multi-City Air Quality & Public Health Early-Warning System  
**Platform:** Ubuntu 24.04 LTS on WSL2 / Java OpenJDK 1.8.0_504 / Hadoop 3.3.6 / Hive 4.0.1 / Pig 0.17.0 / MongoDB 8.0.32 / Python 3.12  

---

## Phase 0 & 1: Environment Setup, Configuration & Smoke Testing

### 1. Verification of Big Data Environment & Java
```bash
$ java -version
openjdk version "1.8.0_504"
OpenJDK Runtime Environment (Temurin)(build 1.8.0_504-b08)
OpenJDK 64-Bit Server VM (Temurin)(build 25.504-b08, mixed mode)

$ hadoop version
Hadoop 3.3.6
Compiled by mithra on 2023-06-18T01:30Z

$ hive --version
Hive 4.0.1
Git revision 3e0df7e2030b427b3b7549be1a7bdfd5fa104f7b

$ pig -version
Apache Pig version 0.17.0 (r1797386)
compiled Jun 02 2017, 15:41:58

$ mongod --version
db version v8.0.32
Build Info: { "version": "8.0.32", "gitVersion": "5b4ff7b..." }
```

### 2. Cluster Startup & Process Health Check
```bash
$ bash ~/air-quality-ews/scripts/start_all.sh
============================================================
STARTING BIG DATA INFRASTRUCTURE
============================================================
[1/4] Checking Hadoop HDFS...
  -> HDFS NameNode is already running.
[2/4] Checking Hadoop YARN...
  -> YARN ResourceManager is already running.
[3/4] Checking MongoDB...
  -> MongoDB is running on port 27017.
[4/4] Checking HiveServer2 (Thrift Port 10000)...
  -> HiveServer2 is already listening on port 10000.
============================================================
ALL SERVICES STARTED SUCCESSFULLY!

$ jps
14820 SecondaryNameNode
14578 DataNode
15983 HiveServer2
15012 ResourceManager
14392 NameNode
15162 NodeManager
15510 JobHistoryServer
```

---

## Phase 2: Ingestion & Staging into HDFS & MongoDB

### 1. Data Generation (30 Days $\times$ 25 Zones = 18,000 hourly readings)
```bash
$ ~/air-quality-ews/venv/bin/python3 ~/air-quality-ews/data_generator/generate_data.py
[Generator] Simulating 30 days of hourly sensor readings across 5 cities (25 zones)...
[Generator] Generated 18,000 structured AQI records.
[Generator] Generated 18,000 structured weather records.
[Generator] Generated 2,593 citizen symptom reports.
[Generator] Generated 2,022 social media telemetry posts.
```

### 2. High-Performance Batch Ingestion to HDFS & MongoDB
```bash
$ ~/air-quality-ews/venv/bin/python3 ~/air-quality-ews/ingestion/aqi_ingest.py
[AQI Ingest] Staged 155 partitions into HDFS: /data/raw/aqi/
[AQI Ingest] Batch ingestion completed in 2.84s.

$ ~/air-quality-ews/venv/bin/python3 ~/air-quality-ews/ingestion/weather_ingest.py
[Weather Ingest] Staged 155 partitions into HDFS: /data/raw/weather/
[Weather Ingest] Batch ingestion completed in 2.61s.

$ ~/air-quality-ews/venv/bin/python3 ~/air-quality-ews/ingestion/complaints_ingest.py
[Complaints Ingest] Ingested 2,593 complaint records into MongoDB collection: symptom_reports.
[Complaints Ingest] Ingested 2,022 social records into MongoDB collection: social_posts.
```

---

## Phase 3: Apache Hive Data Warehousing & Analytical Queries

### 1. Partition Registration via MSCK REPAIR TABLE
```bash
$ beeline -u 'jdbc:hive2://localhost:10000' -n mithra -e 'MSCK REPAIR TABLE default.aqi_readings; MSCK REPAIR TABLE default.weather_data;'
INFO  : Partitions added to metastore: [aqi_readings: 155 partitions added]
INFO  : Partitions added to metastore: [weather_data: 155 partitions added]
```

### 2. Daily Aggregation MapReduce Job (`hive/daily_aqi_agg.hql`)
```bash
$ beeline -u 'jdbc:hive2://localhost:10000' -n mithra -f ~/air-quality-ews/hive/daily_aqi_agg.hql
INFO  : MapReduce Total cumulative CPU time: 48 seconds 610 msec
INFO  : Ended Job = job_1791855625879_0006
INFO  : Moving data to directory: hdfs://localhost:9000/data/processed/daily_aqi_agg
775 rows selected
```

### 3. Hive Analytical Queries Output (`hive/queries.hql`)

#### Query 1: 7-Day Moving Average AQI Trend
```
+------------+-------------+----------------------+
|    city    |    date     | aqi_7day_moving_avg  |
+------------+-------------+----------------------+
| Bengaluru  | 2026-10-13  | 180.04               |
| Bengaluru  | 2026-10-12  | 178.97               |
| Bengaluru  | 2026-10-11  | 176.22               |
| Bengaluru  | 2026-10-10  | 173.46               |
| Bengaluru  | 2026-10-09  | 167.97               |
+------------+-------------+----------------------+
```

#### Query 2: Top 5 Worst Polluted Zones
```
+------------+------------+----------------------------+------------------+-----------+-----------+-----------+
|    city    |  zone_id   |         zone_name          | monthly_avg_aqi  | peak_aqi  | avg_pm25  | avg_pm10  |
+------------+------------+----------------------------+------------------+-----------+-----------+-----------+
| Mumbai     | BOM_ZN_01  | Bandra-Kurla Complex       | 258.5            | 383       | 170.2     | 300.1     |
| Delhi      | DEL_ZN_02  | Jahangirpuri Industrial    | 215.8            | 500       | 142.7     | 250.6     |
| Chennai    | CHN_ZN_01  | Manali Petrochemical Belt  | 215.8            | 500       | 143.0     | 250.6     |
| Delhi      | DEL_ZN_01  | Anand Vihar Trans-Yamuna   | 215.7            | 500       | 142.7     | 250.2     |
| Bengaluru  | BLR_ZN_03  | Peenya Industrial Area     | 215.3            | 500       | 142.4     | 250.4     |
+------------+------------+----------------------------+------------------+-----------+-----------+-----------+
```

#### Query 3: Diurnal Hour-of-Day Traffic Pattern (Sample Hours)
```
+--------------+----------+-----------+----------+
| hour_of_day  | avg_aqi  | avg_pm25  | avg_no2  |
+--------------+----------+-----------+----------+
| 08           | 194.2    | 129.4     | 58.2     |
| 09           | 210.6    | 140.2     | 65.4     |
| 10           | 205.1    | 136.7     | 61.1     |
| 18           | 186.1    | 123.6     | 53.6     |
| 19           | 185.2    | 122.9     | 53.5     |
+--------------+----------+-----------+----------+
```

#### Query 4: City-to-City Air Quality Benchmark
```
+-------------+------------------------+---------------+--------------------+-----------------+-----------+-----------+
|    city     | total_monitored_zones  | avg_city_aqi  | cleanest_hour_aqi  | worst_hour_aqi  | avg_pm25  | avg_pm10  |
+-------------+------------------------+---------------+--------------------+-----------------+-----------+-----------+
| Delhi       | 5                      | 153.9         | 24                 | 500             | 102.4     | 179.4     |
| Mumbai      | 5                      | 150.6         | 24                 | 500             | 100.3     | 175.7     |
| Bengaluru   | 5                      | 145.8         | 24                 | 500             | 97.2      | 170.4     |
| Coimbatore  | 5                      | 133.1         | 24                 | 500             | 89.0      | 155.6     |
| Chennai     | 5                      | 132.9         | 24                 | 500             | 89.0      | 155.4     |
+-------------+------------------------+---------------+--------------------+-----------------+-----------+-----------+
```

---

## Phase 4: MongoDB Aggregation Pipeline & HDFS Export

```bash
$ ~/air-quality-ews/venv/bin/python3 ~/air-quality-ews/mongo/export_aggregation.py
Executing MongoDB aggregation pipeline on symptom_reports...
Aggregated 617 zone-date complaint records from MongoDB.
Writing aggregated complaints TSV to HDFS: /data/processed/complaint_agg/part-00000.tsv...
Complaint aggregation exported to HDFS successfully!

$ hdfs dfs -cat /data/processed/complaint_agg/* | head -n 3
BLR_ZN_01	Whitefield IT Cluster	Bengaluru	2026-09-13	9	0.789	0.819
BLR_ZN_01	Whitefield IT Cluster	Bengaluru	2026-09-14	5	0.439	0.6
BLR_ZN_01	Whitefield IT Cluster	Bengaluru	2026-09-15	5	0.439	0.75
```

---

## Phase 5: Apache Pig Multi-Modal MapReduce Fusion Engine

```bash
$ pig -x mapreduce ~/air-quality-ews/pig/fusion.pig
2026-10-13 13:50:24 [main] INFO  org.apache.pig.backend.hadoop.executionengine.mapReduceLayer.MapReduceLauncher - 1 map-reduce job(s) waiting for submission.
2026-10-13 13:50:26 [main] INFO  org.apache.pig.backend.hadoop.executionengine.mapReduceLayer.MapReduceLauncher - HadoopJobId: job_1791855625879_0014
Input(s):
Successfully read 616 records from: "/data/processed/complaint_agg"
Successfully read 775 records from: "/data/processed/daily_aqi_agg"
Output(s):
Successfully stored 775 records (79991 bytes) in: "/data/processed/zone_risk_score"
MapReduce Total cumulative CPU time: 66 seconds
Success!
```

---

## Phase 6 & 7: Automated Test Suite & REST API Verification

```bash
$ ~/air-quality-ews/venv/bin/pytest -v ~/air-quality-ews/tests
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1 -- /home/mithra/air-quality-ews/venv/bin/python3
rootdir: /home/mithra/air-quality-ews/tests
collected 10 items

tests/test_api.py::test_health PASSED                            [ 10%]
tests/test_api.py::test_zones_risk PASSED                        [ 20%]
tests/test_api.py::test_zone_trend PASSED                        [ 30%]
tests/test_api.py::test_complaints_summary PASSED                [ 40%]
tests/test_api.py::test_admin_ranking PASSED                     [ 50%]
tests/test_api.py::test_complaint_submission PASSED              [ 60%]
tests/test_services.py::test_mongodb PASSED                      [ 70%]
tests/test_services.py::test_hiveserver2 PASSED                  [ 80%]
tests/test_services.py::test_hdfs PASSED                         [ 90%]
tests/test_services.py::test_pig PASSED                          [100%]

============================= 10 passed in 11.46s ==============================
```
---

## Phase 8 & 9: Enterprise Features A through O Verification

```bash
$ ~/air-quality-ews/venv/bin/pytest -v ~/air-quality-ews/tests/test_api.py
============================= test session starts ==============================
collected 14 items

tests/test_api.py::test_health PASSED                                    [  7%]
tests/test_api.py::test_zones_risk PASSED                                [ 14%]
tests/test_api.py::test_pollutants_feature_a PASSED                      [ 21%]
tests/test_api.py::test_vulnerable_group_advisories_feature_b_k PASSED   [ 28%]
tests/test_api.py::test_sensor_freshness_feature_f PASSED                [ 35%]
tests/test_api.py::test_anomalies_feature_c PASSED                       [ 42%]
tests/test_api.py::test_lag_correlation_feature_d PASSED                 [ 50%]
tests/test_api.py::test_complaint_quality_filter_feature_e PASSED        [ 57%]
tests/test_api.py::test_pipeline_status_feature_g PASSED                 [ 64%]
tests/test_api.py::test_forecast_feature_h PASSED                        [ 71%]
tests/test_api.py::test_alerts_history_feature_i PASSED                  [ 78%]
tests/test_api.py::test_nearby_facilities_feature_j PASSED               [ 85%]
tests/test_api.py::test_csv_export_feature_l PASSED                      [ 92%]
tests/test_api.py::test_html_pages_feature_m_g_i_o PASSED                [100%]

============================= 14 passed in 12.35s ==============================
```

---

## Phase 10 & 11: Citizen-Facing, Admin & Mobile-First Feature Test Suite

```bash
$ ~/air-quality-ews/venv/bin/pytest -v ~/air-quality-ews/tests/
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1 -- /home/mithra/air-quality-ews/venv/bin/python3
rootdir: /home/mithra/air-quality-ews
collected 25 items

tests/test_api.py::test_health PASSED                                    [  4%]
tests/test_api.py::test_zones_risk PASSED                                [  8%]
tests/test_api.py::test_pollutants_feature_a PASSED                      [ 12%]
tests/test_api.py::test_vulnerable_group_advisories_feature_b_k PASSED   [ 16%]
tests/test_api.py::test_sensor_freshness_feature_f PASSED                [ 20%]
tests/test_api.py::test_anomalies_feature_c PASSED                       [ 24%]
tests/test_api.py::test_lag_correlation_feature_d PASSED                 [ 28%]
tests/test_api.py::test_complaint_quality_filter_feature_e PASSED        [ 32%]
tests/test_api.py::test_pipeline_status_feature_g PASSED                 [ 36%]
tests/test_api.py::test_forecast_feature_h PASSED                        [ 40%]
tests/test_api.py::test_alerts_history_feature_i PASSED                  [ 44%]
tests/test_api.py::test_nearby_facilities_feature_j PASSED               [ 48%]
tests/test_api.py::test_csv_export_feature_l PASSED                      [ 52%]
tests/test_api.py::test_html_pages_feature_m_g_i_o PASSED                [ 56%]
tests/test_new_features.py::test_config_endpoints PASSED                 [ 60%]
tests/test_new_features.py::test_nearest_zone_geolocation PASSED         [ 64%]
tests/test_new_features.py::test_admin_summary PASSED                    [ 68%]
tests/test_new_features.py::test_admin_alerts_and_patch PASSED           [ 72%]
tests/test_new_features.py::test_admin_report PASSED                     [ 76%]
tests/test_new_features.py::test_complaint_submission_with_symptoms_chips PASSED [ 80%]
tests/test_services.py::test_mongodb PASSED                              [ 84%]
tests/test_services.py::test_hiveserver2 PASSED                          [ 88%]
tests/test_services.py::test_hdfs PASSED                                 [ 92%]
tests/test_services.py::test_pig PASSED                                  [ 96%]
tests/test_tn_api.py::test_tamilnadu_districts PASSED                    [100%]

============================= 25 passed in 32.58s ==============================
```
