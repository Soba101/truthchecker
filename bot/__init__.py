"""
Telegram Bot Game Package

This package contains the main bot application including:
- Command handlers for user interactions
- Game logic and state management
- Database models and operations
- Utility functions and helpers

Author: [Your Name]
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "[Your Name]"

# Package imports for easier access
from .main import main
from .utils.config import get_settings

__all__ = ["main", "get_settings"] 