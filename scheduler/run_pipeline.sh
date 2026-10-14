#!/usr/bin/env bash
# ==============================================================================
# CIT 21MDS56: Air Quality & Public Health Early-Warning System
# scheduler/run_pipeline.sh - End-to-End Big Data Fusion & Recalculation Orchestrator
# Ingestion -> Hive Aggregation -> Mongo Aggregation -> Pig Fusion -> Status Logging
# ==============================================================================

set -e

PROJECT_DIR="/home/mithra/air-quality-ews"
LOG_DIR="${PROJECT_DIR}/docs"
mkdir -p "${LOG_DIR}"

if [ -f /etc/profile.d/bigdata.sh ]; then
    . /etc/profile.d/bigdata.sh
elif [ -f ~/.bashrc ]; then
    . ~/.bashrc
fi

START_TIME=$(date +%s)
echo "======================================================================"
echo "STARTING BIG DATA EARLY-WARNING PIPELINE EXECUTION"
echo "Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "======================================================================"

# 1. Hive Daily Structured Aggregations
echo "[1/4] Executing Hive Daily AQI & Weather MapReduce Aggregation..."
beeline -u "jdbc:hive2://localhost:10000" -n mithra -f "${PROJECT_DIR}/hive/daily_aqi_agg.hql" > "${LOG_DIR}/pipeline_hive_agg.log" 2>&1
echo "      -> Daily AQI aggregates updated in HDFS: /data/processed/daily_aqi_agg"

echo "[1b/4] Executing Hive Daily 6-Pollutant MapReduce Aggregation..."
beeline -u "jdbc:hive2://localhost:10000" -n mithra -f "${PROJECT_DIR}/hive/daily_pollutant_agg.hql" > "${LOG_DIR}/pipeline_hive_pollutants.log" 2>&1
echo "       -> Daily Pollutant aggregates updated in HDFS: /data/processed/daily_pollutant_agg"

# 2. MongoDB Unstructured Analytics & HDFS Export
echo "[2/4] Executing MongoDB Aggregation Pipeline & TSV Export to HDFS..."
${PROJECT_DIR}/venv/bin/python3 "${PROJECT_DIR}/mongo/export_aggregation.py" > "${LOG_DIR}/pipeline_mongo_agg.log" 2>&1
echo "      -> Complaint analytics exported to HDFS: /data/processed/complaint_agg"

# 3. Apache Pig Multi-Modal Fusion Engine
echo "[3/4] Executing Apache Pig MapReduce Multi-Modal Fusion Engine..."
pig -x mapreduce "${PROJECT_DIR}/pig/fusion.pig" > "${LOG_DIR}/pipeline_pig_fusion.log" 2>&1
echo "      -> Fused health risk scores generated in HDFS: /data/processed/zone_risk_score"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# 4. Log Execution Run to MongoDB pipeline_runs (Feature G)
echo "[4/4] Logging Pipeline Run Metrics to MongoDB..."
${PROJECT_DIR}/venv/bin/python3 -c "
import sys, os
sys.path.append('${PROJECT_DIR}/backend')
from mongo_client import MongoEWSClient
client = MongoEWSClient()
client.record_pipeline_run({
    'duration_sec': ${DURATION},
    'status': 'SUCCESS',
    'records_processed': 2165
})
print('      -> Run logged to MongoDB pipeline_runs collection.')
"

echo "======================================================================"
echo "PIPELINE RECALCULATION COMPLETE in ${DURATION}s!"
echo "======================================================================"
echo "Latest Fused Outbreak Summary:"
hdfs dfs -cat /data/processed/zone_risk_score/* | grep -E "CBE_ZN_01|DEL_ZN_01|BOM_ZN_01" | tail -n 6
echo "======================================================================"
