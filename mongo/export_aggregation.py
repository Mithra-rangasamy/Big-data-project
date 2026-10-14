#!/usr/bin/env python3
"""
CIT 21MDS56: Air Quality & Public Health Early-Warning System
mongo/export_aggregation.py
Executes MongoDB symptom aggregation pipeline, normalizes complaint density
against zone baseline, and exports TSV to HDFS (/data/processed/complaint_agg/).
"""

import os
import sys
import json
import csv
import io
from pymongo import MongoClient
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ingestion.hdfs_utils import hdfs_put_string

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "air_quality_ews")

def load_zone_baselines():
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "zones.json")
    if not os.path.exists(config_path):
        config_path = os.path.expanduser("~/air-quality-ews/config/zones.json")
    with open(config_path, "r") as f:
        data = json.load(f)
    baselines = {}
    for city_obj in data:
        for z in city_obj["zones"]:
            baselines[z["zone_id"]] = z.get("baseline_complaints_per_day", 2.0)
    return baselines

def run_and_export_aggregation():
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    baselines = load_zone_baselines()

    # MongoDB aggregation grouping complaints by (city, zone_id, date)
    pipeline = [
        {"$unwind": {"path": "$symptoms", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "city": 1,
                "zone_id": 1,
                "zone_name": 1,
                "date_str": {"$ifNull": ["$date_str", {"$ifNull": ["$date", "2026-10-13"]}]},
                "severity": 1,
                "symptom": {"$toLower": {"$ifNull": ["$symptoms", "other"]}}
            }
        },
        {
            "$group": {
                "_id": {
                    "zone_id": "$zone_id",
                    "date": "$date_str"
                },
                "city": {"$first": "$city"},
                "zone_name": {"$first": "$zone_name"},
                "total_complaints": {"$sum": 1},
                "avg_severity": {"$avg": "$severity"},
                "breathing_count": {
                    "$sum": {"$cond": [{"$regexMatch": {"input": "$symptom", "regex": "breath|shortness|asthma|wheez"}}, 1, 0]}
                },
                "chest_pain_count": {
                    "$sum": {"$cond": [{"$regexMatch": {"input": "$symptom", "regex": "chest"}}, 1, 0]}
                },
                "eye_count": {
                    "$sum": {"$cond": [{"$regexMatch": {"input": "$symptom", "regex": "eye|burn"}}, 1, 0]}
                },
                "cough_count": {
                    "$sum": {"$cond": [{"$regexMatch": {"input": "$symptom", "regex": "cough|throat"}}, 1, 0]}
                },
                "headache_count": {
                    "$sum": {"$cond": [{"$regexMatch": {"input": "$symptom", "regex": "headache|nausea"}}, 1, 0]}
                },
                "smog_count": {
                    "$sum": {"$cond": [{"$regexMatch": {"input": "$symptom", "regex": "smog|haze|odour|odor"}}, 1, 0]}
                }
            }
        }
    ]

    print("Executing MongoDB aggregation pipeline on symptom_reports...")
    cursor = db["symptom_reports"].aggregate(pipeline)
    
    rows = []
    for doc in cursor:
        info = doc["_id"]
        zone_id = info["zone_id"]
        date = info.get("date") or "2026-10-13"
        zone_name = doc.get("zone_name") or "Zone"
        city = doc.get("city") or "City"
        cnt = doc["total_complaints"]

        # Calculate baseline normalized complaint density
        # density = (complaints_today / baseline_complaints)
        base = baselines.get(zone_id, 2.0)
        raw_ratio = cnt / base
        complaint_density = round(min(raw_ratio / 3.0, 1.0), 3)

        # Weighted symptom severity score [0.0 - 1.0]
        score_numerator = (
            doc["breathing_count"] * 1.0 +
            doc["chest_pain_count"] * 0.9 +
            doc["eye_count"] * 0.6 +
            doc["cough_count"] * 0.5 +
            doc["headache_count"] * 0.4 +
            doc["smog_count"] * 0.3
        )
        symptom_severity = round(min(score_numerator / max(1.0, cnt * 0.8), 1.0), 3)

        rows.append([
            zone_id,
            zone_name,
            city,
            date,
            cnt,
            complaint_density,
            symptom_severity
        ])

    print(f"Aggregated {len(rows)} zone-date complaint records from MongoDB.")
    
    # Sort for deterministic HDFS partition ordering
    rows.sort(key=lambda x: (x[2], x[0], x[3])) # city, zone_id, date

    # Generate TSV
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter='\t')
    for r in rows:
        writer.writerow(r)
    
    tsv_content = buf.getvalue()
    hdfs_dest = "/data/processed/complaint_agg/part-00000.tsv"
    print(f"Writing aggregated complaints TSV to HDFS: {hdfs_dest}...")
    hdfs_put_string(tsv_content, hdfs_dest)
    print("Complaint aggregation exported to HDFS successfully!")
    return len(rows)

if __name__ == "__main__":
    run_and_export_aggregation()
