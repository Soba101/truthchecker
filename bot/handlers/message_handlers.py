"""
Message Handlers

This module handles text messages that are not commands.
It processes user input during games and conversations.
"""

from telegram import Update
from telegram.ext import ContextTypes

from ..utils.logging_config import log_user_action, get_logger

# Logger setup
logger = get_logger(__name__)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle incoming text messages that are not commands.
    
    This handler processes user input during active games or conversations.
    It also handles custom keyboard button presses and enforces shadow ban restrictions.
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    if not update.message or not update.message.text:
        return
    user = update.effective_user
    chat_id = update.effective_chat.id
    message_text = update.message.text
    
    # Check for shadow ban enforcement in group chats during active games
    if chat_id < 0:  # Group chat (negative chat IDs)
        shadow_ban_handled = await _handle_shadow_ban_enforcement(update, context)
        if shadow_ban_handled:
            return  # Message was deleted due to shadow ban
    
    # Log user action
    log_user_action(
        user.id, 
        "text_message", 
        username=user.username,
        message_length=len(message_text)
    )
    
    # Handle custom keyboard button presses
    if message_text == "🎮 Start Truth Wars":
        from .truth_wars_handlers import start_truth_wars
        await start_truth_wars(update, context)
        return
    elif message_text == "📊 My Stats":
        from .command_handlers import stats_command
        await stats_command(update, context)
        return
    elif message_text == "🏆 Leaderboard":
        from .command_handlers import leaderboard_command
        await leaderboard_command(update, context)
        return
    elif message_text == "❓ Help":
        from .command_handlers import help_command
        await help_command(update, context)
        return
    elif message_text == "🎯 How to Play":
        await context.bot.send_message(
            chat_id=chat_id,
            text="""
📚 **How to Play Truth Wars**

👥 **Roles & Powers**
🧠 *Fact Checker* – Gets insider info (up to 3 peeks) and one-time **SNIPE**
😈 *Scammer* – Already knows real/fake and tries to mislead the group
🎭 *Influencer* – Your vote counts as **2** instead of 1
🧍 *Normie* – No powers, rely on critical thinking!

🔵 Truth Seekers – expose misinformers  
🔴 Misinformers – avoid detection

🌀 **Round Loop** (5 rounds)  
1️⃣ Headline appears  
2️⃣ Discuss & use `/ability`  
3️⃣ Vote **Trust** or **Flag**  
4️⃣ Truth + tips revealed

⚡ **Setup**  
• Add the bot to a group (5-10 players)  
• Type `/truthwars` → players join → start

💡 Verify sources, question sensational claims, think critically!
            """,
            parse_mode='Markdown'
        )
        return
    elif message_text == "⚙️ Settings":
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚙️ **Settings feature coming soon!**\n\nFor now, use the command menu or type commands directly.",
            parse_mode='Markdown'
        )
        return
    # Only respond to commands (messages starting with '/')
    if message_text.strip().startswith("/"):
        # Let the command handler process it (do nothing here)
        return
    # For all other messages, do nothing (ignore)
    return


async def _handle_shadow_ban_enforcement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Handle shadow ban enforcement for group messages during active games.
    
    Args:
        update: Telegram update object
        context: Bot context
        
    Returns:
        bool: True if message was handled (deleted), False if not
    """
    if not update.message or not update.effective_user:
        return False
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    try:
        # Check if there's an active game in this chat
        # Look for game data in chat_data
        current_game_id = context.chat_data.get('current_game_id')
        if not current_game_id:
            return False  # No active game, no shadow ban enforcement needed
        
        # Import here to avoid circular imports
        from .truth_wars_handlers import truth_wars_manager
        
        # Get current game status
        game_status = await truth_wars_manager.get_game_status(current_game_id)
        if not game_status:
            return False  # Game not found
        
        # Only enforce shadow ban during discussion phase
        current_phase = game_status.get("phase")
        if current_phase != "discussion":
            return False  # Not in discussion phase
        
        # Check if player is shadow banned
        game_session = truth_wars_manager.active_games.get(current_game_id)
        if not game_session:
            return False
        
        shadow_banned_players = game_session.get("shadow_banned_players", {})
        if user_id in shadow_banned_players and shadow_banned_players[user_id] > 0:
            # Player is shadow banned - delete their message
            try:
                await update.message.delete()
                logger.info(f"Deleted message from shadow banned player {user_id} in chat {chat_id}")
                
                # Send private notification to the shadow banned player
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=(
                            "🚫 **You are shadow banned!**\n\n"
                            "You cannot speak during discussion phases, but you can still vote on headlines.\n\n"
                            "💡 **Tip:** Use this time to think carefully about the headline before voting!"
                        ),
                        parse_mode='Markdown'
                    )
                except Exception as pm_error:
                    # User might have blocked the bot or disabled private messages
                    logger.debug(f"Could not send private message to shadow banned user {user_id}: {pm_error}")
                
                return True  # Message was handled (deleted)
                
            except Exception as delete_error:
                logger.error(f"Failed to delete message from shadow banned player {user_id}: {delete_error}")
                return False
        
        return False  # Player not shadow banned
        
    except Exception as e:
        logger.error(f"Error in shadow ban enforcement: {e}")
        return False