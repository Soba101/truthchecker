"""
Bot Command Handlers

This module contains handlers for all bot commands.
Each handler processes a specific command and provides appropriate responses.
"""

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from ..utils.logging_config import log_user_action, get_logger
from ..utils.config import get_settings
from .truth_wars_handlers import (
    start_truth_wars, join_game_callback, start_game_callback, 
    how_to_play_callback, vote_command, ability_command, status_command
)

# Logger setup
logger = get_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /start command.
    
    This is the first command users see when they start the bot.
    It provides a welcome message and basic instructions.
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Log user action
    log_user_action(user.id, "start_command", username=user.username)
    
    # Create custom keyboard for quick access to main features
    keyboard = [
        [KeyboardButton("🎮 Start Truth Wars"), KeyboardButton("📊 My Stats")],
        [KeyboardButton("🏆 Leaderboard"), KeyboardButton("❓ Help")],
        [KeyboardButton("🎯 How to Play"), KeyboardButton("⚙️ Settings")]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, 
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Choose an option or type a command..."
    )
    
    # Welcome message
    welcome_text = f"""
🕵️‍♂️ **Welcome to Truth Wars, {user.first_name}!** 🕵️‍♀️

🎯 **Learn to spot fake news while playing a fun social game!**

🚀 **QUICK START:**
1️⃣ Add me to a **group chat** (5-10 friends)
2️⃣ Type `/truthwars` to create a game
3️⃣ Everyone clicks "Join Game"  
4️⃣ Start playing & learning!

🎮 **WHAT IS TRUTH WARS?**
• 🎭 Get a **secret role** (Truth Seeker or Misinformer)
• 📰 Analyze **real news headlines** each round
• 🔍 Vote **Trust** or **Flag** based on your analysis
• 🧠 Learn **media literacy skills** from explanations
• 🏆 Your team wins by achieving the objective!

📊 **TRACK YOUR PROGRESS:**
📈 `/stats` - Your game statistics & learning progress
🏆 `/leaderboard` - Top misinformation detectives

❓ **NEED HELP?**
📚 `/help` - Complete guide with pro tips
🔤 `/play` - Other games (coming soon)

💡 **Ready to become a misinformation detective?** 
**Add me to a group chat and use `/truthwars` to start!**

**Use the menu below or type any command:**
    """
    
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=welcome_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        logger.info(f"Start command processed - user_id={user.id}, chat_id={chat_id}")
        
    except Exception as e:
        logger.error(f"Error in start command - user_id={user.id}, error={str(e)}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Sorry, something went wrong. Please try again later."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /help command.
    
    Provides detailed information about bot features and commands.
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Log user action
    log_user_action(user.id, "help_command", username=user.username)
    
    help_text = """
📖 **Truth Wars Bot - Complete Guide**

🎮 **QUICK START:**
1️⃣ Add bot to group chat (5-10 players)
2️⃣ Type `/truthwars` to create game
3️⃣ Everyone clicks "Join Game"
4️⃣ Creator clicks "Start Game"
5️⃣ Check private messages for your secret role!

**🕵️ GAME COMMANDS:**
• `/truthwars` - Create new game lobby (group chats only)
• `/status` - Check game phase & trigger events
• `/ability` - View your role & special powers
• `/vote` - Eliminate players (reply to their message)

**📊 PROGRESS TRACKING:**
• `/stats` - Your personal game statistics
• `/leaderboard` - Top misinformation detectives

**📋 GENERAL COMMANDS:**
• `/start` - Welcome message
• `/help` - This detailed guide

**🎯 HOW TO WIN:**
🔵 **Truth Seekers:** Identify & eliminate all misinformers
🔴 **Misinformers:** Survive until you equal/outnumber truth team

**📰 CORE GAMEPLAY:**
Each round you'll see a **news headline**. Your job:
• 🤔 **Analyze** - Is it real or fake news?
• 💬 **Discuss** - Share thoughts with others
• 🔍 **Investigate** - Use your role's special abilities
• 🗳️ **Vote** - Trust/Flag the headline as real/fake
• 📚 **Learn** - Get explanations & detection tips!

**🎭 EXAMPLE ROLES:**
📋 **Fact-Checker** - Investigate other players
🔬 **Researcher** - Verify news sources
📰 **Journalist** - Share insider knowledge
😈 **Scammer** - Spread misinformation secretly
🎭 **Deepfaker** - Create convincing lies
🧍 **Normie** - Learn through discussion

**🧠 EDUCATIONAL VALUE:**
• Learn **real media literacy skills**
• Practice **critical thinking**
• Understand **bias detection**
• Master **source verification**
• Develop **fact-checking habits**

**💡 PRO TIPS:**
• Pay attention to **source credibility**
• Look for **emotional language** (red flag!)
• Check if claims seem **too extreme**
• Ask **"Who benefits?"** from this story
• Cross-reference with **known facts**

**🎪 GAME FLOW:**
1️⃣ **Role Assignment** - Get secret role privately
2️⃣ **News Phase** - Headlines presented with Trust/Flag buttons
3️⃣ **Resolution** - Learn the truth + educational content
4️⃣ **Repeat** for 5 rounds total
5️⃣ **Victory** - One team wins & everyone learns!

Happy fact-checking! 🔍✨
    """
    
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=help_text,
            parse_mode='Markdown'
        )
        logger.info(f"Help command processed - user_id={user.id}, chat_id={chat_id}")
        
    except Exception as e:
        logger.error(f"Error in help command - user_id={user.id}, error={str(e)}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Sorry, something went wrong. Please try again later."
        )


