#!/usr/bin/env python3
"""
CIT 21MDS56: Air Quality & Public Health Early-Warning System
ingestion/weather_ingest.py
High-throughput Weather ingestion landing partitioned CSV into HDFS (/data/raw/weather/city=<c>/date=<d>/).
"""

import os
import sys
import csv
import shutil
from collections import defaultdict
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ingestion.hdfs_utils import hdfs_sync_staging_tree
from data_generator.generate_data import generate_hourly_telemetry

load_dotenv()

def ingest_weather(days=30):
    mode = os.getenv("DATA_MODE", "synthetic").lower()
    print(f"Starting Weather ingestion in [{mode.upper()}] mode for {days} days...")

    _, records, _, _ = generate_hourly_telemetry(days=days)
    print(f"Partitioning {len(records)} Weather records by city and date...")

    partitioned = defaultdict(list)
    for r in records:
        partitioned[(r["city"], r["date_str"])].append(r)

    staging_dir = "/tmp/weather_staging"
    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir)
    os.makedirs(staging_dir, exist_ok=True)

    for (city, date_str), partition_rows in partitioned.items():
        part_dir = os.path.join(staging_dir, f"city={city}", f"date={date_str}")
        os.makedirs(part_dir, exist_ok=True)
        csv_file = os.path.join(part_dir, "weather_data.csv")
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            for row in partition_rows:
                writer.writerow([
                    row["record_id"],
                    row["city"],
                    row["zone_id"],
                    row["timestamp"],
                    row["temp"],
                    row["humidity"],
                    row["wind_speed"],
                    row["wind_direction"]
                ])

    print("Syncing staged Weather partitions to HDFS /data/raw/weather/ in batch...")
    hdfs_sync_staging_tree(staging_dir, "/data/raw/weather")
    shutil.rmtree(staging_dir)
    print(f"Weather Ingestion Complete: {len(records)} records across {len(partitioned)} partitions.")
    return len(records)

if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    ingest_weather(days=days)
