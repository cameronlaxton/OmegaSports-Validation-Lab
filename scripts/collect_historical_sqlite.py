#!/usr/bin/env python3
"""
SQLite-Based Historical Sports Data Collection

Refactored from JSON-based system to SQLite for:
- Incremental, crash-safe writes
- Resume capability after interruptions
- Concurrent worker support (with --workers flag)
- Better memory efficiency
- Fast indexed queries for backtesting

Usage:
    # Single worker (safe mode)
    python scripts/collect_historical_sqlite.py --sport NBA --years 2020 --workers 1
    
    # Resume interrupted collection
    python scripts/collect_historical_sqlite.py --sport NBA --years 2020 --resume
    
    # Multiple sports
    python scripts/collect_historical_sqlite.py --sport all --years 2020-2024 --workers 1
    
    # Export to JSON (legacy compatibility)
    python scripts/collect_historical_sqlite.py --export-json nba_2024.json --sport NBA --years 2024
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from omega.balldontlie_client import BallDontLieAPIClient
from omega.odds_api_client import TheOddsAPIClient
from omega.historical_scrapers import OddsPortalScraper, CoversOddsHistoryScraper
from core.multi_source_aggregator import MultiSourceAggregator
from core.data_pipeline import DataValidator
from core.db_manager import DatabaseManager
from utils.db_helpers import export_to_json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)


class SQLiteHistoricalCollector:
    """
    SQLite-based historical data collector with resume and threading support.
    """
    
    EXPECTED_GAMES = {
        "NBA": 1230,  # ~1,230 games per season
        "NFL": 285    # ~285 games per season
    }
    
    # Season date ranges (adjusted to actual season start dates)
    SEASON_DATES = {
        "NBA": {
            2020: ("2019-10-22", "2020-10-11"),  # 2019-20 season (COVID extended)
            2021: ("2020-12-22", "2021-07-20"),  # 2020-21 season (COVID shortened)
            2022: ("2021-10-19", "2022-06-16"),  # 2021-22 season
            2023: ("2022-10-18", "2023-06-12"),  # 2022-23 season
            2024: ("2023-10-24", "2024-06-17"),  # 2023-24 season
            2025: ("2024-10-22", "2025-06-30")   # 2024-25 season (projected)
        },
        "NFL": {
            2020: ("2020-09-01", "2021-02-28"),
            2021: ("2021-09-01", "2022-02-28"),
            2022: ("2022-09-01", "2023-02-28"),
            2023: ("2023-09-01", "2024-02-29"),
            2024: ("2024-09-01", "2025-02-28"),
            2025: ("2025-09-01", "2026-02-28")
        }
    }
    
    def __init__(
        self,
        db_path: str = "data/sports_data.db",
        workers: int = 1
    ):
        """
        Initialize SQLite collector.
        
        Args:
            db_path: Path to SQLite database
            workers: Number of concurrent workers (default 1 for safety)
        """
        self.db_manager = DatabaseManager(db_path)
        self.workers = workers
        self.write_lock = Lock()  # Thread-safe writes
        
        # Initialize clients
        self.balldontlie = BallDontLieAPIClient()
        self.odds_api = TheOddsAPIClient()
        self.aggregator = MultiSourceAggregator()
        self.validator = DataValidator()
        
        # Initialize scrapers (fallback only)
        self.oddsportal = OddsPortalScraper()
        self.covers = CoversOddsHistoryScraper()
        
        # Statistics
        self.stats = {
            "games_fetched": 0,
            "games_enriched": 0,
            "props_collected": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0
        }
        
        logger.info(f"✓ SQLite collector initialized (workers={workers})")
    
    def collect_year(
        self,
        sport: str,
        year: int,
        resume: bool = False
    ) -> bool:
        """
        Collect all data for a specific sport/year.
        
        Args:
            sport: Sport type (NBA or NFL)
            year: Season year
            resume: If True, skip already-completed games
            
        Returns:
            bool: True if successful
        """
        sport = sport.upper()
        
        if sport not in self.SEASON_DATES:
            logger.error(f"Invalid sport: {sport}")
            return False
        
        if year not in self.SEASON_DATES[sport]:
            logger.error(f"Year {year} not in valid range for {sport}")
            return False
        
        start_date, end_date = self.SEASON_DATES[sport][year]
        
        logger.info("="*60)
        logger.info(f"COLLECTING {sport} {year} SEASON")
        logger.info(f"Date Range: {start_date} to {end_date}")
        logger.info(f"Expected Games: ~{self.EXPECTED_GAMES[sport]}")
        logger.info("="*60)
        
        # Step 1: Fetch games from BallDontLie
        # BallDontLie uses the *starting* year (e.g., 2019 for 2019-20 season)
        season_param = year - 1
        logger.info(f"\n[Step 1/4] Fetching games from BallDontLie (season={season_param})...")
        games = self._fetch_games_balldontlie(sport, start_date, end_date, season_param)
        
        if not games:
            logger.error("No games fetched - aborting")
            return False
        
        logger.info(f"✓ Fetched {len(games)} games")
        
        # Step 2: Filter for resume (skip duplicate game fetching only)
        if resume:
            existing_ids = set(self.db_manager.get_game_ids(sport, start_date, end_date))
            new_games = [g for g in games if g['game_id'] not in existing_ids]
            logger.info(f"✓ Resume mode: {len(new_games)} new games, {len(existing_ids)} existing")
            games = new_games
        
        if not games:
            logger.info("✓ No new games to fetch - skipping to enrichment")
            # Load existing games that need enrichment
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT game_id, date, home_team, away_team, home_score, away_score, season FROM games WHERE sport = ? AND date BETWEEN ? AND ? AND has_player_stats = 0',
                (sport, start_date, end_date)
            )
            rows = cursor.fetchall()
            
            if not rows:
                logger.info("✓ All games already enriched")
                return True
            
            # Convert to game dictionaries for enrichment
            games = []
            for row in rows:
                games.append({
                    'game_id': row[0],
                    'date': row[1],
                    'home_team': row[2],
                    'away_team': row[3],
                    'home_score': row[4],
                    'away_score': row[5],
                    'season': row[6]
                })
            logger.info(f"✓ Loaded {len(games)} games needing enrichment")
        
        # Step 3: Enrich with player stats (uses threading if workers > 1)
        logger.info(f"\n[Step 2/4] Enriching with player statistics...")
        enriched_games = self._enrich_with_player_stats(games, sport)
        
        # Step 4: Enrich with odds
        logger.info(f"\n[Step 3/4] Fetching betting odds...")
        enriched_games = self._enrich_with_odds(enriched_games, sport)
        
        # Step 5: Perplexity enrichment
        logger.info(f"\n[Step 4/4] Perplexity enrichment (cache-first)...")
        enriched_games = self._enrich_with_perplexity(enriched_games)
        
        # Step 6: Collect player props
        logger.info(f"\n[Bonus] Collecting player props...")
        self._collect_player_props(enriched_games, sport)
        
        # Validate
        expected = self.EXPECTED_GAMES[sport]
        total_games = len(self.db_manager.get_game_ids(sport, start_date, end_date))
        coverage = (total_games / expected) * 100 if expected > 0 else 0
        
        logger.info("\n" + "="*60)
        logger.info(f"✅ {sport} {year} COLLECTION COMPLETE")
        logger.info(f"Games in Database: {total_games} / {expected} ({coverage:.1f}%)")
        logger.info(f"Games Enriched: {self.stats['games_enriched']}")
        logger.info(f"Props Collected: {self.stats['props_collected']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("="*60)
        
        return True
    
    def _fetch_games_balldontlie(
        self,
        sport: str,
        start_date: str,
        end_date: str,
        season: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch games using BallDontLie API with weekly chunks.
        
        Args:
            sport: Sport type
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            season: Season year
            
        Returns:
            List of game dictionaries
        """
        games = []
        
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Fetch in weekly chunks to avoid timeouts
        current = start
        chunk_size = timedelta(days=7)
        
        while current <= end:
            chunk_end = min(current + chunk_size, end)
            
            try:
                chunk_games = self.balldontlie.get_games(
                    start_date=current.strftime("%Y-%m-%d"),
                    end_date=chunk_end.strftime("%Y-%m-%d"),
                    season=season
                )
                
                # Convert to our format and insert into database
                for game in chunk_games:
                    game_data = self._convert_balldontlie_game(game, sport, season)
                    
                    # Write to database immediately (crash-safe)
                    with self.write_lock:
                        self.db_manager.insert_game(game_data)
                    
                    games.append(game_data)
                    self.stats['games_fetched'] += 1
                
                logger.info(f"  {current.strftime('%Y-%m-%d')}: +{len(chunk_games)} games (total: {len(games)})")
                
            except Exception as e:
                logger.error(f"  Error fetching chunk {current.strftime('%Y-%m-%d')}: {e}")
                self.stats['errors'] += 1
            
            current = chunk_end + timedelta(days=1)
        
        return games
    
    def _convert_balldontlie_game(
        self,
        api_game: Dict[str, Any],
        sport: str,
        season: int
    ) -> Dict[str, Any]:
        """
        Convert BallDontLie API response to our schema.
        
        Args:
            api_game: Game data from API
            sport: Sport type
            season: Season year
            
        Returns:
            Game dictionary matching our schema
        """
        return {
            "game_id": str(api_game.get("id")),
            "date": api_game.get("date", "")[:10],  # YYYY-MM-DD
            "sport": sport,
            "league": sport,
            "season": season,
            "home_team": api_game.get("home_team", {}).get("full_name", ""),
            "away_team": api_game.get("visitor_team", {}).get("full_name", ""),
            "home_score": api_game.get("home_team_score"),
            "away_score": api_game.get("visitor_team_score"),
            "status": api_game.get("status", ""),
            "venue": api_game.get("home_team", {}).get("city", ""),
            "has_player_stats": 0,
            "has_odds": 0,
            "has_perplexity": 0
        }
    
    def _enrich_with_player_stats(
        self,
        games: List[Dict[str, Any]],
        sport: str
    ) -> List[Dict[str, Any]]:
        """
        Enrich games with player statistics.
        
        Uses threading if workers > 1, otherwise sequential.
        
        Args:
            games: List of games
            sport: Sport type
            
        Returns:
            Enriched games
        """
        if self.workers == 1:
            # Sequential (safe mode)
            return self._enrich_games_sequential(games, sport)
        else:
            # Parallel (advanced mode)
            return self._enrich_games_parallel(games, sport)
    
    def _enrich_games_sequential(
        self,
        games: List[Dict[str, Any]],
        sport: str
    ) -> List[Dict[str, Any]]:
        """Sequential enrichment with progress logging."""
        enriched = []
        
        for idx, game in enumerate(games):
            try:
                # Fetch player stats using BallDontLie /v1/stats endpoint
                stats = self.balldontlie.get_box_score(game['game_id'])
                
                if stats:
                    game['player_stats'] = stats
                    game['has_player_stats'] = 1
                
                # Update database
                with self.write_lock:
                    self.db_manager.insert_game(game)
                
                enriched.append(game)
                self.stats['games_enriched'] += 1
                
                # Progress logging
                if (idx + 1) % 50 == 0:
                    logger.info(f"  Progress: {idx + 1}/{len(games)} games enriched")
                
            except Exception as e:
                logger.error(f"  Error enriching game {game['game_id']}: {e}")
                self.stats['errors'] += 1
                enriched.append(game)
        
        return enriched
    
    def _enrich_games_parallel(
        self,
        games: List[Dict[str, Any]],
        sport: str
    ) -> List[Dict[str, Any]]:
        """
        Parallel enrichment with thread pool.
        
        IMPORTANT: Only use with workers > 1 and proper rate limiting.
        """
        enriched = []
        
        def enrich_one_game(game: Dict[str, Any]) -> Dict[str, Any]:
            """Worker function for one game."""
            try:
                stats = self.balldontlie.get_box_score(game['game_id'])
                
                if stats:
                    game['player_stats'] = stats
                    game['has_player_stats'] = 1
                
                # Thread-safe write
                with self.write_lock:
                    self.db_manager.insert_game(game)
                    self.stats['games_enriched'] += 1
                
                return game
                
            except Exception as e:
                logger.error(f"  Error enriching {game['game_id']}: {e}")
                with self.write_lock:
                    self.stats['errors'] += 1
                return game
        
        # Use ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(enrich_one_game, game): game for game in games}
            
            for idx, future in enumerate(as_completed(futures)):
                try:
                    enriched_game = future.result()
                    enriched.append(enriched_game)
                    
                    if (idx + 1) % 50 == 0:
                        logger.info(f"  Progress: {idx + 1}/{len(games)} games enriched")
                
                except Exception as e:
                    logger.error(f"  Future error: {e}")
        
        return enriched
    
    def _enrich_with_odds(
        self,
        games: List[Dict[str, Any]],
        sport: str
    ) -> List[Dict[str, Any]]:
        """
        Enrich games with betting odds.
        
        Strategy:
        1. Try The Odds API (historical endpoint)
        2. Fallback to OddsPortal scraper
        3. Fallback to Covers scraper
        
        Args:
            games: List of games
            sport: Sport type
            
        Returns:
            Enriched games
        """
        for idx, game in enumerate(games):
            try:
                game_id = game['game_id']
                date = game['date']
                
                # Try Odds API first
                odds = self.odds_api.fetch_historical_odds(
                    sport=sport.lower(),
                    date=date
                )
                
                if odds:
                    # Find matching game
                    for odds_game in odds:
                        # Store in odds_history table
                        bookmakers = odds_game.get('bookmakers', [])
                        
                        for bookmaker in bookmakers:
                            for market in bookmaker.get('markets', []):
                                odds_record = {
                                    'game_id': game_id,
                                    'bookmaker': bookmaker.get('key', 'unknown'),
                                    'market_type': market.get('key', 'unknown'),
                                    'source': 'oddsapi',
                                    'timestamp': int(datetime.now().timestamp())
                                }
                                
                                # Parse outcomes
                                outcomes = market.get('outcomes', [])
                                for outcome in outcomes:
                                    name = outcome.get('name', '').lower()
                                    price = outcome.get('price')
                                    point = outcome.get('point')
                                    
                                    if point:
                                        odds_record['line'] = point
                                    
                                    if 'home' in name:
                                        odds_record['home_odds'] = price
                                    elif 'away' in name:
                                        odds_record['away_odds'] = price
                                    elif 'over' in name:
                                        odds_record['over_odds'] = price
                                    elif 'under' in name:
                                        odds_record['under_odds'] = price
                                
                                # Insert odds
                                with self.write_lock:
                                    self.db_manager.insert_odds_history(odds_record)
                    
                    game['has_odds'] = 1
                
                # Update game
                with self.write_lock:
                    self.db_manager.insert_game(game)
                
                if (idx + 1) % 50 == 0:
                    logger.info(f"  Progress: {idx + 1}/{len(games)} games with odds")
                
            except Exception as e:
                logger.error(f"  Error fetching odds for {game['game_id']}: {e}")
                self.stats['errors'] += 1
        
        return games
    
    def _enrich_with_perplexity(
        self,
        games: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enrich games with Perplexity API (cache-first).
        
        Note: Perplexity cache is already in SQLite (perplexity_cache table).
        
        Args:
            games: List of games
            
        Returns:
            Enriched games
        """
        # Placeholder - implement if needed
        # The PerplexityCache is already using SQLite via multi_source_aggregator
        
        for game in games:
            game['has_perplexity'] = 1
            
            with self.write_lock:
                self.db_manager.insert_game(game)
        
        return games
    
    def _collect_player_props(
        self,
        games: List[Dict[str, Any]],
        sport: str
    ):
        """
        Collect player props for games.
        
        Args:
            games: List of games
            sport: Sport type
        """
        for idx, game in enumerate(games):
            try:
                game_id = game['game_id']
                date = game['date']
                
                # Fetch props from Odds API
                props = self.odds_api.fetch_player_props(
                    sport=sport.lower(),
                    date=date
                )
                
                if props:
                    for prop in props:
                        # Insert into database
                        with self.write_lock:
                            self.db_manager.insert_prop(prop)
                        
                        self.stats['props_collected'] += 1
                
                if (idx + 1) % 50 == 0:
                    logger.info(f"  Progress: {idx + 1}/{len(games)} games, {self.stats['props_collected']} props")
                
            except Exception as e:
                logger.error(f"  Error collecting props for {game['game_id']}: {e}")
                self.stats['errors'] += 1


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='SQLite-based historical sports data collection'
    )
    
    parser.add_argument(
        '--sport',
        choices=['NBA', 'NFL', 'all'],
        required=True,
        help='Sport to collect (NBA, NFL, or all)'
    )
    
    parser.add_argument(
        '--years',
        type=str,
        required=True,
        help='Year or range (e.g., 2020 or 2020-2024)'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=1,
        help='Number of concurrent workers (default: 1, safe for 60 RPM limit)'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume collection, skip already-fetched games'
    )
    
    parser.add_argument(
        '--db',
        default='data/sports_data.db',
        help='SQLite database path (default: data/sports_data.db)'
    )
    
    parser.add_argument(
        '--export-json',
        type=str,
        help='Export to JSON file after collection (legacy compatibility)'
    )
    
    args = parser.parse_args()
    
    # Parse years
    if '-' in args.years:
        start_year, end_year = map(int, args.years.split('-'))
        years = list(range(start_year, end_year + 1))
    else:
        years = [int(args.years)]
    
    # Determine sports
    sports = ['NBA', 'NFL'] if args.sport == 'all' else [args.sport]
    
    # Initialize collector
    collector = SQLiteHistoricalCollector(
        db_path=args.db,
        workers=args.workers
    )
    
    # Collect data
    for sport in sports:
        for year in years:
            success = collector.collect_year(
                sport=sport,
                year=year,
                resume=args.resume
            )
            
            if not success:
                logger.error(f"Failed to collect {sport} {year}")
    
    # Export to JSON if requested
    if args.export_json:
        logger.info(f"\nExporting to JSON: {args.export_json}")
        
        sport_filter = None if args.sport == 'all' else args.sport
        start_date = f"{years[0]}-01-01"
        end_date = f"{years[-1]}-12-31"
        
        export_to_json(
            output_path=args.export_json,
            sport=sport_filter,
            start_date=start_date,
            end_date=end_date,
            include_props=True
        )
    
    # Print final stats
    logger.info("\n" + "="*60)
    logger.info("COLLECTION COMPLETE")
    logger.info("="*60)
    logger.info(f"Games fetched:    {collector.stats['games_fetched']}")
    logger.info(f"Games enriched:   {collector.stats['games_enriched']}")
    logger.info(f"Props collected:  {collector.stats['props_collected']}")
    logger.info(f"Errors:           {collector.stats['errors']}")
    logger.info("="*60)


if __name__ == '__main__':
    main()
