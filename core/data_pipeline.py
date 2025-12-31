"""
Data pipeline for ingesting, validating, and curating sports betting data.

This module provides comprehensive data ingestion from OmegaSports scraper engine,
with validation, caching, and historical database management.
"""

import logging
import json
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class GameData:
    """Structured game data."""

    game_id: str
    date: str
    sport: str
    league: str
    home_team: str
    away_team: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    moneyline: Optional[Dict[str, Any]] = None
    spread: Optional[Dict[str, Any]] = None
    total: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class DataValidator:
    """Validates game data against schema requirements."""

    REQUIRED_FIELDS = [
        "game_id",
        "date",
        "sport",
        "league",
        "home_team",
        "away_team",
    ]

    VALID_SPORTS = ["NBA", "NFL", "MLB", "NHL", "NCAAB", "NCAAF"]

    @classmethod
    def validate(cls, game: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate game data.

        Args:
            game: Game data dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        for field in cls.REQUIRED_FIELDS:
            if field not in game or game[field] is None:
                return False, f"Missing required field: {field}"

        # Validate sport
        if game["sport"] not in cls.VALID_SPORTS:
            return False, f"Invalid sport: {game['sport']}"

        # Validate date format
        try:
            datetime.strptime(game["date"], "%Y-%m-%d")
        except ValueError:
            return False, f"Invalid date format: {game['date']}"

        # Validate teams are non-empty strings
        if not isinstance(game["home_team"], str) or not game["home_team"]:
            return False, "home_team must be non-empty string"
        if not isinstance(game["away_team"], str) or not game["away_team"]:
            return False, "away_team must be non-empty string"

        # Check for duplicate teams
        if game["home_team"].lower() == game["away_team"].lower():
            return False, "home_team and away_team cannot be the same"

        return True, ""


class CacheManager:
    """Manages caching of API responses and processed data."""

    def __init__(self, cache_dir: Path):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for cache storage
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"CacheManager initialized with cache_dir={cache_dir}")

    def _get_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """
        Generate cache key from prefix and parameters.

        Args:
            prefix: Cache key prefix
            params: Parameters dictionary

        Returns:
            Cache key (hash-based)
        """
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"{prefix}_{params_hash}"

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve cached data.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found/expired
        """
        cache_file = self.cache_dir / f"{key}.json"
        if not cache_file.exists():
            return None

        # Check if cache is older than 24 hours
        file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if file_age > timedelta(hours=24):
            logger.debug(f"Cache expired: {key}")
            return None

        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
            logger.debug(f"Cache hit: {key}")
            return data
        except Exception as e:
            logger.warning(f"Error reading cache {key}: {e}")
            return None

    def set(self, key: str, data: Any) -> None:
        """
        Cache data.

        Args:
            key: Cache key
            data: Data to cache
        """
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, "w") as f:
                json.dump(data, f, default=str)
            logger.debug(f"Cache set: {key}")
        except Exception as e:
            logger.warning(f"Error writing cache {key}: {e}")

    def clear(self, prefix: Optional[str] = None) -> None:
        """
        Clear cache.

        Args:
            prefix: Clear only cache keys with this prefix. If None, clear all.
        """
        for cache_file in self.cache_dir.glob("*.json"):
            if prefix is None or cache_file.stem.startswith(prefix):
                cache_file.unlink()
        logger.info(f"Cache cleared (prefix={prefix})")


class HistoricalDatabase:
    """Manages persistent storage of historical game data."""

    def __init__(self, data_dir: Path):
        """
        Initialize historical database.

        Args:
            data_dir: Directory for data storage
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"HistoricalDatabase initialized with data_dir={data_dir}")

    def _get_file_path(self, sport: str, year: int) -> Path:
        """
        Get file path for sport/year combination.

        Args:
            sport: Sport name
            year: Year

        Returns:
            Path to data file
        """
        return self.data_dir / f"{sport.lower()}_{year}.json"

    def save_games(self, games: List[Dict[str, Any]], sport: str, year: int) -> int:
        """
        Save games to database.

        Args:
            games: List of game dictionaries
            sport: Sport name
            year: Year

        Returns:
            Number of games saved
        """
        file_path = self._get_file_path(sport, year)

        # Validate all games
        valid_games = []
        for game in games:
            is_valid, error = DataValidator.validate(game)
            if is_valid:
                valid_games.append(game)
            else:
                logger.warning(f"Invalid game data: {error}")

        if not valid_games:
            logger.warning(f"No valid games to save for {sport} {year}")
            return 0

        # Save to file
        with open(file_path, "w") as f:
            json.dump(valid_games, f, indent=2, default=str)

        logger.info(f"Saved {len(valid_games)} games to {file_path}")
        return len(valid_games)

    def load_games(
        self, sport: str, start_year: int, end_year: int
    ) -> List[Dict[str, Any]]:
        """
        Load games from database.

        Args:
            sport: Sport name
            start_year: Start year (inclusive)
            end_year: End year (inclusive)

        Returns:
            List of game dictionaries
        """
        all_games = []

        for year in range(start_year, end_year + 1):
            file_path = self._get_file_path(sport, year)
            if not file_path.exists():
                logger.warning(f"No data file found: {file_path}")
                continue

            try:
                with open(file_path, "r") as f:
                    games = json.load(f)
                all_games.extend(games)
                logger.info(f"Loaded {len(games)} games from {file_path}")
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")

        logger.info(f"Total games loaded: {len(all_games)} ({sport}, {start_year}-{end_year})")
        return all_games

    def game_count(self, sport: str, year: int) -> int:
        """
        Get count of games for sport/year.

        Args:
            sport: Sport name
            year: Year

        Returns:
            Number of games
        """
        file_path = self._get_file_path(sport, year)
        if not file_path.exists():
            return 0

        try:
            with open(file_path, "r") as f:
                games = json.load(f)
            return len(games)
        except Exception as e:
            logger.error(f"Error counting games in {file_path}: {e}")
            return 0


