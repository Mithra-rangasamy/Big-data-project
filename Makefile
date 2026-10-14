# CIT 21MDS56: Air Quality & Public Health Early-Warning System - Makefile
SHELL := /bin/bash
PROJECT_DIR := /home/mithra/air-quality-ews
PYTHON := $(PROJECT_DIR)/venv/bin/python3
PYTEST := $(PROJECT_DIR)/venv/bin/pytest

.PHONY: all services stop status ingest hive mongo pig pipeline dashboard test clean

all: status

# 1. Cluster Infrastructure Management
services:
	@echo "Starting Big Data Cluster..."
	@bash $(PROJECT_DIR)/scripts/start_all.sh

stop:
	@echo "Stopping Big Data Infrastructure & Dashboard..."
	@bash $(PROJECT_DIR)/scripts/stop_dashboard.sh || true
	@bash $(PROJECT_DIR)/scripts/stop_all.sh

status:
	@bash $(PROJECT_DIR)/scripts/status.sh

# 2. Ingestion & Synthetic Data Generation
ingest:
	@echo "Generating and Ingesting 30 Days of Multi-Modal Telemetry..."
	@$(PYTHON) $(PROJECT_DIR)/data_generator/generate_data.py
	@$(PYTHON) $(PROJECT_DIR)/ingestion/aqi_ingest.py
	@$(PYTHON) $(PROJECT_DIR)/ingestion/weather_ingest.py
	@$(PYTHON) $(PROJECT_DIR)/ingestion/complaints_ingest.py

# 3. Component Processing
hive:
	@echo "Executing Hive Structured Analytical Queries..."
	@beeline -u "jdbc:hive2://localhost:10000" -n mithra -f $(PROJECT_DIR)/hive/daily_aqi_agg.hql

mongo:
	@echo "Executing MongoDB Aggregation Pipeline..."
	@$(PYTHON) $(PROJECT_DIR)/mongo/export_aggregation.py

pig:
	@echo "Executing Apache Pig Multi-Modal MapReduce Fusion Engine..."
	@pig -x mapreduce $(PROJECT_DIR)/pig/fusion.pig

# 4. End-to-End Pipeline & Dashboard
pipeline:
	@echo "Triggering End-to-End Fusion Pipeline..."
	@bash $(PROJECT_DIR)/scheduler/run_pipeline.sh

dashboard:
	@echo "Launching Flask Dashboard..."
	@bash $(PROJECT_DIR)/scripts/start_dashboard.sh

# 5. Verification & Testing
test:
	@echo "Running Automated Big Data Lab Test Suite..."
	@$(PYTEST) -v $(PROJECT_DIR)/tests

clean:
	@echo "Cleaning transient logs..."
	@rm -f $(PROJECT_DIR)/*.log
