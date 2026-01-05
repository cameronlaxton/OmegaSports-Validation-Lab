#!/bin/bash
# Run stats collection for all seasons with missing data

LOG_DIR="/workspaces/OmegaSports-Validation-Lab/data/logs"
PYTHON="/workspaces/OmegaSports-Validation-Lab/.venv/bin/python"
SCRIPT="/workspaces/OmegaSports-Validation-Lab/scripts/collect_data.py"

echo "$(date): Starting full stats collection" >> "$LOG_DIR/stats_all.log"

for YEAR in 2019 2022 2023 2024; do
    echo "$(date): Starting NBA $YEAR stats collection" >> "$LOG_DIR/stats_all.log"
    $PYTHON $SCRIPT --sport NBA --years $YEAR --phase stats >> "$LOG_DIR/stats_$YEAR.log" 2>&1
    echo "$(date): Completed NBA $YEAR stats collection" >> "$LOG_DIR/stats_all.log"
done

echo "$(date): All stats collection complete" >> "$LOG_DIR/stats_all.log"
$PYTHON /workspaces/OmegaSports-Validation-Lab/scripts/check_status.py >> "$LOG_DIR/stats_all.log" 2>&1

# Also run odds collection after stats
echo "$(date): Starting odds collection" >> "$LOG_DIR/stats_all.log"
for YEAR in 2019 2020 2021 2022 2023 2024 2025; do
    echo "$(date): Starting NBA $YEAR odds collection" >> "$LOG_DIR/stats_all.log"
    $PYTHON $SCRIPT --sport NBA --years $YEAR --phase odds >> "$LOG_DIR/odds_$YEAR.log" 2>&1
    echo "$(date): Completed NBA $YEAR odds collection" >> "$LOG_DIR/stats_all.log"
done
echo "$(date): All collection complete" >> "$LOG_DIR/stats_all.log"
