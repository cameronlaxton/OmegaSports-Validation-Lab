#!/bin/bash
# Run odds collection for all seasons

LOG_DIR="/workspaces/OmegaSports-Validation-Lab/data/logs"
PYTHON="/workspaces/OmegaSports-Validation-Lab/.venv/bin/python"
SCRIPT="/workspaces/OmegaSports-Validation-Lab/scripts/collect_data.py"

echo "$(date): Starting odds collection for all seasons" >> "$LOG_DIR/odds_all.log"

for YEAR in 2019 2020 2021 2022 2023 2024 2025; do
    echo "$(date): Starting NBA $YEAR odds collection" >> "$LOG_DIR/odds_all.log"
    $PYTHON $SCRIPT --sport NBA --years $YEAR --phase odds >> "$LOG_DIR/odds_$YEAR.log" 2>&1
    echo "$(date): Completed NBA $YEAR odds collection" >> "$LOG_DIR/odds_all.log"
done

echo "$(date): All odds collection complete" >> "$LOG_DIR/odds_all.log"
$PYTHON /workspaces/OmegaSports-Validation-Lab/scripts/check_status.py >> "$LOG_DIR/odds_all.log" 2>&1
