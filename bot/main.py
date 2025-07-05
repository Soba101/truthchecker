"""
Truth Wars Bot Main Application

This is the main entry point for the Truth Wars Telegram bot.
It initializes the database, sets up handlers, and starts the bot.
"""

import asyncio
import logging
import sys
from typing import Optional

from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.constants import ParseMode
from telegram.ext import Defaults  # For setting default parse mode globally

from .handlers.command_handlers import (
    start_command, help_command, play_command, stats_command, leaderboard_command
)
from .handlers.truth_wars_handlers import (
    start_truth_wars, vote_command, ability_command, status_command
)
from .handlers.message_handlers import handle_text_message
from .handlers.error_handlers import error_handler
from .handlers.truth_wars_handlers import handle_truth_wars_callback

from .database.database import init_database, close_database
from .database.seed_data import seed_all_data
from .utils.config import get_settings
from .utils.logging_config import setup_logging, get_logger

# Setup logging first
setup_logging()
logger = get_logger(__name__)


class TruthWarsBot:
    """
    Main Truth Wars bot application class.
    
    This handles the complete lifecycle of the bot including:
    - Database initialization and seeding
    - Handler registration
    - Application startup and shutdown
    """
    
    def __init__(self):
        """Initialize the bot application."""
        self.settings = get_settings()
        self.application: Optional[Application] = None
        
    async def initialize_database(self) -> None:
        """
        Initialize database with refined Truth Wars schema and seed data.
        
        This creates all necessary tables and populates them with
        educational headlines and initial content.
        """
        try:
            logger.info("Initializing database for refined Truth Wars system...")
            
            # Initialize database schema
            await init_database()
            
            # Seed initial data (headlines, educational content)
            await seed_all_data()
            
            logger.info("Database initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def setup_bot_commands(self) -> None:
        """
        Set up the bot command menu that appears when users type '/'.
        
        This creates the shortcut bar with all available commands
        that users can easily access, and ensures commands work cleanly
        without showing the @botusername suffix.
        """
        if not self.application:
            raise RuntimeError("Application not initialized")
            
        try:
            logger.info("Setting up bot command menu...")
            
            # Define all bot commands with descriptions
            # These will appear in the command menu when users type '/'
            commands = [
                BotCommand("start", "Welcome message and introduction"),
                BotCommand("help", "Complete guide and instructions"), 
                BotCommand("truthwars", "Start Truth Wars game (groups only)"),
                BotCommand("status", "Check current game status"),
                BotCommand("ability", "View your role and abilities"),
                BotCommand("vote", "Vote to eliminate a player"),
                BotCommand("stats", "View your game statistics"),
                BotCommand("leaderboard", "See top players"),
                BotCommand("play", "Browse other games"),
            ]
            
            # Set the commands for the bot - this creates the clean command menu
            await self.application.bot.set_my_commands(commands)
            
            # Get bot info to ensure proper setup
            bot_info = await self.application.bot.get_me()
            logger.info(f"Bot username: @{bot_info.username}")
            logger.info(f"Bot commands menu configured with {len(commands)} commands")
            
            # Log instructions for BotFather configuration
            logger.debug("=" * 70)
            logger.debug("🚨 CRITICAL: BOTFATHER CONFIGURATION REQUIRED 🚨")
            logger.debug("Commands will show @username suffix until BotFather is configured!")
            logger.debug("")
            logger.debug("1. Message @BotFather on Telegram")
            logger.debug("2. Send: /setcommands")
            logger.debug("3. Select your bot")
            logger.debug("4. Copy and paste EXACTLY this list:")
            logger.debug("")
            for cmd in commands:
                logger.debug(f"{cmd.command} - {cmd.description}")
            logger.debug("")
            logger.debug("5. Send: /setprivacy")
            logger.debug("6. Select your bot") 
            logger.debug("7. Choose: Disable")
            logger.debug("")
            logger.debug("8. Restart this bot after completing steps above")
            logger.debug("=" * 70)
            
        except Exception as e:
            logger.error(f"Failed to set bot commands: {e}")
            # Don't raise - this is not critical for bot operation
    
    def setup_handlers(self) -> None:
        """
        Register all bot command and message handlers.
        
        This sets up the complete handler system for the refined
        Truth Wars game including reputation tracking, Trust/Flag voting,
        and educational features.
        """
        if not self.application:
            raise RuntimeError("Application not initialized")
        
        logger.info("Setting up bot handlers for refined Truth Wars system...")
        
        # Command handlers - these automatically handle both /command and /command@botusername
        command_handlers = [
            CommandHandler("start", start_command),
            CommandHandler("help", help_command),
            CommandHandler("play", play_command),
            CommandHandler("stats", stats_command),
            CommandHandler("leaderboard", leaderboard_command),
            CommandHandler("truthwars", start_truth_wars),
            CommandHandler("vote", vote_command),
            CommandHandler("ability", ability_command),
            CommandHandler("status", status_command),
        ]
        
        for handler in command_handlers:
            self.application.add_handler(handler)
        
        # Callback query handler for inline buttons (Trust/Flag voting, snipe actions, etc.)
        self.application.add_handler(
            CallbackQueryHandler(handle_truth_wars_callback)
        )
        
        # Message handlers for general chat and educational discussions
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
        )
        
        # Error handler for comprehensive error tracking
        self.application.add_error_handler(error_handler)
        
        logger.info("All handlers registered successfully")
        logger.info("Bot ready for refined Truth Wars gameplay with:")
        logger.info("- Reputation system (3 RP → Ghost Viewer)")
        logger.info("- Trust/Flag voting on headlines")
        logger.info("- Shadow ban mechanics via snipe abilities")
        logger.info("- Educational content via rotating Drunk role")
        logger.info("- Fixed 5-round game structure")
    

    
    async def cleanup(self) -> None:
        """
        Cleanup resources when shutting down.
        
        This ensures proper database connection closure and
        resource cleanup.
        """
        try:
            logger.info("Shutting down Truth Wars Bot...")
            
            # Close database connections
            await close_database()
            
            # Stop application if running
            if self.application:
                if hasattr(self.application, 'updater') and self.application.updater.running:
                    await self.application.updater.stop()
                if self.application.running:
                    await self.application.stop()
                await self.application.shutdown()
            
            logger.info("Bot shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def main() -> None:
    """
    Main entry point for the Truth Wars bot.
    
    This function creates and starts the bot application,
    handling any startup errors gracefully.
    """
    bot = TruthWarsBot()
    
    try:
        logger.info("Starting Truth Wars Bot - Refined Educational System")
        
        # Create application with global Markdown parse mode so **text** renders bold
        defaults = Defaults(parse_mode=ParseMode.MARKDOWN)
        bot.application = (
            Application.builder()
            .token(bot.settings.telegram_bot_token)
            .defaults(defaults)
            .build()
        )
        
        # Initialize database and seed data
        await bot.initialize_database()
        
        # Setup bot command menu
        await bot.setup_bot_commands()
        
        # Setup all handlers
        bot.setup_handlers()
        
        # Start polling (using async version)
        logger.info("Bot initialization complete, starting polling...")
        async with bot.application:
            await bot.application.start()
            await bot.application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
            # Keep running until interrupted
            try:
                await asyncio.Event().wait()
            except (KeyboardInterrupt, SystemExit):
                logger.info("Received shutdown signal")
            finally:
                await bot.application.updater.stop()
                await bot.application.stop()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1) 