"""
Game Manager

This module orchestrates game sessions, manages player interactions,
and coordinates between different game types and the bot handlers.
"""

import uuid
from typing import Dict, Optional, Type, Any
from datetime import datetime, timedelta, timezone

from ..database.models import Game, GamePlayer, GameState, User, GameStatus
from ..database.database import DatabaseSession
from ..utils.logging_config import get_logger, log_game_event
from ..utils.config import get_settings

# Logger setup
logger = get_logger(__name__)


class GameManager:
    """
    Central game manager that orchestrates all game sessions.
    
    This class handles:
    - Creating new games
    - Managing player joining/leaving
    - Routing player actions to game instances
    - Saving/loading game state
    - Game lifecycle management
    """
    
    def __init__(self):
        """Initialize the game manager."""
        self.active_games: Dict[str, Any] = {}  # game_id -> game_instance
        self.user_games: Dict[int, str] = {}    # user_id -> game_id
        self.settings = get_settings()
    
    async def create_game(
        self, 
        game_type: str, 
        chat_id: int, 
        creator_user_id: int,
        settings: Optional[Dict] = None
    ) -> str:
        """
        Create a new game session.
        
        Args:
            game_type: Type of game to create
            chat_id: Telegram chat ID where game will be played
            creator_user_id: User ID of the game creator
            settings: Optional game-specific settings
            
        Returns:
            str: Game ID
        """
        try:
            # Create game record in database
            async with DatabaseSession() as session:
                # Create game
                game = Game(
                    game_type=game_type,
                    chat_id=chat_id,
                    settings=settings or {},
                    status="waiting"
                )
                session.add(game)
                await session.flush()  # Get the ID
                
                # Add creator as first player
                game_player = GamePlayer(
                    game_id=game.id,
                    user_id=creator_user_id
                )
                session.add(game_player)
                
                game_id = str(game.id)
            
            # Log game creation
            log_game_event(game_id, "game_created", 
                          game_type=game_type, creator=creator_user_id)
            
            # Track user's current game
            self.user_games[creator_user_id] = game_id
            
            logger.info("Game created", game_id=game_id, game_type=game_type)
            return game_id
            
        except Exception as e:
            logger.error("Failed to create game", error=str(e))
            raise
    
    async def join_game(self, game_id: str, user_id: int) -> bool:
        """
        Add a player to an existing game.
        
        Args:
            game_id: ID of the game to join
            user_id: User ID of the player joining
            
        Returns:
            bool: True if successfully joined, False otherwise
        """
        try:
            async with DatabaseSession() as session:
                # Get game
                game = await session.get(Game, game_id)
                if not game or game.status != "waiting":
                    return False
                
                # Check if game is full
                if game.is_full:
                    return False
                
                # Check if user is already in this game
                existing_player = await session.execute(
                    "SELECT * FROM game_players WHERE game_id = ? AND user_id = ?",
                    (game_id, user_id)
                )
                if existing_player.first():
                    return False
                
                # Add player
                game_player = GamePlayer(
                    game_id=game_id,
                    user_id=user_id
                )
                session.add(game_player)
            
            # Track user's current game
            self.user_games[user_id] = game_id
            
            log_game_event(game_id, "player_joined", user_id=user_id)
            logger.info("Player joined game", game_id=game_id, user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Failed to join game", game_id=game_id, user_id=user_id, error=str(e))
            return False
    
    async def start_game(self, game_id: str) -> bool:
        """
        Start a game if it has enough players.
        
        Args:
            game_id: ID of the game to start
            
        Returns:
            bool: True if game started successfully
        """
        try:
            async with DatabaseSession() as session:
                game = await session.get(Game, game_id)
                if not game or game.status != "waiting":
                    return False
                
                if not game.can_start:
                    return False
                
                # Update game status
                game.status = GameStatus.ACTIVE
                game.started_at = datetime.now(timezone.utc)
                
                # Create initial game state
                initial_state = GameState(
                    game_id=game_id,
                    state_data={"phase": "started", "turn": 1}
                )
                session.add(initial_state)
            
            log_game_event(game_id, "game_started")
            logger.info("Game started", game_id=game_id)
            return True
            
        except Exception as e:
            logger.error("Failed to start game", game_id=game_id, error=str(e))
            return False
    
    async def process_player_action(
        self, 
        user_id: int, 
        action: str, 
        data: Any = None
    ) -> Optional[Dict]:
        """
        Process a player action in their current game.
        
        Args:
            user_id: ID of the player taking action
            action: Type of action being taken
            data: Action data/parameters
            
        Returns:
            Optional[Dict]: Response data or None if no active game
        """
        # Check if user has an active game
        game_id = self.user_games.get(user_id)
        if not game_id:
            return None
        
        try:
            # For now, just log the action since specific games aren't implemented
            log_game_event(game_id, "player_action", 
                          user_id=user_id, action=action, data=data)
            
            logger.info("Player action processed", 
                       game_id=game_id, user_id=user_id, action=action)
            
            # Return a placeholder response
            return {
                "status": "acknowledged",
                "message": f"Action '{action}' received but not yet implemented.",
                "game_id": game_id
            }
            
        except Exception as e:
            logger.error("Failed to process player action", 
                        user_id=user_id, action=action, error=str(e))
            return None
    
    async def end_game(self, game_id: str, reason: str = "completed") -> bool:
        """
        End a game and clean up resources.
        
        Args:
            game_id: ID of the game to end
            reason: Reason for ending (completed, cancelled, timeout)
            
        Returns:
            bool: True if game ended successfully
        """
        try:
            async with DatabaseSession() as session:
                game = await session.get(Game, game_id)
                if not game:
                    return False
                
                # Update game status
                game.status = GameStatus.COMPLETED
                game.completed_at = datetime.now(timezone.utc)
            
            # Remove from active games
            if game_id in self.active_games:
                del self.active_games[game_id]
            
            # Remove users from game tracking
            users_to_remove = [uid for uid, gid in self.user_games.items() if gid == game_id]
            for user_id in users_to_remove:
                del self.user_games[user_id]
            
            log_game_event(game_id, "game_ended", reason=reason)
            logger.info("Game ended", game_id=game_id, reason=reason)
            return True
            
        except Exception as e:
            logger.error("Failed to end game", game_id=game_id, error=str(e))
            return False
    
    async def get_user_current_game(self, user_id: int) -> Optional[str]:
        """
        Get the current game ID for a user.
        
        Args:
            user_id: User ID to check
            
        Returns:
            Optional[str]: Game ID if user has active game, None otherwise
        """
        return self.user_games.get(user_id)
    
    async def cleanup_inactive_games(self) -> None:
        """
        Clean up games that have been inactive for too long.
        
        This should be called periodically to prevent resource leaks.
        """
        timeout_seconds = self.settings.game_session_timeout
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)
        
        try:
            async with DatabaseSession() as session:
                # Find inactive games
                inactive_games = await session.execute(
                    """
                    SELECT id FROM games 
                    WHERE status IN ('waiting', 'active') 
                    AND updated_at < ?
                    """,
                    (cutoff_time,)
                )
                
                for game_row in inactive_games:
                    game_id = str(game_row.id)
                    await self.end_game(game_id, "timeout")
            
            logger.info("Inactive games cleanup completed")
            
        except Exception as e:
            logger.error("Failed to cleanup inactive games", error=str(e))


# Global game manager instance
game_manager = GameManager() 