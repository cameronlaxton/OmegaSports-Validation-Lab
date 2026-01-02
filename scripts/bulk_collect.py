#!/usr/bin/env python3
"""
⚠️ DEPRECATED - DO NOT USE

This script is deprecated and will be removed in a future version.

Use instead:
    python scripts/collect_historical_sqlite.py --sports NBA NFL --start-year 2020 --end-year 2024

Reason for deprecation:
    - Superseded by collect_historical_sqlite.py which provides:
      * SQLite database storage (more reliable)
      * Better error handling and resume capability
      * Multi-threading support
      * Comprehensive data validation
    
See: START_HERE.md for current script recommendations

---

LEGACY: Bulk collection tool for multiple seasons of NBA/NFL data.
"""

import sys
import logging
from datetime import datetime
from scripts.collect_games_only import collect_games, SEASON_DATES

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def bulk_collect(sport='NBA', start_season=2020, end_season=2024):
    """
    Collect multiple seasons of data.
    
    Args:
        sport: Sport type (NBA or NFL)
        start_season: First season to collect (ending year)
        end_season: Last season to collect (ending year)
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"🏀 BULK COLLECTION: {sport} {start_season}-{end_season}")
    logger.info(f"{'='*80}\n")
    
    if sport not in SEASON_DATES:
        logger.error(f"Invalid sport: {sport}")
        return
    
    total_games = 0
    seasons_collected = 0
    
    for season_year in range(start_season, end_season + 1):
        if season_year not in SEASON_DATES[sport]:
            logger.warning(f"Skipping {season_year} - no season dates defined")
            continue
        
        try:
            logger.info(f"\n--- Season {season_year} ---")
            collect_games(sport=sport, season_year=season_year)
            seasons_collected += 1
        except Exception as e:
            logger.error(f"Error collecting {sport} {season_year}: {e}")
            continue
    
    logger.info(f"\n{'='*80}")
    logger.info(f"✅ BULK COLLECTION COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"  Seasons collected: {seasons_collected}")
    logger.info()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Bulk collect multiple seasons of data')
    parser.add_argument('--sport', default='NBA', choices=['NBA', 'NFL'], help='Sport type')
    parser.add_argument('--start', type=int, default=2020, help='Start season (ending year)')
    parser.add_argument('--end', type=int, default=2024, help='End season (ending year)')
    
    args = parser.parse_args()
    
    bulk_collect(sport=args.sport, start_season=args.start, end_season=args.end)
