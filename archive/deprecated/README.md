# Deprecated Scripts Archive

**⚠️ DO NOT USE SCRIPTS IN THIS DIRECTORY ⚠️**

This directory contains historical data collection scripts that have been **deprecated** and replaced by more robust implementations.

---

## Why These Scripts Were Deprecated

These scripts were superseded by `scripts/collect_historical_sqlite.py` which provides:

✅ **Better Architecture:**
- Unified SQLite storage instead of fragmented JSON files
- Thread-safe concurrent operations with proper locking
- Crash recovery and resume capability

✅ **Better Reliability:**
- Comprehensive error handling and retry logic
- Progress tracking with detailed logging
- Automatic validation of collected data

✅ **Better Performance:**
- Multi-threaded data collection (`--workers` flag)
- Indexed database queries for fast backtesting
- Efficient memory usage

✅ **Better Maintainability:**
- Single script instead of 5+ overlapping scripts
- Clear CLI interface with `--help` documentation
- Consistent code style and error messages

---

## Deprecated Scripts in This Archive

| Script | Original Purpose | Replacement |
|--------|------------------|-------------|
| `collect_historical_5years.py` | 5-year bulk collection | `scripts/collect_historical_sqlite.py --start-year 2020 --end-year 2024` |
| `bulk_collect.py` | Multi-season wrapper | `scripts/collect_historical_sqlite.py` (built-in iteration) |
| `collect_games_only.py` | Basic game collection | `scripts/collect_historical_sqlite.py` (includes enrichment) |
| `collect_all_seasons.py` | Season iteration wrapper | `scripts/collect_historical_sqlite.py --start-year X --end-year Y` |
| `collect_historical_odds.py` | Historical odds backfill | Integrated into main collection script |
| `collect_data.py` | First-generation collector | Complete rewrite in new script |
| `run_collection_consolidated.sh` | Shell orchestration | Not needed (Python CLI is sufficient) |
| `run_collection_background.sh` | Background execution | Use `nohup` or `screen` directly |
| `run_persistent_collection.sh` | Daemon mode | Not needed for one-time historical collection |
| `monitor_collection.sh` | Progress monitoring | Built into Python script output |
| `check_collection_status.sh` | Status checker | Replaced by `scripts/check_status.py` |
| `run_all_odds.sh` | Odds collection wrapper | Integrated into main script |
| `run_all_stats.sh` | Stats collection wrapper | Integrated into main script |

---

## If You Need Historical Collection

**Current Recommendation (2026):**

```bash
# ✅ USE THIS - Modern SQLite-based collection
python scripts/collect_historical_sqlite.py \
    --sports NBA NFL \
    --start-year 2020 \
    --end-year 2024 \
    --workers 2

# Check what you have
python scripts/check_status.py
```

**❌ DO NOT USE:**
```bash
# Old fragmented approach (deprecated)
python archive/deprecated/collect_historical_5years.py --sport NBA
python archive/deprecated/collect_historical_odds.py --sport NBA
```

---

## Historical Collection is Complete

**Important:** As of January 2026, historical data collection is **COMPLETE**:

- ✅ **9,093 NBA games** collected (2019-2025, ~7 years)
- ✅ Stored in `data/sports_data.db` (596 MB)
- ✅ Includes game results, team stats, player stats, betting lines
- ✅ Ready for backtesting and calibration

**You should NOT need to run any collection scripts** unless:
1. You're setting up a fresh installation
2. You need to collect data for new sports (NFL, NCAAB, etc.)
3. You're updating data with recent games (use incremental mode)

---

## Rollback Instructions

If you encounter issues and need to restore a deprecated script temporarily:

```bash
# 1. Copy script back to scripts/ directory
cp archive/deprecated/{script_name}.py scripts/

# 2. Install any missing dependencies
pip install -r requirements.txt

# 3. Run the script (see original documentation in script header)
python scripts/{script_name}.py --help

# 4. Report the issue
# File a GitHub issue explaining why the new script didn't work
```

**Please report issues rather than permanently reverting** so we can fix the root cause.

---

## Migration History

- **2024-12:** Multiple collection scripts created during development
- **2025-01:** Consolidated into `collect_historical_sqlite.py`
- **2026-01-05:** Deprecated scripts archived (this archive created)

---

## Questions?

See the main documentation:
- [Repository Audit](../../docs/audit_repo.md) - Full deprecation rationale
- [Scripts README](../../scripts/README.md) - Current script recommendations
- [Data Collection Guide](../../DATA_COLLECTION_GUIDE.md) - Collection best practices
- [Database Guide](../../DATABASE_STORAGE_GUIDE.md) - Database structure

---

**Status:** 🔒 **ARCHIVE ONLY - DO NOT USE FOR NEW WORK**
