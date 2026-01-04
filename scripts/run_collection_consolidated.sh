#!/bin/bash
# Consolidated collection runner - stats THEN odds, sequential to avoid overlap/corruption
# Single unified log for monitoring all progress

set -e

LOG_DIR="/workspaces/OmegaSports-Validation-Lab/data/logs"
PYTHON="/workspaces/OmegaSports-Validation-Lab/.venv/bin/python"
SCRIPT="/workspaces/OmegaSports-Validation-Lab/scripts/collect_data.py"
UNIFIED_LOG="$LOG_DIR/collection_consolidated.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$UNIFIED_LOG"
}

log "================================================================================"
log "STARTING CONSOLIDATED DATA COLLECTION (Stats → Odds, Sequential)"
log "================================================================================"
log "Start Time: $(date)"
log ""

# ============================================================================
# PHASE 1: STATS COLLECTION (Sequential by season)
# ============================================================================
log "PHASE 1: STATS COLLECTION"
log "--------"

SEASONS_STATS=(2019 2022 2023 2024)
for YEAR in "${SEASONS_STATS[@]}"; do
    log "Starting NBA $YEAR stats collection..."
    if $PYTHON $SCRIPT --sport NBA --years $YEAR --phase stats >> "$UNIFIED_LOG" 2>&1; then
        log "✓ Completed NBA $YEAR stats collection"
    else
        log "✗ ERROR in NBA $YEAR stats collection (exit code $?)"
        log "Continuing to next season..."
    fi
    log ""
done

log "=========================================="
log "PHASE 1 COMPLETE: All stats seasons done"
log "=========================================="
log ""

# Checkpoint: Show current status
log "Status Checkpoint after Stats Collection:"
$PYTHON /workspaces/OmegaSports-Validation-Lab/scripts/check_status.py >> "$UNIFIED_LOG" 2>&1 || log "Status check failed (non-fatal)"
log ""

# ============================================================================
# PHASE 2: ODDS COLLECTION (Sequential by season)
# ============================================================================
log "PHASE 2: ODDS COLLECTION"
log "--------"

SEASONS_ODDS=(2019 2020 2021 2022 2023 2024 2025)
for YEAR in "${SEASONS_ODDS[@]}"; do
    log "Starting NBA $YEAR odds collection..."
    if $PYTHON $SCRIPT --sport NBA --years $YEAR --phase odds >> "$UNIFIED_LOG" 2>&1; then
        log "✓ Completed NBA $YEAR odds collection"
    else
        log "✗ ERROR in NBA $YEAR odds collection (exit code $?)"
        log "Continuing to next season..."
    fi
    log ""
done

log "=========================================="
log "PHASE 2 COMPLETE: All odds seasons done"
log "=========================================="
log ""

# Final status
log "Final Status Checkpoint:"
$PYTHON /workspaces/OmegaSports-Validation-Lab/scripts/check_status.py >> "$UNIFIED_LOG" 2>&1 || log "Status check failed (non-fatal)"
log ""

log "================================================================================"
log "✓ ALL COLLECTION PHASES COMPLETE"
log "End Time: $(date)"
log "================================================================================"
