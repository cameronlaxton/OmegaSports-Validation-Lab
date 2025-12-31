"""
ScraperEngine compatibility module for Validation Lab.

This module provides the ScraperEngine interface expected by the validation lab,
wrapping the actual OmegaScraper from OmegaSportsAgent.

SUPPORTED SPORTS:
- NBA (National Basketball Association)
- NFL (National Football League)
- NHL (National Hockey League)
- MLB (Major League Baseball)
- NCAAB (NCAA Men's Basketball)

RELATIONSHIP TO OMEGAAGENT:
This Validation Lab is a companion research platform to OmegaAgent. The lab:
- Tests and validates OmegaAgent's algorithms and parameters
- Optimizes model parameters through systematic experimentation
- Feeds validated improvements back into OmegaAgent production system
- Provides rigorous statistical validation of all optimizations
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add omega engine path to sys.path if configured
try:
    from utils.config import config
    omega_path = config.omega_engine_path
    if omega_path and omega_path.exists():
        if str(omega_path) not in sys.path:
            sys.path.insert(0, str(omega_path))
except Exception:
    pass

# Try to import the actual scraper
try:
    from scraper_engine import OmegaScraper
    OMEGA_SCRAPER_AVAILABLE = True
except ImportError:
    OMEGA_SCRAPER_AVAILABLE = False
    OmegaScraper = None


# Supported sports for omni-sports functionality
SUPPORTED_SPORTS = {
    'NBA': 'National Basketball Association',
    'NFL': 'National Football League',
    'NHL': 'National Hockey League',
    'MLB': 'Major League Baseball',
    'NCAAB': 'NCAA Men\'s Basketball',
    'NCAAF': 'NCAA Football',  # Also support NCAAF
    'WNBA': 'Women\'s National Basketball Association',
    'MLS': 'Major League Soccer'
}


class ScraperEngine:
    """
    Compatibility wrapper for ScraperEngine interface.
    
    This class provides the interface expected by the validation lab,
    wrapping the actual OmegaScraper implementation from OmegaAgent.
    
    Supports omni-sports functionality for NBA, NFL, NHL, MLB, and NCAAB.
    Uses OmegaAgent's schedule_api to fetch games from ESPN API.
    
    RELATIONSHIP TO OMEGAAGENT:
    This Validation Lab tests and improves OmegaAgent. Optimizations discovered
    here feed back into the OmegaAgent production system.
    """
    
    def __init__(self):
        """Initialize the scraper engine."""
        if not OMEGA_SCRAPER_AVAILABLE:
            # Don't raise error, just warn - the scraper may not be needed
            self._scraper = None
        else:
            self._scraper = OmegaScraper()
    
    def fetch_games(
        self, 
        sport: str, 
        start_date: Optional[str] = None, 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch games for a sport (omni-sports support).
        
        Supports: NBA, NFL, NHL, MLB, NCAAB, NCAAF, WNBA, MLS
        
        Args:
            sport: Sport code (NBA, NFL, NHL, MLB, NCAAB, etc.)
            start_date: Start date in YYYY-MM-DD format (optional)
            limit: Maximum number of games to return (optional)
        
        Returns:
            List of game dictionaries in format expected by validation lab
        
        Raises:
            ValueError: If sport is not supported
        """
        # Validate sport
        sport_upper = sport.upper()
        if sport_upper not in SUPPORTED_SPORTS:
            raise ValueError(
                f"Sport '{sport}' not supported. Supported sports: {', '.join(SUPPORTED_SPORTS.keys())}"
            )
        try:
            # Try to use omega.data.schedule_api to get games
            # Need to import from the actual OmegaSportsAgent omega package
            # First, try to import directly from the engine path
            import importlib.util
            from pathlib import Path
            from datetime import datetime, timedelta
            import logging
            
            logger = logging.getLogger(__name__)
            games = []
            
            # Try to load schedule_api from OmegaSportsAgent
            schedule_api = None
            try:
                from utils.config import config
                omega_path = config.omega_engine_path
                if omega_path and omega_path.exists():
                    # Import from the actual omega package in OmegaSportsAgent
                    spec = importlib.util.spec_from_file_location(
                        "omega.data.schedule_api",
                        omega_path / "omega" / "data" / "schedule_api.py"
                    )
                    if spec and spec.loader:
                        schedule_api_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(schedule_api_module)
                        schedule_api = schedule_api_module
            except Exception as e:
                logger.debug(f"Could not load schedule_api from engine path: {e}")
                # Fallback: try normal import (might work if omega is in path)
                try:
                    # Temporarily remove our local omega from path to import from engine
                    import sys
                    original_path = sys.path.copy()
                    try:
                        # Remove current directory from path temporarily
                        if '.' in sys.path:
                            sys.path.remove('.')
                        if str(Path.cwd()) in sys.path:
                            sys.path.remove(str(Path.cwd()))
                        from omega.data import schedule_api as schedule_api_module
                        schedule_api = schedule_api_module
                    finally:
                        sys.path = original_path
                except ImportError:
                    pass
            
            if start_date:
                # Parse start date and calculate days to look ahead
                try:
                    start = datetime.strptime(start_date, "%Y-%m-%d")
                    today = datetime.now()
                    days_ahead = (start - today).days
                    
                    if days_ahead < 0:
                        # Start date is in the past, look back or return empty
                        return []
                    
                    # Get games for the specified date range
                    # Look ahead up to 7 days from start_date
                    days = min(7, days_ahead + 7)
                    raw_games = schedule_api.get_upcoming_games(sport_upper, days=days)
                    
                    # Filter by start_date
                    for game in raw_games:
                        game_date_str = game.get("date", "")
                        if game_date_str:
                            try:
                                # Parse ESPN date format (ISO 8601)
                                game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
                                if game_date.date() >= start.date():
                                    games.append(self._format_game(game, sport_upper))
                            except (ValueError, AttributeError):
                                # If date parsing fails, include the game anyway
                                games.append(self._format_game(game, sport_upper))
                        else:
                            # No date in game, include it anyway
                            games.append(self._format_game(game, sport_upper))
                except ValueError:
                    # Invalid date format, just get upcoming games
                    raw_games = schedule_api.get_upcoming_games(sport_upper, days=7)
                    games = [self._format_game(g, sport_upper) for g in raw_games]
            else:
                # No start_date specified, get upcoming games
                raw_games = schedule_api.get_upcoming_games(sport_upper, days=7)
                logger.debug(f"Fetched {len(raw_games)} raw games from schedule_api")
                games = [self._format_game(g, sport_upper) for g in raw_games]
            
            # Apply limit if specified
            if limit and limit > 0:
                games = games[:limit]
            
            logger.debug(f"Returning {len(games)} formatted games")
            return games
            
        except ImportError as e:
            # omega.data.schedule_api not available
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not import omega.data.schedule_api: {e}")
            return []
        except Exception as e:
            # Log error but don't fail - return empty list
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error fetching games: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []
    
    def _format_game(self, game: Dict[str, Any], sport: str) -> Dict[str, Any]:
        """
        Format a game from OmegaSports format to validation lab format.
        
        Args:
            game: Game dictionary from OmegaSports
            sport: Sport name
        
        Returns:
            Formatted game dictionary
        """
        # Extract team names
        home_team_data = game.get("home_team", {})
        away_team_data = game.get("away_team", {})
        
        home_team = home_team_data.get("name", "") if isinstance(home_team_data, dict) else str(home_team_data)
        away_team = away_team_data.get("name", "") if isinstance(away_team_data, dict) else str(away_team_data)
        
        # Format date
        date_str = game.get("date", "")
        if date_str:
            try:
                from datetime import datetime
                # Parse ISO format and convert to YYYY-MM-DD
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                pass
        
        # Format game for validation lab
        formatted = {
            "game_id": game.get("game_id", ""),
            "date": date_str,
            "sport": sport.upper(),
            "league": sport.upper(),
            "home_team": home_team,
            "away_team": away_team,
            "home_score": None,
            "away_score": None,
            "moneyline": None,
            "spread": None,
            "total": None,
        }
        
        # Try to extract odds if available
        odds = game.get("odds", {})
        if odds:
            if isinstance(odds, dict):
                # Extract spread and total from odds
                spread = odds.get("spread")
                total = odds.get("over_under")
                
                if spread:
                    formatted["spread"] = {"home": spread}
                if total:
                    formatted["total"] = {"over": total, "under": total}
        
        return formatted
    
    def fetch_season_games(self, sport: str, season: int) -> List[Dict[str, Any]]:
        """
        Fetch games for a season.
        
        Args:
            sport: Sport name
            season: Season year
        
        Returns:
            List of game dictionaries
        """
        # Stub implementation
        return []

