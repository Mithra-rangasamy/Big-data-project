#!/usr/bin/env bash
# ==============================================================================
# CIT 21MDS56: Air Quality & Public Health Early-Warning System
# scripts/status.sh - Reports status and ports of all services
# ==============================================================================

if [ -f /etc/profile.d/bigdata.sh ]; then
    . /etc/profile.d/bigdata.sh
elif [ -f ~/.bashrc ]; then
    . ~/.bashrc
fi

echo "============================================================"
echo "BIG DATA CLUSTER STATUS REPORT"
echo "============================================================"

echo "--- 1. Java Virtual Machine Processes (jps) ---"
jps -l | grep -v "sun.tools.jps" || true
echo ""

echo "--- 2. Network Ports Listening ---"
printf "%-10s %-12s %-25s\n" "PORT" "SERVICE" "STATUS"
check_port() {
    local port=$1
    local name=$2
    if ss -tulpn 2>/dev/null | grep -q ":$port "; then
        printf "%-10s %-12s %-25s\n" "$port" "$name" "ONLINE (Listening)"
    else
        printf "%-10s %-12s %-25s\n" "$port" "$name" "OFFLINE"
    fi
}
check_port 9000  "HDFS RPC"
check_port 9870  "HDFS WebUI"
check_port 8088  "YARN WebUI"
check_port 10000 "HiveServer2"
check_port 27017 "MongoDB"
check_port 5000  "Flask App"
echo ""

echo "--- 3. HDFS Health ---"
hdfs dfsadmin -safemode get 2>/dev/null || echo "Unable to connect to NameNode"
echo ""

echo "--- 4. MongoDB Health ---"
if mongosh --eval "db.runCommand({ping: 1})" --quiet >/dev/null 2>&1; then
    echo "MongoDB: ACTIVE (Responding to ping)"
else
    echo "MongoDB: INACTIVE or Unreachable"
fi
echo ""

echo "--- 5. Hive Metastore & HiveServer2 Health ---"
if ss -tulpn 2>/dev/null | grep -q ":10000 "; then
    echo "HiveServer2: LISTENING on port 10000"
else
    echo "HiveServer2: NOT LISTENING"
fi
echo "============================================================"
