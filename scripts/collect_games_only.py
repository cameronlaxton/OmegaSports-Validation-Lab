#!/usr/bin/env python3
"""
⚠️ DEPRECATED - DO NOT USE

This script is deprecated and will be removed in a future version.

Use instead:
    python scripts/collect_historical_sqlite.py --sports NBA NFL --start-year 2020 --end-year 2024

Reason for deprecation:
    - Superseded by collect_historical_sqlite.py which provides:
      * Better data validation
      * Comprehensive error handling
      * Multi-threading support
      * Resume capability
      * Unified collection pipeline
    
See: START_HERE.md for current script recommendations

---

LEGACY: Simple script to collect games only (no enrichment).
Supports both NBA and NFL data collection.
"""

import sys
import logging
from datetime import datetime, timedelta
from core.db_manager import DatabaseManager
from omega.balldontlie_client import BallDontLieAPIClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Season date ranges (BallDontLie uses starting year for season parameter)
SEASON_DATES = {
    "NBA": {
        2020: (datetime(2019, 10, 22), datetime(2020, 10, 11), 2019),  # (start, end, api_season)
        2021: (datetime(2020, 12, 22), datetime(2021, 7, 20), 2020),
        2022: (datetime(2021, 10, 19), datetime(2022, 6, 16), 2021),
        2023: (datetime(2022, 10, 18), datetime(2023, 6, 12), 2022),
        2024: (datetime(2023, 10, 24), datetime(2024, 6, 17), 2023),
    },
    "NFL": {
        2020: (datetime(2019, 9, 5), datetime(2020, 2, 2), 2019),
        2021: (datetime(2020, 9, 10), datetime(2021, 2, 7), 2020),
        2022: (datetime(2021, 9, 9), datetime(2022, 2, 13), 2021),
        2023: (datetime(2022, 9, 8), datetime(2023, 2, 12), 2022),
        2024: (datetime(2023, 9, 7), datetime(2024, 2, 11), 2023),
    }
}


def collect_games(sport='NBA', season_year=2020):
    """
    Collect games for a specific sport and season.
    
    Args:
        sport: Sport type (NBA or NFL)
        season_year: Ending year of the season (e.g., 2020 for 2019-20 season)
    """
    # Initialize
    db = DatabaseManager('data/sports_data.db')
    client = BallDontLieAPIClient()
    
    if sport not in SEASON_DATES or season_year not in SEASON_DATES[sport]:
        logger.error(f"Invalid sport/season: {sport} {season_year}")
        return
    
    start_date, end_date, api_season = SEASON_DATES[sport][season_year]
    
    logger.info(f"📥 Collecting {sport} {season_year} season ({start_date.date()} to {end_date.date()})")
    
    total_games = 0
    duplicates = 0
    current = start_date
    chunk_size = timedelta(days=7)
    
    while current <= end_date:
        chunk_end = min(current + chunk_size, end_date)
        
        # Fetch games
        games = client.get_games(
            start_date=current.strftime("%Y-%m-%d"),
            end_date=chunk_end.strftime("%Y-%m-%d"),
            season=api_season
        )
        
        # Insert each game
        for game in games:
            sport_prefix = sport.lower()
            game_data = {
                'game_id': f"{sport_prefix}_{game['id']}",
                'date': game['date'],
                'sport': sport,
                'league': sport,
                'season': season_year,  # Store as ending year
                'home_team': game['home_team']['full_name'],
                'away_team': game['visitor_team']['full_name'],
                'home_score': game.get('home_team_score'),
                'away_score': game.get('visitor_team_score'),
                'status': game.get('status', 'Final')
            }
            
            try:
                db.insert_game(game_data)
                total_games += 1
            except Exception as e:
                if "UNIQUE constraint" in str(e):
                    duplicates += 1
                else:
                    logger.error(f"Error inserting game {game_data['game_id']}: {e}")
        
        logger.info(f"  {current.strftime('%Y-%m-%d')}: +{len(games)} games (total: {total_games})")
        current += chunk_size + timedelta(days=1)
    
    logger.info(f"\n✅ Collection complete!")
    logger.info(f"   New games: {total_games}")
    logger.info(f"   Duplicates skipped: {duplicates}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect games from BallDontLie API')
    parser.add_argument('--sport', default='NBA', choices=['NBA', 'NFL'], help='Sport type')
    parser.add_argument('--season', type=int, required=True, help='Season ending year (e.g., 2020 for 2019-20)')
    
    args = parser.parse_args()
    
    collect_games(sport=args.sport, season_year=args.season)
