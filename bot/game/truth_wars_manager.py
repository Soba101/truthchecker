"""
Truth Wars Game Manager

This module manages Truth Wars game sessions, coordinating between the database,
role system, state machine, and bot interface. It handles the complete game lifecycle.
"""

import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio
import random

from ..database.models import (
    Game, GamePlayer, TruthWarsGame, PlayerRole, 
    Headline, HeadlineVote, PlayerReputationHistory, GameStatus
)
from ..database.database import DatabaseSession
from .roles import assign_roles, create_role_instance, Role
from .game_states import GameStateMachine, PhaseType
from ..utils.logging_config import get_logger, log_game_event
from ..utils.config import get_settings

# Setup logger
logger = get_logger(__name__)


class TruthWarsManager:
    """
    Central manager for Truth Wars game sessions.
    
    This coordinates all aspects of the game including:
    - Player management and role assignment
    - Game state transitions
    - Headline selection and presentation
    - Voting and elimination logic
    - Educational content delivery
    """
    
    def __init__(self):
        """Initialize the Truth Wars manager."""
        self.active_games: Dict[str, Dict] = {}  # game_id -> game_session_data
        self.settings = get_settings()
        self.bot_context = None  # Will be set by the bot handlers
        
    async def create_game(self, chat_id: int, creator_user_id: int, settings: Optional[Dict] = None) -> str:
        """
        Create a new Truth Wars game session.
        
        Args:
            chat_id: Telegram chat ID where game will be played
            creator_user_id: User ID of the game creator
            settings: Optional game configuration
            
        Returns:
            str: Game ID
        """
        try:
            # Create game with database support
            async with DatabaseSession() as session:
                # Create main game record
                game = Game(
                    game_type="truth_wars",
                    chat_id=chat_id,
                    max_players=10,
                    min_players=1,  # Allow 1 player for testing
                    settings=settings or {},
                    status=GameStatus.WAITING
                )
                session.add(game)
                await session.flush()  # Get the ID
                
                # Create Truth Wars specific record
                truth_wars_game = TruthWarsGame(
                    game_id=game.id,
                    settings=settings or {}
                )
                session.add(truth_wars_game)
                
                await session.commit()
                game_id = game.id
                game_id_str = str(game_id)
            
            # Initialize game session data
            self.active_games[game_id_str] = {
                "game_id": game_id,
                "chat_id": chat_id,
                "creator_id": creator_user_id,
                "players": {},  # Don't auto-add creator - let them join manually
                "player_roles": {},
                "state_machine": GameStateMachine(),
                "current_headline": None,
                "round_number": 1,
                "votes": {},
                "eliminated_players": [],
                "game_effects": {},  # Store temporary effects like troll ability
                "created_at": datetime.utcnow()
            }
            
            # Start the lobby phase
            lobby_result = self.active_games[game_id_str]["state_machine"].start_game()
            
            log_game_event(game_id_str, "truth_wars_created", creator=creator_user_id)
            logger.info(f"Truth Wars game created - game_id: {game_id}, creator: {creator_user_id}")
            
            # Start the game loop for automatic phase transitions
            asyncio.create_task(self._game_loop(game_id_str))
            
            return game_id_str
            
        except Exception as e:
            logger.error(f"Failed to create Truth Wars game - error: {str(e)}")
            raise
    
    async def join_game(self, game_id: str, user_id: int) -> Tuple[bool, str]:
        """
        Add a player to an existing game.
        
        Args:
            game_id: ID of the game to join
            user_id: User ID of the player joining
            
        Returns:
            Tuple: (success, message)
        """
        if game_id not in self.active_games:
            return False, "Game not found"
            
        game_session = self.active_games[game_id]
        
        # Check if game is in lobby phase
        if game_session["state_machine"].get_current_phase_type() != PhaseType.LOBBY:
            return False, "Game has already started"
            
        # Check if player already joined
        if user_id in game_session["players"]:
            return False, "You are already in this game"
            
        # Check if game is full
        if len(game_session["players"]) >= 10:
            return False, "Game is full (maximum 10 players)"
            
        try:
            # Get the actual UUID from the game session data
            actual_game_id = game_session["game_id"]
            
            # Add player to database
            async with DatabaseSession() as session:
                game_player = GamePlayer(
                    game_id=actual_game_id,
                    user_id=user_id
                )
                session.add(game_player)
                await session.commit()
            
            # Add to session data
            game_session["players"][user_id] = {
                "user_id": user_id,
                "joined_at": datetime.utcnow()
            }
            
            player_count = len(game_session["players"])
            log_game_event(game_id, "player_joined", user_id=user_id, player_count=player_count)
            
            return True, f"Joined game! ({player_count}/10 players)"
            
        except Exception as e:
            logger.error(f"Failed to join game - game_id: {game_id}, user_id: {user_id}, error: {str(e)}")
            return False, "Failed to join game"
    
    async def start_game(self, game_id: str, force_start: bool = False, user_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Start a Truth Wars game if conditions are met.
        
        Args:
            game_id: ID of the game to start
            force_start: Whether to force start with minimum players
            user_id: User ID trying to start the game (for permission check)
            
        Returns:
            Tuple: (success, message)
        """
        if game_id not in self.active_games:
            return False, "Game not found"
            
        game_session = self.active_games[game_id]
        
        # Check if user is the creator (only creator can start the game)
        if user_id is not None and user_id != game_session["creator_id"]:
            return False, "Only the game creator can start the game"
        
        player_count = len(game_session["players"])
        
        # Check minimum players (reduced to 1 for testing)
        if player_count < 1:
            return False, f"Need at least 1 player to start (currently {player_count})"
            
        # Check if already started
        current_phase = game_session["state_machine"].get_current_phase_type()
        if current_phase != PhaseType.LOBBY:
            return False, "Game has already started"
            
        try:
            # Get the actual UUID from the game session data
            actual_game_id = game_session["game_id"]
            
            # Update game status in database
            async with DatabaseSession() as session:
                game = await session.get(Game, actual_game_id)
                if game:
                    game.status = GameStatus.ACTIVE
                    game.started_at = datetime.utcnow()
                
                truth_wars_game = await session.get(TruthWarsGame, actual_game_id)
                if truth_wars_game:
                    truth_wars_game.phase = "role_assignment"
                    truth_wars_game.phase_end_time = datetime.utcnow() + timedelta(seconds=60)
            
            # Assign roles to players
            player_ids = list(game_session["players"].keys())
            role_assignments = assign_roles(player_ids)
            
            # Store role assignments
            game_session["player_roles"] = {}
            
            # Store roles in database and session
            async with DatabaseSession() as session:
                for player_id, role in role_assignments.items():
                    # Store in session data
                    game_session["player_roles"][player_id] = {
                        "role": role,
                        "faction": role.faction,
                        "is_alive": True
                    }
                    
                    # Create role record in database
                    from sqlalchemy import select
                    result = await session.execute(
                        select(GamePlayer.id).where(
                            GamePlayer.game_id == actual_game_id,
                            GamePlayer.user_id == player_id
                        )
                    )
                    game_player_row = result.first()
                    
                    if game_player_row:
                        player_role = PlayerRole(
                            game_player_id=game_player_row.id,
                            role_name=role.name.lower().replace("-", "_").replace(" ", "_"),
                            faction=role.faction
                        )
                        session.add(player_role)
                
                await session.commit()
            
            # Transition to role assignment phase
            game_session["state_machine"].force_transition(
                PhaseType.ROLE_ASSIGNMENT, 
                self._get_game_state(game_session)
            )
            
            log_game_event(game_id, "game_started", player_count=player_count)
            logger.info(f"Truth Wars game started - game_id: {game_id}, players: {player_count}")
            
            return True, "Game started! Role assignment in progress..."
            
        except Exception as e:
            logger.error(f"Failed to start game - game_id: {game_id}, error: {str(e)}")
            return False, "Failed to start game"
    
    async def get_random_headline(self, difficulty: str = "medium", category: Optional[str] = None) -> Optional[Headline]:
        """
        Get a random headline for the current round.
        
        Args:
            difficulty: Difficulty level (easy, medium, hard)
            category: Optional category filter
            
        Returns:
            Optional[Headline]: Selected headline or None if none available
        """
        try:
            # Try to get headline from database first
            async with DatabaseSession() as session:
                from sqlalchemy import select, func
                
                # Build query with filters
                query = select(Headline)
                if difficulty:
                    query = query.where(Headline.difficulty == difficulty)
                if category:
                    query = query.where(Headline.category == category)
                
                # Get random headline
                query = query.order_by(func.random()).limit(1)
                result = await session.execute(query)
                headline = result.scalar_one_or_none()
                
                if headline:
                    return headline
                    
            # Fallback to sample headlines if database is empty
            sample_headlines = [
                {
                    "text": "Scientists discover chocolate consumption linked to improved memory",
                    "is_real": True,
                    "source": "Nature Neuroscience",
                    "explanation": "This is based on a real study published in Nature Neuroscience about flavonoids in chocolate."
                },
                {
                    "text": "Breaking: Local man trains squirrels to deliver mail",
                    "is_real": False,
                    "source": "The Onion",
                    "explanation": "This is a satirical headline typical of The Onion, a known satire publication."
                },
                {
                    "text": "New AI system achieves 95% accuracy in detecting fake news",
                    "is_real": True,
                    "source": "MIT Technology Review",
                    "explanation": "This is based on recent research in AI-powered misinformation detection."
                },
                {
                    "text": "Study finds that eating pizza for breakfast is healthier than cereal",
                    "is_real": True,
                    "source": "Daily Mail",
                    "explanation": "This was actually reported by nutritionist Chelsey Amer, though the claim is somewhat misleading."
                },
                {
                    "text": "Scientists create method to turn plastic bottles into vanilla flavoring",
                    "is_real": True,
                    "source": "BBC Science",
                    "explanation": "Researchers at Edinburgh University developed this method using engineered bacteria."
                }
            ]
            
            selected = random.choice(sample_headlines)
            
            # Create a temporary headline object
            headline = type('Headline', (), {
                'id': str(uuid.uuid4()),
                'text': selected['text'],
                'is_real': selected['is_real'],
                'source': selected['source'],
                'explanation': selected['explanation'],
                'category': category or 'general',
                'difficulty': difficulty
            })()
            
            return headline
                
        except Exception as e:
            logger.error(f"Failed to get headline - error: {str(e)}")
            return None
    
    async def process_player_action(self, game_id: str, user_id: int, action: str, data: Any = None) -> Dict[str, Any]:
        """
        Process a player action in their current game.
        
        Args:
            game_id: ID of the game
            user_id: ID of the player taking action
            action: Type of action being taken
            data: Action data/parameters
            
        Returns:
            Dict: Response data
        """
        if game_id not in self.active_games:
            return {"success": False, "message": "Game not found"}
            
        game_session = self.active_games[game_id]
        
        # Check if player is in this game
        if user_id not in game_session["players"]:
            return {"success": False, "message": "You are not in this game"}
            
        # Check if player is eliminated
        if user_id in game_session["eliminated_players"]:
            return {"success": False, "message": "You have been eliminated from the game"}
            
        try:
            # Log the action
            await self._log_action(game_id, user_id, action, data)
            
            # Process action through state machine
            game_state = self._get_game_state(game_session)
            result = game_session["state_machine"].handle_action(action, user_id, data, game_state)
            
            # Handle specific actions
            if action == "vote" and result.get("success"):
                await self._handle_vote(game_session, user_id, data)
            elif action == "use_ability" and result.get("success"):
                await self._handle_ability_use(game_session, user_id, data)
            
            # Check for phase transitions
            await self._check_phase_transition(game_session)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process action - game_id: {game_id}, user_id: {user_id}, action: {action}, error: {str(e)}")
            return {"success": False, "message": "Failed to process action"}
    
    async def get_game_status(self, game_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a game.
        
        Args:
            game_id: Game ID
            
        Returns:
            Optional[Dict]: Game status or None if not found
        """
        if game_id not in self.active_games:
            return None
            
        game_session = self.active_games[game_id]
        current_phase = game_session["state_machine"].get_current_phase_type()
        time_remaining = game_session["state_machine"].get_time_remaining()
        
        return {
            "game_id": game_id,
            "phase": current_phase.value if current_phase else None,
            "time_remaining": time_remaining,
            "round_number": game_session["round_number"],
            "player_count": len(game_session["players"]),
            "eliminated_count": len(game_session["eliminated_players"]),
            "current_headline": game_session["current_headline"]
        }
    
    async def get_pending_notifications(self, game_id: str) -> List[Dict[str, Any]]:
        """
        Get and clear pending notifications for a game.
        
        Args:
            game_id: Game ID
            
        Returns:
            List[Dict]: Pending notifications
        """
        if game_id not in self.active_games:
            return []
            
        game_session = self.active_games[game_id]
        notifications = game_session.get("pending_notifications", [])
        game_session["pending_notifications"] = []  # Clear after retrieving
        
        return notifications
    
    async def get_player_role_info(self, game_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get role information for a specific player.
        
        Args:
            game_id: Game ID
            user_id: Player ID
            
        Returns:
            Optional[Dict]: Role information or None if not found
        """
        if game_id not in self.active_games:
            return None
            
        game_session = self.active_games[game_id]
        role_info = game_session["player_roles"].get(user_id)
        
        if not role_info:
            return None
            
        role = role_info["role"]
        return {
            "role_name": role.name,
            "faction": role.faction,
            "description": role.get_description(),
            "win_condition": role.get_win_condition(),
            "abilities": role.get_abilities(),
            "is_alive": role_info["is_alive"]
        }
    
    def _get_game_state(self, game_session: Dict) -> Dict[str, Any]:
        """
        Build complete game state dictionary.
        
        Args:
            game_session: Current game session data
            
        Returns:
            Dict: Complete game state
        """
        return {
            "active_players": [pid for pid in game_session["players"].keys() 
                             if pid not in game_session["eliminated_players"]],
            "all_players": list(game_session["players"].keys()),
            "eliminated_players": game_session["eliminated_players"],
            "player_roles": {pid: {"faction": info["faction"], "role": info["role"]} 
                           for pid, info in game_session["player_roles"].items()},
            "creator_id": game_session["creator_id"],
            "current_headline": game_session["current_headline"],
            "round_number": game_session["round_number"],
            "votes": game_session["votes"],
            "game_effects": game_session["game_effects"],
            "force_start": game_session.get("force_start", False),
            "all_players_ready": False,  # TODO: Implement ready system
            "all_players_voted": len(game_session["votes"]) == len([pid for pid in game_session["players"].keys() 
                                                                   if pid not in game_session["eliminated_players"]]),
            "all_roles_assigned": len(game_session["player_roles"]) == len(game_session["players"]),
            "game_over": self._check_win_conditions(game_session)
        }
    
    async def _handle_vote(self, game_session: Dict, voter_id: int, vote_data: Any) -> None:
        """Handle a player vote on a headline."""
        vote_type = vote_data.get("vote_type")  # "trust" or "flag"
        headline_id = vote_data.get("headline_id")
        
        if vote_type and headline_id:
            game_session["votes"][voter_id] = {
                "vote_type": vote_type,
                "headline_id": headline_id
            }
            
            # TODO: Calculate if vote is correct based on headline truth
            is_correct = True  # Placeholder - implement actual logic
            
            # Log headline vote to database
            await self._log_headline_vote(
                game_session["game_id"], 
                voter_id, 
                headline_id, 
                vote_type, 
                is_correct
            )
    
    async def _handle_ability_use(self, game_session: Dict, user_id: int, ability_data: Any) -> None:
        """Handle a role ability use."""
        role_info = game_session["player_roles"].get(user_id)
        if not role_info:
            return
            
        role = role_info["role"]
        ability = ability_data.get("ability")
        target = ability_data.get("target")
        
        # Check if it's a snipe ability and if the role can use it
        if ability == "snipe" and role.can_use_snipe():
            game_state = self._get_game_state(game_session)
            result = role.use_snipe(target, game_state)
            
            # Apply ability effects
            if result.get("success"):
                await self._apply_ability_effects(game_session, result)
    
    async def _check_phase_transition(self, game_session: Dict) -> None:
        """Check if current phase should transition."""
        game_state = self._get_game_state(game_session)
        
        if game_session["state_machine"].can_transition(game_state):
            transition_result = game_session["state_machine"].transition_phase(game_state)
            
            if transition_result:
                # Handle phase-specific transitions
                new_phase = transition_result["to_phase"]
                
                if new_phase == "news":
                    await self._start_news_phase(game_session)
                elif new_phase == "resolution":
                    await self._resolve_voting(game_session)
    
    async def _start_news_phase(self, game_session: Dict) -> None:
        """Start a new news phase with a fresh headline."""
        headline = await self.get_random_headline()
        if headline:
            game_session["current_headline"] = {
                "id": headline.id,
                "text": headline.text,
                "is_real": headline.is_real,
                "source": headline.source,
                "explanation": headline.explanation
            }
            
            # Add a notification for the bot to send voting interface
            game_session["pending_notifications"] = game_session.get("pending_notifications", [])
            game_session["pending_notifications"].append({
                "type": "headline_voting",
                "headline": {
                    "id": headline.id,
                    "text": headline.text,
                    "source": headline.source,
                    "is_real": headline.is_real,
                    "explanation": headline.explanation
                },
                "message": "📰 New headline posted! Read carefully and vote!"
            })
            
            logger.info(f"News phase started for game {game_session['game_id']} with headline: {headline.text[:50]}...")
        else:
            logger.warning(f"No headline available for game {game_session['game_id']} news phase")
    
    async def _resolve_voting(self, game_session: Dict) -> None:
        """Resolve headline voting and update reputation."""
        votes = game_session["votes"]
        
        if not votes:
            return
            
        # Count Trust vs Flag votes
        trust_votes = 0
        flag_votes = 0
        
        for vote_data in votes.values():
            if isinstance(vote_data, dict):
                if vote_data.get("vote_type") == "trust":
                    trust_votes += 1
                elif vote_data.get("vote_type") == "flag":
                    flag_votes += 1
        
        # Determine majority vote
        majority_trusts = trust_votes > flag_votes
        
        # Get current headline truth value
        current_headline = game_session.get("current_headline")
        if current_headline:
            headline_is_real = current_headline.get("is_real", True)
            
            # Update win condition counters
            if headline_is_real and majority_trusts:
                # Real headline trusted correctly - no change to win counters
                pass
            elif not headline_is_real and not majority_trusts:
                # Fake headline flagged correctly - Truth team progress
                # This would be tracked in the Game model
                pass
            elif not headline_is_real and majority_trusts:
                # Fake headline trusted - Scammer team progress
                # This would be tracked in the Game model
                pass
            
            # TODO: Update individual player reputations based on their votes
        
        # Clear votes for next round
        game_session["votes"] = {}
        game_session["round_number"] += 1
    
    def _check_win_conditions(self, game_session: Dict) -> bool:
        """Check if any faction has won the game."""
        alive_players = [pid for pid in game_session["players"].keys() 
                        if pid not in game_session["eliminated_players"]]
        
        if not alive_players:
            return True
            
        alive_truth_seekers = 0
        alive_misinformers = 0
        
        for player_id in alive_players:
            role_info = game_session["player_roles"].get(player_id)
            if role_info:
                if role_info["faction"] == "truth_seekers":
                    alive_truth_seekers += 1
                elif role_info["faction"] == "misinformers":
                    alive_misinformers += 1
        
        # Truth Seekers win if all Misinformers eliminated
        if alive_misinformers == 0:
            return True
            
        # Misinformers win if they equal or outnumber Truth Seekers
        if alive_misinformers >= alive_truth_seekers:
            return True
            
        return False
    
    async def _log_action(self, game_id: str, player_id: int, action_type: str, data: Any) -> None:
        """Log a player action to the database."""
        try:
            # For now, just log to console since GameAction model may not be implemented yet
            logger.info(f"Action logged - game_id: {game_id}, player_id: {player_id}, action: {action_type}")
            
            # TODO: Implement GameAction model and uncomment when ready
            # async with DatabaseSession() as session:
            #     game_action = GameAction(
            #         game_id=int(game_id),
            #         player_id=player_id,
            #         action_type=action_type,
            #         action_data=data,
            #         round_number=self.active_games[game_id]["round_number"],
            #         phase=self.active_games[game_id]["state_machine"].get_current_phase_type().value
            #     )
            #     session.add(game_action)
            #     await session.commit()
        except Exception as e:
            logger.error(f"Failed to log action - error: {str(e)}")
    
    async def _log_headline_vote(self, game_id: str, voter_id: int, headline_id: str, vote_type: str, is_correct: bool) -> None:
        """Log a headline vote to the database."""
        try:
            # Get the actual UUID from the game session data
            game_session = self.active_games.get(game_id)
            if not game_session:
                logger.error(f"Game session not found for game_id: {game_id}")
                return
            actual_game_id = game_session["game_id"]
            
            # Log headline vote to database
            async with DatabaseSession() as session:
                from ..database.models import VoteType
                vote = HeadlineVote(
                    game_id=actual_game_id,
                    user_id=voter_id,
                    headline_id=headline_id,
                    vote=VoteType.TRUST if vote_type == "trust" else VoteType.FLAG,
                    is_correct=is_correct,
                    round_number=self.active_games[game_id]["round_number"],
                    voter_reputation_before=3,  # TODO: Get from player data
                    voter_reputation_after=3   # TODO: Calculate based on vote result
                )
                session.add(vote)
                await session.commit()
                
            logger.info(f"Headline vote logged - game_id: {game_id}, voter_id: {voter_id}, vote: {vote_type}")
        except Exception as e:
            logger.error(f"Failed to log headline vote - error: {str(e)}")
    
    async def _apply_ability_effects(self, game_session: Dict, ability_result: Dict) -> None:
        """Apply the effects of a role ability."""
        # Store temporary effects
        if "effect" in ability_result:
            effect_name = ability_result["effect"]
            duration = ability_result.get("duration_rounds", 1)
            
            game_session["game_effects"][effect_name] = {
                "duration": duration,
                "expires_round": game_session["round_number"] + duration,
                "data": ability_result
            }
    
    async def _game_loop(self, game_id: str) -> None:
        """
        Main game loop that handles automatic phase transitions.
        
        This runs continuously for each game, checking if phases should
        transition based on time limits or game conditions.
        """
        try:
            while game_id in self.active_games:
                game_session = self.active_games[game_id]
                current_phase = game_session["state_machine"].get_current_phase_type()
                
                # Stop loop if game ended
                if current_phase == PhaseType.GAME_END:
                    logger.info(f"Game loop ending for game {game_id} - game finished")
                    break
                
                # Check if phase should transition
                game_state = self._get_game_state(game_session)
                if game_session["state_machine"].can_transition(game_state):
                    transition_result = game_session["state_machine"].transition_phase(game_state)
                    
                    if transition_result:
                        new_phase = transition_result["to_phase"]
                        logger.info(f"Game {game_id} transitioned to phase: {new_phase}")
                        
                        # Handle specific phase transitions
                        if new_phase == "news":
                            await self._start_news_phase(game_session)
                        elif new_phase == "resolution":
                            await self._resolve_voting(game_session)
                
                # Wait 5 seconds before next check
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"Game loop error for game {game_id}: {e}")
            import traceback
            traceback.print_exc()
    
    async def cleanup_finished_games(self) -> None:
        """Remove finished games from memory."""
        finished_games = []
        
        for game_id, game_session in self.active_games.items():
            # Remove games that ended more than 1 hour ago
            if (datetime.utcnow() - game_session["created_at"]) > timedelta(hours=1):
                current_phase = game_session["state_machine"].get_current_phase_type()
                if current_phase == PhaseType.GAME_END:
                    finished_games.append(game_id)
        
        for game_id in finished_games:
            del self.active_games[game_id]
            logger.info(f"Cleaned up finished game - game_id: {game_id}") 