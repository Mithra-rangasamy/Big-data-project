# Multi-City Air Quality & Public Health Early-Warning System: Architecture & Data Flow

**Course:** 21MDS56 – Big Data Computing Laboratory  
**Institution:** Coimbatore Institute of Technology (CIT), Coimbatore  
**Author:** Mithra (M.Sc Data Science)  

---

## 1. System Architecture Overview

The system architecture is organized into four distinct operational tiers:
1. **Multi-Modal Data Ingestion Tier:** Hourly physical sensor feeds and asynchronous citizen symptom streams.
2. **Distributed Storage & Processing Tier (Hadoop / Hive / MongoDB):** HDFS distributed filesystem, Hive partitioning, and MongoDB document indexing.
3. **Big Data Fusion Engine (Apache Pig):** MapReduce relational joining, normalization, composite health risk scoring, and tier escalation.
4. **Surveillance & Early-Warning Delivery Tier:** High-performance Flask REST API service with TTL caching and an interactive Leaflet/Chart.js web dashboard.

```mermaid
flowchart TD
    subgraph Data_Sources ["1. Multi-Modal Data Sources (5 Cities / 25 Zones)"]
        S1["Structured Telemetry<br>(AQI, PM2.5, PM10, Weather)"]
        S2["Unstructured Citizen Reports<br>(Hotlines, Web Portal, Symptoms)"]
    end

    subgraph Storage_Tier ["2. Storage & Big Data Processing Tier"]
        HDFS_RAW["HDFS Raw Partitioned Lake<br>/data/raw/aqi/date=.../city=...<br>/data/raw/weather/date=.../city=..."]
        MONGO_DB["MongoDB 8.0 Enterprise<br>db: air_quality_ews<br>col: symptom_reports"]
        
        HIVE_AGG["Apache Hive 4.0.1 (MapReduce)<br>daily_aqi_agg.hql<br>Aggregates 24h Mean AQI & Wind"]
        MONGO_AGG["PyMongo Aggregation Pipeline<br>export_aggregation.py<br>Computes Symptom Density & Severity"]
        
        HDFS_PROC_AQI["HDFS Processed Structured<br>/data/processed/daily_aqi_agg"]
        HDFS_PROC_COMP["HDFS Processed Unstructured<br>/data/processed/complaint_agg"]
    end

    subgraph Fusion_Engine ["3. Big Data Fusion Engine (Apache Pig 0.17.0)"]
        PIG_JOIN["Pig Latin Outer Join<br>JOIN daily_aqi_raw BY (zone_id, date)<br>LEFT OUTER complaints_raw BY (c_zone_id, c_date)"]
        PIG_SCORE["Composite Health Risk Scoring<br>100 * (0.35*A + 0.15*T + 0.30*C + 0.15*S + 0.05*W)"]
        PIG_ESCALATE["Compound Alert Escalator<br>Elevates High AQI + Surging Illness to RED"]
        HDFS_RISK["HDFS Fused Output TSV<br>/data/processed/zone_risk_score"]
        HIVE_EXT["Hive External Table<br>air_quality_ews.zone_risk_score"]
    end

    subgraph Serving_Dashboard ["4. Serving & Surveillance Dashboard Tier"]
        FLASK_API["Flask REST API Backend (0.0.0.0:5000)<br>High-Performance In-Memory TTL Cache<br>Clinical Advisory Rule Engine"]
        WEB_UI["Interactive Early-Warning Web Dashboard<br>Leaflet.js Map + Chart.js 30-Day Trends<br>Citizen Symptom Reporting Portal"]
    end

    S1 -->|Batch HDFS Put| HDFS_RAW
    S2 -->|PyMongo Direct / Web API| MONGO_DB

    HDFS_RAW --> HIVE_AGG
    HIVE_AGG --> HDFS_PROC_AQI

    MONGO_DB --> MONGO_AGG
    MONGO_AGG --> HDFS_PROC_COMP

    HDFS_PROC_AQI --> PIG_JOIN
    HDFS_PROC_COMP --> PIG_JOIN
    PIG_JOIN --> PIG_SCORE
    PIG_SCORE --> PIG_ESCALATE
    PIG_ESCALATE --> HDFS_RISK
    HDFS_RISK --> HIVE_EXT

    HDFS_RISK --> FLASK_API
    HIVE_EXT --> FLASK_API
    MONGO_DB --> FLASK_API
    FLASK_API --> WEB_UI
    WEB_UI -->|Citizen Report POST| FLASK_API
```

