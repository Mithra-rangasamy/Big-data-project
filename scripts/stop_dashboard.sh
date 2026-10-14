#!/usr/bin/env bash
# ==============================================================================
# CIT 21MDS56: Air Quality & Public Health Early-Warning System
# scripts/stop_dashboard.sh - Gracefully terminates Flask dashboard
# ==============================================================================

echo "Stopping Flask Web Dashboard..."
if pgrep -f "backend/app.py" >/dev/null; then
    pkill -f "backend/app.py" || true
    echo "Dashboard stopped."
else
    echo "Dashboard is not currently running."
fi
