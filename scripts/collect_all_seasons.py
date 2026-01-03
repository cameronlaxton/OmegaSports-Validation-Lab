#!/usr/bin/env python3
"""
Collect games for multiple seasons at once.
"""

import sys
import logging
from collect_games_only import collect_games

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Collect all specified seasons."""
    
    if len(sys.argv) > 1:
        years = [int(y) for y in sys.argv[1].split(',')]
    else:
        # Default: last 5 years
        years = [2021, 2022, 2023, 2024, 2025]
    
    sport = sys.argv[2] if len(sys.argv) > 2 else 'NBA'
    
    logger.info("="*80)
    logger.info(f"🚀 BULK COLLECTION: {sport} Seasons {years}")
    logger.info("="*80)
    
    for year in years:
        try:
            collect_games(sport=sport, season_year=year)
            logger.info(f"✅ {sport} {year} complete\n")
        except Exception as e:
            logger.error(f"❌ {sport} {year} failed: {e}\n")
            continue
    
    logger.info("="*80)
    logger.info("🎉 BULK COLLECTION COMPLETE")
    logger.info("="*80)


if __name__ == "__main__":
    main()
