# Scripts Directory

This directory contains utility scripts for the OmegaSports Validation Lab.

## Available Scripts

### load_and_validate_games.py

Loads and validates historical game data (2020-2024) for sports betting analysis.

**Features:**
- Fetches comprehensive game data with statistics (beyond just schedules)
- Supports multiple sports: NBA, NFL, NCAAB, NCAAF
- Includes detailed player statistics and team metrics
- Retry logic for failed requests
- Data validation and caching
- Progress reporting

**Usage:**

```bash
# Load all sports with default settings (2020-2024, min 1000 games)
python scripts/load_and_validate_games.py

# Load specific sports
python scripts/load_and_validate_games.py --sports NBA NFL

# Custom year range
python scripts/load_and_validate_games.py --start-year 2022 --end-year 2024

# Custom minimum count
python scripts/load_and_validate_games.py --min-count 500

# Verbose output
python scripts/load_and_validate_games.py --verbose

# All options combined
python scripts/load_and_validate_games.py \
    --start-year 2020 \
    --end-year 2024 \
    --sports NBA NFL NCAAB NCAAF \
    --min-count 1000 \
    --max-retries 3 \
    --verbose
```

**Output:**
- Saves game data to `data/historical/{sport}_{year}_games.json`
- Logs activity to `data/logs/load_games.log`
- Caches API responses in `data/cache/`
- Reports summary statistics and validation results

**Data Sources:**
The script fetches data from multiple sources to ensure comprehensive coverage:
- **ESPN API**: Game results, scores, basic statistics
- **Additional statistics**: Team performance metrics, player statistics
- **Betting lines**: Moneyline, spread, totals (when available)

This goes beyond ESPN's scheduler API to include:
- Historical game results (not just upcoming schedules)
- Complete player statistics
- Team statistics and advanced metrics
- Betting lines and odds history

**Example Output:**

```
================================================================================
                  Loading and Validating Historical Games
================================================================================

Start Year: 2020
End Year: 2024
Sports: NBA, NFL, NCAAB, NCAAF
Minimum Count: 1000

Initializing components...
✓ Components initialized

Processing NBA...
-------------------------------
NBA: 5190 games loaded (took 45.23s)
✓ NBA has sufficient data: 5190 >= 1000

Processing NFL...
-------------------------------
NFL: 1280 games loaded (took 23.12s)
✓ NFL has sufficient data: 1280 >= 1000

================================================================================
                                   Summary
================================================================================

✓ NBA: 5190 games
✓ NFL: 1280 games
✓ NCAAB: 3450 games
✓ NCAAF: 1320 games

✓ All sports ready for Module 1
```

## Directory Structure

```
scripts/
├── __init__.py
├── README.md
└── load_and_validate_games.py
```

## Adding New Scripts

When adding new scripts to this directory:

1. Follow Python naming conventions (snake_case)
2. Include a docstring at the top explaining purpose and usage
3. Make scripts executable: `chmod +x script_name.py`
4. Add logging to `data/logs/`
5. Update this README with usage information
