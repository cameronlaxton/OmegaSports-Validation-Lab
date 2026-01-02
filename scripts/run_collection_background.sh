#!/bin/bash
# Background data collection runner
# Runs independently of terminal sessions

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_DIR/data/collection_background.log"
PID_FILE="$PROJECT_DIR/data/collection.pid"

echo "Starting historical data collection in background..."
echo "Log file: $LOG_FILE"
echo "PID file: $PID_FILE"

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "Collection is already running (PID: $OLD_PID)"
        echo "To monitor: tail -f $LOG_FILE"
        exit 1
    else
        echo "Removing stale PID file"
        rm -f "$PID_FILE"
    fi
fi

# Create data directory if needed
mkdir -p "$PROJECT_DIR/data"

# Run collection with nohup (persists after terminal closes)
cd "$PROJECT_DIR"
nohup python -u scripts/collect_historical_5years.py --sport all --years 2020-2025 > "$LOG_FILE" 2>&1 &
COLLECTION_PID=$!

# Save PID
echo "$COLLECTION_PID" > "$PID_FILE"

echo "✓ Collection started successfully!"
echo "  PID: $COLLECTION_PID"
echo "  Monitor with: tail -f $LOG_FILE"
echo "  Stop with: kill $COLLECTION_PID"
echo ""
echo "This process will continue even if you close the terminal."
