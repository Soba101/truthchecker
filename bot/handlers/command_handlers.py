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
    vote_command, ability_command, status_command
)

# Logger setup
logger = get_logger(__name__)

# Database imports for stats & leaderboard
from ..database.database import DatabaseSession
from ..database.models import User as UserModel
from sqlalchemy import select, desc, func


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
    
    # Concise help text – easier to read on mobile
    help_text = """
📖 **Truth Wars – Quick Guide**

🚀 **Start a Game**
1. Add the bot to a group (5-10 players)
2. Type `/truthwars`
3. Players tap **Join**, creator taps **Start**

🕹 **Core Commands**
`/truthwars` – create lobby  
`/ability` – your role info  
`/vote` – Trust/Flag a headline  
`/status` – current phase  
`/stats` – your stats  
`/leaderboard` – top players

🎮 **Round Flow** (5 rounds)
• Headline appears  
• Discuss & use abilities  
• Vote **Trust** or **Flag**  
• Truth + tips revealed

🔵 Truth Seekers win by finding all misinformers  
🔴 Misinformers win by staying hidden

💡 **Tip:** Check sources, spot emotional language, stay skeptical!
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
    
    Display user's personal game statistics from the database.
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Log user action
    log_user_action(user.id, "stats_command", username=user.username)
    
    try:
        # Query user stats from database
        async with DatabaseSession() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.id == user.id)
            )
            user_stats = result.scalar_one_or_none()
            
            if user_stats is None:
                # Create new user if they don't exist
                user_stats = UserModel(
                    id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    is_active=True
                )
                session.add(user_stats)
                await session.commit()
            
            # Determine most played role
            role_counts = {
                'Fact Checker': user_stats.times_as_fact_checker,
                'Scammer': user_stats.times_as_scammer,
                'Influencer': user_stats.times_as_influencer,
                'Drunk': user_stats.times_as_drunk,
                'Normie': user_stats.times_as_normie
            }
            most_played_role = max(role_counts, key=role_counts.get) if max(role_counts.values()) > 0 else "None yet"
            
            # Calculate role performance
            best_performance = "None yet"
            if user_stats.total_games > 0:
                # Simple heuristic: role with highest win rate
                truth_win_rate = (user_stats.truth_team_wins / max(user_stats.total_games, 1)) * 100
                scammer_win_rate = (user_stats.scammer_team_wins / max(user_stats.total_games, 1)) * 100
                if truth_win_rate > scammer_win_rate:
                    best_performance = "Truth Team Roles"
                elif scammer_win_rate > 0:
                    best_performance = "Scammer Team Roles"
            
            # Generate achievements based on stats
            achievements = []
            if user_stats.total_games >= 10:
                achievements.append("🎮 Veteran Player (10+ games)")
            if user_stats.win_rate >= 60:
                achievements.append("🏆 Skilled Player (60%+ win rate)")
            if user_stats.headline_accuracy >= 75:
                achievements.append("🔍 Sharp Detective (75%+ accuracy)")
            if user_stats.best_learning_streak >= 5:
                achievements.append("🔥 Learning Streak (5+ correct)")
            if user_stats.snipe_success_rate >= 70:
                achievements.append("🎯 Snipe Master (70%+ success)")
            if user_stats.media_literacy_level >= 5:
                achievements.append("🧠 Media Literate (Level 5+)")
            
            if not achievements:
                achievements_text = "• No achievements yet - start playing to earn some!"
            else:
                achievements_text = "\n".join([f"• {achievement}" for achievement in achievements])
            
            # Format best game info
            best_game_info = "N/A"
            if user_stats.total_games > 0:
                best_game_info = f"Best Streak: {user_stats.best_learning_streak} correct votes"
            
            stats_text = f"""
📊 **Your Truth Wars Statistics**

👤 **Player:** {user_stats.first_name or user.first_name}

🎮 **Game Stats:**
• **Games Played:** {user_stats.total_games}
• **Games Won:** {user_stats.total_wins}
• **Win Rate:** {user_stats.win_rate:.1f}%
• **Total Score:** {user_stats.total_reputation_earned} RP

🧠 **Media Literacy Progress:**
• **Headlines Analyzed:** {user_stats.headlines_voted_on}
• **Correct Identifications:** {user_stats.headline_accuracy:.1f}%
• **Detection Accuracy:** {user_stats.headline_accuracy:.1f}%
• **Learning Streak:** {user_stats.learning_streak}

