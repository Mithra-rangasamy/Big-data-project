#!/usr/bin/env python3
"""
CIT 21MDS56: Air Quality & Public Health Early-Warning System
ingestion/complaints_ingest.py
High-throughput Complaints ingestion inserting into MongoDB and mirroring raw JSON to HDFS.
"""

import os
import sys
import json
import shutil
from collections import defaultdict
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ingestion.hdfs_utils import hdfs_sync_staging_tree
from data_generator.generate_data import generate_hourly_telemetry

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "air_quality_ews")

def get_mongo_db():
    client = MongoClient(MONGO_URI)
    return client[MONGO_DB]

def init_mongo_indexes():
    db = get_mongo_db()
    db["symptom_reports"].create_index([("city", 1), ("zone_id", 1), ("date_str", 1)])
    db["symptom_reports"].create_index([("report_id", 1)], unique=True)
    db["symptom_reports"].create_index([("text", "text")])

    db["social_posts"].create_index([("city", 1), ("zone_id", 1), ("date_str", 1)])
    db["social_posts"].create_index([("post_id", 1)], unique=True)
    db["social_posts"].create_index([("text", "text")])
    print("MongoDB indexes initialized successfully.")

def ingest_complaints(days=30):
    db = get_mongo_db()
    init_mongo_indexes()

    print(f"Generating and ingesting complaints data for {days} days...")
    _, _, complaints, social_posts = generate_hourly_telemetry(days=days)

    if complaints:
        ops = [
            UpdateOne({"report_id": c["report_id"]}, {"$set": c}, upsert=True)
            for c in complaints
        ]
        res = db["symptom_reports"].bulk_write(ops)
        print(f"MongoDB symptom_reports: Upserted {res.upserted_count}, Modified {res.modified_count} documents.")

    if social_posts:
        ops = [
            UpdateOne({"post_id": s["post_id"]}, {"$set": s}, upsert=True)
            for s in social_posts
        ]
        res = db["social_posts"].bulk_write(ops)
        print(f"MongoDB social_posts: Upserted {res.upserted_count}, Modified {res.modified_count} documents.")

    # Mirroring to HDFS via local staging
    print("Mirroring complaints raw JSON to HDFS landing zone in batch...")
    staging_dir = "/tmp/complaints_staging"
    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir)
    os.makedirs(staging_dir, exist_ok=True)

    partitioned = defaultdict(list)
    for c in complaints:
        partitioned[(c["city"], c["date_str"])].append(c)

    for (city, date_str), partition_records in partitioned.items():
        part_dir = os.path.join(staging_dir, f"city={city}", f"date={date_str}")
        os.makedirs(part_dir, exist_ok=True)
        json_file = os.path.join(part_dir, "complaints.json")
        with open(json_file, "w") as f:
            for r in partition_records:
                f.write(json.dumps(r) + "\n")

    hdfs_sync_staging_tree(staging_dir, "/data/raw/complaints")
    shutil.rmtree(staging_dir)
    print(f"Complaints HDFS mirroring complete: {len(complaints)} records in {len(partitioned)} partitions.")
    return len(complaints)

if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    ingest_complaints(days=days)
