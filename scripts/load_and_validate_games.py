#!/usr/bin/env python3
"""
Load and validate historical games for OmegaSports Validation Lab.

This script loads historical game data (2020-2024) for all supported sports,
validates data quality, and saves to the historical database.

Features:
- Fetches comprehensive game data with statistics (not just schedules)
- Supports multiple sports: NBA, NFL, NCAAB, NCAAF
- Includes retry logic for failed requests
- Validates data quality and completeness
- Caches results for efficiency
- Generates detailed reports

Usage:
    python scripts/load_and_validate_games.py --start-year 2020 --end-year 2024 --sports NBA NFL --min-count 1000
"""

import argparse
import logging
import sys
from pathlib import Path
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data_pipeline import DataPipeline
from core.historical_data_scraper import HistoricalDataScraper


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path('data/logs/load_games.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Load and validate historical sports betting games'
    )
    parser.add_argument(
        '--start-year',
        type=int,
        default=2020,
        help='Start year for historical data (default: 2020)'
    )
    parser.add_argument(
        '--end-year',
        type=int,
        default=2024,
        help='End year for historical data (default: 2024)'
    )
    parser.add_argument(
        '--sports',
        nargs='+',
        default=['NBA', 'NFL', 'NCAAB', 'NCAAF'],
        choices=['NBA', 'NFL', 'NCAAB', 'NCAAF'],
        help='Sports to load (default: all)'
    )
    parser.add_argument(
        '--min-count',
        type=int,
        default=1000,
        help='Minimum number of games required per sport (default: 1000)'
    )
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum number of retry attempts per request (default: 3)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--enable-multi-source',
        action='store_true',
        help='Enable multi-source data aggregation for enhanced statistics (requires additional API keys)'
    )
    return parser.parse_args()


def print_banner(text: str, char: str = '='):
    """Print a formatted banner."""
    width = 80
    print()
    print(char * width)
    print(text.center(width))
    print(char * width)
    print()


def print_section(text: str):
    """Print a section header."""
    print(f"\n{text}")
    print("-" * len(text))


def load_sport_data(
    sport: str,
    start_year: int,
    end_year: int,
    scraper: HistoricalDataScraper,
    pipeline: DataPipeline,
    max_retries: int = 3
) -> int:
    """
    Load historical game data for a specific sport.
    
    Args:
        sport: Sport name (NBA, NFL, NCAAB, NCAAF)
        start_year: Start year
        end_year: End year
        scraper: Historical data scraper instance
        pipeline: Data pipeline instance
        max_retries: Maximum retry attempts
        
    Returns:
        Number of games loaded
    """
    logger.info(f"Loading {sport} games from {start_year} to {end_year}")
    start_time = time.time()
    
    try:
        # Fetch historical games with comprehensive statistics
        games = scraper.fetch_historical_games(
            sport=sport,
            start_year=start_year,
            end_year=end_year,
            max_retries=max_retries
        )
        
        # Save games by year
        total_saved = 0
        for year in range(start_year, end_year + 1):
            # Filter games by year using proper date parsing
            year_games = []
            for g in games:
                try:
                    game_year = datetime.fromisoformat(g['date']).year
                    if game_year == year:
                        year_games.append(g)
                except (ValueError, KeyError):
                    logger.warning(f"Invalid date format in game: {g.get('game_id', 'unknown')}")
                    continue
            
            if year_games:
                saved = pipeline.save_games(year_games, sport, year)
                total_saved += saved
                logger.info(f"  Saved {saved} games for {sport} {year}")
        
        elapsed = time.time() - start_time
        logger.info(f"{sport}: {total_saved} games loaded (took {elapsed:.2f}s)")
        
        return total_saved
        
    except Exception as e:
        logger.error(f"Error loading {sport} data: {e}", exc_info=True)
        return 0


def main():
    """Main execution function."""
    args = parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Print startup banner
    print_banner("Loading and Validating Historical Games")
    
    print(f"Start Year: {args.start_year}")
    print(f"End Year: {args.end_year}")
    print(f"Sports: {', '.join(args.sports)}")
    print(f"Minimum Count: {args.min_count}")
    print(f"Multi-Source Enabled: {args.enable_multi_source}")
    print()
    
    # Initialize components
    print("Initializing components...")
    pipeline = DataPipeline(
        cache_dir=Path("data/cache"),
        data_dir=Path("data/historical")
    )
    scraper = HistoricalDataScraper(
        cache_dir=Path("data/cache"),
        enable_multi_source=args.enable_multi_source
    )
    print("✓ Components initialized")
    if args.enable_multi_source:
        print("  ℹ Multi-source data aggregation enabled (enhanced statistics)")
    else:
        print("  ℹ Using primary ESPN source (use --enable-multi-source for enhanced stats)")
    
    # Load data for each sport
    results = {}
    for sport in args.sports:
        print_section(f"Processing {sport}...")
        count = load_sport_data(
            sport=sport,
            start_year=args.start_year,
            end_year=args.end_year,
            scraper=scraper,
            pipeline=pipeline,
            max_retries=args.max_retries
        )
        results[sport] = count
        
        # Validate minimum count
        if count >= args.min_count:
            print(f"✓ {sport} has sufficient data: {count} >= {args.min_count}")
        else:
            print(f"✗ {sport} has insufficient data: {count} < {args.min_count}")
    
    # Print summary
    print_banner("Summary")
    
    all_sufficient = True
    failed_sports = []
    
    for sport in args.sports:
        count = results[sport]
        if count >= args.min_count:
            print(f"✓ {sport}: {count} games")
        else:
            print(f"✗ {sport}: {count} games")
            all_sufficient = False
            failed_sports.append(sport)
    
    print()
    
    if not all_sufficient:
        print("✗ Some sports failed minimum count requirement:")
        for sport in failed_sports:
            count = results[sport]
            print(f"  - {sport}: {count} games (required: {args.min_count})")
        print()
        print("Suggested actions:")
        print("  1. Check scraper logs for API errors")
        print("  2. Verify OMEGA_ENGINE_PATH is set correctly")
        print("  3. Try increasing fetch limits or date ranges")
        print("  4. Check if historical data source is available")
        sys.exit(1)
    else:
        print("✓ All sports ready for Module 1")
        sys.exit(0)


if __name__ == "__main__":
    main()
