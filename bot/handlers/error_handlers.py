"""
Error Handlers

This module handles errors and exceptions that occur during bot operation.
It provides graceful error handling and user-friendly error messages.
"""

import traceback
from telegram import Update
from telegram.ext import ContextTypes

from ..utils.logging_config import get_logger
from ..utils.config import is_development

# Logger setup
logger = get_logger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle errors that occur during bot operation.
    
    This function logs errors and provides appropriate user feedback.
    In development, it shows detailed error information.
    
    Args:
        update: Telegram update object (may be None)
        context: Bot context containing error information
    """
    # Extract error information
    error = context.error
    error_message = str(error) if error else "Unknown error"
    
    # Get user and chat information if available
    user_id = None
    chat_id = None
    
    if isinstance(update, Update):
        if update.effective_user:
            user_id = update.effective_user.id
        if update.effective_chat:
            chat_id = update.effective_chat.id
    
    # Log the error with context
    update_type = type(update).__name__ if update else None
    tb = traceback.format_exc() if error else None
    logger.error(
        f"Bot error occurred - error_message={error_message}, user_id={user_id}, "
        f"chat_id={chat_id}, update_type={update_type}, traceback={tb}"
    )
    
    # Send user-friendly error message if we have a chat to send to
    if chat_id:
        try:
            if is_development():
                # In development, show detailed error for debugging
                error_text = f"""
🐛 **Development Error**

An error occurred: `{error_message}`

This detailed message is only shown in development mode.
                """
            else:
                # In production, show generic error message
                error_text = """
⚠️ **Something went wrong**

I encountered an error while processing your request. 
Please try again in a few moments.

If the problem persists, contact the bot administrator.
                """
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=error_text,
                parse_mode='Markdown'
            )
            
        except Exception as send_error:
            # If we can't even send an error message, log it
            logger.error(
                f"Failed to send error message to user - original_error={error_message}, "
                f"send_error={str(send_error)}, chat_id={chat_id}"
            )


async def handle_telegram_error(update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception) -> None:
    """
    Handle specific Telegram API errors.
    
    This function deals with common Telegram API errors like rate limiting,
    blocked users, deleted chats, etc.
    
    Args:
        update: Telegram update object
        context: Bot context
        error: The specific error that occurred
    """
    user_id = update.effective_user.id if update.effective_user else None
    chat_id = update.effective_chat.id if update.effective_chat else None
    
    error_type = type(error).__name__
    
    logger.warning(
        f"Telegram API error - error_type={error_type}, error_message={str(error)}, "
        f"user_id={user_id}, chat_id={chat_id}"
    )
    
    # Handle specific error types
    if "rate limit" in str(error).lower():
        logger.warning(f"Rate limit exceeded - user_id={user_id}")
        # Could implement retry logic here
        
    elif "blocked" in str(error).lower():
        logger.info(f"User has blocked the bot - user_id={user_id}")
        # Mark user as inactive in database
        
    elif "chat not found" in str(error).lower():
        logger.info(f"Chat no longer exists - chat_id={chat_id}")
        # Clean up any game states for this chat
        
    else:
        # For other errors, use the general error handler
        await error_handler(update, context) 