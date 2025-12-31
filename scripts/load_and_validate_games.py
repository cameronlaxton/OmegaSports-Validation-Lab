#!/usr/bin/env python
"""
Load and validate historical games for multiple sports.

Fetches games from OmegaSports scraper, caches them, validates them,
and ensures minimum counts per sport.
"""

import argparse
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ensure data directories exist first
Path('data/logs').mkdir(parents=True, exist_ok=True)
Path('data/cache').mkdir(parents=True, exist_ok=True)
Path('data/experiments').mkdir(parents=True, exist_ok=True)
Path('data/historical').mkdir(parents=True, exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/load_games.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from core.data_pipeline import DataPipeline
from omega.scraper_engine import ScraperEngine


def fetch_games_for_year(
    scraper: ScraperEngine,
    pipeline: DataPipeline,
    sport: str,
    year: int,
    max_retries: int = 3
) -> List[Dict[str, Any]]:
    """
    Fetch games for a specific sport and year with retry logic.
    
    Args:
        scraper: ScraperEngine instance
        pipeline: DataPipeline instance
        sport: Sport code
        year: Year to fetch
        max_retries: Maximum number of retry attempts
        
    Returns:
        List of game dictionaries
    """
    cache_key = f"omega_games_{sport}_{year}"
    
    # Check cache first
    cached = pipeline.get_cached_data(cache_key)
    if cached:
        logger.info(f"Using cached data for {sport} {year} ({len(cached)} games)")
        return cached
    
    # Fetch from scraper with retry logic
    all_games = []
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching {sport} {year} (attempt {attempt + 1}/{max_retries})...")
            
            # Fetch games for the year (we'll need to fetch by date ranges)
            # For now, fetch upcoming games and filter by year
            # Note: The scraper fetches upcoming games, so for historical data
            # we'll need to use a different approach or the scraper needs historical support
            
            # Since the scraper currently only fetches upcoming games,
            # we'll simulate by fetching what's available and saving it
            # In production, you'd want to use a historical data source
            
            # For this script, we'll fetch available games and save them
            games = scraper.fetch_games(sport, start_date=start_date, limit=1000)
            
            if games:
                # Filter games by year
                year_games = []
                for game in games:
                    game_date = game.get('date', '')
                    if game_date and game_date.startswith(str(year)):
                        year_games.append(game)
                
                all_games.extend(year_games)
                logger.info(f"Fetched {len(year_games)} games for {sport} {year}")
                
                # Cache the results
                pipeline.cache_data(cache_key, year_games)
                
                # Save to database
                if year_games:
                    saved = pipeline.save_games(year_games, sport, year)
                    logger.info(f"Saved {saved} games to database for {sport} {year}")
                
                return year_games
            else:
                logger.warning(f"No games returned for {sport} {year}")
                
        except Exception as e:
            wait_time = (2 ** attempt) * 1  # Exponential backoff
            logger.warning(f"Error fetching {sport} {year} (attempt {attempt + 1}): {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to fetch {sport} {year} after {max_retries} attempts")
                raise
    
    return all_games


def fetch_and_cache_games(
    pipeline: DataPipeline,
    scraper: ScraperEngine,
    sport: str,
    start_year: int,
    end_year: int
) -> List[Dict[str, Any]]:
    """
    Fetch and cache games for a sport across multiple years.
    
    Args:
        pipeline: DataPipeline instance
        scraper: ScraperEngine instance
        sport: Sport code
        start_year: Start year (inclusive)
        end_year: End year (inclusive)
        
    Returns:
        List of all game dictionaries
    """
    all_games = []
    
    for year in range(start_year, end_year + 1):
        try:
            games = fetch_games_for_year(scraper, pipeline, sport, year)
            all_games.extend(games)
        except Exception as e:
            logger.error(f"Failed to fetch {sport} {year}: {e}")
            continue
    
    return all_games


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Load and validate historical games for multiple sports'
    )
    parser.add_argument(
        '--start-year',
        type=int,
        default=2020,
        help='Start year (inclusive)'
    )
    parser.add_argument(
        '--end-year',
        type=int,
        default=2024,
        help='End year (inclusive)'
    )
    parser.add_argument(
        '--sports',
        nargs='+',
        default=['NBA', 'NFL', 'NCAAB', 'NCAAF'],
        help='List of sports to process'
    )
    parser.add_argument(
        '--min-count',
        type=int,
        default=1000,
        help='Minimum number of games required per sport'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("Loading and Validating Historical Games")
    print("="*80)
    print(f"Start Year: {args.start_year}")
    print(f"End Year: {args.end_year}")
    print(f"Sports: {', '.join(args.sports)}")
    print(f"Minimum Count: {args.min_count}")
    print("="*80 + "\n")
    
    # Initialize components
    try:
        pipeline = DataPipeline()
        scraper = ScraperEngine()
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        sys.exit(1)
    
    # Process each sport
    results = {}
    failed_sports = []
    
    for sport in args.sports:
        print(f"\nProcessing {sport}...")
        start_time = time.time()
        
        try:
            # Fetch and cache games
            games = fetch_and_cache_games(
                pipeline, scraper, sport, args.start_year, args.end_year
            )
            
            # Get count from database
            count = pipeline.get_game_count(sport, args.start_year, args.end_year)
            
            elapsed = time.time() - start_time
            results[sport] = count
            
            print(f"{sport}: {count} games loaded (took {elapsed:.2f}s)")
            
            # Validate minimum count
            if count < args.min_count:
                error_msg = f"{sport} has insufficient data: {count} < {args.min_count}"
                print(f"✗ {error_msg}")
                failed_sports.append((sport, count, args.min_count))
                logger.error(error_msg)
            else:
                print(f"✓ {sport} meets minimum requirement ({count} >= {args.min_count})")
                
        except Exception as e:
            error_msg = f"Failed to process {sport}: {e}"
            print(f"✗ {error_msg}")
            logger.error(error_msg, exc_info=True)
            failed_sports.append((sport, 0, args.min_count))
    
    # Summary
    print("\n" + "="*80)
    print("Summary")
    print("="*80)
    
    for sport, count in results.items():
        status = "✓" if count >= args.min_count else "✗"
        print(f"{status} {sport}: {count} games")
    
    if failed_sports:
        print("\n✗ Some sports failed minimum count requirement:")
        for sport, count, min_count in failed_sports:
            print(f"  - {sport}: {count} games (required: {min_count})")
        print("\nSuggested actions:")
        print("  1. Check scraper logs for API errors")
        print("  2. Verify OMEGA_ENGINE_PATH is set correctly")
        print("  3. Try increasing fetch limits or date ranges")
        print("  4. Check if historical data source is available")
        sys.exit(1)
    else:
        print("\n✓ All sports ready for Module 1")
    
    # Print paths
    print("\n" + "="*80)
    print("Data Paths")
    print("="*80)
    print(f"Cache: {Path('data/cache').absolute()}")
    print(f"Historical: {Path('data/historical').absolute()}")
    print(f"Experiments: {Path('data/experiments').absolute()}")
    print(f"Logs: {Path('data/logs').absolute()}")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()

