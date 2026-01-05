#!/bin/bash
# Monitor the consolidated collection progress in real-time

LOG="/workspaces/OmegaSports-Validation-Lab/data/logs/collection_consolidated.log"
PID_FILE="/workspaces/OmegaSports-Validation-Lab/data/collection_consolidated.pid"

if [[ ! -f "$PID_FILE" ]]; then
    echo "No collection runner found. PID file: $PID_FILE"
    exit 1
fi

PID=$(cat "$PID_FILE")
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "Collection runner (PID $PID) is not running."
    exit 1
fi

echo "Monitoring collection (PID $PID)..."
echo "Log: $LOG"
echo "---"
tail -f "$LOG"
