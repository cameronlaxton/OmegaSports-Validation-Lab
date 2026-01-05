#!/usr/bin/env python3
"""
Simple Historical Data Collection Script

Clear, straightforward data collection with 4 independent phases:
1. GAMES   - Fetch game schedule/results from BallDontLie
2. STATS   - Fetch player box scores for games missing stats  
3. ODDS    - Fetch betting lines for games missing odds
4. PROPS   - Fetch player props for games missing props

Each phase only fetches what's missing. No overwrites. No re-fetching.

Usage:
    # Run all phases for NBA 2020-2024
    python scripts/collect_data.py --sport NBA --years 2020-2024
    
    # Run specific phase only
    python scripts/collect_data.py --sport NBA --years 2024 --phase games
    python scripts/collect_data.py --sport NBA --years 2024 --phase stats
    python scripts/collect_data.py --sport NBA --years 2024 --phase odds
    
    # Check what's missing
    python scripts/collect_data.py --status
"""

import argparse
import logging
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from omega.balldontlie_client import BallDontLieAPIClient
from omega.odds_api_client import TheOddsAPIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Season date ranges (key = season label in DB, value = date range)
SEASON_DATES = {
    "NBA": {
        2019: ("2019-10-22", "2020-10-11"),  # 2019-20 season
        2020: ("2019-10-22", "2020-10-11"),  # alias
        2021: ("2020-12-22", "2022-06-16"),  # 2020-21 + overlap
        2022: ("2021-10-19", "2022-06-16"),  # 2021-22 season
        2023: ("2022-10-18", "2024-06-17"),  # 2022-23 + overlap
        2024: ("2023-10-24", "2024-06-17"),  # 2023-24 season
        2025: ("2024-10-22", "2025-06-30"),  # 2024-25 season
    }
}


