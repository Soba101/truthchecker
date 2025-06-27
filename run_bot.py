#!/usr/bin/env python3
"""
Bot Runner Script

Simple script to run the Telegram bot game.
This provides an easy way to start the bot during development.

Usage:
    python run_bot.py
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main function
from bot.main import main

if __name__ == "__main__":
    print("🎮 Starting Telegram Bot Game...")
    print("📋 Make sure you have configured your environment variables!")
    print("🔑 You need to set TELEGRAM_BOT_TOKEN in your .env file")
    print("📂 Copy env.example to .env and configure it first")
    print("")
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("❌ No .env file found!")
        print("📝 Please copy env.example to .env and configure your settings:")
        print("   cp env.example .env")
        print("   # Then edit .env with your bot token and other settings")
        sys.exit(1)
    
    try:
        # Run the bot (main is async again)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Bot failed to start: {e}")
        print("💡 Check your configuration and try again")
        sys.exit(1) 