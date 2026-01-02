#!/usr/bin/env python3
"""
⚠️ DEPRECATED - DO NOT USE

This script is deprecated and will be removed in a future version.

Use instead:
    python scripts/collect_historical_sqlite.py --sports NBA NFL --start-year 2020 --end-year 2024

Reason for deprecation:
    - Superseded by collect_historical_sqlite.py which provides:
      * Unified SQLite storage instead of fragmented JSON files
      * Better multi-threading implementation
      * Improved error handling and resume capability
      * Cleaner code organization
      * Better progress tracking
    
See: START_HERE.md for current script recommendations

---

LEGACY: 5-Year Historical Sports Data Collection Script

Comprehensive data collection orchestrator for NBA and NFL (2020-2024).
Integrates all enhanced components:
- BallDontLie API for games and player stats (/v1/games, /v1/stats)
- The Odds API for primary betting lines and player props
- OddsPortal/Covers scrapers for historical odds gaps
- Perplexity API for missing/ambiguous data enrichment
- SQLite cache for fast lookups during backtesting

Usage:
    # Manual execution only - DO NOT auto-run
    python scripts/collect_historical_5years.py --sport NBA --years 2020-2024
    python scripts/collect_historical_5years.py --sport NFL --years 2020-2024
    python scripts/collect_historical_5years.py --all  # Both sports, all years
    
Data Storage:
    - data/historical/{sport}_{year}_games.json    # Game results + odds
    - data/historical/{sport}_{year}_props.json    # Player props
    - data/cache/perplexity.db                     # Perplexity cache (SQLite)
    
Validation:
    - ~1,230 games per NBA season
    - ~285 games per NFL season
    - >80% prop coverage required
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from omega.balldontlie_client import BallDontLieAPIClient
from omega.odds_api_client import TheOddsAPIClient
from omega.historical_scrapers import OddsPortalScraper, CoversOddsHistoryScraper
from core.multi_source_aggregator import MultiSourceAggregator, PerplexityCache
from core.data_pipeline import DataValidator, HistoricalDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Historical5YearCollector:
    """
    Orchestrates 5-year historical data collection with multi-source integration.
    
    Architecture:
    1. BallDontLie: Primary source for games and player statistics
    2. The Odds API: Primary source for betting lines and player props
    3. Scrapers: Fallback for historical odds gaps (OddsPortal, Covers)
    4. Perplexity: Enrichment for missing/ambiguous data
    5. SQLite: Fast cached lookups for backtesting
    """
    
    EXPECTED_GAMES = {
        "NBA": 1230,  # ~1,230 games per season (82 games × 30 teams / 2)
        "NFL": 285    # ~285 games per season (17 games × 32 teams / 2 + playoffs)
    }
    
    def __init__(self, data_dir: str = "data/historical"):
        """
        Initialize the 5-year collector.
        
        Args:
            data_dir: Directory to store historical data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize clients
        self.balldontlie = BallDontLieAPIClient()
        self.odds_api = TheOddsAPIClient()
        self.aggregator = MultiSourceAggregator()
        self.validator = DataValidator()
        self.database = HistoricalDatabase(data_dir=self.data_dir)
        
        # Initialize scrapers (fallback only)
        self.oddsportal = OddsPortalScraper()
        self.covers = CoversOddsHistoryScraper()
        
        # Statistics tracking
        self.stats = {
            "years_completed": 0,
            "total_games": 0,
            "total_props": 0,
            "validation_errors": 0,
            "api_requests": 0,
            "scraper_fallbacks": 0,
            "perplexity_enrichments": 0
        }
        
        logger.info("Historical5YearCollector initialized")
    
    def collect_year(
        self,
        sport: str,
        year: int,
        include_props: bool = True
    ) -> Dict[str, Any]:
        """
        Collect all data for a single season year with incremental saves.
        
        Args:
            sport: Sport name (NBA or NFL)
            year: Season year (e.g., 2024)
            include_props: Whether to collect player props
        
        Returns:
            Collection statistics
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"COLLECTING {sport} {year} SEASON")
        logger.info(f"{'='*60}\n")
        
        year_stats = {
            "year": year,
            "sport": sport,
            "games_collected": 0,
            "props_collected": 0,
            "validation_passed": False
        }
        
        try:
            # Step 1: Fetch games from BallDontLie
            logger.info("Step 1/4: Fetching games from BallDontLie...")
            games = self._fetch_games_balldontlie(sport, year)
            logger.info(f"✓ Fetched {len(games)} games")
            
            # Save after step 1 (incremental)
            self._save_games(games, sport, year)
            logger.info("✓ Incremental save: games fetched")
            
            # Step 2: Fetch player stats (box scores)
            logger.info("Step 2/4: Fetching player statistics...")
            games = self._enrich_with_player_stats(games)
            logger.info(f"✓ Enriched {len(games)} games with player stats")
            
            # Save after step 2 (incremental)
            self._save_games(games, sport, year)
            logger.info("✓ Incremental save: player stats added")
            
            # Step 3: Fetch odds (primary: Odds API, fallback: scrapers)
            logger.info("Step 3/4: Fetching betting odds...")
            games = self._enrich_with_odds(games, sport)
            logger.info(f"✓ Enriched {len(games)} games with odds")
            
            # Save after step 3 (incremental)
            self._save_games(games, sport, year)
            logger.info("✓ Incremental save: odds added")
            
            # Step 4: Enrich with Perplexity (only missing data)
            logger.info("Step 4/4: Enriching missing data with Perplexity...")
            games = self._enrich_with_perplexity(games)
            logger.info(f"✓ Enriched games with Perplexity data")
            
            # Final save
            self._save_games(games, sport, year)
            year_stats["games_collected"] = len(games)
            logger.info("✓ Final save: all game data complete")
            
            # Collect player props if requested
            if include_props:
                logger.info("Collecting player props...")
                props = self._fetch_player_props(games, sport)
                self._save_props(props, sport, year)
                year_stats["props_collected"] = len(props)
                logger.info("✓ Player props saved")
            
            # Validate collection
            validation_result = self._validate_year(sport, year)
            year_stats["validation_passed"] = validation_result["passed"]
            year_stats["validation_details"] = validation_result
            
        except Exception as e:
            logger.error(f"Error collecting {sport} {year}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            year_stats["error"] = str(e)
        
        return year_stats
    
    def _fetch_games_balldontlie(
        self,
        sport: str,
        year: int
    ) -> List[Dict[str, Any]]:
        """Fetch games from BallDontLie for entire season."""
        # Determine season date range
        if sport == "NBA":
            start_date = f"{year}-10-01"
            end_date = f"{year+1}-06-30"
        elif sport == "NFL":
            start_date = f"{year}-09-01"
            end_date = f"{year+1}-02-28"
        else:
            logger.error(f"Sport {sport} not supported")
            return []
        
        games = []
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Fetch in weekly chunks to respect rate limits
        while current_date <= end_dt:
            chunk_end = min(current_date + timedelta(days=7), end_dt)
            
            chunk_games = self.balldontlie.get_games(
                start_date=current_date.strftime("%Y-%m-%d"),
                end_date=chunk_end.strftime("%Y-%m-%d")
            )
            
            if chunk_games:
                games.extend(chunk_games)
                self.stats["api_requests"] += 1
            
            current_date = chunk_end + timedelta(days=1)
        
        return games
    
    def _enrich_with_player_stats(
        self,
        games: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enrich games with player statistics from BallDontLie /v1/stats."""
        enriched_games = []
        
        for idx, game in enumerate(games):
            try:
                game_id = game.get("id")
                
                if game_id:
                    box_score = self.balldontlie.get_box_score(game_id)
                    
                    if box_score:
                        game["player_stats"] = box_score.get("player_stats", [])
                        self.stats["api_requests"] += 1
                
                enriched_games.append(game)
                
                # Log progress every 50 games
                if (idx + 1) % 50 == 0:
                    logger.info(f"Player stats progress: {idx + 1}/{len(games)} games")
                    
            except Exception as e:
                logger.error(f"Error enriching game {game.get('id')}: {e}")
                enriched_games.append(game)  # Add without stats
        
        return enriched_games
    
    def _enrich_with_odds(
        self,
        games: List[Dict[str, Any]],
        sport: str
    ) -> List[Dict[str, Any]]:
        """Enrich with odds: Odds API (primary) -> scrapers (fallback)."""
        enriched_games = []
        
        for game in games:
            game_date = game.get("date", "")[:10]  # YYYY-MM-DD
            
            if not game_date:
                enriched_games.append(game)
                continue
            
            # Try Odds API first
            odds_data = None
            try:
                odds_games = self.odds_api.get_historical_odds(sport, game_date)
                
                if odds_games:
                    # Match by team names
                    home_team = game.get("home_team", {}).get("full_name", "").lower()
                    away_team = game.get("visitor_team", {}).get("full_name", "").lower()
                    
                    for odds_game in odds_games:
                        odds_home = odds_game.get("home_team", "").lower()
                        odds_away = odds_game.get("away_team", "").lower()
                        
                        if (home_team in odds_home or odds_home in home_team) and \
                           (away_team in odds_away or odds_away in away_team):
                            odds_data = odds_game
                            break
                
                self.stats["api_requests"] += 1
            except Exception as e:
                logger.debug(f"Odds API failed for {game_date}: {e}")
            
            # Fallback to scrapers if Odds API had no data
            if not odds_data:
                odds_data = self._fetch_odds_fallback(sport, game_date, game)
            
            if odds_data:
                game["odds"] = odds_data
            
            enriched_games.append(game)
        
        return enriched_games
    
    def _fetch_odds_fallback(
        self,
        sport: str,
        date: str,
        game: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Fallback to scrapers for odds."""
        home_team = game.get("home_team", {}).get("full_name", "").lower()
        away_team = game.get("visitor_team", {}).get("full_name", "").lower()
        
        # Try OddsPortal
        try:
            scraped_games = self.oddsportal.scrape_game_odds(sport, date)
            
            for scraped in scraped_games:
                scraped_home = scraped.get("home_team", "").lower()
                scraped_away = scraped.get("away_team", "").lower()
                
                if (home_team in scraped_home or scraped_home in home_team) and \
                   (away_team in scraped_away or scraped_away in away_team):
                    self.stats["scraper_fallbacks"] += 1
                    return scraped
        except Exception as e:
            logger.debug(f"OddsPortal failed: {e}")
        
        # Try Covers
        try:
            scraped_games = self.covers.scrape_game_odds(sport, date)
            
            for scraped in scraped_games:
                scraped_home = scraped.get("home_team", "").lower()
                scraped_away = scraped.get("away_team", "").lower()
                
                if (home_team in scraped_home or scraped_home in home_team) and \
                   (away_team in scraped_away or scraped_away in away_team):
                    self.stats["scraper_fallbacks"] += 1
                    return scraped
        except Exception as e:
            logger.debug(f"Covers failed: {e}")
        
        return None
    
    def _enrich_with_perplexity(
        self,
        games: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enrich with Perplexity only for missing/ambiguous data."""
        enriched_games = []
        
        for game in games:
            missing_fields = []
            
            # Check for missing critical data
            if not game.get("odds"):
                missing_fields.append("odds")
            if not game.get("player_stats"):
                missing_fields.append("player_stats")
            
            # Use Perplexity only if we have missing data
            if missing_fields:
                enriched = self.aggregator._integrate_perplexity(game, missing_fields)
                self.stats["perplexity_enrichments"] += 1
                enriched_games.append(enriched)
            else:
                enriched_games.append(game)
        
        return enriched_games
    
    def _fetch_player_props(
        self,
        games: List[Dict[str, Any]],
        sport: str
    ) -> List[Dict[str, Any]]:
        """Fetch player props from Odds API."""
        all_props = []
        
        # Get unique dates from games
        dates = set()
        for game in games:
            game_date = game.get("date", "")[:10]
            if game_date:
                dates.add(game_date)
        
        # Fetch props for each date
        for date in sorted(dates):
            try:
                props = self.odds_api.fetch_player_props(sport, date)
                
                if props:
                    all_props.extend(props)
                    self.stats["api_requests"] += 1
                
            except Exception as e:
                logger.debug(f"Props fetch failed for {date}: {e}")
        
        return all_props
    
    def _save_games(
        self,
        games: List[Dict[str, Any]],
        sport: str,
        year: int
    ):
        """Save games to JSON database with backup."""
        output_file = self.data_dir / f"{sport.lower()}_{year}_games.json"
        backup_file = self.data_dir / f"{sport.lower()}_{year}_games.backup.json"
        
        try:
            # Create backup if file exists
            if output_file.exists():
                import shutil
                shutil.copy2(output_file, backup_file)
            
            # Save new data
            with open(output_file, 'w') as f:
                json.dump(games, f, indent=2)
            
            logger.info(f"✓ Saved {len(games)} games to {output_file}")
            self.stats["total_games"] += len(games)
            
            # Remove backup after successful save
            if backup_file.exists():
                backup_file.unlink()
        
        except Exception as e:
            logger.error(f"Failed to save games: {e}")
            # Restore from backup if save failed
            if backup_file.exists():
                import shutil
                shutil.copy2(backup_file, output_file)
                logger.info("Restored from backup")
    
    def _save_props(
        self,
        props: List[Dict[str, Any]],
        sport: str,
        year: int
    ):
        """Save player props to JSON database."""
        output_file = self.data_dir / f"{sport.lower()}_{year}_props.json"
        
        try:
            with open(output_file, 'w') as f:
                json.dump(props, f, indent=2)
            
            logger.info(f"✓ Saved {len(props)} props to {output_file}")
            self.stats["total_props"] += len(props)
        
        except Exception as e:
            logger.error(f"Failed to save props: {e}")
    
    def _validate_year(
        self,
        sport: str,
        year: int
    ) -> Dict[str, Any]:
        """Validate collected data for a season year."""
        games_file = self.data_dir / f"{sport.lower()}_{year}_games.json"
        props_file = self.data_dir / f"{sport.lower()}_{year}_props.json"
        
        validation = {
            "passed": False,
            "games_count": 0,
            "props_count": 0,
            "expected_games": self.EXPECTED_GAMES.get(sport, 0),
            "prop_coverage": 0.0,
            "issues": []
        }
        
        # Validate games
        if games_file.exists():
            with open(games_file, 'r') as f:
                games = json.load(f)
                validation["games_count"] = len(games)
        else:
            validation["issues"].append("Games file not found")
            return validation
        
        # Check game count
        expected = validation["expected_games"]
        actual = validation["games_count"]
        
        if actual < expected * 0.9:  # Allow 10% variance
            validation["issues"].append(
                f"Game count low: {actual} < {expected * 0.9:.0f}"
            )
        
        # Validate props
        if props_file.exists():
            with open(props_file, 'r') as f:
                props = json.load(f)
                validation["props_count"] = len(props)
        
        # Calculate prop coverage
        if validation["games_count"] > 0:
            validation["prop_coverage"] = (
                validation["props_count"] / (validation["games_count"] * 10)
            ) * 100
            
            if validation["prop_coverage"] < 80:
                validation["issues"].append(
                    f"Prop coverage low: {validation['prop_coverage']:.1f}% < 80%"
                )
        
        # Overall pass/fail
        validation["passed"] = len(validation["issues"]) == 0
        
        return validation
    
    def collect_all_years(
        self,
        sport: str,
        start_year: int,
        end_year: int
    ) -> Dict[str, Any]:
        """
        Collect data for multiple years sequentially.
        
        Args:
            sport: Sport name (NBA or NFL)
            start_year: Starting year
            end_year: Ending year (inclusive)
        
        Returns:
            Overall collection statistics
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"COLLECTING {sport} SEASONS {start_year}-{end_year}")
        logger.info(f"{'='*60}\n")
        
        all_year_stats = []
        
        for year in range(start_year, end_year + 1):
            try:
                year_stats = self.collect_year(sport, year)
                all_year_stats.append(year_stats)
                
                # Checkpoint after each year
                logger.info(f"\n--- Year {year} Checkpoint ---")
                logger.info(f"Games: {year_stats['games_collected']}")
                logger.info(f"Props: {year_stats['props_collected']}")
                logger.info(f"Validation: {'PASSED' if year_stats['validation_passed'] else 'FAILED'}")
                
                if not year_stats["validation_passed"]:
                    logger.warning(f"Validation issues: {year_stats['validation_details']['issues']}")
                
                self.stats["years_completed"] += 1
                
            except Exception as e:
                logger.error(f"Error collecting {sport} {year}: {e}")
                import traceback
                logger.debug(traceback.format_exc())
        
        return {
            "sport": sport,
            "years": all_year_stats,
            "overall_stats": self.stats
        }
    
    def generate_report(self) -> str:
        """Generate collection report."""
        report = f"""
{'='*60}
5-YEAR DATA COLLECTION REPORT
{'='*60}

Overall Statistics:
- Years Completed: {self.stats['years_completed']}
- Total Games: {self.stats['total_games']}
- Total Props: {self.stats['total_props']}
- API Requests: {self.stats['api_requests']}
- Scraper Fallbacks: {self.stats['scraper_fallbacks']}
- Perplexity Enrichments: {self.stats['perplexity_enrichments']}
- Validation Errors: {self.stats['validation_errors']}

Data Location:
- Games: data/historical/{{sport}}_{{year}}_games.json
- Props: data/historical/{{sport}}_{{year}}_props.json
- Perplexity Cache: data/cache/perplexity.db

Next Steps:
1. Review validation results for any issues
2. Run backtesting experiments with collected data
3. Monitor Perplexity cache hit rate for performance

{'='*60}
"""
        return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Collect 5 years of historical sports data"
    )
    parser.add_argument(
        "--sport",
        choices=["NBA", "NFL", "all"],
        default="all",
        help="Sport to collect (default: all)"
    )
    parser.add_argument(
        "--years",
        default="2020-2024",
        help="Year range (default: 2020-2024)"
    )
    parser.add_argument(
        "--no-props",
        action="store_true",
        help="Skip player props collection"
    )
    
    args = parser.parse_args()
    
    # Parse year range
    if "-" in args.years:
        start_year, end_year = map(int, args.years.split("-"))
    else:
        start_year = end_year = int(args.years)
    
    # Initialize collector
    collector = Historical5YearCollector()
    
    # Collect data
    if args.sport == "all":
        # NBA first, then NFL
        logger.info("Collecting both NBA and NFL...")
        nba_results = collector.collect_all_years("NBA", start_year, end_year)
        nfl_results = collector.collect_all_years("NFL", start_year, end_year)
    else:
        results = collector.collect_all_years(args.sport, start_year, end_year)
    
    # Generate report
    report = collector.generate_report()
    print(report)
    
    # Save report
    report_file = Path("data") / "collection_report.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    logger.info(f"Report saved to {report_file}")


if __name__ == "__main__":
    main()
