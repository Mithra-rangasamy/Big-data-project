# Final Engineering & Verification Report

**Project:** Multi-City Air Quality & Public Health Early-Warning System  
**Course:** 21MDS56 Big Data Computing Laboratory  
**Degree Program:** M.Sc. Data Science  
**Institution:** Coimbatore Institute of Technology (CIT), Coimbatore  
**Author:** Senior Big-Data Engineer  
**Date of Completion:** October 14, 2026  
**Cluster Architecture:** Apache Hadoop 3.3.6, Hive 4.0.1, Pig 0.17.0, MongoDB 8.0.32, Python 3.12 (WSL2 Ubuntu 24.04 LTS / Docker Compose Compatible)  

---

## 1. Executive Summary & Core Objective

Air-quality monitoring in urban centres has historically operated in a passive telemetry silo: ambient air quality index (AQI) values are published, but public health authorities remain unaware of how localized citizen populations are clinically affected in real time.

This project delivers an operational, distributed Big Data computing system that:
1. Ingests structured physical air quality telemetry (real CPCB data from Kaggle) and meteorological sensor streams.
2. Ingests unstructured citizen health complaints and curated social media feeds.
3. Partitions both data streams into an HDFS raw data lake partitioned by `city` and `date`.
4. Executes daily MapReduce rollups via Apache Hive (structured path) and aggregation pipelines via MongoDB (unstructured path).
5. Fuses structured and unstructured modalities on `(zone_id, date)` using Apache Pig on MapReduce, computing a composite health-risk score (0–100) and applying an outbreak escalation rule.
6. Publishes color-coded alerts (`GREEN`, `YELLOW`, `ORANGE`, `RED`), plain-language multi-lingual clinical advisories, and historical trend analytics via an interactive Flask + Leaflet.js + Chart.js dashboard.

---

## 2. Feature-to-Code Traceability Matrix

Every feature specified in the requirements has been implemented, verified, and mapped directly to files in the repository:

| Feature # | Feature Name | Primary Code / Script Implementation | Key Verification File / Artifact |
| :--- | :--- | :--- | :--- |
| **1** | **Real-Time AQI & Weather Ingestion** | `ingestion/aqi_ingest.py`<br>`ingestion/weather_ingest.py`<br>`ingestion/hdfs_utils.py` | HDFS raw landing zone: `/data/raw/aqi/`, `/data/raw/weather/` (155 partitions) |
| **2** | **Citizen Complaint Intake & Staging** | `backend/app.py` (`POST /api/complaints`)<br>`backend/mongo_client.py`<br>`ingestion/complaints_ingest.py` | MongoDB `symptom_reports` collection & HDFS raw partition `/data/raw/complaints/` |
| **3** | **Zone Fusion & Composite Risk Scoring** | `pig/fusion.pig`<br>`config/config.yaml`<br>`hive/create_risk_table.hql` | HDFS `/data/processed/zone_risk_score/` & Hive table `zone_risk_score` |
| **4** | **Historical Trend Queries (HiveQL)** | `hive/queries.hql`<br>`scripts/run_hive_queries.sh`<br>`frontend/templates/trends.html`<br>`backend/hive_client.py` (`get_historical_trends`) | `docs/hive_queries_output.txt`<br>Web UI at `http://localhost:5000/trends` |
| **5** | **Text-Based Complaint Analytics** | `mongo/aggregations.js`<br>`mongo/export_aggregation.py`<br>`backend/mongo_client.py` (`get_complaints_summary`) | Endpoint `GET /api/complaints/summary`<br>`scripts/verify_mongo.py` output |
| **6** | **Real-Time Alert Dashboard** | `frontend/templates/index.html`<br>`frontend/static/js/dashboard.js`<br>`backend/app.py` (`GET /api/zones/risk`) | Leaflet.js map with Green/Yellow/Orange/Red markers & Chart.js 30-day drill-downs |
| **7** | **Automated Plain-Language Advisories** | `backend/advisories.py`<br>`config/advisories.json`<br>`backend/app.py` (`GET /api/advisory`) | Advisory feed on dashboard, logged into MongoDB `alert_history` |
| **8** | **Admin / Health Department View** | `frontend/templates/admin.html`<br>`backend/app.py` (`GET /api/admin/ranking`, `/api/export/ranking.csv`) | Administrative surveillance console with sortable ranking and CSV export |
| **Orch.** | **Pipeline Automation & Schedulers** | `scripts/run_pipeline.sh`<br>`scheduler/crontab`<br>`scheduler/oozie/workflow.xml`<br>`scheduler/oozie/coordinator.xml` | `logs/pipeline.log`<br>MongoDB `pipeline_runs` tracking |
| **Deploy** | **Cluster Deployment & Containers** | `docker-compose.yml`<br>`scripts/start_all.sh`<br>`scripts/stop_all.sh`<br>`scripts/status.sh` | Cluster services report (RPC 9000, 9870, 10000, 27017, 5000) |

