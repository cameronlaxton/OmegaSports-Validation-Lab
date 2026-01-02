#!/usr/bin/env python3
"""
Simple script to collect NBA games only (no enrichment).
This is a simplified version to bypass hanging issues.
"""

import logging
from datetime import datetime, timedelta
from core.db_manager import DatabaseManager
from omega.balldontlie_client import BallDontLieAPIClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Initialize
    db = DatabaseManager('data/sports_data.db')
    client = BallDontLieAPIClient()
    
    # NBA 2019-20 season
    start_date = datetime(2019, 10, 22)
    end_date = datetime(2020, 10, 11)
    season = 2019  # BallDontLie uses starting year
    
    logger.info(f"Collecting NBA 2019-20 season ({start_date.date()} to {end_date.date()})")
    
    total_games = 0
    current = start_date
    chunk_size = timedelta(days=7)
    
    while current <= end_date:
        chunk_end = min(current + chunk_size, end_date)
        
        # Fetch games
        games = client.get_games(
            start_date=current.strftime("%Y-%m-%d"),
            end_date=chunk_end.strftime("%Y-%m-%d"),
            season=season
        )
        
        # Insert each game
        for game in games:
            game_data = {
                'game_id': f"nba_{game['id']}",
                'date': game['date'],
                'sport': 'NBA',
                'league': 'NBA',
                'season': season + 1,  # Store as ending year (2020)
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
                if "UNIQUE constraint" not in str(e):
                    logger.error(f"Error inserting game {game_data['game_id']}: {e}")
        
        logger.info(f"  {current.strftime('%Y-%m-%d')}: +{len(games)} games (total: {total_games})")
        current += chunk_size + timedelta(days=1)
    
    logger.info(f"\n✅ Collection complete! {total_games} games collected")

if __name__ == "__main__":
    main()