🎭 **Favorite Roles:**
• **Most Played:** {most_played_role}
• **Best Performance:** {best_performance}

🥇 **Best Game:** {best_game_info}

🏅 **Achievements:**
{achievements_text}

💡 **Tip:** Use `/truthwars` in a group chat to start your first game!
            """
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=stats_text,
            parse_mode='Markdown'
        )
        logger.info(f"Stats command processed - user_id={user.id}, chat_id={chat_id}")
        
    except Exception as e:
        logger.error(f"Error in stats command - user_id={user.id}, error={str(e)}")
        # Fallback to basic message if database query fails
        await context.bot.send_message(
            chat_id=chat_id,
            text="📊 **Your Stats**\n\nSorry, unable to load your statistics right now. Please try again later."
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
    
    try:
        async with DatabaseSession() as session:
            # Top players by total wins
            result = await session.execute(
                select(UserModel).order_by(UserModel.total_wins.desc()).limit(10)
            )
            top_players = result.scalars().all()

            # Retrieve calling user's record for rank calculation
            user_record = await session.get(UserModel, user.id)

            if not top_players:
                leaderboard_text = "🏆 **Truth Wars Leaderboard**\n\nNo games played yet. Be the first to play!"
            else:
                medals = ["🥇", "🥈", "🥉"]
                lines_wins = []
                for idx, player in enumerate(top_players, start=1):
                    medal = medals[idx-1] if idx <= len(medals) else f"{idx}."
                    # Escape underscores in usernames to avoid Markdown parsing issues
                    username_display = (player.username or f"Player {player.id}").replace("_", "\\_")
                    lines_wins.append(
                        f"{medal} {username_display} — {player.total_wins} wins ({player.win_rate:.1f}% win rate)"
                    )

                # --- Top Win-Rate (min 5 games) ---
                win_rate_expr = (UserModel.total_wins * 1.0 / func.nullif(UserModel.total_games, 0))
                result_wr = await session.execute(
                    select(UserModel, win_rate_expr.label("wr"))
                    .where(UserModel.total_games >= 5)
                    .order_by(desc("wr"))
                    .limit(3)
                )
                top_wr = result_wr.fetchall()
                lines_wr = []
                for idx, (player, wr) in enumerate(top_wr, start=1):
                    medal = medals[idx-1] if idx <= len(medals) else f"{idx}."
                    # Escape underscores in usernames to avoid Markdown parsing issues
                    username_display = (player.username or f"Player {player.id}").replace("_", "\\_")
                    lines_wr.append(f"{medal} {username_display} — {wr*100:.1f}% win rate (\u2191 {player.total_games} games)")

                # --- Top Accuracy (min 20 votes) ---
                accuracy_expr = (UserModel.correct_votes * 1.0 / func.nullif(UserModel.headlines_voted_on, 0))
                result_acc = await session.execute(
                    select(UserModel, accuracy_expr.label("acc"))
                    .where(UserModel.headlines_voted_on >= 20)
                    .order_by(desc("acc"))
                    .limit(3)
                )
                top_acc = result_acc.fetchall()
                lines_acc = []
                for idx, (player, acc) in enumerate(top_acc, start=1):
                    medal = medals[idx-1] if idx <= len(medals) else f"{idx}."
                    # Escape underscores in usernames to avoid Markdown parsing issues
                    username_display = (player.username or f"Player {player.id}").replace("_", "\\_")
                    lines_acc.append(f"{medal} {username_display} — {acc*100:.1f}% accuracy")

                leaderboard_text = (
                    "🏆 **Truth Wars Leaderboard**\n\n"
                    "**Most Wins:**\n" + "\n".join(lines_wins) + "\n\n"
                    "**Best Win-Rate (≥5 games):**\n" + ("\n".join(lines_wr) if lines_wr else "No data yet") + "\n\n"
                    "**Highest Accuracy (≥20 votes):**\n" + ("\n".join(lines_acc) if lines_acc else "No data yet")
                )

                # User rank (by wins)
                if user_record and user_record.total_games > 0:
                    rank_result = await session.execute(
                        select(func.count()).select_from(UserModel).where(UserModel.total_wins > user_record.total_wins)
                    )
                    user_rank = rank_result.scalar_one() + 1
                    leaderboard_text += f"\n\n📍 **Your Rank (Wins):** {user_rank} (Wins: {user_record.total_wins})"

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
            text="🏆 Leaderboard unavailable right now. Please try again later."
        ) 