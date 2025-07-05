"""
Truth Wars Command Handlers

This module handles all Telegram bot commands and interactions for Truth Wars game.
It provides the interface between players and the game system.
"""

from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
import uuid
import asyncio
import telegram

from ..game.truth_wars_manager import TruthWarsManager
from ..utils.logging_config import get_logger
from ..database.models import User
from ..database.database import DatabaseSession

# Setup logger and manager
logger = get_logger(__name__)
truth_wars_manager = TruthWarsManager()


async def start_truth_wars(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /truthwars command to start a new game.
    
    This creates a new Truth Wars game lobby in the current chat.
    """
    # Safety check: ensure we have a message to reply to
    if not update.message:
        logger.warning("start_truth_wars called without a message object")
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Check if chat is suitable for group game
    if update.effective_chat.type == 'private':
        await update.message.reply_text(
            "❌ Truth Wars must be played in a group chat!\n\n"
            "Add me to a group and use /truthwars there to start a game."
        )
        return
    
    try:
        # Set bot context for the manager (needed for sending phase transition messages)
        truth_wars_manager.set_bot_context(context)
        
        # Ensure user exists in database
        await ensure_user_exists(update.effective_user)
        
        # Create new game
        game_id = await truth_wars_manager.create_game(chat_id, user_id)
        
        # Store game ID in context for this chat
        context.chat_data['current_game_id'] = game_id
        
        # Create lobby keyboard
        keyboard = [
            [InlineKeyboardButton("🎮 Join Game", callback_data=f"join_{game_id}")],
            [InlineKeyboardButton("▶️ Start Game", callback_data=f"start_{game_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🕵️‍♂️ **TRUTH WARS** 🕵️‍♀️\n\n"
            "🎮 **Game Lobby Created!**\n\n"
            "📋 **How it works:**\n"
            "• Players get secret roles (Truth Seekers vs Misinformers)\n"
            "• Analyze headlines to spot fake news\n" 
            "• Use abilities and vote out suspicious players\n"
            "• Truth Seekers win by eliminating all Misinformers\n\n"
            "👥 **Players needed:** 5-10\n"
            f"🆔 **Game ID:** `{game_id}`\n\n"
            "🎯 **Creator:** Click **Join Game** first, then start when ready!\n"
            "👫 **Everyone else:** Click **Join Game** to participate!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        logger.info(f"Truth Wars lobby created - game_id: {game_id}, chat_id: {chat_id}, creator: {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to start Truth Wars - chat_id: {chat_id}, user_id: {user_id}, error: {str(e)}")
        await update.message.reply_text(
            "❌ **Failed to create game**\n\n"
            "Something went wrong. Please try again in a moment."
        )


async def join_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle join game button callback."""
    query = update.callback_query
    
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Player"
    
    try:
        # Answer the callback first to avoid timeout
        await query.answer()
        
        # Parse game ID safely
        try:
            game_id = query.data.split('_')[1]
        except (IndexError, AttributeError):
            await query.answer("❌ Invalid game link", show_alert=True)
            return
        
        # Set bot context for the manager
        truth_wars_manager.set_bot_context(context)
        
        # Ensure user exists
        await ensure_user_exists(update.effective_user)
        
        # Attempt to join game
        success, message = await truth_wars_manager.join_game(game_id, user_id, user_name)
        
        if success:
            # Get game status for updated player count
            game_status = await truth_wars_manager.get_game_status(game_id)
            if not game_status:
                await query.answer("❌ Game not found", show_alert=True)
                return
            
            # Create updated keyboard
            keyboard = [
                [InlineKeyboardButton("🎮 Join Game", callback_data=f"join_{game_id}")],
                [InlineKeyboardButton("▶️ Start Game", callback_data=f"start_{game_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Update lobby message - use simpler formatting to avoid parsing issues
            updated_text = (
                f"🕵️‍♂️ TRUTH WARS 🕵️‍♀️\n\n"
                f"🎮 Game Lobby\n\n"
                f"📋 How it works:\n"
                f"• Players get secret roles (Truth Seekers vs Misinformers)\n"
                f"• Analyze headlines to spot fake news\n" 
                f"• Use abilities and vote out suspicious players\n"
                f"• Truth Seekers win by eliminating all Misinformers\n\n"
                f"👥 Players: {game_status['player_count']}/10\n"
                f"🆔 Game ID: {game_id}\n\n"
                f"✅ {user_name} joined the game!"
            )
            
            try:
                await query.edit_message_text(
                    updated_text,
                    reply_markup=reply_markup
                )
            except Exception as edit_error:
                # If message edit fails, try to send a new message
                logger.warning(f"Failed to edit message, sending new one: {edit_error}")
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=updated_text,
                    reply_markup=reply_markup
                )
            
            # Send private confirmation to the user
            try:
                confirmation_text = (
                    f"✅ Joined Truth Wars!\n\n"
                    f"Game ID: {game_id}\n"
                    f"Players: {game_status['player_count']}/10\n\n"
                    f"Wait for the game to start. You'll receive your secret role soon! 🤫"
                )
                
                await context.bot.send_message(
                    chat_id=user_id,
                    text=confirmation_text
                )
            except Exception as pm_error:
                # If private message fails, it's not critical
                logger.warning(f"Failed to send private confirmation to user {user_id}: {pm_error}")
            
        else:
            # Show failure message as alert instead of editing
            await query.answer(f"❌ {message}", show_alert=True)
            
    except Exception as e:
        logger.error(f"Failed to join game - game_id: {game_id if 'game_id' in locals() else 'unknown'}, user_id: {user_id}, error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        try:
            await query.answer("❌ Failed to join game. Please try again.", show_alert=True)
        except Exception as alert_error:
            logger.error(f"Failed to send error alert: {alert_error}")


async def start_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle start game button callback."""
    query = update.callback_query
    
    user_id = update.effective_user.id
    
    try:
        # Answer the callback first to avoid timeout
        await query.answer()
        
        # Parse game ID safely
        try:
            game_id = query.data.split('_')[1]
        except (IndexError, AttributeError):
            await query.answer("❌ Invalid game link", show_alert=True)
            return
        
        # Set bot context for the manager
        truth_wars_manager.set_bot_context(context)
        
        # Get game status to check if user can start
        game_status = await truth_wars_manager.get_game_status(game_id)
        
        if not game_status:
            await query.answer("❌ Game not found", show_alert=True)
            return
        
        # Check if enough players (reduced to 1 for testing)
        if game_status['player_count'] < 1:
            await query.answer(
                f"Need at least 1 player to start! Currently {game_status['player_count']}/1",
                show_alert=True
            )
            return
        
        # Try to start the game (this checks if user is creator)
        success, message = await truth_wars_manager.start_game(game_id, force_start=True, user_id=user_id)
        
        if success:
            # Update message with simpler formatting
            start_text = (
                "🎮 GAME STARTING!\n\n"
                "🎭 Roles are being assigned...\n\n"
                "📱 Check your private messages for your secret role!\n\n"
                "⏰ The game will begin in 60 seconds."
            )
            
            try:
                await query.edit_message_text(start_text)
            except Exception as edit_error:
                logger.warning(f"Failed to edit start message: {edit_error}")
                # If edit fails, send a new message
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=start_text
                )
            
            # Send role information to all players
            try:
                await send_role_assignments(context, game_id)
                
                # Start game progression after roles are sent
                import asyncio
                asyncio.create_task(trigger_game_progression(context, game_id))
                
            except Exception as role_error:
                logger.error(f"Failed to send role assignments: {role_error}")
            
        else:
            await query.answer(message, show_alert=True)
            
    except Exception as e:
        logger.error(f"Failed to start game - game_id: {game_id if 'game_id' in locals() else 'unknown'}, user_id: {user_id}, error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        try:
            await query.answer("❌ Failed to start game. Please try again.", show_alert=True)
        except Exception as alert_error:
            logger.error(f"Failed to send error alert: {alert_error}")



async def vote_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /vote command for eliminating players.
    
    Usage: /vote @username or /vote reply-to-message
    """
    # Safety check: ensure we have a message to reply to
    if not update.message:
        logger.warning("vote_command called without a message object")
        return
    
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text(
            "🗳️ **How to vote:**\n\n"
            "• `/vote @username` - Vote for a specific player\n"
            "• Reply to someone's message and type `/vote`\n\n"
            "You can change your vote anytime during the voting phase.",
            parse_mode='Markdown'
        )
        return
    
    # Get current game ID
    game_id = context.chat_data.get('current_game_id')
    if not game_id:
        await update.message.reply_text(
            "❌ No active Truth Wars game in this chat.\n"
            "Use /truthwars to start a new game."
        )
        return
    
    user_id = update.effective_user.id
    
    # Determine target
    target_id = None
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif context.args:
        # Try to parse @username (this would need username lookup)
        target_username = context.args[0].lstrip('@')
        # For now, show error - would need user lookup implementation
        await update.message.reply_text(
            "❌ **Username voting not yet implemented**\n\n"
            "Please reply to the player's message and use `/vote` instead.",
            parse_mode='Markdown'
        )
        return
    
    if not target_id:
        await update.message.reply_text(
            "❌ **No target specified**\n\n"
            "Reply to a player's message and use `/vote`.",
            parse_mode='Markdown'
        )
        return
    
    try:
        # Set bot context for the manager
        truth_wars_manager.set_bot_context(context)
        
        # Process vote through game manager
        result = await truth_wars_manager.process_player_action(
            game_id, user_id, "vote", {"target_id": target_id}
        )
        
        if result.get("success"):
            target_name = update.message.reply_to_message.from_user.first_name
            player_name_raw = update.effective_user.first_name or "Player"
            player_name = player_name_raw
            message_text = f"🗳️ {player_name} voted for player {target_id} as spreading misinformation."
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message_text
            )
        else:
            await update.message.reply_text(
                f"❌ **Vote failed**\n\n{result.get('message', 'Unknown error')}",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Failed to process vote - game_id: {game_id}, user_id: {user_id}, error: {str(e)}")
        await update.message.reply_text(
            "❌ **Failed to cast vote**\n\nPlease try again.",
            parse_mode='Markdown'
        )


async def ability_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /ability command for using role abilities.
    """
    # Safety check: ensure we have a message to reply to
    if not update.message:
        logger.warning("ability_command called without a message object")
        return
    
    # --- T12: Enforce private chat usage ---
    if update.effective_chat.type != 'private':
        await update.message.reply_text(
            "❌ Please use /ability in a private chat with me (open DM), not in the group chat."
        )
        return
    
    game_id = context.chat_data.get('current_game_id')
    if not game_id:
        await update.message.reply_text(
            "❌ No active Truth Wars game in this chat."
        )
        return
    
    user_id = update.effective_user.id
    
    # Get player's role info
    role_info = await truth_wars_manager.get_player_role_info(game_id, user_id)
    
    if not role_info:
        await update.message.reply_text(
            "❌ You are not in the current game or don't have a role assigned yet."
        )
        return
    
    # Set bot context for the manager
    truth_wars_manager.set_bot_context(context)
    
    # Attempt to use the role ability
    ability_result = await truth_wars_manager.use_role_ability(game_id, user_id)
    
    if ability_result["success"]:
        # Ability was successfully used
        await update.message.reply_text(
            f"✅ {ability_result['message']}",
            parse_mode='Markdown'
        )
    else:
        # Ability couldn't be used or already used
        await update.message.reply_text(
            f"❌ {ability_result['message']}"
        )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command to show game status."""
    # Safety check: ensure we have a message to reply to
    if not update.message:
        logger.warning("status_command called without a message object")
        return
    
    game_id = context.chat_data.get('current_game_id')
    if not game_id:
        await update.message.reply_text(
            "❌ No active Truth Wars game in this chat."
        )
        return
    
    try:
        # Set bot context for the manager
        truth_wars_manager.set_bot_context(context)
        
        # Check for pending notifications first
        notifications = await truth_wars_manager.get_pending_notifications(game_id)
        for notification in notifications:
            try:
                if notification["type"] == "headline_voting":
                    # Send headline with voting interface
                    await send_headline_voting(context, game_id, notification["headline"])
                else:
                    # Send regular text notification
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=notification["message"]
                    )
            except Exception as notify_error:
                logger.error(f"Failed to send notification: {notify_error}")
        
        game_status = await truth_wars_manager.get_game_status(game_id)
        
        if not game_status:
            await update.message.reply_text("❌ Game not found.")
            return
        
        # Phase emoji mapping for visual feedback
        phase_emojis = {
            "lobby": "🏠",
            "role_assignment": "🎭",
            "headline_reveal": "📰",
            "discussion": "💬",
            "voting": "🗳️",
            "round_results": "⚖️",
            "snipe_opportunity": "🎯",
            "game_end": "🏁"
        }
        
        phase = game_status['phase']
        emoji = phase_emojis.get(phase, "🎲")
        time_remaining = game_status['time_remaining']
        
        status_text = (
            f"📊 GAME STATUS\n\n"
            f"{emoji} Phase: {phase.replace('_', ' ').title()}\n"
            f"🔢 Round: {game_status['round_number']}\n"
            f"👥 Players: {game_status['player_count'] - game_status['eliminated_count']}"
            f"/{game_status['player_count']}\n"
            f"💀 Eliminated: {game_status['eliminated_count']}\n"
        )
        
        if time_remaining:
            minutes, seconds = divmod(time_remaining, 60)
            status_text += f"⏰ Time Remaining: {minutes:02d}:{seconds:02d}\n"
        
        if game_status['current_headline']:
            headline = game_status['current_headline']
            status_text += f"\n📰 Current Headline:\n{headline['text']}"
        
        await update.message.reply_text(status_text)
        
    except Exception as e:
        logger.error(f"Failed to get game status - game_id: {game_id}, error: {str(e)}")
        await update.message.reply_text("❌ Failed to get game status.")


async def send_role_assignments(context: ContextTypes.DEFAULT_TYPE, game_id: str) -> None:
    """Send role assignments to all players via private message."""
    try:
        # Get game status to find all players
        game_status = await truth_wars_manager.get_game_status(game_id)
        if not game_status:
            logger.error(f"Cannot send roles - game {game_id} not found")
            return
        
        # Get the active game session to access player list
        if game_id not in truth_wars_manager.active_games:
            logger.error(f"Cannot send roles - game session {game_id} not in active games")
            return
            
        game_session = truth_wars_manager.active_games[game_id]
        
        # Send role to each player
        for player_id in game_session["players"].keys():
            try:
                # Get this player's role information
                role_info = await truth_wars_manager.get_player_role_info(game_id, player_id)
                
                if role_info:
                    # Create role message with all the details
                    role_message = (
                        f"🎭 YOUR SECRET ROLE 🎭\n\n"
                        f"Role: {role_info['role_name']}\n"
                        f"Faction: {role_info['faction'].replace('_', ' ').title()}\n\n"
                        f"📋 Description:\n{role_info['description']}\n\n"
                        f"🎯 Win Condition:\n{role_info['win_condition']}\n\n"
                        f"🔧 Abilities:\n"
                    )
                    
                    # Add abilities list
                    if role_info['abilities']:
                        for ability in role_info['abilities']:
                            role_message += f"• {ability.replace('_', ' ').title()}\n"
                    else:
                        role_message += "• No special abilities\n"
                    
                    role_message += f"\n🎮 Game ID: {game_id}\n"
                    role_message += f"\n💡 Use /ability to activate your special abilities during the game!"
                    
                    # Send private message to player
                    await context.bot.send_message(
                        chat_id=player_id,
                        text=role_message
                    )
                    
                    logger.info(f"Role sent to player {player_id}: {role_info['role_name']}")
                    
                else:
                    logger.warning(f"No role info found for player {player_id} in game {game_id}")
                    
            except Exception as player_error:
                logger.error(f"Failed to send role to player {player_id}: {player_error}")
                # Continue with other players even if one fails
                continue
        
        logger.info(f"Role assignment completed for game {game_id}")
        
    except Exception as e:
        logger.error(f"Failed to send role assignments - game_id: {game_id}, error: {str(e)}")
        import traceback
        traceback.print_exc()


async def handle_truth_wars_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle all Truth Wars callback queries (button presses).
    
    This dispatches to specific handlers based on the callback data.
    """
    query = update.callback_query
    callback_data = query.data
    
    logger.info(f"Truth Wars callback received: {callback_data}")
    
    try:
        if callback_data.startswith("join_"):
            await join_game_callback(update, context)
        elif callback_data.startswith("start_"):
            await start_game_callback(update, context)
        elif callback_data.startswith("vote_trust_"):
            await handle_trust_vote(update, context)
        elif callback_data.startswith("vote_flag_"):
            await handle_flag_vote(update, context)
        elif callback_data.startswith("vote_player_"):
            await handle_vote_player_callback(update, context)
        elif callback_data.startswith("continue_game_"):
            await handle_continue_game_callback(update, context)
        elif callback_data.startswith("end_game_"):
            await handle_end_game_callback(update, context)
        elif callback_data.startswith("snipe_"):
            await handle_snipe_callback(update, context)
        else:
            logger.warning(f"Unhandled callback data: {callback_data}")
            await query.answer("❌ Unknown action", show_alert=True)
        
    except Exception as e:
        logger.error(f"Error handling Truth Wars callback: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            await query.answer("❌ Something went wrong. Please try again.", show_alert=True)
        except Exception as alert_error:
            logger.error(f"Failed to send error alert: {alert_error}")


async def handle_trust_vote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Trust vote on a headline."""
    query = update.callback_query
    user_id = update.effective_user.id
    # Ensure current_game_id is set
    game_id = context.chat_data.get('current_game_id')
    if not game_id:
        # Try to extract from callback_data
        try:
            game_id = query.data.split('_')[3]
            context.chat_data['current_game_id'] = game_id
        except Exception:
            await query.answer("❌ No active game found", show_alert=True)
            return
    
    try:
        # Set bot context for the manager
        truth_wars_manager.set_bot_context(context)
        
        # Extract headline ID from callback data
        headline_id = query.data.split('_')[2]
        
        # Register the vote ONLY (do not trigger phase transitions yet)
        result = await truth_wars_manager.register_vote_only(
            game_id, user_id, "trust", headline_id
        )
        
        if result.get("success"):
            await query.answer("✅ You voted TRUST", show_alert=False)
            # Send confirmation to chat immediately
            player_name = update.effective_user.first_name or "Player"
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"✅ {player_name} voted TRUST on the headline"
            )
            # Now check and advance phase (may send round results, etc.)
            await truth_wars_manager.check_and_advance_phase(game_id)
        else:
            # Improved: Also send a message to the group chat explaining why the vote was not counted
            error_message = result.get('message', 'Vote failed')
            await query.answer(f"❌ {error_message}", show_alert=True)
            # Only send to group if not a generic failure
            if error_message:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"❌ Vote not counted: {error_message}"
                )
        
    except Exception as e:
        logger.error(f"Failed to handle trust vote: {e}")
        await query.answer("❌ Failed to process vote", show_alert=True)


async def handle_flag_vote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Flag vote on a headline."""
    query = update.callback_query
    user_id = update.effective_user.id
    # Ensure current_game_id is set
    game_id = context.chat_data.get('current_game_id')
    if not game_id:
        # Try to extract from callback_data
        try:
            game_id = query.data.split('_')[3]
            context.chat_data['current_game_id'] = game_id
        except Exception:
            await query.answer("❌ No active game found", show_alert=True)
            return
    
    try:
        # Set bot context for the manager
        truth_wars_manager.set_bot_context(context)
        
        # Extract headline ID from callback data
        headline_id = query.data.split('_')[2]
        
        # Register the vote ONLY (do not trigger phase transitions yet)
        result = await truth_wars_manager.register_vote_only(
            game_id, user_id, "flag", headline_id
        )
        
        if result.get("success"):
            await query.answer("🚩 You voted FLAG", show_alert=False)
            # Send confirmation to chat immediately
            player_name = update.effective_user.first_name or "Player"
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🚩 {player_name} voted FLAG on the headline"
            )
            # Now check and advance phase (may send round results, etc.)
            await truth_wars_manager.check_and_advance_phase(game_id)
        else:
            # Improved: Also send a message to the group chat explaining why the vote was not counted
            error_message = result.get('message', 'Vote failed')
            await query.answer(f"❌ {error_message}", show_alert=True)
            if error_message:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"❌ Vote not counted: {error_message}"
                )
        
    except Exception as e:
        logger.error(f"Failed to handle flag vote: {e}")
        await query.answer("❌ Failed to process vote", show_alert=True)


async def send_headline_voting(context: ContextTypes.DEFAULT_TYPE, game_id: str, headline: Dict) -> None:
    """Send a headline with Trust/Flag voting buttons to the chat."""
    try:
        # Get game session to find chat ID
        if game_id not in truth_wars_manager.active_games:
            logger.error(f"Cannot send headline - game {game_id} not found")
            return
            
        game_session = truth_wars_manager.active_games[game_id]
        chat_id = game_session["chat_id"]
        
        # Create voting buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ TRUST", callback_data=f"vote_trust_{headline['id']}"),
                InlineKeyboardButton("🚩 FLAG", callback_data=f"vote_flag_{headline['id']}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Format combined headline and discussion message
        headline_message = (
            f"📰 **BREAKING NEWS**\n\n"
            f"**Headline:** {headline['text']}\n\n"
            f"**Source:** {headline['source']}\n\n"
            f"🤔 **What do you think?**\n"
            f"• **TRUST** = You believe this is real news\n"
            f"• **FLAG** = You think this is fake/misleading\n\n"
            f"💬 **Discussion Time!**\n"
            f"• Share your thoughts about the headline\n"
            f"• Vote TRUST or FLAG when you're ready\n"
            f"• Use your role abilities\n"
            f"• Watch for suspicious behavior\n\n"
            f"⏰ 3 minutes to discuss (or until everyone votes)!"
        )
        
        # Send headline to chat
        await context.bot.send_message(
            chat_id=chat_id,
            text=headline_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        logger.info(f"Headline sent to chat {chat_id} for game {game_id}")
        
    except Exception as e:
                 logger.error(f"Failed to send headline voting - game_id: {game_id}, error: {str(e)}")


async def trigger_game_progression(context: ContextTypes.DEFAULT_TYPE, game_id: str) -> None:
    """
    Trigger automatic game progression by checking status periodically.
    
    This function runs in the background and automatically advances
    the game phases and sends necessary notifications to players.
    """
    try:
        # Set bot context for the manager (critical for phase transition messages)
        truth_wars_manager.set_bot_context(context)
        
        logger.info(f"Starting game progression for game {game_id}")
        
        # Wait a moment for roles to be sent
        await asyncio.sleep(10)
        
        # Run status check periodically to trigger notifications
        for i in range(60):  # Run for up to 10 minutes
            try:
                # Get game status to check if game is still active
                game_status = await truth_wars_manager.get_game_status(game_id)
                
                if not game_status:
                    logger.info(f"Game {game_id} no longer exists, stopping progression")
                    break
                    
                if game_status.get("phase") == "game_end":
                    logger.info(f"Game {game_id} ended, stopping progression")
                    break
                
                # Check for pending notifications
                notifications = await truth_wars_manager.get_pending_notifications(game_id)
                
                for notification in notifications:
                    try:
                        # Get the chat ID for this game
                        if game_id in truth_wars_manager.active_games:
                            chat_id = truth_wars_manager.active_games[game_id]["chat_id"]
                            
                            if notification["type"] == "headline_voting":
                                # Send headline with voting interface
                                await send_headline_voting(context, game_id, notification["headline"])
                            else:
                                # Send regular text notification
                                await context.bot.send_message(
                                    chat_id=chat_id,
                                    text=notification["message"]
                                )
                        
                    except Exception as notify_error:
                        logger.error(f"Failed to send notification during progression: {notify_error}")
                
                # Wait 10 seconds before next check
                await asyncio.sleep(10)
                
            except Exception as loop_error:
                logger.error(f"Error in game progression loop: {loop_error}")
                await asyncio.sleep(10)  # Continue even if there's an error
                
        logger.info(f"Game progression completed for game {game_id}")
        
    except Exception as e:
        logger.error(f"Failed to run game progression for {game_id}: {e}")
        import traceback
        traceback.print_exc()


async def handle_continue_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle continue game button press."""
    query = update.callback_query
    user_id = update.effective_user.id
    callback_data = query.data
    
    # Extract game ID from callback data
    game_id = callback_data.split('_')[2]
    
    try:
        # Set bot context for the manager
        truth_wars_manager.set_bot_context(context)
        
        # Check if user is the game creator
        if game_id not in truth_wars_manager.active_games:
            await query.answer("❌ Game not found", show_alert=True)
            return
            
        game_session = truth_wars_manager.active_games[game_id]
        creator_id = game_session["creator_id"]
        
        if user_id != creator_id:
            await query.answer("❌ Only the game creator can continue the game", show_alert=True)
            return
            
        # Continue the game to next round
        result = await truth_wars_manager.continue_game(game_id)
        
        if result["success"]:
            await query.answer("▶️ Game continued to next round!", show_alert=False)
            
            # Send confirmation to chat
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="▶️ **Game Continued!**\n\nStarting next round..."
            )
            
            # Edit the message to remove buttons
            try:
                await query.edit_message_reply_markup(reply_markup=None)
            except Exception:
                pass  # Message might be too old to edit
                
        else:
            await query.answer(f"❌ {result.get('message', 'Failed to continue game')}", show_alert=True)
            
    except Exception as e:
        logger.error(f"Failed to handle continue game: {e}")
        await query.answer("❌ Failed to continue game", show_alert=True)


