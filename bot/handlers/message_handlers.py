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
    It also handles custom keyboard button presses.
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    message_text = update.message.text
    
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
🎯 **How to Play Truth Wars**

**🎮 SETUP:**
1. Add bot to group (5-10 players)
2. Use `/truthwars` to create game
3. Players join & creator starts

**🎭 ROLES:**
• **Truth Seekers** - Identify fake news
• **Misinformers** - Spread confusion secretly

**📰 GAMEPLAY:**
1. View headline each round
2. Vote "Trust" or "Flag" 
3. Learn from explanations
4. Survive or eliminate threats

**🏆 WIN CONDITIONS:**
• Truth Seekers: Find all misinformers
• Misinformers: Outnumber truth seekers

Use `/help` for detailed guide!
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
    
    # Default response for other messages
    response_text = """
💬 I received your message, but I'm not sure what to do with it yet!

🎮 **To get started:**
• Use the menu buttons below
• Use `/truthwars` in a group to start a game
• Use `/help` for more information
• Use `/stats` to see your statistics

Once games are active, I'll be able to process your moves and responses during gameplay.
    """
    
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=response_text,
            parse_mode='Markdown'
        )
        logger.info(
            "Text message processed", 
            user_id=user.id, 
            chat_id=chat_id,
            message_preview=message_text[:50] + "..." if len(message_text) > 50 else message_text
        )
        
    except Exception as e:
        logger.error(f"Error handling text message - user_id={user.id}, error={str(e)}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Sorry, something went wrong processing your message."
        ) 