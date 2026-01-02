#!/bin/bash
# Check the status of the historical data collection process

echo "=== Historical Data Collection Status ==="
echo ""

# Check if process is running
if pgrep -f "collect_historical_5years" > /dev/null; then
    PID=$(pgrep -f "collect_historical_5years")
    RUNTIME=$(ps -p $PID -o etime= | tr -d ' ')
    echo "✓ RUNNING (PID: $PID, Runtime: $RUNTIME)"
else
    echo "✗ NOT RUNNING"
fi

echo ""
echo "=== Last 15 Log Lines ==="
tail -15 /workspaces/OmegaSports-Validation-Lab/data/collection_log.txt

echo ""
echo "=== Log File Size ==="
ls -lh /workspaces/OmegaSports-Validation-Lab/data/collection_log.txt | awk '{print $5, $9}'

echo ""
echo "To monitor live: tail -f data/collection_log.txt"
echo "To stop process: pkill -f collect_historical_5years"
