"""
BallDontLie API Client - Enhanced NBA/NFL statistics.

Provides structured, reliable data for NBA and NFL with ALL-STAR package access.
Better than web scraping for consistency and rate limits.

API Documentation: https://docs.balldontlie.io/
"""

import os
import requests
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class BallDontLieAPIClient:
    """
    Client for BallDontLie API - provides NBA and NFL statistics.
    
    Benefits over web scraping:
    - Structured, consistent data format
    - Better rate limits (ALL-STAR package)
    - Player game logs
    - Team statistics
    - More reliable than ESPN scraping
    """
    
    BASE_URL = "https://api.balldontlie.io/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize BallDontLie API client.
        
        Args:
            api_key: BallDontLie API key (or will read from BALLDONTLIE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("BALLDONTLIE_API_KEY")
        if not self.api_key:
            logger.warning("BALLDONTLIE_API_KEY not set - enhanced NBA/NFL data will not be available")
        else:
            logger.info("✓ BallDontLie API client initialized (ALL-STAR package)")
        
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                "Authorization": self.api_key,
                'User-Agent': 'OmegaSports-Validation-Lab/1.0'
            })
        
        self.rate_limit_delay = 0.6  # ALL-STAR package allows more requests
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Enforce rate limiting."""
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def get_games(
        self,
        start_date: str,
        end_date: str,
        season: Optional[int] = None,
        team_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch NBA games for a date range.
        
        Args:
            start_date: Start date YYYY-MM-DD
            end_date: End date YYYY-MM-DD
            season: Season year (optional)
            team_ids: Optional list of team IDs to filter
        
        Returns:
            List of games with statistics
        """
        if not self.api_key:
            logger.debug("No API key - skipping BallDontLie fetch")
            return []
        
        self._rate_limit()
        
        try:
            url = f"{self.BASE_URL}/games"
            params = {
                "start_date": start_date,
                "end_date": end_date,
                "per_page": 100
            }
            
            if season:
                params["seasons[]"] = season
            
            if team_ids:
                params["team_ids[]"] = team_ids
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 401:
                logger.error("BallDontLie API authentication failed - check API key")
                return []
            
            response.raise_for_status()
            data = response.json()
            
            games = data.get("data", [])
            logger.info(f"✓ Fetched {len(games)} NBA games from BallDontLie API")
            
            return games
            
        except requests.RequestException as e:
            logger.error(f"Error fetching from BallDontLie API: {e}")
            return []
    
    def get_game_stats(
        self,
        game_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Fetch player statistics for specific games.
        
        Args:
            game_ids: List of BallDontLie game IDs
        
        Returns:
            List of player stat dictionaries
        """
        if not self.api_key:
            return []
        
        self._rate_limit()
        
        try:
            url = f"{self.BASE_URL}/stats"
            params = {
                "game_ids[]": game_ids,
                "per_page": 100
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            stats = data.get("data", [])
            
            logger.debug(f"Fetched stats for {len(stats)} players")
            return stats
            
        except requests.RequestException as e:
            logger.error(f"Error fetching player stats: {e}")
            return []
    
    def get_team_stats(
        self,
        season: int,
        team_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch team statistics for a season.
        
        Args:
            season: Season year
            team_id: Optional specific team ID
        
        Returns:
            List of team stat dictionaries
        """
        if not self.api_key:
            return []
        
        self._rate_limit()
        
        try:
            url = f"{self.BASE_URL}/season_averages"
            params = {
                "season": season,
                "per_page": 100
            }
            
            if team_id:
                params["team_id"] = team_id
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get("data", [])
            
        except requests.RequestException as e:
            logger.error(f"Error fetching team stats: {e}")
            return []
    
    def enrich_game_with_stats(
        self,
        game: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrich a game with player and team statistics.
        
        Args:
            game: Base game dictionary
        
        Returns:
            Game with enhanced statistics
        """
        if not self.api_key:
            return game
        
        # For now, just return the game
        # Full implementation would map ESPN game to BallDontLie game
        # and fetch detailed statistics
        
        return game
    
    def get_player_season_stats(
        self,
        player_id: int,
        season: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get season averages for a specific player.
        
        Args:
            player_id: Player ID
            season: Season year
        
        Returns:
            Player season statistics or None
        """
        if not self.api_key:
            return None
        
        self._rate_limit()
        
        try:
            url = f"{self.BASE_URL}/season_averages"
            params = {
                "player_ids[]": [player_id],
                "season": season
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            stats = data.get("data", [])
            
            return stats[0] if stats else None
            
        except requests.RequestException as e:
            logger.error(f"Error fetching player season stats: {e}")
            return None
