# Player Props Betting Lines Setup Guide

## Problem

The `player_props` table has `actual_value` (player performance) but is missing betting lines (`over_line`, `over_odds`, `under_odds`). This prevents player props calibration from working.

## Solution: Two-Step Process

### Step 1: Fetch Odds from The Odds API

Use the existing `ingest_player_prop_odds.py` script to fetch player prop odds and store them in the `player_props_odds` table:

```bash
# Single date
python scripts/ingest_player_prop_odds.py --sport NBA --date 2024-01-15

# Date range
python scripts/ingest_player_prop_odds.py --sport NBA --start-date 2024-01-01 --end-date 2024-01-07
```

**What this does:**
- Fetches player prop odds from The Odds API
- Stores them in `player_props_odds` table
- Matches games by team names

**Requirements:**
- `THE_ODDS_API_KEY` environment variable must be set
- Historical data may require a paid API plan

### Step 2: Transfer Odds to player_props Table

Use the new `update_player_props_with_lines.py` script to copy betting lines from `player_props_odds` to `player_props`:

```bash
# Single date
python scripts/update_player_props_with_lines.py --sport NBA --date 2024-01-15

# Date range
python scripts/update_player_props_with_lines.py --sport NBA --start-date 2024-01-01 --end-date 2024-01-07
```

**What this does:**
- Reads odds from `player_props_odds` table
- Matches them to `player_props` records (by game_id, player_name, prop_type)
- Updates `player_props` with betting lines and odds
- Uses fuzzy matching for player names

## Complete Workflow

```bash
# 1. Fetch odds for a date range
python scripts/ingest_player_prop_odds.py --sport NBA --start-date 2024-01-01 --end-date 2024-01-31

# 2. Transfer odds to player_props
python scripts/update_player_props_with_lines.py --sport NBA --start-date 2024-01-01 --end-date 2024-01-31

# 3. Verify data
python -c "from core.db_manager import DatabaseManager; db = DatabaseManager(); conn = db.get_connection(); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM player_props WHERE sport=\"NBA\" AND over_line IS NOT NULL'); print(f'Props with lines: {cursor.fetchone()[0]:,}')"

# 4. Run calibration (will now include player props!)
python cli.py backtest --league NBA --start-date 2019-10-22 --end-date 2024-12-31
```

## Why Two Steps?

1. **`ingest_player_prop_odds.py`** - Fetches from API and stores in a separate table (`player_props_odds`) because:
   - API game IDs may not match our game IDs
   - API player names may not match our player names exactly
   - Allows multiple bookmakers per prop
   - Separates data collection from data integration

2. **`update_player_props_with_lines.py`** - Transfers to `player_props` because:
   - Matches by game_id (after resolving API IDs to our IDs)
   - Fuzzy matches player names
   - Updates existing `player_props` records with betting lines
   - This is what calibration needs

## Troubleshooting

### No odds fetched
- Check `THE_ODDS_API_KEY` is set
- Check API plan includes historical data (if fetching past dates)
- Try a recent date (today or tomorrow) - current odds are more likely to work

### No matches found
- Check that `player_props_odds` has data: `SELECT COUNT(*) FROM player_props_odds`
- Check that `player_props` has data: `SELECT COUNT(*) FROM player_props WHERE sport='NBA'`
- Player name matching may need adjustment - check logs for unmatched players

### Calibration still shows 0 props
- Verify props have lines: `SELECT COUNT(*) FROM player_props WHERE over_line IS NOT NULL AND sport='NBA'`
- Check date range matches your calibration period
- Re-run calibration after updating props

## Alternative: Manual Update

If API doesn't work, you can manually update `player_props`:

```sql
UPDATE player_props
SET over_line = 27.5,
    under_line = 27.5,
    over_odds = -110,
    under_odds = -110
WHERE prop_id = 'your_prop_id';
```

But this is not scalable for thousands of props.