class DataPipeline:
    """
    Main data pipeline for ingesting, validating, and curating sports data.
    """

    def __init__(self, cache_dir: Optional[Path] = None, data_dir: Optional[Path] = None):
        """
        Initialize data pipeline.

        Args:
            cache_dir: Directory for caching data
            data_dir: Directory for historical database
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path("./data/cache")
        self.data_dir = Path(data_dir) if data_dir else Path("./data/historical")

        self.cache = CacheManager(self.cache_dir)
        self.database = HistoricalDatabase(self.data_dir)
        self.validator = DataValidator()

        logger.info(
            f"DataPipeline initialized (cache={self.cache_dir}, data={self.data_dir})"
        )

    def fetch_historical_games(
        self, sport: str, start_year: int = 2020, end_year: int = 2024
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical game data for a sport and year range.

        This fetches from the local database. For fresh data, use
        fetch_and_save_games() first.

        Args:
            sport: Sport name (NBA, NFL, etc.)
            start_year: Start year (inclusive)
            end_year: End year (inclusive)

        Returns:
            List of game dictionaries
        """
        logger.info(f"Fetching historical games: {sport} {start_year}-{end_year}")

        games = self.database.load_games(sport, start_year, end_year)
        if not games:
            logger.warning(f"No historical games found for {sport}")
            return []

        return games

    def validate_game_data(self, game: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate game data against schema.

        Args:
            game: Game data dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        return self.validator.validate(game)

    def save_games(
        self, games: List[Dict[str, Any]], sport: str, year: int
    ) -> int:
        """
        Save games to historical database.

        Args:
            games: List of game dictionaries
            sport: Sport name
            year: Year

        Returns:
            Number of games saved
        """
        logger.info(f"Saving {len(games)} games for {sport} {year}")
        return self.database.save_games(games, sport, year)

    def get_game_count(self, sport: str, start_year: int = 2020, end_year: int = 2024) -> int:
        """
        Get total count of games for sport/year range.

        Args:
            sport: Sport name
            start_year: Start year
            end_year: End year

        Returns:
            Total number of games
        """
        total = 0
        for year in range(start_year, end_year + 1):
            count = self.database.game_count(sport, year)
            total += count

        return total

    def cache_data(self, key: str, data: Any) -> None:
        """
        Cache data for future use.

        Args:
            key: Cache key
            data: Data to cache
        """
        self.cache.set(key, data)

    def get_cached_data(self, key: str) -> Optional[Any]:
        """
        Retrieve cached data.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found
        """
        return self.cache.get(key)

    def clear_cache(self, prefix: Optional[str] = None) -> None:
        """
        Clear cache.

        Args:
            prefix: Clear only cache keys with this prefix
        """
        self.cache.clear(prefix)
