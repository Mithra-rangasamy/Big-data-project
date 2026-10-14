import pymongo

client = pymongo.MongoClient()
db = client.air_quality_ews

print("=== MONGODB COLLECTIONS & DOCUMENT COUNTS ===")
for c in sorted(db.list_collection_names()):
    print(f"  {c}: {db[c].count_documents({})} documents")

print("\n=== MONGODB AGGREGATION: TOP SYMPTOM KEYWORDS ===")
pipeline_kw = [
    {"$unwind": "$symptoms"},
    {"$group": {"_id": "$symptoms", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
]
for doc in list(db.symptom_reports.aggregate(pipeline_kw))[:7]:
    print(f"  - {doc['_id']}: {doc['count']} reports")

print("\n=== MONGODB AGGREGATION: COMPLAINT DENSITY SAMPLE (BY ZONE & DATE) ===")
pipeline_density = [
    {"$group": {"_id": {"zone_id": "$zone_id", "date": "$date_str"}, "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
    {"$limit": 5}
]
for doc in db.symptom_reports.aggregate(pipeline_density):
    print(f"  Zone: {doc['_id']['zone_id']}, Date: {doc['_id']['date']}, Complaints: {doc['count']}")