class SimpleDataCollector:
    """Simple, straightforward data collector."""
    
    def __init__(self, db_path: str = "data/sports_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        # Initialize API clients
        self.bdl = BallDontLieAPIClient()
        self.odds_api = TheOddsAPIClient()
        
        logger.info(f"Connected to {db_path}")
    
    # =========================================================================
    # PHASE 1: GAMES - Fetch game schedule and results
    # =========================================================================
    
    def collect_games(self, sport: str, year: int) -> int:
        """
        Fetch games for a season. Only inserts NEW games (no overwrites).
        
        Returns: Number of new games added
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"PHASE 1: COLLECTING {sport} {year} GAMES")
        logger.info(f"{'='*60}")
        
        if year not in SEASON_DATES.get(sport, {}):
            logger.error(f"Year {year} not configured for {sport}")
            return 0
        
        start_date, end_date = SEASON_DATES[sport][year]
        season_param = year - 1  # BallDontLie uses start year
        
        # Get existing game IDs
        existing_ids = set(self._get_existing_game_ids(sport, start_date, end_date))
        logger.info(f"Existing games in DB: {len(existing_ids)}")
        
        # Fetch from API in weekly chunks
        new_games = 0
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        current = start
        
        while current <= end:
            chunk_end = min(current + timedelta(days=7), end)
            
            try:
                games = self.bdl.get_games(
                    start_date=current.strftime("%Y-%m-%d"),
                    end_date=chunk_end.strftime("%Y-%m-%d"),
                    season=season_param
                )
                
                for game in games:
                    game_id = str(game.get("id"))
                    
                    # Skip if already exists
                    if game_id in existing_ids:
                        continue
                    
                    # Insert new game
                    self._insert_game({
                        "game_id": game_id,
                        "date": game.get("date", "")[:10],
                        "sport": sport,
                        "season": year,
                        "home_team": game.get("home_team", {}).get("full_name", ""),
                        "away_team": game.get("visitor_team", {}).get("full_name", ""),
                        "home_score": game.get("home_team_score"),
                        "away_score": game.get("visitor_team_score"),
                        "status": game.get("status", ""),
                    })
                    new_games += 1
                    existing_ids.add(game_id)
                
                logger.info(f"  {current.strftime('%Y-%m-%d')}: +{len(games)} checked, {new_games} new total")
                
            except Exception as e:
                logger.error(f"  Error fetching {current.strftime('%Y-%m-%d')}: {e}")
            
            current = chunk_end + timedelta(days=1)
        
        logger.info(f"✓ Added {new_games} new games")
        return new_games
    
    # =========================================================================
    # PHASE 2: STATS - Fetch player stats for games missing them
    # =========================================================================
    
    def collect_stats(self, sport: str, year: int) -> int:
        """
        Fetch player stats for games that don't have them yet.
        
        Returns: Number of games enriched with stats
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"PHASE 2: COLLECTING {sport} {year} PLAYER STATS")
        logger.info(f"{'='*60}")
        
        if year not in SEASON_DATES.get(sport, {}):
            return 0
        
        start_date, end_date = SEASON_DATES[sport][year]
        
        # Get games missing stats
        games_needing_stats = self._get_games_missing_stats(sport, start_date, end_date)
        logger.info(f"Games needing stats: {len(games_needing_stats)}")
        
        if not games_needing_stats:
            logger.info("✓ All games already have stats")
            return 0
        
        enriched = 0
        errors = 0
        
        for idx, (game_id, game_date) in enumerate(games_needing_stats):
            try:
                # Fetch stats for single game (only for numeric game IDs)
                # BallDontLie API only supports numeric game IDs
                # Skip games with string IDs like 'nba_473679' (from ESPN/other sources)
                try:
                    numeric_game_id = int(game_id)
                except (ValueError, TypeError):
                    errors += 1
                    if errors <= 5:
                        logger.error(f"  Error for game {game_id}: Skipping non-numeric game ID (likely from ESPN API)")
                    continue
                
                stats = self.bdl.get_game_stats([numeric_game_id])
                
                if stats:
                    self._update_game_stats(game_id, stats)
                    enriched += 1
                
                # Progress every 10 games
                if (idx + 1) % 10 == 0:
                    logger.info(f"  Progress: {idx + 1}/{len(games_needing_stats)} ({enriched} enriched, {errors} errors)")
                
            except Exception as e:
                errors += 1
                if errors <= 5:  # Only log first 5 errors
                    logger.error(f"  Error for game {game_id}: {e}")
        
        logger.info(f"✓ Enriched {enriched} games with player stats ({errors} errors)")
        return enriched
    
    # =========================================================================
    # PHASE 3: ODDS - Fetch betting odds for games missing them
    # =========================================================================
    
    def collect_odds(self, sport: str, year: int) -> int:
        """
        Fetch betting odds for games that don't have them yet.
        
        Returns: Number of games enriched with odds
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"PHASE 3: COLLECTING {sport} {year} BETTING ODDS")
        logger.info(f"{'='*60}")
        
        if year not in SEASON_DATES.get(sport, {}):
            return 0
        
        start_date, end_date = SEASON_DATES[sport][year]
        
        # Get games missing odds
        games_needing_odds = self._get_games_missing_odds(sport, start_date, end_date)
        logger.info(f"Games needing odds: {len(games_needing_odds)}")
        
        if not games_needing_odds:
            logger.info("✓ All games already have odds")
            return 0
        
        # Group by date for efficiency
        dates_to_fetch = {}
        for game_id, game_date, home_team, away_team in games_needing_odds:
            if game_date not in dates_to_fetch:
                dates_to_fetch[game_date] = []
            dates_to_fetch[game_date].append((game_id, home_team, away_team))
        
        enriched = 0
        for idx, (date, games) in enumerate(sorted(dates_to_fetch.items())):
            try:
                # Fetch odds for this date
                odds_data = self.odds_api.get_historical_odds(sport=sport, date=date)
                
                if odds_data:
                    for game_id, home_team, away_team in games:
                        # Try to match
                        matched_odds = self._match_odds(odds_data, home_team, away_team)
                        if matched_odds:
                            self._update_game_odds(game_id, matched_odds)
                            enriched += 1
                
                if (idx + 1) % 10 == 0:
                    logger.info(f"  Progress: {idx + 1}/{len(dates_to_fetch)} dates ({enriched} enriched)")
                
            except Exception as e:
                logger.error(f"  Error fetching odds for {date}: {e}")
        
        logger.info(f"✓ Enriched {enriched} games with odds")
        return enriched
    
    # =========================================================================
    # DATABASE HELPERS
    # =========================================================================
    
    def _get_existing_game_ids(self, sport: str, start_date: str, end_date: str) -> List[str]:
        """Get IDs of games already in database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT game_id FROM games 
            WHERE sport = ? AND date >= ? AND date <= ?
        """, (sport, start_date, end_date))
        return [row[0] for row in cursor.fetchall()]
    
    def _get_games_missing_stats(self, sport: str, start_date: str, end_date: str) -> List[tuple]:
        """Get games that don't have player stats yet."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT game_id, date FROM games 
            WHERE sport = ? AND date >= ? AND date <= ?
            AND (has_player_stats = 0 OR has_player_stats IS NULL)
            ORDER BY date
        """, (sport, start_date, end_date))
        return cursor.fetchall()
    
    def _get_games_missing_odds(self, sport: str, start_date: str, end_date: str) -> List[tuple]:
        """Get games that don't have odds yet."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT game_id, date, home_team, away_team FROM games 
            WHERE sport = ? AND date >= ? AND date <= ?
            AND (has_odds = 0 OR has_odds IS NULL)
            ORDER BY date
        """, (sport, start_date, end_date))
        return cursor.fetchall()
    
    def _insert_game(self, game: Dict[str, Any]):
        """Insert a new game (no overwrite)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO games 
            (game_id, date, sport, season, home_team, away_team, home_score, away_score, status, 
             has_player_stats, has_odds, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
        """, (
            game["game_id"], game["date"], game["sport"], game["season"],
            game["home_team"], game["away_team"], game["home_score"], game["away_score"],
            game["status"], int(time.time()), int(time.time())
        ))
        self.conn.commit()
    
    def _update_game_stats(self, game_id: str, stats: List[Dict]):
        """Update game with player stats (only stats fields, nothing else)."""
        import json
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE games 
            SET player_stats = ?, has_player_stats = 1, updated_at = ?
            WHERE game_id = ?
        """, (json.dumps(stats), int(time.time()), game_id))
        self.conn.commit()
    
    def _update_game_odds(self, game_id: str, odds: Dict[str, Any]):
        """Update game with odds (only odds fields, nothing else)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE games 
            SET moneyline_home = ?, moneyline_away = ?,
                spread_line = ?, spread_home_odds = ?, spread_away_odds = ?,
                total_line = ?, total_over_odds = ?, total_under_odds = ?,
                has_odds = 1, updated_at = ?
            WHERE game_id = ?
        """, (
            odds.get("moneyline", {}).get("home"),
            odds.get("moneyline", {}).get("away"),
            odds.get("spread", {}).get("line"),
            odds.get("spread", {}).get("home_odds"),
            odds.get("spread", {}).get("away_odds"),
            odds.get("total", {}).get("line"),
            odds.get("total", {}).get("over_odds"),
            odds.get("total", {}).get("under_odds"),
            int(time.time()),
            game_id
        ))
        self.conn.commit()
    
    def _match_odds(self, odds_list: List[Dict], home_team: str, away_team: str) -> Optional[Dict]:
        """Find matching odds for a game by team names."""
        home_lower = home_team.lower()
        away_lower = away_team.lower()
        
        for odds in odds_list:
            odds_home = odds.get("home_team", "").lower()
            odds_away = odds.get("away_team", "").lower()
            
            # Fuzzy match
            if (self._team_match(home_lower, odds_home) and 
                self._team_match(away_lower, odds_away)):
                return odds
        
        return None
    
    def _team_match(self, t1: str, t2: str) -> bool:
        """Simple team name matching."""
        return t1 in t2 or t2 in t1 or t1 == t2
    
    # =========================================================================
    # STATUS
    # =========================================================================
    
    def print_status(self):
        """Print collection status."""
        cursor = self.conn.cursor()
        
        print("\n" + "="*70)
        print("📊 DATA COLLECTION STATUS")
        print("="*70)
        
        cursor.execute("""
            SELECT 
                sport, season,
                COUNT(*) as total,
                SUM(CASE WHEN has_player_stats = 1 THEN 1 ELSE 0 END) as with_stats,
                SUM(CASE WHEN has_odds = 1 THEN 1 ELSE 0 END) as with_odds,
                MIN(date) as first_date,
                MAX(date) as last_date
            FROM games
            GROUP BY sport, season
            ORDER BY sport, season
        """)
        
        print(f"\n{'Sport':<6} {'Year':<6} {'Games':<8} {'Stats':<15} {'Odds':<15} {'Dates':<25}")
        print("-"*70)
        
        for row in cursor.fetchall():
            sport, season, total, stats, odds, first_date, last_date = row
            stats = stats or 0
            odds = odds or 0
            stats_pct = f"{stats}/{total} ({100*stats//total}%)" if total else "0"
            odds_pct = f"{odds}/{total} ({100*odds//total}%)" if total else "0"
            dates = f"{first_date} to {last_date}" if first_date else "N/A"
            
            print(f"{sport or 'N/A':<6} {season or 'N/A':<6} {total:<8} {stats_pct:<15} {odds_pct:<15} {dates:<25}")
        
        print()


