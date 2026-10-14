#!/usr/bin/env bash
# ==============================================================================
# CIT 21MDS56: Air Quality & Public Health Early-Warning System
# scripts/stop_all.sh - Gracefully stops all big data services in reverse order
# ==============================================================================

if [ -f /etc/profile.d/bigdata.sh ]; then
    . /etc/profile.d/bigdata.sh
elif [ -f ~/.bashrc ]; then
    . ~/.bashrc
fi

echo "============================================================"
echo "STOPPING BIG DATA INFRASTRUCTURE"
echo "============================================================"

# 1. HiveServer2
echo "[1/4] Stopping HiveServer2..."
if pgrep -f "org.apache.hive.service.server.HiveServer2" >/dev/null; then
    pkill -f "org.apache.hive.service.server.HiveServer2" || true
    echo "  -> HiveServer2 stopped."
else
    echo "  -> HiveServer2 is not running."
fi

# 2. MongoDB
echo "[2/4] Stopping MongoDB..."
if systemctl is-active --quiet mongod; then
    sudo systemctl stop mongod
    echo "  -> MongoDB service stopped."
else
    pkill -f "mongod" || true
    echo "  -> MongoDB stopped."
fi

# 3. YARN
echo "[3/4] Stopping Hadoop YARN..."
if jps | grep -q "ResourceManager"; then
    stop-yarn.sh || true
    echo "  -> YARN stopped."
else
    echo "  -> YARN is not running."
fi

# 4. HDFS
echo "[4/4] Stopping Hadoop HDFS..."
if jps | grep -q "NameNode"; then
    stop-dfs.sh || true
    echo "  -> HDFS stopped."
else
    echo "  -> HDFS is not running."
fi

echo "============================================================"
echo "ALL SERVICES STOPPED."
echo "============================================================"