---

## 2. Relational Schemas & Storage Design

### 2.1 HDFS Raw Partitioning Scheme
To optimize partition pruning during daily analytical scans, structured telemetry is partitioned symmetrically by `date` and `city`:
```
/data/raw/aqi/date=YYYY-MM-DD/city=<CityName>/aqi.json
/data/raw/weather/date=YYYY-MM-DD/city=<CityName>/weather.json
```
- Total Partitions per Dataset: 31 days $\times$ 5 cities = **155 partitions**.
- Record Volume: 18,000 hourly AQI records + 18,000 hourly weather records.

### 2.2 Apache Hive Data Definition
Hive external tables manage structured datasets directly on top of HDFS:

```sql
CREATE EXTERNAL TABLE aqi_readings (
    record_id STRING,
    zone_id STRING,
    zone_name STRING,
    ts STRING,
    aqi INT,
    pm25 DOUBLE,
    pm10 DOUBLE,
    no2 DOUBLE,
    so2 DOUBLE,
    co DOUBLE
)
PARTITIONED BY (`date` STRING, city STRING)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.JsonSerDe'
LOCATION '/data/raw/aqi';
```

### 2.3 MongoDB Document Structure
Citizen complaints are represented as rich JSON documents in MongoDB `symptom_reports`:

```json
{
  "_id": "6ace3a72353f02c466dbdf02",
  "report_id": "RPT-WEB-1791900252",
  "city": "Coimbatore",
  "zone_id": "CBE_ZN_01",
  "zone_name": "SIDCO Industrial Estate",
  "date": "2026-10-13",
  "date_str": "2026-10-13",
  "reported_at": "2026-10-13 14:04:12",
  "symptoms": ["cough", "shortness_of_breath"],
  "severity": "severe",
  "age_group": "adult",
  "channel": "citizen_web_portal",
  "description": "Thick acrid fumes near factory gates"
}
```

---

## 3. End-to-End Orchestration Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Citizen as Citizen / User
    participant Web as Web Dashboard (Browser)
    participant Flask as Flask REST API (Port 5000)
    participant Mongo as MongoDB 8.0 (Port 27017)
    participant Hive as Apache Hive 4.0.1 (MapReduce)
    participant Pig as Apache Pig 0.17.0 (YARN)
    participant HDFS as Hadoop HDFS (Port 9000)

    Citizen->>Web: Submits Symptom Report
    Web->>Flask: POST /api/complaints
    Flask->>Mongo: insert_one(symptom_reports)
    Mongo-->>Flask: Acknowledgement (report_id)
    Flask-->>Web: 201 Created

    Note over Flask,Pig: Pipeline Recalculation Triggered (Manual / Scheduled)
    Flask->>Hive: Execute daily_aqi_agg.hql
    Hive->>HDFS: Stores /data/processed/daily_aqi_agg
    Flask->>Mongo: Execute export_aggregation.py
    Mongo->>HDFS: Exports /data/processed/complaint_agg
    Flask->>Pig: Run pig -x mapreduce fusion.pig
    Pig->>HDFS: Outer join & compute /data/processed/zone_risk_score
    Pig-->>Flask: Pipeline SUCCEEDED
    Flask->>Flask: Reloads in-memory TTL cache
    Web->>Flask: GET /api/zones/risk
    Flask-->>Web: Enriched GeoJSON Risk Scores & Advisories
    Web->>Citizen: Displays Red Pulsing Compound Alert on Map
```
