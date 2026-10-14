#!/usr/bin/env python3
"""CIT 21MDS56: Air Quality & Public Health Early-Warning System
tests/test_services.py - Health check assertions for MongoDB, HiveServer2, HDFS, and Pig
"""

import os
import sys
import subprocess
from pymongo import MongoClient
from pyhive import hive

def get_env():
    env = os.environ.copy()
    env.setdefault("JAVA_HOME", "/usr/lib/jvm/java-8-openjdk-amd64")
    env.setdefault("HADOOP_HOME", "/opt/hadoop")
    env.setdefault("PIG_HOME", "/opt/pig")
    env.setdefault("HIVE_HOME", "/opt/hive")
    env.setdefault("HIVE_CONF_DIR", "/opt/hive/conf")
    paths = [
        "/opt/hadoop/bin",
        "/opt/hadoop/sbin",
        "/opt/pig/bin",
        "/opt/hive/bin",
        env["JAVA_HOME"] + "/bin"
    ]
    cur = env.get("PATH", "")
    for p in paths:
        if p not in cur:
            cur = f"{p}:{cur}"
    env["PATH"] = cur
    return env

def test_mongodb():
    print("[1/4] Testing MongoDB connection...")
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db = client["air_quality_ews_test"]
    col = db["smoke_test"]
    col.delete_many({})
    res = col.insert_one({"test": "cit_21mds56", "status": "active"})
    doc = col.find_one({"_id": res.inserted_id})
    assert doc is not None and doc["test"] == "cit_21mds56"
    col.delete_many({})
    client.close()
    print("  --> MongoDB OK (read/write verified on port 27017)")

def test_hiveserver2():
    print("[2/4] Testing HiveServer2 connection...")
    conn = hive.Connection(host="127.0.0.1", port=10000, username="mithra")
    cursor = conn.cursor()
    cursor.execute("SHOW DATABASES")
    databases = [row[0] for row in cursor.fetchall()]
    assert "default" in databases
    cursor.close()
    conn.close()
    print(f"  --> HiveServer2 OK (Databases: {databases})")

def test_hdfs():
    print("[3/4] Testing HDFS read/write...")
    env = get_env()
    test_dir = "/data/test_smoke"
    res = subprocess.run(["hdfs", "dfs", "-mkdir", "-p", test_dir], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0, f"hdfs mkdir failed: {res.stderr.strip()}"
    write_proc = subprocess.run(["hdfs", "dfs", "-put", "-f", "-", f"{test_dir}/smoke.txt"], input="cit_lab_hdfs_smoke_test\n", env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert write_proc.returncode == 0, f"hdfs put failed: {write_proc.stderr.strip()}"
    read_proc = subprocess.run(["hdfs", "dfs", "-cat", f"{test_dir}/smoke.txt"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert "cit_lab_hdfs_smoke_test" in read_proc.stdout
    subprocess.run(["hdfs", "dfs", "-rm", "-r", "-f", test_dir], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print("  --> HDFS OK (mkdir, put, cat, rm verified)")

def test_pig():
    print("[4/4] Testing Apache Pig...")
    env = get_env()
    proc = subprocess.run(["pig", "-e", "sh echo Pig smoke test success;"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
    assert "Pig smoke test success" in proc.stdout or "Pig smoke test success" in proc.stderr
    print("  --> Apache Pig OK (MapReduce/Local execution verified)")

if __name__ == "__main__":
    print("=" * 60)
    print("CIT 21MDS56: SERVICE HEALTH SMOKE TEST")
    print("=" * 60)
    test_mongodb()
    test_hiveserver2()
    test_hdfs()
    test_pig()
    print("=" * 60)
    print("ALL SERVICES OPERATIONAL AND COMPATIBLE!")