def main():
    parser = argparse.ArgumentParser(description='Simple data collection')
    parser.add_argument('--sport', type=str, default='NBA', help='Sport (NBA, NFL)')
    parser.add_argument('--years', type=str, help='Year or range (2024 or 2020-2024)')
    parser.add_argument('--phase', type=str, choices=['games', 'stats', 'odds', 'all'], 
                        default='all', help='Which phase to run')
    parser.add_argument('--status', action='store_true', help='Show status only')
    parser.add_argument('--db', default='data/sports_data.db', help='Database path')
    
    args = parser.parse_args()
    
    collector = SimpleDataCollector(db_path=args.db)
    
    if args.status:
        collector.print_status()
        return
    
    if not args.years:
        print("Error: --years required (e.g., --years 2024 or --years 2020-2024)")
        return
    
    # Parse years
    if '-' in args.years:
        start_year, end_year = map(int, args.years.split('-'))
        years = list(range(start_year, end_year + 1))
    else:
        years = [int(args.years)]
    
    # Run collection
    for year in years:
        if args.phase in ['all', 'games']:
            collector.collect_games(args.sport, year)
        
        if args.phase in ['all', 'stats']:
            collector.collect_stats(args.sport, year)
        
        if args.phase in ['all', 'odds']:
            collector.collect_odds(args.sport, year)
    
    # Show final status
    collector.print_status()


if __name__ == '__main__':
    main()