async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /play command.
    
    This command starts a new game or allows joining an existing game.
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Log user action
    log_user_action(user.id, "play_command", username=user.username)
    
    play_text = """
🎮 **Game Selection**

**🕵️ Currently Available:**
• **Truth Wars** - Social deduction game that teaches media literacy
  Use `/truthwars` in a group chat to start!

**🔮 Coming Soon:**
• 🔤 Word Guessing Games
• 🧠 Trivia Challenges  
• 🧩 Logic Puzzles
• 🎯 Strategy Games
• 📰 Solo Fact-Check Training

**🎯 Ready to play Truth Wars?**
1. Add me to a group chat (5-10 friends)
2. Use `/truthwars` to create a game
3. Learn to spot fake news while having fun!

Check your `/stats` or view the `/leaderboard` to see your progress!
    """
    
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=play_text,
            parse_mode='Markdown'
        )
        logger.info(f"Play command processed - user_id={user.id}, chat_id={chat_id}")
        
    except Exception as e:
        logger.error(f"Error in play command - user_id={user.id}, error={str(e)}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Sorry, something went wrong. Please try again later."
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /stats command.
    
    Display user's personal game statistics.
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Log user action
    log_user_action(user.id, "stats_command", username=user.username)
    
    # Placeholder stats (will be replaced with real database queries)
    stats_text = f"""
📊 **Your Truth Wars Statistics**

👤 **Player:** {user.first_name}

🎮 **Game Stats:**
• **Games Played:** 0
• **Games Won:** 0
• **Win Rate:** 0%
• **Total Score:** 0

🧠 **Media Literacy Progress:**
• **Headlines Analyzed:** 0
• **Correct Identifications:** 0%
• **Detection Accuracy:** 0%
• **Learning Streak:** 0

🎭 **Favorite Roles:**
• **Most Played:** None yet
• **Best Performance:** None yet

🥇 **Best Game:** N/A

🏅 **Achievements:**
• No achievements yet - start playing to earn some!

💡 **Tip:** Use `/truthwars` in a group chat to start your first game!
    """
    
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=stats_text,
            parse_mode='Markdown'
        )
        logger.info(f"Stats command processed - user_id={user.id}, chat_id={chat_id}")
        
    except Exception as e:
        logger.error(f"Error in stats command - user_id={user.id}, error={str(e)}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Sorry, something went wrong. Please try again later."
        )


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /leaderboard command.
    
    Display the top players and their scores.
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Log user action
    log_user_action(user.id, "leaderboard_command", username=user.username)
    
    # Placeholder leaderboard (will be replaced with real database queries)
    leaderboard_text = """
🏆 **Truth Wars Leaderboard**

**🕵️ Top Misinformation Detectives:**
🥇 No players yet
🥈 No players yet  
🥉 No players yet

**🧠 Media Literacy Champions:**
📰 **Best Fact-Checkers:** None yet
🔍 **Most Accurate:** None yet
🎯 **Longest Streak:** None yet

**📊 Recent Activity:**
• No games played yet

**📍 Your Rank:** Not ranked yet

**🎮 Categories:**
• 🎭 **Role Mastery** - Best performance by role
• 🏅 **Win Rate** - Most successful players
• 📈 **Learning Progress** - Media literacy improvement

💡 **Ready to join the ranks?**
Use `/truthwars` in a group chat to start your detective career!
    """
    
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=leaderboard_text,
            parse_mode='Markdown'
        )
        logger.info(f"Leaderboard command processed - user_id={user.id}, chat_id={chat_id}")
        
    except Exception as e:
        logger.error(f"Error in leaderboard command - user_id={user.id}, error={str(e)}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Sorry, something went wrong. Please try again later."
        ) 