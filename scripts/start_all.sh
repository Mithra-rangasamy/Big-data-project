#!/usr/bin/env bash
# ==============================================================================
# CIT 21MDS56: Air Quality & Public Health Early-Warning System
# scripts/start_all.sh - Starts all big data services in proper dependency order
# ==============================================================================

set -e

# Source system-wide or user big-data environment
if [ -f /etc/profile.d/bigdata.sh ]; then
    . /etc/profile.d/bigdata.sh
elif [ -f ~/.bashrc ]; then
    . ~/.bashrc
fi

echo "============================================================"
echo "STARTING BIG DATA INFRASTRUCTURE"
echo "============================================================"

# 1. HDFS
echo "[1/4] Checking Hadoop HDFS..."
if ! jps | grep -q "NameNode"; then
    echo "  -> Starting NameNode and DataNodes (start-dfs.sh)..."
    start-dfs.sh
else
    echo "  -> HDFS NameNode is already running."
fi

# Ensure safe mode is OFF
hdfs dfsadmin -safemode wait >/dev/null 2>&1 || true

# 2. YARN
echo "[2/4] Checking Hadoop YARN..."
if ! jps | grep -q "ResourceManager"; then
    echo "  -> Starting ResourceManager and NodeManagers (start-yarn.sh)..."
    start-yarn.sh
else
    echo "  -> YARN ResourceManager is already running."
fi

# 3. MongoDB
echo "[3/4] Checking MongoDB..."
if ! systemctl is-active --quiet mongod; then
    echo "  -> Starting MongoDB service..."
    sudo systemctl start mongod
    sleep 2
fi
if mongosh --eval "db.runCommand({ping: 1})" --quiet >/dev/null 2>&1; then
    echo "  -> MongoDB is running on port 27017."
else
    echo "  -> WARNING: MongoDB ping failed. Starting manually with mongod..."
    mkdir -p ~/mongodb-data
    nohup mongod --dbpath ~/mongodb-data --port 27017 --bind_ip 127.0.0.1 > ~/mongodb.log 2>&1 &
    sleep 3
fi

# 4. HiveServer2
echo "[4/4] Checking HiveServer2 (Thrift Port 10000)..."
if ss -tulpn | grep -q ":10000 "; then
    echo "  -> HiveServer2 is already listening on port 10000."
else
    echo "  -> Starting HiveServer2 in background..."
    nohup hiveserver2 > ~/hiveserver2.log 2>&1 &
    echo "  -> Waiting for HiveServer2 port 10000 to become available..."
    for i in {1..30}; do
        if ss -tulpn | grep -q ":10000 "; then
            echo "  -> HiveServer2 started successfully!"
            break
        fi
        sleep 2
    done
fi

echo "============================================================"
echo "ALL SERVICES STARTED SUCCESSFULLY!"
echo "Run 'bash scripts/status.sh' to verify cluster health."
echo "============================================================"