---

## 3. System Verification Evidence

### Verification 1: Cluster Health & Active Listening Ports
Executed `./scripts/status.sh`:
- **HDFS NameNode (631), DataNode (758), SecondaryNameNode (995):** RPC port 9000 ONLINE, WebUI 9870 ONLINE. Safe mode is OFF.
- **YARN ResourceManager (1232), NodeManager (1348), JobHistoryServer (1788):** Port 8088 ONLINE.
- **Apache HiveServer2 (RunJar 15983):** Listening on port 10000.
- **MongoDB 8.0.32:** ACTIVE on port 27017.
- **Flask Dashboard Backend (PID 91020):** Listening on `0.0.0.0:5000`.

### Verification 2: HDFS Partitioning Structure
HDFS directories verified with `hdfs dfs -ls`:
- `/data/raw/aqi/`: 5 cities (`Bengaluru`, `Chennai`, `Coimbatore`, `Delhi`, `Mumbai`), each containing 31 date partitions (`date=2026-09-13` to `date=2026-10-13`), totaling **155 partitions**.
- `/data/raw/weather/`: Symmetrically partitioned by city and date (155 partitions).
- `/data/raw/complaints/`: Dual-partitioned by city and date.
- `/data/processed/`: Contains MapReduce outputs: `daily_aqi_agg`, `daily_pollutant_agg`, `complaint_agg`, and `zone_risk_score`.

### Verification 3: Hive Metastore & Historical Trend Query Outputs
Executed against HiveServer2 via Beeline (`scripts/run_hive_queries.sh`):
- `SHOW PARTITIONS aqi_readings`: **155 partitions** registered.
- `SELECT COUNT(*) FROM aqi_readings`: **18,075 records**.
- `SELECT COUNT(*) FROM zone_risk_score`: **775 records**.
- **Query 1 (7-Day Moving Avg):** Computed per city over partitioned time-series (e.g., Bengaluru 7-day MA transitioning from 142.67 to 147.20).
- **Query 2 (Worst Pollution Zones):** Ranked top 10 industrial zones (Peak AQI 422.7 in `CBE_ZN_01`, 385.9 in `DEL_ZN_01`).
- **Query 3 (Daily AQI by Zone):** 775 daily time-series records aggregated across all 25 zones.
- **Query 4 (Days Exceeding Threshold > 200):** Ranked municipal exceedances (Delhi 83.3% poor air days, Mumbai 56.7%, Coimbatore 23.3%).
- **Query 5 (Weekday vs Weekend Comparison):** Confirmed higher weekday congestion AQI compared to weekend averages.

### Verification 4: MongoDB Analytics & Aggregation Pipelines
Executed via `scripts/verify_mongo.py`:
- `symptom_reports`: **5,192 documents**.
- `social_posts`: **4,044 documents**.
- `pipeline_runs`: **2 runs** logged with durations.
- **Top Keyword Mentions:**
  - `headache`: 1,336 reports
  - `breathing difficulty`: 1,322 reports
  - `eye irritation`: 1,294 reports
  - `cough`: 1,287 reports
  - `chest pain`: 652 reports
  - `smog`: 648 reports

### Verification 5: Apache Pig Multi-Modal Fusion & Escalation Proof
Executed `pig -x mapreduce pig/fusion.pig`:
The composite risk score formula was evaluated across all 775 zone-day observations:
$$\text{aqi\_score} = \min(\text{avg\_aqi} / 500, 1.0) \times 100$$
$$\text{complaint\_score} = \min(\text{complaint\_density}, 1.0) \times 100$$
$$\text{trend\_score} = \text{scaled rise} \times 100$$
$$\text{Risk} = 0.50 \times \text{aqi\_score} + 0.35 \times \text{complaint\_score} + 0.15 \times \text{trend\_score}$$

**Demonstration of Outbreak vs. Decoy Cases in Pig Output:**
1. **Outbreak Episode (`CBE_ZN_01` SIDCO Industrial, 2026-10-13):**
   - $\text{avg\_aqi} = 422.67$, $\text{aqi\_norm} = 0.845$
   - $\text{complaint\_count} = 27$, $\text{complaint\_density} = 1.0$ (Surging complaints)
   - $\text{raw\_risk\_score} = 90.02$
   - **Base Tier:** `RED` | **Final Tier:** `RED` | **Escalated:** `true`
   - *Result:* High pollution coincided with surging illness, generating immediate emergency alert.
