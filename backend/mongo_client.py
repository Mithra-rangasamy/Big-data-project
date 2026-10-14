"""CIT 21MDS56: Air Quality & Public Health Early-Warning System
backend/mongo_client.py - PyMongo analytics, Complaint Quality Filter (Feature E),
Pipeline Tracking (Feature G), Alert History with Cooldown (Feature I),
and Alert Action Tracker (Feature 9)
"""

import datetime
import logging
from typing import Dict, List, Optional, Any
from pymongo import MongoClient

logger = logging.getLogger("MongoClient")

class MongoEWSClient:
    def __init__(self, uri: str = "mongodb://localhost:27017/", db_name: str = "air_quality_ews"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.complaints = self.db["symptom_reports"]
        self.social = self.db["social_posts"]
        self.rejected_reports = self.db["rejected_reports"]
        self.pipeline_runs = self.db["pipeline_runs"]
        self.alert_history = self.db["alert_history"]

    def get_complaints_summary(self, zone_id: Optional[str] = None, city: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
        """Aggregates symptom breakdown, severity distribution, and recent reports."""
        query: Dict[str, Any] = {}
        if zone_id:
            query["zone_id"] = zone_id
        elif city:
            query["city"] = city

        pipeline = [
            {"$match": query},
            {"$unwind": "$symptoms"},
            {"$group": {"_id": "$symptoms", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        symptom_counts = list(self.complaints.aggregate(pipeline))

        sev_pipeline = [
            {"$match": query},
            {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
        ]
        severity_counts = list(self.complaints.aggregate(sev_pipeline))

        recent = list(self.complaints.find(
            query,
            {"_id": 0, "report_id": 1, "zone_id": 1, "zone_name": 1, "city": 1, "symptoms": 1, "severity": 1, "reported_at": 1, "channel": 1, "description": 1}
        ).sort("reported_at", -1).limit(20))

        total_reports = self.complaints.count_documents(query)

        return {
            "total_reports": total_reports,
            "symptoms": [{"symptom": str(s["_id"]), "count": s["count"]} for s in symptom_counts],
            "severity_breakdown": {str(s["_id"]): s["count"] for s in severity_counts},
            "recent_reports": recent
        }

    # =========================================================================
    # Feature E & Feature 3: Complaint Quality Filter & Validation Gate
    # =========================================================================
    def validate_complaint(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Validates incoming report for symptoms, spam, duplicate within 1h, and rate limits."""
        symptoms = data.get("symptoms", [])
        if not symptoms or not isinstance(symptoms, list) or len(symptoms) == 0:
            return False, "SYMPTOM_REQUIRED: At least one symptom must be selected."

        desc = (data.get("description") or "").strip()
        zid = data.get("zone_id", "")
        reporter = data.get("citizen_name", "Anonymous").strip()

        # If description is empty or not provided, auto-generate friendly summary from symptoms
        if not desc:
            desc = f"Citizen reported: {', '.join(symptoms)}"
            data["description"] = desc
        else:
            # 1. Spam check on description: length < 4 or trivial repetition
            if len(desc) < 4:
                return False, "SPAM_OR_TOO_SHORT: Description must be at least 4 characters."
            if len(set(desc.lower())) <= 2 and len(desc) > 5:
                return False, "SPAM_REPETITIVE_CHARACTERS: Repetitive meaningless character sequence."

        # 2. Rate limiting: > 5 reports per day by same reporter
        today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        daily_count = self.complaints.count_documents({
            "citizen_name": reporter,
            "date": today_str
        })
        if daily_count >= 5:
            return False, "RATE_LIMIT_EXCEEDED: Maximum 5 reports permitted per reporter per day."

        # 3. Deduplication: identical text + zone within 1 hour
        one_hour_ago = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        dedup_filter = {
            "zone_id": zid,
            "description": desc,
            "reported_at": {"$gte": one_hour_ago}
        }
        if reporter and reporter != "Anonymous":
            dedup_filter["citizen_name"] = reporter

        duplicate = self.complaints.find_one(dedup_filter)
        if duplicate:
            return False, "DUPLICATE_REPORT_WITHIN_1HR: Identical symptom report already received for this zone within the last hour."

        return True, "VALID"

    def submit_complaint(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validates and routes complaint to symptom_reports or rejected_reports."""
        now = datetime.datetime.now(datetime.timezone.utc)
        report_id = f"RPT-WEB-{int(now.timestamp())}"

        # Normalize severity to integer (1, 2, 3) to preserve Mongo $avg aggregation
        sev_raw = data.get("severity", "moderate")
        sev_map = {"mild": 1, "moderate": 2, "severe": 3, 1: 1, 2: 2, 3: 3}
        sev_num = sev_map.get(sev_raw, 2)
        sev_str = "mild" if sev_num == 1 else ("severe" if sev_num == 3 else "moderate")

        is_valid, reason = self.validate_complaint(data)

        doc = {
            "report_id": report_id,
            "zone_id": data.get("zone_id", "CBE_ZN_01"),
            "zone_name": data.get("zone_name", "Local Zone"),
            "city": data.get("city", "Coimbatore"),
            "reported_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "date_str": now.strftime("%Y-%m-%d"),
            "symptoms": data.get("symptoms", ["cough"]),
            "severity": sev_num,
            "severity_label": sev_str,
            "age_group": data.get("age_group", "adult"),
            "channel": "citizen_web_portal",
            "citizen_name": data.get("citizen_name", "Anonymous Citizen"),
            "description": data.get("description", "Reported via Early Warning Web Portal")
        }

        if not is_valid:
            doc["rejection_reason"] = reason
            self.rejected_reports.insert_one(doc)
            logger.warning(f"Complaint {report_id} REJECTED: {reason}")
            return {
                "status": "rejected",
                "report_id": report_id,
                "rejection_reason": reason,
                "message": f"Report was filtered out by Quality Gate: {reason}"
            }

        result = self.complaints.insert_one(doc)
        logger.info(f"Accepted clean complaint {report_id} into MongoDB with ID {result.inserted_id}")
        return {
            "status": "success",
            "report_id": report_id,
            "message": "Citizen health report verified and queued for fusion engine recalculation."
        }

    def get_rejected_reports(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Returns list of rejected complaints with rejection reasons for admin review."""
        return list(self.rejected_reports.find(
            {},
            {"_id": 0, "report_id": 1, "zone_id": 1, "zone_name": 1, "city": 1, "reported_at": 1, "citizen_name": 1, "description": 1, "rejection_reason": 1}
        ).sort("reported_at", -1).limit(limit))

    # =========================================================================
    # Feature G: Pipeline Execution Status Logging
    # =========================================================================
    def record_pipeline_run(self, run_data: Dict[str, Any]) -> str:
        """Stores pipeline execution metrics in MongoDB."""
        now = datetime.datetime.now(datetime.timezone.utc)
        run_id = f"RUN-{int(now.timestamp())}"
        doc = {
            "run_id": run_id,
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "duration_sec": run_data.get("duration_sec", 0),
            "status": run_data.get("status", "SUCCESS"),
            "stages": run_data.get("stages", [
                {"stage": "Hive Daily Aggregation", "status": "SUCCESS", "records": 775},
                {"stage": "MongoDB TSV Aggregation", "status": "SUCCESS", "records": 616},
                {"stage": "Pig MapReduce Fusion Engine", "status": "SUCCESS", "records": 775}
            ]),
            "records_processed": run_data.get("records_processed", 2165)
        }
        self.pipeline_runs.insert_one(doc)
        return run_id

    def get_recent_pipeline_runs(self, limit: int = 15) -> List[Dict[str, Any]]:
        runs = list(self.pipeline_runs.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
        if not runs:
            # Seed initial run for display if empty
            now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            runs = [{
                "run_id": "RUN-INITIAL-01",
                "timestamp": now,
                "date": "2026-10-13",
                "duration_sec": 93,
                "status": "SUCCESS",
                "stages": [
                    {"stage": "Hive Daily Aggregation", "status": "SUCCESS", "records": 775},
                    {"stage": "MongoDB TSV Aggregation", "status": "SUCCESS", "records": 616},
                    {"stage": "Pig MapReduce Fusion Engine", "status": "SUCCESS", "records": 775}
                ],
                "records_processed": 2165
            }]
        return runs

    # =========================================================================
    # Feature I: Alert Notifications & History with 6-Hour Cooldown
    # =========================================================================
    def log_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Logs Red/Compound alert enforcing a 6-hour cooldown per zone."""
        zid = alert_data.get("zone_id")
        now = datetime.datetime.now(datetime.timezone.utc)
        six_hours_ago = (now - datetime.timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")

        recent_alert = self.alert_history.find_one({
            "zone_id": zid,
            "created_at": {"$gte": six_hours_ago}
        })

        if recent_alert:
            return {
                "status": "cooldown_active",
                "message": f"Alert suppressed for {zid} due to 6-hour notification cooldown window.",
                "last_alert_id": recent_alert.get("alert_id")
            }

        alert_id = f"ALT-{zid}-{int(now.timestamp())}"
        doc = {
            "alert_id": alert_id,
            "zone_id": zid,
            "zone_name": alert_data.get("zone_name", "Zone"),
            "city": alert_data.get("city", "City"),
            "severity": alert_data.get("severity", "RED"),
            "compound_alert": alert_data.get("compound_alert", False),
            "avg_aqi": alert_data.get("avg_aqi", 0.0),
            "complaint_count": alert_data.get("complaint_count", 0),
            "headline": alert_data.get("headline", "Air Quality Health Alert"),
            "message": alert_data.get("message", "Severe air quality and symptom spike detected."),
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "date": alert_data.get("date", now.strftime("%Y-%m-%d")),
            "status": "ACTIVE"
        }
        self.alert_history.insert_one(doc)
        logger.info(f"Logged new alert {alert_id} for zone {zid}")
        return {"status": "logged", "alert_id": alert_id}

    def get_alert_history(self, limit: int = 50, zone_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {"zone_id": zone_id} if zone_id else {}
        return list(self.alert_history.find(query, {"_id": 0}).sort("created_at", -1).limit(limit))

    def get_social_feed(self, city: Optional[str] = None, limit: int = 15) -> List[Dict[str, Any]]:
        query = {"city": city} if city else {}
        return list(self.social.find(
            query,
            {"_id": 0, "post_id": 1, "zone_id": 1, "city": 1, "timestamp": 1, "text": 1, "platform": 1, "sentiment": 1, "symptoms_detected": 1}
        ).sort("timestamp", -1).limit(limit))

    # =========================================================================
    def count_complaints_for_date(self, date_str: Optional[str] = None) -> int:
        if not date_str:
            date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        return self.complaints.count_documents({"$or": [{"date": date_str}, {"date_str": date_str}]})
