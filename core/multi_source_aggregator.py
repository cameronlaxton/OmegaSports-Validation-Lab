"""
Multi-source data aggregator for comprehensive sports statistics.

This module extends the historical data scraper to fetch data from multiple sources
beyond ESPN, including:
- ESPN API (game results, basic stats)
- Sports Reference (advanced statistics)
- The Odds API (historical betting lines)
- Additional sources as needed

Ensures comprehensive data collection with real, not mocked, statistics.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import requests
from pathlib import Path

logger = logging.getLogger(__name__)


class MultiSourceAggregator:
    """
    Aggregates sports data from multiple sources to ensure comprehensive coverage.
    
    Sources:
    1. ESPN API - Primary game results and basic stats
    2. Sports Reference - Advanced team and player statistics
    3. The Odds API - Historical betting lines and odds
    4. Fallback sources for missing data
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize multi-source aggregator.
        
        Args:
            cache_dir: Directory for caching responses
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path("./data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        # Track which sources are available
        self.available_sources = {
            "espn": True,  # Primary source
            "sports_reference": False,  # Requires additional setup
            "odds_api": False,  # Requires API key
        }
        
        logger.info("MultiSourceAggregator initialized")
    
    def enrich_game_data(
        self,
        game: Dict[str, Any],
        fetch_advanced_stats: bool = True,
        fetch_player_stats: bool = True,
        fetch_odds_history: bool = True
    ) -> Dict[str, Any]:
        """
        Enrich game data with statistics from multiple sources.
        
        This ensures we get REAL, comprehensive data beyond basic ESPN results.
        
        Args:
            game: Base game data from ESPN
            fetch_advanced_stats: Whether to fetch advanced team statistics
            fetch_player_stats: Whether to fetch player-level statistics
            fetch_odds_history: Whether to fetch historical odds data
            
        Returns:
            Enriched game dictionary with comprehensive statistics
        """
        enriched = game.copy()
        
        # Try to fetch advanced statistics from additional sources
        if fetch_advanced_stats:
            advanced_stats = self._fetch_advanced_statistics(game)
            if advanced_stats:
                enriched["advanced_stats"] = advanced_stats
        
        # Try to fetch player-level statistics
        if fetch_player_stats:
            player_stats = self._fetch_player_statistics(game)
            if player_stats:
                enriched["player_stats"] = player_stats
        
        # Try to fetch historical odds data
        if fetch_odds_history:
            odds_history = self._fetch_odds_history(game)
            if odds_history:
                enriched["odds_history"] = odds_history
        
        return enriched
    
    def _fetch_advanced_statistics(self, game: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fetch advanced statistics from Sports Reference or similar sources.
        
        This would include:
        - Offensive/Defensive ratings
        - Pace statistics
        - Four factors (eFG%, TO%, OR%, FT rate)
        - Player efficiency ratings
        - Plus/minus statistics
        
        Args:
            game: Base game data
            
        Returns:
            Dictionary of advanced statistics or None if unavailable
        """
        # TODO: Implement Sports Reference scraping
        # For now, return None to indicate this data source needs implementation
        
        # Example structure of what this would return:
        # return {
        #     "home_advanced": {
        #         "offensive_rating": 112.5,
        #         "defensive_rating": 108.3,
        #         "pace": 98.7,
        #         "effective_fg_pct": 0.545,
        #         "turnover_pct": 0.132,
        #         "offensive_rebound_pct": 0.287,
        #         "free_throw_rate": 0.245
        #     },
        #     "away_advanced": { ... }
        # }
        
        logger.debug(f"Advanced statistics not yet implemented for game {game.get('game_id')}")
        return None
    
    def _fetch_player_statistics(self, game: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch player-level statistics from box scores.
        
        This would include:
        - Points, rebounds, assists per player
        - Shooting percentages
        - Plus/minus
        - Minutes played
        - Advanced metrics (PER, usage rate, etc.)
        
        Args:
            game: Base game data
            
        Returns:
            List of player stat dictionaries or None if unavailable
        """
        # TODO: Implement player statistics fetching
        # This could come from ESPN's box score API or Sports Reference
        
        # Example structure:
        # return [
        #     {
        #         "player_name": "LeBron James",
        #         "team": "Los Angeles Lakers",
        #         "points": 28,
        #         "rebounds": 8,
        #         "assists": 11,
        #         "field_goals": "11-20",
        #         "three_pointers": "3-7",
        #         "free_throws": "3-4",
        #         "minutes": 36,
        #         "plus_minus": +15
        #     },
        #     ...
        # ]
        
        logger.debug(f"Player statistics not yet implemented for game {game.get('game_id')}")
        return None
    
    def _fetch_odds_history(self, game: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fetch historical odds data from The Odds API or similar sources.
        
        This would include:
        - Opening lines
        - Line movements over time
        - Multiple sportsbook odds
        - Closing lines
        - Steam moves and reverse line movement
        
        Args:
            game: Base game data
            
        Returns:
            Dictionary of odds history or None if unavailable
        """
        # TODO: Implement The Odds API integration
        # Requires API key from https://the-odds-api.com/
        
        # Example structure:
        # return {
        #     "opening_lines": {
        #         "moneyline": {"home": -145, "away": 125},
        #         "spread": {"line": -3.0, "home_odds": -110, "away_odds": -110},
        #         "total": {"line": 225.0, "over_odds": -110, "under_odds": -110}
        #     },
        #     "closing_lines": {
        #         "moneyline": {"home": -150, "away": 130},
        #         "spread": {"line": -3.5, "home_odds": -110, "away_odds": -110},
        #         "total": {"line": 225.5, "over_odds": -110, "under_odds": -110}
        #     },
        #     "line_movements": [
        #         {"timestamp": "2024-01-15T10:00:00Z", "spread": -3.0, ...},
        #         {"timestamp": "2024-01-15T12:00:00Z", "spread": -3.5, ...},
        #     ],
        #     "sharp_money_indicator": "home",
        #     "public_betting_pct": 65.2
        # }
        
        logger.debug(f"Odds history not yet implemented for game {game.get('game_id')}")
        return None
    
    def verify_data_completeness(self, game: Dict[str, Any]) -> Dict[str, bool]:
        """
        Verify completeness of data to ensure we're not using mocked/sample data.
        
        Args:
            game: Game data to verify
            
        Returns:
            Dictionary indicating which data fields are present and valid
        """
        completeness = {
            "has_basic_info": all(k in game for k in [
                "game_id", "date", "sport", "home_team", "away_team"
            ]),
            "has_final_score": all(k in game for k in ["home_score", "away_score"]),
            "has_team_stats": "home_team_stats" in game and "away_team_stats" in game,
            "has_betting_lines": "moneyline" in game or "spread" in game or "total" in game,
            "has_venue_info": "venue" in game,
            "has_real_scores": (
                game.get("home_score", 0) > 0 and 
                game.get("away_score", 0) > 0 and
                game.get("status") == "final"
            ),
        }
        
        # Check for obviously mocked data patterns
        completeness["appears_real"] = (
            completeness["has_real_scores"] and
            completeness["has_basic_info"] and
            game.get("game_id", "").strip() != "" and
            game.get("home_team") != game.get("away_team")
        )
        
        return completeness
    
    def get_data_source_priority(self, sport: str, data_type: str) -> List[str]:
        """
        Get prioritized list of data sources for a given sport and data type.
        
        Args:
            sport: Sport name (NBA, NFL, etc.)
            data_type: Type of data needed (game_results, team_stats, player_stats, etc.)
            
        Returns:
            List of source names in priority order
        """
        # Define source priorities by sport and data type
        priorities = {
            "NBA": {
                "game_results": ["espn", "sports_reference"],
                "team_stats": ["espn", "sports_reference"],
                "player_stats": ["espn", "sports_reference"],
                "betting_lines": ["espn", "odds_api"],
                "advanced_stats": ["sports_reference"],
            },
            "NFL": {
                "game_results": ["espn", "sports_reference"],
                "team_stats": ["espn", "sports_reference"],
                "player_stats": ["espn", "sports_reference"],
                "betting_lines": ["espn", "odds_api"],
                "advanced_stats": ["sports_reference"],
            },
            "NCAAB": {
                "game_results": ["espn", "sports_reference"],
                "team_stats": ["espn", "sports_reference"],
                "player_stats": ["espn"],
                "betting_lines": ["espn"],
                "advanced_stats": ["sports_reference"],
            },
            "NCAAF": {
                "game_results": ["espn", "sports_reference"],
                "team_stats": ["espn", "sports_reference"],
                "player_stats": ["espn"],
                "betting_lines": ["espn"],
                "advanced_stats": ["sports_reference"],
            },
        }
        
        return priorities.get(sport, {}).get(data_type, ["espn"])
    
    def get_available_sources_status(self) -> Dict[str, bool]:
        """
        Get status of which data sources are currently available.
        
        Returns:
            Dictionary mapping source names to availability status
        """
        return self.available_sources.copy()


def validate_not_sample_data(game: Dict[str, Any]) -> bool:
    """
    Validate that game data is real, not sample/mocked data.
    
    Checks for:
    - Valid game IDs (not placeholder values)
    - Realistic scores
    - Real team names
    - Actual dates
    - Non-default values
    
    Args:
        game: Game data to validate
        
    Returns:
        True if data appears to be real, False if it appears to be sample/mocked
    """
    # Check for placeholder/sample indicators
    sample_indicators = [
        "sample", "test", "mock", "fake", "example", "demo",
        "placeholder", "xxx", "tbd", "n/a"
    ]
    
    game_id = str(game.get("game_id", "")).lower()
    home_team = str(game.get("home_team", "")).lower()
    away_team = str(game.get("away_team", "")).lower()
    
    # Check for sample indicators in key fields
    for indicator in sample_indicators:
        if (indicator in game_id or 
            indicator in home_team or 
            indicator in away_team):
            logger.warning(f"Game appears to be sample data: {game_id}")
            return False
    
    # Check for valid scores
    home_score = game.get("home_score", 0)
    away_score = game.get("away_score", 0)
    
    if home_score == 0 and away_score == 0 and game.get("status") == "final":
        logger.warning(f"Game has 0-0 final score (likely invalid): {game_id}")
        return False
    
    # Check for valid date
    try:
        game_date = datetime.fromisoformat(game.get("date", ""))
        current_year = datetime.now().year
        
        # Reject dates too far in future or past
        if game_date.year < 2000 or game_date.year > current_year + 1:
            logger.warning(f"Game has invalid year: {game_date.year}")
            return False
    except (ValueError, TypeError):
        logger.warning(f"Game has invalid date format: {game.get('date')}")
        return False
    
    # All checks passed
    return True