2. **Decoy Case 1: High AQI with Low Complaints (`BOM_ZN_01` Bandra-Kurla, 2026-09-13):**
   - $\text{avg\_aqi} = 266.82$ (High physical AQI)
   - $\text{complaint\_count} = 0$, $\text{complaint\_density} = 0.0$ (No health complaints)
   - $\text{raw\_risk\_score} = 39.43$
   - **Base Tier:** `YELLOW` | **Final Tier:** `YELLOW` | **Escalated:** `false`
   - *Result:* Despite high ambient AQI, risk remained moderate (39.43 YELLOW) without false alarms.
3. **Decoy Case 2: Escalated Alert Promotion (`BOM_ZN_01`, 2026-09-15):**
   - $\text{avg\_aqi} = 258.67$, $\text{complaint\_count} = 7$, $\text{complaint\_density} = 1.0$
   - $\text{raw\_risk\_score} = 73.62$ (Base Tier: `ORANGE`)
   - **Escalation Rule Triggered:** Rising AQI $\ge 0.50$ AND rising complaints $\ge 0.40$.
   - **Final Tier Promoted:** `ORANGE` $\to$ `RED` | **Escalated:** `true`.

### Verification 6: Live Web Form Intake & Recalculation
Executed `scripts/verify_complaint_pipeline.py`:
1. Baseline query for `CBE_ZN_02` retrieved risk score 46.16 (`YELLOW`).
2. Submitted new complaint via HTTP `POST /api/complaints` with severe respiratory symptoms.
3. Successfully persisted into MongoDB `symptom_reports` (Report ID: `RPT-WEB-1791967997`).
4. Staged and appended directly into HDFS raw landing zone (`/data/raw/complaints/city=Coimbatore/date=.../complaints.csv`).

### Verification 7: Automated Test Suite (100% Pass)
Executed `pytest tests/` in WSL:
- `tests/test_api.py` (14 tests): Verified all REST endpoints, health checks, advisories, sensor freshness, and anomaly detection.
- `tests/test_fusion_formula.py` (4 tests): Verified 0.50 / 0.35 / 0.15 weights, base tiers, and outbreak escalation promotion.
- `tests/test_generators.py` (2 tests): Verified deterministic generation reproducibility with seed=42 and synthetic data labeling.
- `tests/test_new_features.py` (3 tests): Verified geolocation, social sharing, and onboarding tours.
- `tests/test_services.py` (4 tests): Verified live connectivity to MongoDB, HiveServer2, HDFS, and Pig.
- `tests/test_tn_api.py` (1 test): Verified Tamil Nadu state surveillance across 30 districts.
- **Result:** **28 passed in 20.36s (100% success rate)**.

### Verification 8: Dashboard Screenshot Evidence
High-resolution captures committed in `docs/SCREENSHOTS/` (and `docs/screenshots/`):
1. `dashboard_desktop_1280px.png`: Main Leaflet map showing color-coded zones across 5 cities, pulsing compound alert halos, top KPI metrics banner, and Tamil Nadu 30-district choropleth.
2. `dashboard_tablet_768px.png`: Responsive tablet layout with mobile-optimized navigation.
3. `dashboard_mobile_360px.png`: Mobile viewport with collapsible drawer and citizen complaint intake modal.
4. `admin_desktop_1280px.png`: Administrative triage console displaying sortable zone risk ranking, alert status, and CSV download.
5. `situation_report_desktop_1280px.png`: Printable public health situation report.
6. `tamilnadu_surveillance_1280px.png`: State-wide environmental surveillance choropleth.

---

## 4. Engineering Assumptions & Controlled Deviations

1. **Host Environment:**
   - The system is built and fully operational on the developer's native WSL2 Ubuntu 24.04 Big Data stack where Hadoop, Hive, Pig, and MongoDB daemons are running natively and listening on standard ports. A complete `docker-compose.yml` is provided for containerized environments.
2. **Kaggle Dataset Scope:**
   - Real AQI data from Rohan Rao's Kaggle dataset was cleaned into a focused 30-day window covering 25 primary stations across 5 major hubs to keep MapReduce execution times within optimal viva demonstration limits ($<5$ minutes).
3. **Synthetic Data Disclosure:**
   - Weather observations, social posts, and citizen symptom reports outside the Kaggle dataset were synthesized using reproducible generator scripts (`seed=42`). Every synthetic record includes the field `source="synthetic"` as disclosed in the README and dashboard footer.
4. **Machine Learning Scope:**
   - As strictly requested, no ML or predictive training models are active in the core pipeline. ML predictive models and deep learning sequence forecasting are explicitly categorized under future work in the README.

---

## 5. Summary & Viva Readiness

The Multi-City Air Quality & Public Health Early-Warning System is completely built, validated, and operational. All big data infrastructure components—from HDFS dual-partitioned storage and HiveQL window functions to MongoDB aggregation pipelines and Apache Pig MapReduce fusion—function cohesively to solve the real-world limitation of passive air-quality monitoring.
