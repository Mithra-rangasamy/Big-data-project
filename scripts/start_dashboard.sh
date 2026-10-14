#!/usr/bin/env bash
# ==============================================================================
# CIT 21MDS56: Air Quality & Public Health Early-Warning System
# scripts/start_dashboard.sh - Starts Flask Web Dashboard on 0.0.0.0:5000
# ==============================================================================

PROJECT_DIR="/home/mithra/air-quality-ews"

if ss -tulpn 2>/dev/null | grep -q ":5000 "; then
    echo "Dashboard is already running on port 5000."
    exit 0
fi

echo "Starting Air Quality & Public Health Early-Warning Dashboard on port 5000..."
nohup "${PROJECT_DIR}/venv/bin/python3" "${PROJECT_DIR}/backend/app.py" > "${PROJECT_DIR}/flask_dashboard.log" 2>&1 &
PID=$!
echo "Dashboard launched with PID $PID."

for i in {1..10}; do
    if ss -tulpn 2>/dev/null | grep -q ":5000 "; then
        echo "Dashboard is ONLINE and accessible at http://localhost:5000"
        exit 0
    fi
    sleep 1
done

echo "WARNING: Dashboard did not bind to port 5000 within 10 seconds. Check flask_dashboard.log."
exit 1
