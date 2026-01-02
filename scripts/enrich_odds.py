#!/usr/bin/env python3
"""
⚠️ EXPERIMENTAL - USE WITH CAUTION

This script is experimental and may not work as expected.

Consider using:
    python scripts/collect_historical_sqlite.py --sports NBA NFL

Note:
    - This was an experimental enrichment approach
    - Odds collection is now better integrated into the main collection script
    - Keep for reference or experimental purposes only
    
See: START_HERE.md for recommended scripts

---

EXPERIMENTAL: Enrich games with historical betting odds.
Processes games where has_odds = 0.
"""

import sys
import json
import logging
from datetime import datetime, timedelta
from core.db_manager import DatabaseManager
from omega.odds_api_client import TheOddsAPIClient
from core.multi_source_aggregator import MultiSourceAggregator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def enrich_odds(sport='NBA', season=None, limit=None):
    """
    Enrich games with betting odds.
    
    Args:
        sport: Sport type (NBA or NFL)
        season: Season year to filter (optional)
        limit: Max number of games to enrich (optional)
    """
    db = DatabaseManager('data/sports_data.db')
    odds_api = TheOddsAPIClient()
    aggregator = MultiSourceAggregator()
    
    # Query for games needing odds
    query = 'SELECT game_id, date, home_team, away_team, season FROM games WHERE sport = ? AND has_odds = 0'
    params = [sport]
    
    if season:
        query += ' AND season = ?'
        params.append(season)
    
    if limit:
        query += f' LIMIT {limit}'
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    games = cursor.fetchall()
    
    if not games:
        logger.info(f"✅ All {sport} games already have odds")
        return
    
    logger.info(f"🔄 Enriching {len(games)} {sport} games with betting odds...")
    
    enriched = 0
    errors = 0
    
    for game in games:
        game_id, date, home_team, away_team, game_season = game
        
        try:
            # Try to get odds from cache or aggregator
            odds_data = aggregator.get_historical_odds(
                sport=sport,
                home_team=home_team,
                away_team=away_team,
                game_date=date
            )
            
            if odds_data:
                # Extract betting lines
                odds_entry = {
                    'game_id': game_id,
                    'date': date,
                    'sport': sport,
                    'home_team': home_team,
                    'away_team': away_team,
                    'bookmaker': odds_data.get('bookmaker', 'aggregated'),
                    'market_type': odds_data.get('market_type'),
                    'odds_data': odds_data
                }
                
                # Insert into odds_history table
                db.insert_odds_history(odds_entry)
                
                # Update game record with flattened odds
                update_data = {
                    'has_odds': 1,
                    'updated_at': int(datetime.now().timestamp())
                }
                
                # Extract main betting lines if available
                if 'moneyline' in odds_data:
                    update_data['moneyline_home'] = odds_data['moneyline'].get('home')
                    update_data['moneyline_away'] = odds_data['moneyline'].get('away')
                
                if 'spread' in odds_data:
                    update_data['spread_line'] = odds_data['spread'].get('line')
                    update_data['spread_home_odds'] = odds_data['spread'].get('home_odds')
                    update_data['spread_away_odds'] = odds_data['spread'].get('away_odds')
                
                if 'total' in odds_data:
                    update_data['total_line'] = odds_data['total'].get('line')
                    update_data['total_over_odds'] = odds_data['total'].get('over_odds')
                    update_data['total_under_odds'] = odds_data['total'].get('under_odds')
                
                # Build UPDATE query
                set_clause = ', '.join([f"{k} = ?" for k in update_data.keys()])
                values = list(update_data.values()) + [game_id]
                
                cursor.execute(
                    f'UPDATE games SET {set_clause} WHERE game_id = ?',
                    values
                )
                conn.commit()
                
                enriched += 1
                if enriched % 10 == 0:
                    logger.info(f"  Progress: {enriched}/{len(games)} games enriched")
            else:
                # Mark as checked even if no odds found
                cursor.execute(
                    'UPDATE games SET has_odds = -1, updated_at = ? WHERE game_id = ?',
                    (int(datetime.now().timestamp()), game_id)
                )
                conn.commit()
                logger.debug(f"  No odds found for game {game_id}")
                
        except Exception as e:
            logger.error(f"  Error enriching odds for {game_id}: {e}")
            errors += 1
            continue
    
    logger.info(f"\n✅ Odds enrichment complete!")
    logger.info(f"   Enriched: {enriched}")
    logger.info(f"   Not found: {len(games) - enriched - errors}")
    logger.info(f"   Errors: {errors}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich games with betting odds')
    parser.add_argument('--sport', default='NBA', choices=['NBA', 'NFL'], help='Sport type')
    parser.add_argument('--season', type=int, help='Season year (optional)')
    parser.add_argument('--limit', type=int, help='Max games to process (optional)')
    
    args = parser.parse_args()
    
    enrich_odds(sport=args.sport, season=args.season, limit=args.limit)
