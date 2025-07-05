"""
Logging Configuration

This module sets up basic logging for the application.
Simplified version without structlog for initial setup.
"""

import logging
import sys
from typing import Dict, Any

from .config import get_settings, is_development


def setup_logging() -> None:
    """
    Set up basic logging configuration.
    
    This function configures standard logging for the application.
    """
    settings = get_settings()
    
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    
    # Create application logger
    logger = logging.getLogger(__name__)
    logger.info("Logging configuration initialized")


def get_logger(name: str):
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


def log_user_action(user_id: int, action: str, **kwargs) -> None:
    """
    Log user actions for audit and analytics.
    
    Args:
        user_id: Telegram user ID
        action: Action description
        **kwargs: Additional context data
    """
    logger = get_logger("user_actions")
    extra_info = " ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.debug(f"User action: user_id={user_id} action={action} {extra_info}")


def log_game_event(game_id: str, event_type: str, **kwargs) -> None:
    """
    Log game-related events for debugging and analytics.
    
    Args:
        game_id: Unique game identifier
        event_type: Type of game event
        **kwargs: Additional event data
    """
    logger = get_logger("game_events")
    extra_info = " ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.debug(f"Game event: game_id={game_id} event_type={event_type} {extra_info}") 