async def handle_end_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle end game button press."""
    query = update.callback_query
    user_id = update.effective_user.id
    callback_data = query.data
    
    # Extract game ID from callback data
    game_id = callback_data.split('_')[2]
    
    try:
        # Set bot context for the manager
        truth_wars_manager.set_bot_context(context)
        
        # Check if user is the game creator
        if game_id not in truth_wars_manager.active_games:
            await query.answer("❌ Game not found", show_alert=True)
            return
            
        game_session = truth_wars_manager.active_games[game_id]
        creator_id = game_session["creator_id"]
        
        if user_id != creator_id:
            await query.answer("❌ Only the game creator can end the game", show_alert=True)
            return
            
        # End the game
        result = await truth_wars_manager.end_game(game_id)
        
        if result["success"]:
            await query.answer("🛑 Game ended!", show_alert=False)
            
            # Edit the message to remove buttons
            try:
                await query.edit_message_reply_markup(reply_markup=None)
            except Exception:
                pass  # Message might be too old to edit
                
        else:
            await query.answer(f"❌ {result.get('message', 'Failed to end game')}", show_alert=True)
            
    except Exception as e:
        logger.error(f"Failed to handle end game: {e}")
        await query.answer("❌ Failed to end game", show_alert=True)


async def ensure_user_exists(telegram_user) -> None:
    """
    Ensure user exists in database.
    
    Creates user record if it doesn't exist.
    """
    try:
        # Create user in database if needed
        async with DatabaseSession() as session:
            user = await session.get(User, telegram_user.id)
            if not user:
                user = User(
                    id=telegram_user.id,
                    username=telegram_user.username,
                    first_name=telegram_user.first_name,
                    last_name=telegram_user.last_name
                )
                session.add(user)
                await session.commit()
                logger.info(f"Created user record - user_id: {telegram_user.id}, username: {telegram_user.username}")
            else:
                logger.debug(f"User exists - user_id: {telegram_user.id}, username: {telegram_user.username}")
                
    except Exception as e:
        logger.error(f"Failed to ensure user exists - user_id: {telegram_user.id}, error: {str(e)}")


async def handle_vote_player_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle voting for who is spreading misinformation (misinformation vote)."""
    query = update.callback_query
    user_id = update.effective_user.id
    callback_data = query.data

    # Extract the target player ID from the callback data
    try:
        target_id = int(callback_data.split('_')[2])
    except (IndexError, ValueError):
        await query.answer("❌ Invalid vote", show_alert=True)
        return

    # Get the current game ID
    game_id = context.chat_data.get('current_game_id')
    if not game_id:
        await query.answer("❌ No active game found", show_alert=True)
        return

    # Set bot context for the manager
    truth_wars_manager.set_bot_context(context)

    # Register the vote using the new 'vote_player' action
    result = await truth_wars_manager.process_player_action(
        game_id, user_id, "vote_player", {"target_id": target_id}
    )

    if result.get("success"):
        await query.answer("✅ Vote registered", show_alert=False)
        # Optionally, send a confirmation message to the chat
        player_name_raw = update.effective_user.first_name or "Player"
        player_name = player_name_raw
        message_text = f"🗳️ {player_name} voted for player {target_id} as spreading misinformation."
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message_text
        )
        # Optionally, check and advance phase if needed
        await truth_wars_manager.check_and_advance_phase(game_id)
    else:
        # Improved error feedback for wrong phase or duplicate vote
        error_message = result.get('message', 'Vote failed')
        await query.answer(f"❌ {error_message}", show_alert=True)
        if error_message:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"❌ Vote not counted: {error_message}"
            )


# === T11: Handle snipe callback from Fact Checker ===
async def handle_snipe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process inline button callback when Fact Checker selects a snipe target."""
    query = update.callback_query
    user_id = update.effective_user.id
    data = query.data  # Expected format: snipe_<targetId>_<gameId>
    try:
        _, target_id_str, game_id = data.split('_', 2)
        target_id = int(target_id_str)
    except ValueError:
        await query.answer("Invalid snipe data", show_alert=True)
        return

    # Ensure current_game_id context for convenience
    context.chat_data['current_game_id'] = game_id

    try:
        truth_wars_manager.set_bot_context(context)
        result = await truth_wars_manager.process_player_action(
            game_id,
            user_id,
            "use_ability",
            {"ability": "snipe", "target": target_id}
        )
        if result.get("success"):
            await query.answer("🎯 Snipe executed!", show_alert=False)
        else:
            await query.answer(f"❌ {result.get('message', 'Snipe failed')}", show_alert=True)
    except Exception as e:
        logger.error(f"Error processing snipe callback: {e}")
        await query.answer("❌ Snipe failed", show_alert=True) 