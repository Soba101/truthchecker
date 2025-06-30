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
                "game_over": False,  # Cache game over status to prevent repeated win condition checks
                "created_at": datetime.utcnow(),
                
                # Reputation System tracking
                "player_reputation": {},  # Will be populated when players join
                
                # Headline-based win condition tracking
                "win_progress": {
                    "fake_headlines_trusted": 0,    # Scammer win condition
                    "fake_headlines_flagged": 0,    # Truth team win condition
                    "rounds_completed": 0
                },
                
                # Additional tracking for RP calculations
                "headline_results": {
                    "fake_headlines_trusted": 0,
                    "fake_headlines_flagged": 0,
                    "real_headlines_trusted": 0,
                    "real_headlines_flagged": 0
                },
                
                # Drunk role rotation tracking
                "drunk_rotation": {
                    "current_drunk_id": None,      # Currently drunk player
                    "normie_ids": [],              # List of normie player IDs for rotation
                    "rotation_index": 0            # Current position in rotation
                },
                
                # Fact Checker balance - one round without info
                "fact_checker_no_info_round": None  # Will be set to random round 1-5
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
    
    async def join_game(self, game_id: str, user_id: int, username: str = None) -> Tuple[bool, str]:
        """
        Add a player to an existing game.
        
        Args:
            game_id: ID of the game to join
            user_id: User ID of the player joining
            username: Username of the player joining
            
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
                "username": username or f"Player {user_id}",
                "joined_at": datetime.utcnow()
            }
            
            # Initialize player reputation (starts with 3 RP as per design document)
            game_session["player_reputation"][user_id] = 3
            
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
            
            # Initialize drunk rotation system
            self._initialize_drunk_rotation(game_session)
            
            # Initialize fact checker balance (one round without info)
            self._initialize_fact_checker_balance(game_session)
            
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
            elif action == "vote_headline" and result.get("success"):
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
            "game_over": game_session.get("game_over", False)  # Use cached status instead of recalculating
        }
    
    async def _handle_vote(self, game_session: Dict, voter_id: int, vote_data: Any) -> None:
        """Handle a player vote on a headline."""
        # Check if player can vote (not a Ghost Viewer with 0 RP)
        if not self._can_player_vote(game_session, voter_id):
            logger.info(f"Player {voter_id} cannot vote - Ghost Viewer status (0 RP)")
            return
        
        vote_type = vote_data.get("vote_type")  # "trust" or "flag"
        headline_id = vote_data.get("headline_id")
        
        if vote_type and headline_id:
            game_session["votes"][voter_id] = {
                "vote_type": vote_type,
                "headline_id": headline_id
            }
            
            # Calculate if vote is correct based on headline truth
            current_headline = game_session.get("current_headline")
            is_correct = False
            if current_headline:
                headline_is_real = current_headline.get("is_real", True)
                # Correct if: (real headline + trust vote) OR (fake headline + flag vote)
                is_correct = (headline_is_real and vote_type == "trust") or (not headline_is_real and vote_type == "flag")
            
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
        # Check if player can use abilities (not a Ghost Viewer with 0 RP)
        if not self._can_player_use_ability(game_session, user_id):
            logger.info(f"Player {user_id} cannot use abilities - Ghost Viewer status (0 RP)")
            return
            
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
        # Rotate drunk role to next normie (if not round 1)
        current_round = game_session["round_number"]
        if current_round > 1:
            await self._rotate_drunk_role(game_session)
        
        headline = await self.get_random_headline()
        if headline:
            game_session["current_headline"] = {
                "id": headline.id,
                "text": headline.text,
                "is_real": headline.is_real,
                "source": headline.source,
                "explanation": headline.explanation
            }
            
            # Send correct answer to current drunk player
            await self._send_drunk_correct_answer(game_session)
            
            # Send info to Fact Checker (unless it's their no-info round)
            await self._send_fact_checker_info(game_session)
            
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
            
        # Collect voters by type and calculate weighted votes
        trust_voters = []
        flag_voters = []
        weighted_trust_votes = 0
        weighted_flag_votes = 0
        
        for voter_id, vote_data in votes.items():
            if isinstance(vote_data, dict):
                # Get voter's role to determine vote weight
                role_info = game_session["player_roles"].get(voter_id, {})
                role = role_info.get("role")
                vote_weight = role.get_vote_weight() if role and hasattr(role, 'get_vote_weight') else 1
                
                if vote_data.get("vote_type") == "trust":
                    trust_voters.append(voter_id)
                    weighted_trust_votes += vote_weight
                elif vote_data.get("vote_type") == "flag":
                    flag_voters.append(voter_id)
                    weighted_flag_votes += vote_weight
        
        # Determine majority vote using weighted counts (Influencer vote counts as 2)
        majority_trusts = weighted_trust_votes > weighted_flag_votes
        
        # Log vote weights for debugging
        logger.info(f"Vote count - Trust: {len(trust_voters)} voters ({weighted_trust_votes} weighted), Flag: {len(flag_voters)} voters ({weighted_flag_votes} weighted)")
        logger.info(f"Majority decision: {'TRUST' if majority_trusts else 'FLAG'} (based on weighted votes)")
        
        # Get current headline truth value
        current_headline = game_session.get("current_headline")
        if current_headline:
            headline_is_real = current_headline.get("is_real", True)
            
            # Update headline results tracking
            if headline_is_real and majority_trusts:
                game_session["headline_results"]["real_headlines_trusted"] += 1
            elif headline_is_real and not majority_trusts:
                game_session["headline_results"]["real_headlines_flagged"] += 1
            elif not headline_is_real and majority_trusts:
                game_session["headline_results"]["fake_headlines_trusted"] += 1
                # Update win progress for Scammers
                game_session["win_progress"]["fake_headlines_trusted"] += 1
            elif not headline_is_real and not majority_trusts:
                game_session["headline_results"]["fake_headlines_flagged"] += 1
                # Update win progress for Truth Team
                game_session["win_progress"]["fake_headlines_flagged"] += 1
            
            # Update player reputations based on votes
            vote_results = {
                "headline_is_real": headline_is_real,
                "majority_trusts": majority_trusts,
                "trust_voters": trust_voters,
                "flag_voters": flag_voters
            }
            await self._update_player_reputation(game_session, vote_results)
            
            # Check for win conditions after reputation update
            if self._check_headline_win_conditions(game_session):
                # Cache the game over status to prevent repeated checks
                game_session["game_over"] = True
                self._trigger_game_end(game_session)
                return
        
        # Update round counter and clear votes for next round
        game_session["round_number"] += 1
        game_session["win_progress"]["rounds_completed"] = game_session["round_number"] - 1
        game_session["votes"] = {}
    
    def _check_headline_win_conditions(self, game_session: Dict) -> bool:
        """Check headline-based win conditions as per design document."""
        win_progress = game_session["win_progress"]
        
        # Scammer win: 3 fake headlines trusted
        if win_progress["fake_headlines_trusted"] >= 3:
            game_session["winner"] = "misinformers"
            game_session["win_reason"] = "3 fake headlines trusted by majority"
            logger.info(f"Game {game_session['game_id']}: Scammers won - 3 fake headlines trusted")
            return True
        
        # Truth team win: 3 fake headlines flagged
        if win_progress["fake_headlines_flagged"] >= 3:
            game_session["winner"] = "truth_seekers"
            game_session["win_reason"] = "3 fake headlines flagged correctly"
            logger.info(f"Game {game_session['game_id']}: Truth Team won - 3 fake headlines flagged")
            return True
        
        # Truth team win: 5 rounds completed
        if win_progress["rounds_completed"] >= 5:
            game_session["winner"] = "truth_seekers"
            game_session["win_reason"] = "5 rounds completed without Scammer victory"
            logger.info(f"Game {game_session['game_id']}: Truth Team won - 5 rounds completed")
            return True
        
        # Check elimination-based backup win conditions
        alive_players = [pid for pid in game_session["players"].keys() 
                        if pid not in game_session["eliminated_players"]]
        
        # Don't check elimination win conditions if we have less than 2 players
        # This prevents single-player games from immediately ending
        if len(alive_players) >= 2:
            alive_truth_seekers = 0
            alive_misinformers = 0
            
            for player_id in alive_players:
                role_info = game_session["player_roles"].get(player_id)
                if role_info:
                    if role_info["faction"] == "truth_seekers":
                        alive_truth_seekers += 1
                    elif role_info["faction"] == "misinformers":
                        alive_misinformers += 1
            
            # Truth Seekers win if all Misinformers eliminated (but only if there were Misinformers to begin with)
            if alive_misinformers == 0 and alive_truth_seekers > 0:
                # Check if there were actually Misinformers in the game to begin with
                total_misinformers = 0
                for player_id in game_session["players"].keys():
                    role_info = game_session["player_roles"].get(player_id)
                    if role_info and role_info["faction"] == "misinformers":
                        total_misinformers += 1
                
                # Only trigger this win condition if there were actually Misinformers in the game
                if total_misinformers > 0:
                    game_session["winner"] = "truth_seekers"
                    game_session["win_reason"] = "All Scammers eliminated"
                    logger.info(f"Game {game_session['game_id']}: Truth Team won - all Scammers eliminated")
                    return True
                    
            # Misinformers win if all Truth Seekers eliminated
            if alive_truth_seekers == 0 and alive_misinformers > 0:
                game_session["winner"] = "misinformers"
                game_session["win_reason"] = "All Truth Seekers eliminated"
                logger.info(f"Game {game_session['game_id']}: Scammers won - all Truth Seekers eliminated")
                return True
        
        return False
    
    def _trigger_game_end(self, game_session: Dict) -> None:
        """Trigger immediate game end by transitioning to game end phase."""
        try:
            # Force transition to game end phase
            game_session["state_machine"].force_transition(
                PhaseType.GAME_END, 
                self._get_game_state(game_session)
            )
            
            # Mark game as over
            game_session["game_over"] = True
            
            logger.info(f"Game {game_session['game_id']} ended: {game_session.get('win_reason', 'Unknown reason')}")
            
        except Exception as e:
            logger.error(f"Failed to trigger game end: {e}")
    
    def _get_win_progress_display(self, game_session: Dict) -> str:
        """Generate progress display for current win conditions."""
        progress = game_session["win_progress"]
        
        return (
            f"📊 **Win Progress:**\n"
            f"🔴 **Scammers:** {progress['fake_headlines_trusted']}/3 fake headlines trusted\n"
            f"🔵 **Truth Team:** {progress['fake_headlines_flagged']}/3 fake headlines flagged\n"
            f"⏱️ **Round:** {progress['rounds_completed']}/5"
        )
    
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
    
    async def _handle_phase_transition(self, game_session: Dict, transition_result: Dict) -> None:
        """Handle phase transition by sending appropriate messages to chat."""
        try:
            from ..handlers.truth_wars_handlers import send_headline_voting
            
            new_phase = transition_result["to_phase"]
            start_result = transition_result.get("start_result", {})
            message = start_result.get("message")
            
            if not message:
                return
                
            # Get chat ID from bot context
            chat_id = game_session.get("chat_id")
            if not chat_id:
                logger.error(f"No chat_id found for game {game_session.get('game_id')}")
                return
            
            # Import bot context from handlers - this is a bit hacky but needed for now
            # TODO: Pass bot context properly through the manager
            bot_context = getattr(self, '_bot_context', None)
            if not bot_context:
                logger.warning("No bot context available for sending phase messages")
                return
            
            # Send basic phase message
            await bot_context.bot.send_message(
                chat_id=chat_id,
                text=message
            )
            
            # Handle special cases for specific phases
            if new_phase == "discussion":
                # Send voting buttons for headline during discussion phase
                current_headline = game_session.get("current_headline")
                if current_headline:
                    # Use chat_id instead of non-existent session_id
                    await send_headline_voting(bot_context, game_session["chat_id"], current_headline)
            
            elif new_phase == "voting":
                # Send player voting interface
                alive_players = [
                    player_data for pid, player_data in game_session["players"].items() 
                    if pid not in game_session["eliminated_players"]
                ]
                if len(alive_players) > 1:  # Only if there are players to vote for
                    await self._send_player_voting_interface(game_session, bot_context)
            
            elif new_phase == "resolution":
                # Send headline resolution results
                await self._send_headline_resolution(game_session, bot_context)
                
            elif new_phase == "game_end":
                # Send final results and role reveals
                await self._send_game_end_results(game_session, bot_context)
                
        except Exception as e:
            logger.error(f"Failed to handle phase transition: {e}")
            import traceback
            traceback.print_exc()
    
    async def _send_player_voting_interface(self, game_session: Dict, bot_context) -> None:
        """Send interface for players to vote each other out."""
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            alive_players = [
                (pid, player_data) for pid, player_data in game_session["players"].items() 
                if pid not in game_session["eliminated_players"]
            ]
            
            if len(alive_players) <= 1:
                return
            
            # Create voting buttons for each player
            keyboard = []
            for player_id, player_data in alive_players:
                username = player_data.get("username", f"Player {player_id}")
                button = InlineKeyboardButton(
                    f"Vote {username}",
                    callback_data=f"vote_player_{player_id}"
                )
                keyboard.append([button])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await bot_context.bot.send_message(
                chat_id=game_session["chat_id"],
                text="🗳️ **Vote for who you think is spreading misinformation:**",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Failed to send player voting interface: {e}")
    
    async def _send_headline_resolution(self, game_session: Dict, bot_context) -> None:
        """Send headline resolution results showing truth/false and voting results."""
        try:
            current_headline = game_session.get("current_headline")
            if not current_headline:
                logger.warning("No current headline for resolution")
                return
                
            votes = game_session.get("votes", {})
            
            # Build resolution message
            headline_text = current_headline.get("text", "Unknown headline")
            headline_is_real = current_headline.get("is_real", True)
            explanation = current_headline.get("explanation", "No explanation available")
            source = current_headline.get("source", "Unknown source")
            
            # Determine the correct answer and result
            correct_answer = "TRUST" if headline_is_real else "FLAG"
            truth_status = "✅ REAL" if headline_is_real else "❌ FAKE"
            
            resolution_text = f"📊 **HEADLINE RESOLUTION**\n\n"
            resolution_text += f"📰 **Headline:** {headline_text}\n\n"
            resolution_text += f"🎯 **Result:** {truth_status}\n"
            resolution_text += f"✅ **Correct Answer:** {correct_answer}\n\n"
            resolution_text += f"💡 **Explanation:**\n{explanation}\n\n"
            resolution_text += f"🔗 **Source:** {source}\n\n"
            
            # Show voting results with weighted counts
            resolution_text += "🗳️ **Voting Results:**\n"
            
            if votes:
                trust_voters = []
                flag_voters = []
                weighted_trust_votes = 0
                weighted_flag_votes = 0
                
                for voter_id, vote_data in votes.items():
                    # Get username for the voter
                    player_data = game_session["players"].get(voter_id, {})
                    username = player_data.get("username", f"Player {voter_id}")
                    
                    # Get voter's role to determine vote weight
                    role_info = game_session["player_roles"].get(voter_id, {})
                    role = role_info.get("role")
                    vote_weight = role.get_vote_weight() if role and hasattr(role, 'get_vote_weight') else 1
                    
                    if isinstance(vote_data, dict):
                        vote_type = vote_data.get("vote_type")
                        if vote_type == "trust":
                            # Add vote weight indicator for Influencer
                            if vote_weight > 1:
                                trust_voters.append(f"{username} (x{vote_weight})")
                            else:
                                trust_voters.append(username)
                            weighted_trust_votes += vote_weight
                        elif vote_type == "flag":
                            # Add vote weight indicator for Influencer
                            if vote_weight > 1:
                                flag_voters.append(f"{username} (x{vote_weight})")
                            else:
                                flag_voters.append(username)
                            weighted_flag_votes += vote_weight
                
                # Show who voted what with weighted totals
                if trust_voters:
                    resolution_text += f"🟢 **TRUSTED** ({len(trust_voters)} voters, {weighted_trust_votes} votes): {', '.join(trust_voters)}\n"
                else:
                    resolution_text += "🟢 **TRUSTED** (0 voters, 0 votes): No one\n"
                    
                if flag_voters:
                    resolution_text += f"🔴 **FLAGGED** ({len(flag_voters)} voters, {weighted_flag_votes} votes): {', '.join(flag_voters)}\n"
                else:
                    resolution_text += "🔴 **FLAGGED** (0 voters, 0 votes): No one\n"
                    
                # Show majority result based on weighted votes
                majority_result = "TRUST" if weighted_trust_votes > weighted_flag_votes else "FLAG"
                resolution_text += f"\n⚖️ **Majority Decision:** {majority_result} (based on weighted votes)\n"
                    
                # Show who was correct
                resolution_text += "\n🎯 **Correct Votes:**\n"
                correct_voters = trust_voters if headline_is_real else flag_voters
                incorrect_voters = flag_voters if headline_is_real else trust_voters
                
                if correct_voters:
                    resolution_text += f"✅ {', '.join(correct_voters)}\n"
                else:
                    resolution_text += "✅ No one voted correctly\n"
                    
                if incorrect_voters:
                    resolution_text += f"❌ {', '.join(incorrect_voters)}\n"
            else:
                resolution_text += "No votes were cast this round.\n"
            
            await bot_context.bot.send_message(
                chat_id=game_session["chat_id"],
                text=resolution_text
            )
            
        except Exception as e:
            logger.error(f"Failed to send headline resolution: {e}")
            import traceback
            traceback.print_exc()
    
    async def _send_game_end_results(self, game_session: Dict, bot_context) -> None:
        """Send final game results and role reveals."""
        try:
            # Build final results message with win reason
            win_reason = game_session.get("win_reason", "Game completed")
            winner = game_session.get("winner", "unknown")
            
            if winner == "misinformers":
                winner_emoji = "🔴"
                winner_name = "**SCAMMERS**"
            elif winner == "truth_seekers":
                winner_emoji = "🔵"
                winner_name = "**TRUTH TEAM**"
            else:
                winner_emoji = "🎯"
                winner_name = "**UNKNOWN**"
            
            results_text = f"🎉 **GAME OVER - FINAL RESULTS**\n\n"
            results_text += f"{winner_emoji} **WINNER:** {winner_name}\n"
            results_text += f"📄 **Reason:** {win_reason}\n\n"
            
            # Add win progress summary
            results_text += self._get_win_progress_display(game_session) + "\n\n"
            
            # Show all player roles
            results_text += "👥 **Role Reveals:**\n"
            for player_id, player_data in game_session["players"].items():
                username = player_data.get("username", f"Player {player_id}")
                role_info = game_session["player_roles"].get(player_id, {})
                
                # Get role name from role object
                role = role_info.get("role")
                role_name = role.name if role else "Unknown"
                faction = role_info.get("faction", "Unknown")
                
                status = "💀 Eliminated" if player_id in game_session["eliminated_players"] else "✅ Survived"
                current_rp = game_session["player_reputation"].get(player_id, 3)
                rp_status = "👻 Ghost Viewer" if current_rp == 0 else f"{current_rp} RP"
                results_text += f"• {username}: {role_name} ({faction}) - {status} - {rp_status}\n"
            
            # Show game statistics
            results_text += f"\n📊 **Game Stats:**\n"
            results_text += f"• Rounds played: {game_session['round_number']}\n"
            results_text += f"• Players eliminated: {len(game_session['eliminated_players'])}\n"
            
            # TODO: Determine winning faction and show win/loss
            results_text += "\n🎮 Type /truthwars to start a new game!"
            
            await bot_context.bot.send_message(
                chat_id=game_session["chat_id"],
                text=results_text
            )
            
        except Exception as e:
            logger.error(f"Failed to send game end results: {e}")
    
    async def _update_player_reputation(self, game_session: Dict, vote_results: Dict) -> None:
        """
        Update player reputation based on voting results.
        
        Args:
            game_session: Current game session
            vote_results: Dict with voting outcomes and headline truth value
                         Expected format: {
                             "headline_is_real": bool,
                             "majority_trusts": bool,
                             "trust_voters": [user_ids],
                             "flag_voters": [user_ids]
                         }
        """
        try:
            headline_is_real = vote_results["headline_is_real"]
            trust_voters = vote_results.get("trust_voters", [])
            flag_voters = vote_results.get("flag_voters", [])
            majority_trusts = vote_results["majority_trusts"]
            
            # Calculate RP changes for each voter
            reputation_changes = {}
            
            # Process TRUST voters
            for voter_id in trust_voters:
                current_rp = game_session["player_reputation"].get(voter_id, 3)
                if headline_is_real:
                    # Correct vote on real headline → +1 RP
                    new_rp = current_rp + 1
                    reputation_changes[voter_id] = {"change": +1, "reason": "Correctly trusted real headline"}
                else:
                    # Wrong vote on fake headline → -1 RP
                    new_rp = max(0, current_rp - 1)  # RP cannot go below 0
                    reputation_changes[voter_id] = {"change": -1, "reason": "Incorrectly trusted fake headline"}
                
                game_session["player_reputation"][voter_id] = new_rp
            
            # Process FLAG voters
            for voter_id in flag_voters:
                current_rp = game_session["player_reputation"].get(voter_id, 3)
                if not headline_is_real:
                    # Correct vote on fake headline → +1 RP
                    new_rp = current_rp + 1
                    reputation_changes[voter_id] = {"change": +1, "reason": "Correctly flagged fake headline"}
                else:
                    # Wrong vote on real headline → -1 RP
                    new_rp = max(0, current_rp - 1)  # RP cannot go below 0
                    reputation_changes[voter_id] = {"change": -1, "reason": "Incorrectly flagged real headline"}
                
                game_session["player_reputation"][voter_id] = new_rp
            
            # Scammer bonus: When majority votes wrong → +1 RP for all Scammers
            majority_is_correct = (headline_is_real and majority_trusts) or (not headline_is_real and not majority_trusts)
            if not majority_is_correct:
                for player_id, role_info in game_session["player_roles"].items():
                    role = role_info.get("role")
                    if role and role.faction == "misinformers":  # Scammers
                        current_rp = game_session["player_reputation"].get(player_id, 3)
                        new_rp = current_rp + 1
                        game_session["player_reputation"][player_id] = new_rp
                        reputation_changes[player_id] = reputation_changes.get(player_id, {"change": 0, "reason": ""})
                        reputation_changes[player_id]["change"] += 1
                        reputation_changes[player_id]["reason"] += " + Scammer bonus (majority voted wrong)"
            
            # Log reputation changes to database
            await self._log_reputation_changes(game_session, reputation_changes)
            
            # Check for new Ghost Viewers
            await self._check_ghost_viewer_status(game_session)
            
            logger.info(f"Reputation updated for game {game_session['game_id']}: {reputation_changes}")
            
        except Exception as e:
            logger.error(f"Failed to update player reputation: {e}")
            import traceback
            traceback.print_exc()
    
    async def _log_reputation_changes(self, game_session: Dict, reputation_changes: Dict) -> None:
        """Log reputation changes to the database."""
        try:
            if not reputation_changes:
                return
                
            # Get the actual UUID from the game session data
            actual_game_id = game_session["game_id"]
            current_round = game_session["round_number"]
            
            # For now, just log reputation changes to console
            # TODO: Implement proper database logging with game_player_id lookup
            for player_id, change_info in reputation_changes.items():
                if change_info["change"] == 0:
                    continue  # Skip if no actual change
                    
                # Get current reputation for logging
                current_rp = game_session["player_reputation"].get(player_id, 3)
                logger.info(f"Reputation change for player {player_id}: {change_info['change']} RP ({change_info['reason']}) - New RP: {current_rp}")
                
        except Exception as e:
            logger.error(f"Failed to log reputation changes: {e}")
    
    async def _check_ghost_viewer_status(self, game_session: Dict) -> None:
        """Check for players who became Ghost Viewers (0 RP) and notify."""
        try:
            new_ghost_viewers = []
            
            for player_id, reputation in game_session["player_reputation"].items():
                if reputation == 0:
                    player_data = game_session["players"].get(player_id, {})
                    username = player_data.get("username", f"Player {player_id}")
                    new_ghost_viewers.append(username)
            
            if new_ghost_viewers:
                # Notify about new Ghost Viewers
                bot_context = getattr(self, '_bot_context', None)
                if bot_context:
                    ghost_message = (
                        f"👻 **New Ghost Viewers!**\n\n"
                        f"Players with 0 RP can watch but cannot vote:\n"
                        f"• {', '.join(new_ghost_viewers)}\n\n"
                        f"💡 Vote accurately to maintain your reputation!"
                    )
                    
                    await bot_context.bot.send_message(
                        chat_id=game_session["chat_id"],
                        text=ghost_message
                    )
                    
        except Exception as e:
            logger.error(f"Failed to check Ghost Viewer status: {e}")
    
    def _can_player_vote(self, game_session: Dict, player_id: int) -> bool:
        """Check if player can vote (not Ghost Viewer)."""
        current_rp = game_session["player_reputation"].get(player_id, 3)
        return current_rp > 0
    
    def _can_player_use_ability(self, game_session: Dict, player_id: int) -> bool:
        """Check if player can use abilities (not Ghost Viewer)."""
        current_rp = game_session["player_reputation"].get(player_id, 3)
        return current_rp > 0
    
    def _initialize_drunk_rotation(self, game_session: Dict) -> None:
        """Initialize the drunk role rotation system after roles are assigned."""
        try:
            # Find all normie players (those who can become drunk)
            normie_ids = []
            initial_drunk_id = None
            
            for player_id, role_info in game_session["player_roles"].items():
                role = role_info.get("role")
                if role:
                    role_name = role.__class__.__name__
                    # Normies can become drunk; also include initial Drunk player
                    if role_name in ["Normie", "Drunk"]:
                        normie_ids.append(player_id)
                        if role_name == "Drunk":
                            initial_drunk_id = player_id
            
            # Set up rotation tracking
            game_session["drunk_rotation"]["normie_ids"] = normie_ids
            game_session["drunk_rotation"]["current_drunk_id"] = initial_drunk_id
            
            # Set initial rotation index based on current drunk
            if initial_drunk_id in normie_ids:
                game_session["drunk_rotation"]["rotation_index"] = normie_ids.index(initial_drunk_id)
            else:
                game_session["drunk_rotation"]["rotation_index"] = 0
                
            logger.info(f"Drunk rotation initialized: {len(normie_ids)} normies, current drunk: {initial_drunk_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize drunk rotation: {e}")
    
    async def _rotate_drunk_role(self, game_session: Dict) -> None:
        """Rotate the Drunk role to a different normie each round."""
        try:
            drunk_rotation = game_session["drunk_rotation"]
            normie_ids = drunk_rotation["normie_ids"]
            current_round = game_session["round_number"]
            
            if not normie_ids:
                logger.warning("No normies available for drunk rotation")
                return
                
            # Calculate new drunk player (rotate each round)
            new_rotation_index = (current_round - 1) % len(normie_ids)
            new_drunk_id = normie_ids[new_rotation_index]
            old_drunk_id = drunk_rotation["current_drunk_id"]
            
            # Only rotate if it's actually changing
            if new_drunk_id != old_drunk_id:
                # Update role assignments
                if old_drunk_id:
                    # Convert old drunk back to normie
                    old_role_info = game_session["player_roles"].get(old_drunk_id, {})
                    if old_role_info:
                        from ..game.roles import Normie
                        new_normie = Normie()
                        old_role_info["role"] = new_normie
                        logger.info(f"Player {old_drunk_id} is no longer drunk (converted back to normie)")
                
                # Convert new player to drunk
                new_role_info = game_session["player_roles"].get(new_drunk_id, {})
                if new_role_info:
                    from ..game.roles import Drunk
                    new_drunk = Drunk()
                    new_role_info["role"] = new_drunk
                    logger.info(f"Player {new_drunk_id} is now the drunk")
                
                # Update tracking
                drunk_rotation["current_drunk_id"] = new_drunk_id
                drunk_rotation["rotation_index"] = new_rotation_index
                
                # Notify players about the rotation
                await self._notify_drunk_rotation(game_session, old_drunk_id, new_drunk_id)
                
            else:
                logger.info(f"Drunk role staying with player {new_drunk_id} (no rotation needed)")
                
        except Exception as e:
            logger.error(f"Failed to rotate drunk role: {e}")
            import traceback
            traceback.print_exc()
    
    async def _notify_drunk_rotation(self, game_session: Dict, old_drunk_id: int, new_drunk_id: int) -> None:
        """Notify players about drunk role rotation."""
        try:
            bot_context = getattr(self, '_bot_context', None)
            if not bot_context:
                return
                
            # Get usernames
            old_username = "Unknown"
            new_username = "Unknown"
            
            if old_drunk_id:
                old_player_data = game_session["players"].get(old_drunk_id, {})
                old_username = old_player_data.get("username", f"Player {old_drunk_id}")
                
            if new_drunk_id:
                new_player_data = game_session["players"].get(new_drunk_id, {})
                new_username = new_player_data.get("username", f"Player {new_drunk_id}")
            
            # Send rotation notification to chat
            rotation_message = (
                f"🔄 **Drunk Role Rotation!**\n\n"
                f"🧍 **New Drunk:** {new_username}\n"
                f"💡 The drunk player receives inside information this round and should share source verification tips with everyone!\n\n"
                f"📚 **Educational Tip:** Always check multiple reliable sources before believing news!"
            )
            
            await bot_context.bot.send_message(
                chat_id=game_session["chat_id"],
                text=rotation_message
            )
            
            # Send private message to new drunk with their role info
            if new_drunk_id:
                private_message = (
                    f"🧍 **You are now the DRUNK for this round!**\n\n"
                    f"🎯 **Your role:**\n"
                    f"• You will receive the correct answer for this round's headline\n"
                    f"• Share source verification tips with the group\n"
                    f"• Help educate others about identifying reliable news\n\n"
                    f"💡 **Remember:** Your job is to help others learn media literacy skills!"
                )
                
                await bot_context.bot.send_message(
                    chat_id=new_drunk_id,
                    text=private_message
                )
                
        except Exception as e:
            logger.error(f"Failed to notify drunk rotation: {e}")
    
    async def _send_drunk_correct_answer(self, game_session: Dict) -> None:
        """Send the correct answer to the current drunk player."""
        try:
            drunk_rotation = game_session["drunk_rotation"]
            current_drunk_id = drunk_rotation.get("current_drunk_id")
            
            if not current_drunk_id:
                return
                
            current_headline = game_session.get("current_headline")
            if not current_headline:
                return
                
            bot_context = getattr(self, '_bot_context', None)
            if not bot_context:
                return
                
            headline_is_real = current_headline.get("is_real", True)
            headline_text = current_headline.get("text", "Unknown headline")
            explanation = current_headline.get("explanation", "No explanation available")
            
            correct_answer = "REAL" if headline_is_real else "FAKE"
            drunk_message = (
                f"🧍 **DRUNK INSIDE INFO**\n\n"
                f"📰 **Headline:** {headline_text}\n\n"
                f"🎯 **Correct Answer:** This headline is **{correct_answer}**\n\n"
                f"💡 **Explanation:** {explanation}\n\n"
                f"📚 **Your job:** Share source verification tips with the group during discussion!"
            )
            
            await bot_context.bot.send_message(
                chat_id=current_drunk_id,
                text=drunk_message
            )
            
            logger.info(f"Sent correct answer to drunk player {current_drunk_id}")
            
        except Exception as e:
            logger.error(f"Failed to send drunk correct answer: {e}")
    
    def _initialize_fact_checker_balance(self, game_session: Dict) -> None:
        """Initialize the Fact Checker balance by selecting one round where they get no info."""
        try:
            import random
            # Randomly select one round (1-5) where Fact Checker gets no information
            no_info_round = random.randint(1, 5)
            game_session["fact_checker_no_info_round"] = no_info_round
            
            logger.info(f"Fact Checker will not receive info in round {no_info_round}")
            
        except Exception as e:
            logger.error(f"Failed to initialize fact checker balance: {e}")
    
    async def _send_fact_checker_info(self, game_session: Dict) -> None:
        """Send correct answer to Fact Checker (unless it's their no-info round)."""
        try:
            current_round = game_session["round_number"]
            no_info_round = game_session.get("fact_checker_no_info_round")
            
            # Find the Fact Checker
            fact_checker_id = None
            for player_id, role_info in game_session["player_roles"].items():
                role = role_info.get("role")
                if role and role.__class__.__name__ == "FactChecker":
                    fact_checker_id = player_id
                    break
            
            if not fact_checker_id:
                return  # No Fact Checker in this game
                
            current_headline = game_session.get("current_headline")
            if not current_headline:
                return
                
            bot_context = getattr(self, '_bot_context', None)
            if not bot_context:
                return
            
            # Check if this is the no-info round
            if current_round == no_info_round:
                # Send "no info" message
                no_info_message = (
                    f"🧠 **FACT CHECKER - NO INFO ROUND**\n\n"
                    f"📰 **Headline:** {current_headline.get('text', 'Unknown headline')}\n\n"
                    f"❓ **This round, you must rely on your own knowledge and analysis skills!**\n\n"
                    f"🤔 You will not receive the correct answer this round.\n"
                    f"💡 Use your critical thinking to evaluate this headline like everyone else.\n\n"
                    f"🎯 **Tip:** Look for credible sources, check for bias, and consider the plausibility of the claim."
                )
                
                await bot_context.bot.send_message(
                    chat_id=fact_checker_id,
                    text=no_info_message
                )
                
                logger.info(f"Sent 'no info' message to Fact Checker {fact_checker_id} for round {current_round}")
                
            else:
                # Send correct answer as usual
                headline_is_real = current_headline.get("is_real", True)
                headline_text = current_headline.get("text", "Unknown headline")
                explanation = current_headline.get("explanation", "No explanation available")
                
                correct_answer = "REAL" if headline_is_real else "FAKE"
                fact_checker_message = (
                    f"🧠 **FACT CHECKER INTEL**\n\n"
                    f"📰 **Headline:** {headline_text}\n\n"
                    f"🎯 **Correct Answer:** This headline is **{correct_answer}**\n\n"
                    f"💡 **Explanation:** {explanation}\n\n"
                    f"🤫 **Your job:** Guide the discussion subtly without revealing your role!\n"
                    f"💭 Share your analysis in a way that seems natural and helps others reach the right conclusion."
                )
                
                await bot_context.bot.send_message(
                    chat_id=fact_checker_id,
                    text=fact_checker_message
                )
                
                logger.info(f"Sent correct answer to Fact Checker {fact_checker_id} for round {current_round}")
                
        except Exception as e:
            logger.error(f"Failed to send fact checker info: {e}")
    
    def set_bot_context(self, bot_context) -> None:
        """Set the bot context for sending messages."""
        self._bot_context = bot_context
    
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
                        
                        # Send phase transition message to chat
                        await self._handle_phase_transition(game_session, transition_result)
                        
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