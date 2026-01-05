#!/bin/bash
# Persistent historical data collection runner
# This script ensures the collection process runs to completion

LOG_FILE="/workspaces/OmegaSports-Validation-Lab/data/collection_log.txt"
SCRIPT_DIR="/workspaces/OmegaSports-Validation-Lab"

cd "$SCRIPT_DIR"

echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting historical data collection..." | tee -a "$LOG_FILE"

# Run with error handling and auto-retry on failure
MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Attempt $((RETRY_COUNT + 1)) of $MAX_RETRIES" | tee -a "$LOG_FILE"
    
    # Run the collection script
    python -u scripts/collect_historical_5years.py --sport all --years 2020-2024 2>&1 | tee -a "$LOG_FILE"
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - ✓ Collection completed successfully!" | tee -a "$LOG_FILE"
        exit 0
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - ✗ Collection failed with exit code $EXIT_CODE" | tee -a "$LOG_FILE"
        RETRY_COUNT=$((RETRY_COUNT + 1))
        
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Retrying in 10 seconds..." | tee -a "$LOG_FILE"
            sleep 10
        fi
    fi
done

echo "$(date '+%Y-%m-%d %H:%M:%S') - ✗ Collection failed after $MAX_RETRIES attempts" | tee -a "$LOG_FILE"
exit 1
