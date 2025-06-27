"""
Configuration Management

This module handles all application configuration using environment variables.
Simplified version without Pydantic for initial setup.
"""

import os
from functools import lru_cache
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """
    Application settings loaded from environment variables.
    
    All settings have sensible defaults for development.
    """
    
    def __init__(self):
        # Telegram Bot Configuration
        self.telegram_bot_token: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.telegram_webhook_url: Optional[str] = os.getenv('TELEGRAM_WEBHOOK_URL')
        
        # Database Configuration
        self.database_url: str = os.getenv('DATABASE_URL', 'sqlite:///game_bot.db')
        
        # Redis Configuration (optional)
        self.redis_url: Optional[str] = os.getenv('REDIS_URL')
        
        # Application Settings
        self.debug: bool = os.getenv('DEBUG', 'false').lower() == 'true'
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
        self.environment: str = os.getenv('ENVIRONMENT', 'development')
        
        # Game Configuration
        try:
            self.max_concurrent_games: int = int(os.getenv('MAX_CONCURRENT_GAMES', '100'))
        except ValueError as e:
            raise ValueError(f"Invalid MAX_CONCURRENT_GAMES value: {os.getenv('MAX_CONCURRENT_GAMES')}. Must be a number.") from e
            
        try:
            # Clean the timeout value - remove any comments or extra characters
            timeout_str = os.getenv('GAME_SESSION_TIMEOUT', '3600').split('#')[0].strip()
            self.game_session_timeout: int = int(timeout_str)
        except ValueError as e:
            raise ValueError(f"Invalid GAME_SESSION_TIMEOUT value: '{os.getenv('GAME_SESSION_TIMEOUT')}'. Must be a number without comments.") from e
            
        self.default_game_type: str = os.getenv('DEFAULT_GAME_TYPE', 'word_guess')
        
        # Security Settings
        self.secret_key: str = os.getenv('SECRET_KEY', 'dev-secret-key')
        admin_ids_str = os.getenv('ADMIN_USER_IDS', '')
        self.admin_user_ids: List[int] = []
        if admin_ids_str:
            try:
                self.admin_user_ids = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip()]
            except ValueError:
                self.admin_user_ids = []
        
        # Monitoring Settings
        self.sentry_dsn: Optional[str] = os.getenv('SENTRY_DSN')
        self.prometheus_port: int = int(os.getenv('PROMETHEUS_PORT', '8000'))
        
        # Rate Limiting
        try:
            # Clean rate limit values - remove any comments or extra characters
            rate_limit_str = os.getenv('RATE_LIMIT_PER_USER', '10').split('#')[0].strip()
            self.rate_limit_per_user: int = int(rate_limit_str)
        except ValueError as e:
            raise ValueError(f"Invalid RATE_LIMIT_PER_USER value: '{os.getenv('RATE_LIMIT_PER_USER')}'. Must be a number without comments.") from e
            
        try:
            # Clean rate limit window value - remove any comments or extra characters
            window_str = os.getenv('RATE_LIMIT_WINDOW', '60').split('#')[0].strip()
            self.rate_limit_window: int = int(window_str)
        except ValueError as e:
            raise ValueError(f"Invalid RATE_LIMIT_WINDOW value: '{os.getenv('RATE_LIMIT_WINDOW')}'. Must be a number without comments.") from e


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with caching.
    
    Uses LRU cache to avoid reloading settings on every call.
    Cache is cleared when the process restarts.
    
    Returns:
        Settings: Application configuration settings
    """
    return Settings()


def is_admin_user(user_id: int) -> bool:
    """
    Check if a user ID is in the admin list.
    
    Args:
        user_id: Telegram user ID to check
        
    Returns:
        bool: True if user is admin, False otherwise
    """
    settings = get_settings()
    return user_id in settings.admin_user_ids


def is_development() -> bool:
    """
    Check if running in development environment.
    
    Returns:
        bool: True if in development, False otherwise
    """
    settings = get_settings()
    return settings.environment.lower() in ["development", "dev", "local"]


def is_production() -> bool:
    """
    Check if running in production environment.
    
    Returns:
        bool: True if in production, False otherwise
    """
    settings = get_settings()
    return settings.environment.lower() in ["production", "prod"] 