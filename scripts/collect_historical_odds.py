#!/usr/bin/env python3
"""
⚠️ DEPRECATED - DO NOT USE

This script is deprecated and will be removed in a future version.

Use instead:
    python scripts/collect_historical_sqlite.py --sports NBA NFL --start-year 2020 --end-year 2024

Reason for deprecation:
    - Odds collection is now integrated into collect_historical_sqlite.py
    - Better integration with the unified database
    - Improved error handling and caching
    - No need for separate odds collection step
    
See: START_HERE.md for current script recommendations

---

LEGACY: Historical Odds Data Collection Script

This script fetches and caches ALL historical betting odds for NBA/NFL games
from 2020-2024. Run this ONCE during your paid month to gather all data,
then you can use the cached data forever without needing the paid plan.

Usage:
    python scripts/collect_historical_odds.py --sport NBA --year 2024
    python scripts/collect_historical_odds.py --sport NFL --year 2020-2024
    python scripts/collect_historical_odds.py --all  # Fetch everything
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from omega.odds_api_client import TheOddsAPIClient
from omega.espn_historical_scraper import ESPNHistoricalScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HistoricalOddsCollector:
    """Collects and caches historical betting odds data."""
    
    def __init__(self, cache_dir: str = "data/odds_cache"):
        """
        Initialize collector.
        
        Args:
            cache_dir: Directory to store cached odds data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.odds_client = TheOddsAPIClient()
        self.espn_scraper = ESPNHistoricalScraper()
        
        self.stats = {
            "total_dates": 0,
            "successful_dates": 0,
            "failed_dates": 0,
            "total_games": 0,
            "api_requests": 0,
            "cached_hits": 0
        }
    
    def get_cache_path(self, sport: str, date: str) -> Path:
        """Get cache file path for a specific sport/date."""
        year = date[:4]
        return self.cache_dir / sport.lower() / year / f"{date}.json"
    
    def load_cached_odds(self, sport: str, date: str) -> List[Dict[str, Any]]:
        """Load odds from cache if available."""
        cache_file = self.get_cache_path(sport, date)
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    self.stats["cached_hits"] += 1
                    return data
            except Exception as e:
                logger.warning(f"Failed to load cache for {date}: {e}")
        
        return None
    
    def save_odds_to_cache(self, sport: str, date: str, odds: List[Dict[str, Any]]):
        """Save odds to cache."""
        cache_file = self.get_cache_path(sport, date)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(odds, f, indent=2)
            logger.debug(f"Cached {len(odds)} games for {date}")
        except Exception as e:
            logger.error(f"Failed to save cache for {date}: {e}")
    
    def get_game_dates(self, sport: str, start_year: int, end_year: int) -> List[str]:
        """
        Get all game dates for a sport and year range.
        Uses ESPN to find actual game dates (more efficient than checking every day).
        """
        logger.info(f"Finding {sport} game dates from {start_year} to {end_year}...")
        
        all_dates = set()
        
        for year in range(start_year, end_year + 1):
            # NBA season runs Oct-June, NFL runs Sep-Feb
            if sport == "NBA":
                start_date = f"{year-1}-10-01"
                end_date = f"{year}-06-30"
            elif sport == "NFL":
                start_date = f"{year}-09-01"
                end_date = f"{year+1}-02-15"
            else:
                # Generic: full calendar year
                start_date = f"{year}-01-01"
                end_date = f"{year}-12-31"
            
            logger.info(f"  Fetching {sport} games for {year} season ({start_date} to {end_date})...")
            
            try:
                if sport == "NBA":
                    games = self.espn_scraper.fetch_nba_games(start_date, end_date)
                elif sport == "NFL":
                    games = self.espn_scraper.fetch_nfl_games(start_date, end_date)
                else:
                    logger.warning(f"Sport {sport} not supported for date detection")
                    continue
                
                # Extract unique dates
                dates = set(game.get("date") for game in games if game.get("date"))
                all_dates.update(dates)
                
                logger.info(f"  Found {len(dates)} game dates for {year} season")
                
            except Exception as e:
                logger.error(f"Failed to fetch game dates for {year}: {e}")
        
        sorted_dates = sorted(all_dates)
        logger.info(f"✓ Total unique game dates found: {len(sorted_dates)}")
        
        return sorted_dates
    
    def collect_odds_for_date(
        self, 
        sport: str, 
        date: str, 
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Collect odds for a specific date.
        
        Args:
            sport: Sport name (NBA, NFL, etc.)
            date: Date in YYYY-MM-DD format
            force_refresh: Force API call even if cached
        
        Returns:
            List of games with odds
        """
        # Check cache first
        if not force_refresh:
            cached = self.load_cached_odds(sport, date)
            if cached is not None:
                logger.debug(f"Using cached odds for {date} ({len(cached)} games)")
                self.stats["total_games"] += len(cached)
                return cached
        
        # Fetch from API
        try:
            odds = self.odds_client.get_historical_odds(
                sport=sport,
                date=date,
                markets=["h2h", "spreads", "totals"],
                regions="us"
            )
            
            self.stats["api_requests"] += 1
            self.stats["total_games"] += len(odds)
            
            if odds:
                # Save to cache
                self.save_odds_to_cache(sport, date, odds)
                logger.info(f"✓ {date}: Fetched {len(odds)} games")
                self.stats["successful_dates"] += 1
            else:
                logger.warning(f"✗ {date}: No odds returned")
                self.stats["failed_dates"] += 1
            
            return odds
            
        except Exception as e:
            logger.error(f"✗ {date}: Error fetching odds - {e}")
            self.stats["failed_dates"] += 1
            return []
    
    def collect_season(
        self,
        sport: str,
        start_year: int,
        end_year: int,
        force_refresh: bool = False,
        check_usage_interval: int = 50
    ):
        """
        Collect odds for entire season(s).
        
        Args:
            sport: Sport name (NBA, NFL)
            start_year: Starting year
            end_year: Ending year (inclusive)
            force_refresh: Force API calls even if cached
            check_usage_interval: Check API usage every N requests
        """
        logger.info("="*80)
        logger.info(f"Historical Odds Collection: {sport} {start_year}-{end_year}")
        logger.info("="*80)
        
        # Get all game dates
        game_dates = self.get_game_dates(sport, start_year, end_year)
        self.stats["total_dates"] = len(game_dates)
        
        if not game_dates:
            logger.error("No game dates found!")
            return
        
        logger.info(f"\nStarting odds collection for {len(game_dates)} dates...")
        logger.info(f"Cache directory: {self.cache_dir}")
        
        # Check initial API usage
        usage = self.odds_client.check_usage()
        initial_remaining = int(usage.get("requests_remaining", 0))
        logger.info(f"API requests remaining: {initial_remaining}")
        
        if initial_remaining < len(game_dates):
            logger.warning(f"⚠️  May not have enough API requests! Need ~{len(game_dates)}, have {initial_remaining}")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return
        
        # Collect odds for each date
        for i, date in enumerate(game_dates, 1):
            logger.info(f"\n[{i}/{len(game_dates)}] Processing {date}...")
            
            odds = self.collect_odds_for_date(sport, date, force_refresh)
            
            # Check usage periodically
            if i % check_usage_interval == 0:
                usage = self.odds_client.check_usage()
                remaining = usage.get("requests_remaining", "unknown")
                logger.info(f"📊 Progress: {i}/{len(game_dates)} dates | API requests remaining: {remaining}")
        
        # Final statistics
        self.print_summary()
    
    def print_summary(self):
        """Print collection statistics."""
        logger.info("\n" + "="*80)
        logger.info("COLLECTION SUMMARY")
        logger.info("="*80)
        logger.info(f"Total dates processed:    {self.stats['total_dates']}")
        logger.info(f"  Successful:             {self.stats['successful_dates']}")
        logger.info(f"  Failed:                 {self.stats['failed_dates']}")
        logger.info(f"  Cached hits:            {self.stats['cached_hits']}")
        logger.info(f"Total games collected:    {self.stats['total_games']}")
        logger.info(f"API requests made:        {self.stats['api_requests']}")
        
        # Check final usage
        usage = self.odds_client.check_usage()
        if usage:
            logger.info(f"\nFinal API usage:")
            logger.info(f"  Requests remaining:     {usage.get('requests_remaining', 'N/A')}")
            logger.info(f"  Requests used:          {usage.get('requests_used', 'N/A')}")
        
        logger.info(f"\nCache location: {self.cache_dir.absolute()}")
        logger.info("="*80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Collect historical betting odds data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Collect NBA 2024 season
  python scripts/collect_historical_odds.py --sport NBA --year 2024
  
  # Collect NFL 2020-2024
  python scripts/collect_historical_odds.py --sport NFL --start-year 2020 --end-year 2024
  
  # Collect everything
  python scripts/collect_historical_odds.py --all
  
  # Force refresh (ignore cache)
  python scripts/collect_historical_odds.py --sport NBA --year 2024 --force-refresh
        """
    )
    
    parser.add_argument("--sport", choices=["NBA", "NFL"], help="Sport to collect")
    parser.add_argument("--year", type=int, help="Single year to collect")
    parser.add_argument("--start-year", type=int, help="Start year (inclusive)")
    parser.add_argument("--end-year", type=int, help="End year (inclusive)")
    parser.add_argument("--all", action="store_true", help="Collect all sports/years (2020-2024)")
    parser.add_argument("--force-refresh", action="store_true", help="Force API calls, ignore cache")
    parser.add_argument("--cache-dir", default="data/odds_cache", help="Cache directory")
    parser.add_argument("--check-usage", action="store_true", help="Just check API usage and exit")
    
    args = parser.parse_args()
    
    # Just check usage
    if args.check_usage:
        client = TheOddsAPIClient()
        usage = client.check_usage()
        print(f"\nThe Odds API Usage:")
        print(f"  Requests remaining: {usage.get('requests_remaining', 'N/A')}")
        print(f"  Requests used: {usage.get('requests_used', 'N/A')}")
        return
    
    # Initialize collector
    collector = HistoricalOddsCollector(cache_dir=args.cache_dir)
    
    # Determine what to collect
    if args.all:
        # Collect everything: NBA and NFL 2020-2024
        for sport in ["NBA", "NFL"]:
            collector.collect_season(
                sport=sport,
                start_year=2020,
                end_year=2024,
                force_refresh=args.force_refresh
            )
    elif args.sport and (args.year or (args.start_year and args.end_year)):
        # Collect specific sport/years
        if args.year:
            start_year = end_year = args.year
        else:
            start_year = args.start_year
            end_year = args.end_year
        
        collector.collect_season(
            sport=args.sport,
            start_year=start_year,
            end_year=end_year,
            force_refresh=args.force_refresh
        )
    else:
        parser.print_help()
        print("\n❌ Error: Must specify --all OR --sport with --year/--start-year/--end-year")
        sys.exit(1)


if __name__ == "__main__":
    main()
