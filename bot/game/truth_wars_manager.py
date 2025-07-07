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
from .refined_game_states import RefinedGameStateMachine, PhaseType
from ..utils.logging_config import get_logger, log_game_event
from ..utils.config import get_settings
from ..database.seed_data import get_media_literacy_tip
from ..ai.headline_generator import get_headline_generator
from sqlalchemy.sql import func

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
                "state_machine": RefinedGameStateMachine(),
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
                
                # v3 team scoring (first to 3 points)
                "team_scores": {
                    "truth": 0,
                    "scam": 0
                },
                
                # Drunk role rotation tracking
                "drunk_rotation": {
                    "current_drunk_id": None,      # Currently drunk player
                    "normie_ids": [],              # List of normie player IDs for rotation
                    "rotation_index": 0            # Current position in rotation
                },
                
                # Fact Checker balance - one round without info
                "fact_checker_no_info_round": None,  # Will be set to random round 1-5
                
                # Shadow ban system tracking
                "shadow_banned_players": {},  # {player_id: rounds_remaining}
                "snipe_abilities_used": [],  # Track which players used snipe abilities
                # === NEW: elimination cap tracking ===
                "elimination_limit": None,   # Will be set once game starts
                "eliminations_total": 0,     # Count of all shadow bans (vote or snipe)
                "snipe_used_this_round": False  # Reset each round
            }
            
            # === NEW: set elimination cap based on player count ===
            game_session["elimination_limit"] = max(0, len(game_session["players"]) - 2)
            # Ensure counters start fresh
            game_session["eliminations_total"] = 0
            game_session["snipe_used_this_round"] = False
            
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
            
            # Prepare headline pool according to v3 distribution rules (Set A/B)
            await self._prepare_headline_set(game_session)
            
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
        
        This method uses a hybrid approach:
        1. Try AI headline generation (if enabled and available)
        2. Fallback to database headlines
        3. Final fallback to sample headlines
        
        Args:
            difficulty: Difficulty level (easy, medium, hard)
            category: Optional category filter
            
        Returns:
            Optional[Headline]: Selected headline or None if none available
        """
        try:
            # First, try AI headline generation if enabled
            headline_generator = get_headline_generator()
            settings = get_settings()
            
            # Determine if we should use AI based on configuration
            use_ai = (
                headline_generator.is_available() 
                and random.randint(1, 100) <= settings.ai_headline_usage_percentage
            )
            
            if use_ai:
                logger.info(f"Attempting AI headline generation - difficulty: {difficulty}, category: {category}")
                ai_headline = await headline_generator.generate_headline(
                    difficulty=difficulty,
                    category=category or "general"
                )
                
                if ai_headline:
                    # Create a temporary headline object from AI data
                    headline = type('Headline', (), {
                        'id': str(uuid.uuid4()),
                        'text': ai_headline['text'],
                        'is_real': ai_headline['is_real'],
                        'source': ai_headline['source'],
                        'explanation': ai_headline['explanation'],
                        'category': ai_headline['category'],
                        'difficulty': ai_headline['difficulty']
                    })()
                    
                    logger.info(f"Successfully generated AI headline: {ai_headline['text'][:50]}...")
                    return headline
                else:
                    logger.warning("AI headline generation failed, falling back to database")
            
            # Fallback: Try to get headline from database
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
                    logger.info(f"Using database headline: {headline.text[:50]}...")
                    return headline
                    
            # Final fallback: Use sample headlines if database is empty
            logger.info("Database empty, using sample headlines as final fallback")
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
            
            # For ability usage we bypass state-machine validation (it only knows 'snipe_player')
            if action == "use_ability":
                result = {"success": True}
            else:
                game_state = self._get_game_state(game_session)
                result = game_session["state_machine"].handle_action(action, user_id, data, game_state)
            
            # Handle specific actions
            if action == "vote" and result.get("success"):
                await self._handle_vote(game_session, user_id, data)
            elif action == "vote_headline" and result.get("success"):
                await self._handle_vote(game_session, user_id, data)
            elif action == "vote_player" and result.get("success"):
                # Record player accusation vote in game_session['player_votes']
                if "player_votes" not in game_session:
                    game_session["player_votes"] = {}
                if user_id not in game_session["player_votes"]:
                    game_session["player_votes"][user_id] = data["target_id"]
                # Optionally, log the vote
                logger.info(f"Player {user_id} voted for player {data['target_id']} as spreading misinformation.")
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
        # Get state machine counters if available
        state_machine = game_session.get("state_machine")
        fake_headlines_trusted = 0
        fake_headlines_flagged = 0
        if state_machine:
            fake_headlines_trusted = state_machine.fake_headlines_trusted
            fake_headlines_flagged = state_machine.fake_headlines_flagged
        # CRITICAL FIX: Get win progress data from game session
        win_progress = game_session.get("win_progress", {})

        # --- CRITICAL: Use correct vote dict depending on phase ---
        current_phase = None
        if "state_machine" in game_session:
            current_phase = game_session["state_machine"].get_current_phase_type().value
        # Default to headline voting
        vote_dict = game_session.get("votes", {})
        if current_phase == "player_voting":
            # During player accusation voting, use player_votes
            vote_dict = game_session.get("player_votes", {})
        # Compute eligible voters (not eliminated, not ghost, not shadow banned)
        eligible_voters = [
            pid for pid in game_session["players"].keys()
            if pid not in game_session["eliminated_players"]
            and self._can_player_vote(game_session, pid)
        ]
        all_players_voted = len(vote_dict) == len(eligible_voters)
        all_eligible_voted = all_players_voted
        # --- END CRITICAL FIX ---
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
            # Use correct vote dict for voting checks
            "all_players_voted": all_players_voted,
            "all_eligible_voted": all_eligible_voted,
            "all_roles_assigned": len(game_session["player_roles"]) == len(game_session["players"]),
            "game_over": game_session.get("game_over", False),  # Use cached status instead of recalculating
            # CRITICAL FIX: Pass both state machine counters AND game session win progress
            "fake_headlines_trusted": max(fake_headlines_trusted, win_progress.get("fake_headlines_trusted", 0)),
            "fake_headlines_flagged": max(fake_headlines_flagged, win_progress.get("fake_headlines_flagged", 0)),
            "win_progress": win_progress,
            "rounds_completed": win_progress.get("rounds_completed", 0),
            "player_reputation": game_session.get("player_reputation", {}),
            "shadow_banned_players": game_session.get("shadow_banned_players", {}),
            # v3 team scoring (first to 3 points)
            "team_scores": game_session.get("team_scores", {"truth": 0, "scam": 0}),
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
            # Log vote and eligible voters for debugging
            eligible_voters = [pid for pid in game_session["players"].keys() 
                              if pid not in game_session["eliminated_players"] 
                              and self._can_player_vote(game_session, pid)]
            logger.info(f"Vote received: voter_id={voter_id}, vote_type={vote_type}, headline_id={headline_id}")
            logger.info(f"Total votes: {len(game_session['votes'])}, Eligible voters: {eligible_voters} (count: {len(eligible_voters)})")
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
        # Always check phase transition after a vote
        logger.debug("Calling _check_phase_transition after vote.")
        await self._check_phase_transition(game_session)
    
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
            # CRITICAL: Validate snipe timing restrictions
            if not self._can_use_snipe_this_round(game_session, user_id):
                logger.info(f"Player {user_id} attempted snipe outside valid timing")
                return
                
            game_state = self._get_game_state(game_session)
            result = role.use_snipe(target, game_state, user_id)  # Pass sniper_id
            
            # Apply ability effects
            if result.get("success"):
                await self._apply_ability_effects(game_session, result)
    
    def _can_use_snipe_this_round(self, game_session: Dict, player_id: int) -> bool:
        """Check if player can use snipe ability this round."""
        # Check if we're in the correct phase
        current_phase = game_session["state_machine"].get_current_phase_type()
        if current_phase.value != "snipe_opportunity":
            return False
            
        # Check if this is a valid snipe round (2 or 4)
        current_round = game_session["round_number"]
        if not self._is_snipe_round(current_round):
            return False
        
        # Check if player has snipe ability and hasn't used it
        role_info = game_session["player_roles"].get(player_id)
        if not role_info:
            return False
            
        role = role_info.get("role")
        return role and role.can_use_snipe()

    def _is_snipe_round(self, round_number: int) -> bool:
        """Check if current round allows snipe abilities."""
        return round_number in [1, 2, 3, 4]
    
    async def _check_phase_transition(self, game_session: Dict) -> None:
        """Check if current phase should transition."""
        game_state = self._get_game_state(game_session)
        # CRITICAL FIX: Log the correct vote count for the current phase
        current_phase = game_session['state_machine'].get_current_phase_type().value
        if current_phase == "player_voting":
            vote_count = len(game_session.get("player_votes", {}))
        else:
            vote_count = len(game_session.get("votes", {}))
        logger.debug(f"_check_phase_transition: phase={current_phase}, votes={vote_count}, all_eligible_voted={game_state.get('all_eligible_voted')}, time_remaining={game_session['state_machine'].get_time_remaining()}")
        if game_session["state_machine"].can_transition(game_state):
            logger.debug("Phase can transition. Calling transition_phase.")
            transition_result = game_session["state_machine"].transition_phase(game_state)
            if transition_result:
                # Handle phase-specific transitions first
                new_phase = transition_result["to_phase"]
                logger.info(f"Transitioned to new phase: {new_phase}")
                if new_phase == "headline_reveal":
                    await self._start_news_phase(game_session)
                elif new_phase == "round_results":
                    await self._resolve_voting(game_session)
                elif new_phase == "snipe_opportunity":
                    # Send enhanced snipe opportunity message
                    await self._send_snipe_opportunity_message(game_session, getattr(self, '_bot_context', None))
                # CRITICAL: Send phase transition messages to chat
                await self._handle_phase_transition(game_session, transition_result)
        else:
            logger.debug("Phase cannot transition yet.")
    
    async def _start_news_phase(self, game_session: Dict) -> None:
        """Start a new news phase with a fresh headline."""
        # (REMOVED) Do NOT increment round_number here. It will be incremented just before this function is called.
        # game_session["round_number"] += 1
        if "state_machine" in game_session:
            # Overwrite the session's round_number with the authoritative value
            # from the state machine. This prevents the round counter from being
            # reset to 1 every time a new headline starts.
            game_session["round_number"] = game_session["state_machine"].round_number
            logger.info(f"Synchronized session round number to {game_session['round_number']}")
        current_round = game_session["round_number"]
        
        # Clear any remaining votes from previous round (safeguard)
        game_session["votes"] = {}
        
        # === NEW: reset round-based tracking ===
        game_session["snipe_used_this_round"] = False
        # Calculate elimination limit if not already set (handles cases where it was 0 during lobby)
        if game_session.get("elimination_limit") in (None, 0):
            game_session["elimination_limit"] = max(0, len(game_session["players"]) - 2)
        
        # Reduce shadow ban durations at start of new round
        if current_round > 1:
            self._reduce_shadow_ban_durations(game_session)
        
        # Rotate drunk role to next normie (if not round 1)
        if current_round > 1:
            await self._rotate_drunk_role(game_session)
        
        # v3: pop headline from prepared queue first; fallback to generator
        headline_data = None
        queue = game_session.get("headline_queue", [])
        if queue:
            headline_data = queue.pop(0)
            # If we popped a raw Headline object previously stored, keep object format consistent
            if isinstance(headline_data, dict):
                headline = headline_data["obj"]
            else:
                headline = headline_data
        else:
            headline = await self.get_random_headline()
        
        if headline:
            game_session["current_headline"] = {
                "id": headline.id,
                "text": headline.text,
                "is_real": headline.is_real,
                "source": headline.source,
                "explanation": headline.explanation
            }

            # === NEW: Provide the Drunk player with inside info immediately ===
            # Ensure the active Drunk receives the correct answer and teaching tip as soon as
            # the headline for this round is ready. This keeps the gameplay experience
            # consistent with the role description ("You know the truth about THIS round's headline").
            await self._send_drunk_correct_answer(game_session)
            
            # Note: Players must use /ability command to activate their special abilities
            # No automatic ability activation
            
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
        if weighted_trust_votes == weighted_flag_votes:
            # Tie – no side scores this round
            logger.info("Voting tie detected – no points awarded this round")
            majority_trusts = None
        else:
            majority_trusts = weighted_trust_votes > weighted_flag_votes
        
        # Log vote weights for debugging
        logger.info(f"Vote count - Trust: {len(trust_voters)} voters ({weighted_trust_votes} weighted), Flag: {len(flag_voters)} voters ({weighted_flag_votes} weighted)")
        logger.info(f"Majority decision: {'TRUST' if majority_trusts else 'FLAG'} (based on weighted votes)")
        
        # Get current headline truth value
        current_headline = game_session.get("current_headline")
        if current_headline:
            headline_is_real = current_headline.get("is_real", True)
            
            # Update headline results tracking
            if majority_trusts is not None:
                truth_point = (headline_is_real and majority_trusts) or (not headline_is_real and not majority_trusts)
                scam_point = not truth_point
                if truth_point:
                    game_session["team_scores"]["truth"] += 1
                elif scam_point:
                    game_session["team_scores"]["scam"] += 1

                # Keep detailed results for analytics (optional)
                if headline_is_real and majority_trusts:
                    game_session["headline_results"]["real_headlines_trusted"] += 1
                elif headline_is_real and not majority_trusts:
                    game_session["headline_results"]["real_headlines_flagged"] += 1
                elif not headline_is_real and majority_trusts:
                    game_session["headline_results"]["fake_headlines_trusted"] += 1
                else:
                    game_session["headline_results"]["fake_headlines_flagged"] += 1
            
            # Update state machine counters for win conditions
            if "state_machine" in game_session:
                game_session["state_machine"].update_win_condition_counters(
                    headline_was_fake=not headline_is_real,
                    majority_trusted=majority_trusts
                )
            
            # Update player reputations based on votes
            vote_results = {
                "headline_is_real": headline_is_real,
                "majority_trusts": majority_trusts,
                "trust_voters": trust_voters,
                "flag_voters": flag_voters
            }
            await self._update_player_reputation(game_session, vote_results)
            
            # Check for win conditions after reputation update
            if game_session["team_scores"]["truth"] >= 3:
                game_session["winner"] = "truth_seekers"
                game_session["win_reason"] = "Truth Team reached 3 points"
                game_session["game_over"] = True
                self._trigger_game_end(game_session)
                return
            if game_session["team_scores"]["scam"] >= 3:
                game_session["winner"] = "misinformers"
                game_session["win_reason"] = "Scammers reached 3 points"
                game_session["game_over"] = True
                self._trigger_game_end(game_session)
                return
        
        # Update completed rounds count BEFORE incrementing to next round
        game_session["win_progress"]["rounds_completed"] = game_session["round_number"]
        # IMPORTANT: Do NOT clear the votes here.
        # They are still needed by _send_headline_resolution to show the voting breakdown.
        # They will be cleared after the resolution message has been delivered.
    
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
        
        # 5 rounds completed: Calculate RP totals for each faction
        if win_progress["rounds_completed"] >= 5:
            return self._calculate_rp_based_victory(game_session)
        
        # Check shadow ban-based win conditions (all scammers banned)
        return self._check_shadow_ban_win_conditions(game_session)
        
        return False
    
    def _calculate_rp_based_victory(self, game_session: Dict) -> bool:
        """Calculate faction victory based on total RP after 5 rounds."""
        try:
            truth_seekers_rp = 0
            misinformers_rp = 0
            
            # Calculate total RP for each faction
            for player_id, reputation in game_session["player_reputation"].items():
                role_info = game_session["player_roles"].get(player_id)
                if role_info:
                    faction = role_info.get("faction")
                    if faction == "truth_seekers":
                        truth_seekers_rp += reputation
                    elif faction == "misinformers":
                        misinformers_rp += reputation
            
            # Determine winner based on total RP
            if truth_seekers_rp > misinformers_rp:
                game_session["winner"] = "truth_seekers"
                game_session["win_reason"] = f"Truth Team won after 5 rounds: {truth_seekers_rp} RP vs {misinformers_rp} RP"
                logger.info(f"Game {game_session['game_id']}: Truth Team won by RP - {truth_seekers_rp} vs {misinformers_rp}")
                return True
            elif misinformers_rp > truth_seekers_rp:
                game_session["winner"] = "misinformers"
                game_session["win_reason"] = f"Scammers won after 5 rounds: {misinformers_rp} RP vs {truth_seekers_rp} RP"
                logger.info(f"Game {game_session['game_id']}: Scammers won by RP - {misinformers_rp} vs {truth_seekers_rp}")
                return True
            else:
                # Tie goes to Truth Team (default win condition)
                game_session["winner"] = "truth_seekers"
                game_session["win_reason"] = f"Truth Team won after 5 rounds (tie): {truth_seekers_rp} RP each"
                logger.info(f"Game {game_session['game_id']}: Truth Team won by tiebreaker - {truth_seekers_rp} RP each")
                return True
                
        except Exception as e:
            logger.error(f"Failed to calculate RP-based victory: {e}")
            # Default to Truth Team win if calculation fails
            game_session["winner"] = "truth_seekers"
            game_session["win_reason"] = "Truth Team won after 5 rounds (calculation error)"
            return True
    
    def _check_shadow_ban_win_conditions(self, game_session: Dict) -> bool:
        """Check if all scammers are shadow banned (Truth Team wins)."""
        try:
            shadow_banned_players = game_session.get("shadow_banned_players", {})
            
            # Count active players by faction (not shadow banned and not ghost viewers)
            active_truth_seekers = 0
            active_misinformers = 0
            total_misinformers = 0
            
            for player_id, role_info in game_session["player_roles"].items():
                if not role_info:
                    continue
                    
                faction = role_info.get("faction")
                player_rp = game_session["player_reputation"].get(player_id, 3)
                is_shadow_banned = player_id in shadow_banned_players and shadow_banned_players[player_id] > 0
                
                if faction == "truth_seekers":
                    # Truth seeker is active if they have RP > 0 and are not shadow banned
                    if player_rp > 0 and not is_shadow_banned:
                        active_truth_seekers += 1
                elif faction == "misinformers":
                    total_misinformers += 1
                    # Misinformer is active if they have RP > 0 and are not shadow banned
                    if player_rp > 0 and not is_shadow_banned:
                        active_misinformers += 1
            
            # Truth Team wins if all Scammers are shadow banned or have 0 RP
            if total_misinformers > 0 and active_misinformers == 0 and active_truth_seekers > 0:
                game_session["winner"] = "truth_seekers"
                game_session["win_reason"] = "All Scammers shadow banned or eliminated"
                logger.info(f"Game {game_session['game_id']}: Truth Team won - all Scammers neutralized")
                return True
                
            # Scammers win if all Truth Seekers are shadow banned or have 0 RP (rare but possible)
            if active_truth_seekers == 0 and active_misinformers > 0:
                game_session["winner"] = "misinformers"
                game_session["win_reason"] = "All Truth Seekers shadow banned or eliminated"
                logger.info(f"Game {game_session['game_id']}: Scammers won - all Truth Seekers neutralized")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check shadow ban win conditions: {e}")
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
            
            # Send final summary to main chat asynchronously
            bot_context = self._get_bot_context_safely("game end summary")
            if bot_context:
                import asyncio
                asyncio.create_task(self._send_game_end_results(game_session, bot_context))
         
        except Exception as e:
            logger.error(f"Failed to trigger game end: {e}")
    
    def _get_win_progress_display(self, game_session: Dict) -> str:
        """Generate progress display for current win conditions."""
        # Retrieve both legacy headline counters and the newer v3 team point scores
        progress = game_session.get("win_progress", {})
        scores = game_session.get("team_scores", {"truth": 0, "scam": 0})
        rounds_completed = progress.get("rounds_completed", game_session.get("round_number", 0))

        # Prefer the v3 point system if any points have been recorded; otherwise, show headline counters
        if scores.get("truth", 0) > 0 or scores.get("scam", 0) > 0:
            return (
                f"📊 **Win Progress:**\n"
                f"🔴 **Scammers:** {scores['scam']}/3 points\n"
                f"🔵 **Truth Team:** {scores['truth']}/3 points\n"
                f"⏱️ **Round:** {rounds_completed}/5"
            )
        else:
            return (
                f"📊 **Win Progress:**\n"
                f"🔴 **Scammers:** {progress.get('fake_headlines_trusted', 0)}/3 fake headlines trusted\n"
                f"🔵 **Truth Team:** {progress.get('fake_headlines_flagged', 0)}/3 fake headlines flagged\n"
                f"⏱️ **Round:** {rounds_completed}/5"
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
                
                # === Update user statistics ===
                # Fetch headline truth value to update specific accuracy counters
                from ..database.models import User as UserModel, Headline as HeadlineModel

                headline_record = await session.get(HeadlineModel, headline_id)
                headline_is_real = headline_record.is_real if headline_record else None
                
                # Ensure user record exists
                user_record = await session.get(UserModel, voter_id)
                if user_record is None:
                    # Create minimal user record if not present
                    player_data = game_session["players"].get(voter_id, {})
                    user_record = UserModel(
                        id=voter_id,
                        username=player_data.get("username"),
                        first_name=player_data.get("username")
                    )
                    session.add(user_record)
                    await session.flush()
                
                # Increment generic counters
                user_record.headlines_voted_on += 1
                if is_correct:
                    user_record.correct_votes += 1
                
                # Increment specialised counters when headline truth known
                if headline_is_real is not None:
                    if vote_type == "flag" and not headline_is_real and is_correct:
                        user_record.fake_headlines_correctly_flagged += 1
                    if vote_type == "trust" and headline_is_real and is_correct:
                        user_record.real_headlines_correctly_trusted += 1
                
                await session.commit()
                
            logger.info(f"Headline vote logged - game_id: {game_id}, voter_id: {voter_id}, vote: {vote_type}")
        except Exception as e:
            logger.error(f"Failed to log headline vote - error: {str(e)}")
    
    async def _apply_ability_effects(self, game_session: Dict, ability_result: Dict) -> None:
        """Apply the effects of a role ability, including shadow bans."""
        try:
            effect = ability_result.get("effect")
            
            if effect == "shadow_ban_target":
                # Shadow ban the target player
                target_id = ability_result.get("target")
                if target_id:
                    await self._apply_shadow_ban(game_session, target_id, rounds=1)
                    logger.info(f"Applied shadow ban to player {target_id}")
                    # Mark that a snipe was used this round
                    game_session["snipe_used_this_round"] = True
                    
            elif effect == "shadow_ban_self":
                # Shadow ban the sniper (failed snipe)
                sniper_id = ability_result.get("sniper_id")  # This should be passed from the role
                if sniper_id:
                    await self._apply_shadow_ban(game_session, sniper_id, rounds=1)
                    logger.info(f"Applied shadow ban to sniper {sniper_id} (failed snipe)")
                    # Mark that a snipe was used this round
                    game_session["snipe_used_this_round"] = True
            
            # Store temporary effects (for other abilities)
            if "effect" in ability_result:
                effect_name = ability_result["effect"]
                duration = ability_result.get("duration_rounds", 1)
                
                game_session["game_effects"][effect_name] = {
                    "duration": duration,
                    "expires_round": game_session["round_number"] + duration,
                    "data": ability_result
                }
                
        except Exception as e:
            logger.error(f"Failed to apply ability effects: {e}")
    
    async def _apply_shadow_ban(self, game_session: Dict, player_id: int, rounds: int = 1) -> None:
        """Apply a shadow ban to a player for a certain number of rounds."""
        try:
            # Add player to shadow ban tracking
            game_session["shadow_banned_players"][player_id] = rounds
            
            # === NEW: increment total eliminations counter ===
            game_session["eliminations_total"] = game_session.get("eliminations_total", 0) + 1
            
            # Get player info for notification
            player_data = game_session["players"].get(player_id, {})
            username = player_data.get("username", f"Player {player_id}")
            
            # Send notification to chat
            bot_context = getattr(self, '_bot_context', None)
            if bot_context:
                shadow_ban_message = (
                    f"🚫 **Player Shadow Banned!**\n\n"
                    f"**{username}** has been shadow banned for {rounds} round(s).\n\n"
                    f"❌ They cannot speak during discussion phases\n"
                    f"✅ They can still vote on headlines\n\n"
                    f"🤔 **Strategic Question:** Was this a Scammer or Fact Checker?"
                )
                
                await bot_context.bot.send_message(
                    chat_id=game_session["chat_id"],
                    text=shadow_ban_message
                )
            
            logger.info(f"Player {player_id} shadow banned for {rounds} rounds")
            
            # v3: If the banned player currently holds Drunk hint, mark for reassignment next round
            drunk_rot = game_session.get("drunk_rotation", {})
            if drunk_rot.get("current_drunk_id") == player_id:
                drunk_rot["current_drunk_id"] = None  # Cleared; _rotate_drunk_role will reassign
            
        except Exception as e:
            logger.error(f"Failed to apply shadow ban to player {player_id}: {e}")
    
    def _reduce_shadow_ban_durations(self, game_session: Dict) -> None:
        """Reduce shadow ban durations at the start of each round."""
        try:
            shadow_banned_players = game_session.get("shadow_banned_players", {})
            expired_bans = []
            
            for player_id, rounds_remaining in shadow_banned_players.items():
                if rounds_remaining <= 1:
                    expired_bans.append(player_id)
                else:
                    shadow_banned_players[player_id] = rounds_remaining - 1
            
            # Remove expired shadow bans
            for player_id in expired_bans:
                del shadow_banned_players[player_id]
                
                # Notify about ban expiration
                player_data = game_session["players"].get(player_id, {})
                username = player_data.get("username", f"Player {player_id}")
                logger.info(f"Shadow ban expired for player {player_id} ({username})")
                
        except Exception as e:
            logger.error(f"Failed to reduce shadow ban durations: {e}")
    
    async def _handle_phase_transition(self, game_session: Dict, transition_result: Dict) -> None:
        """Handle phase transition by sending appropriate messages to chat."""
        try:
            from ..handlers.truth_wars_handlers import send_headline_voting
            new_phase = transition_result["to_phase"]
            start_result = transition_result.get("start_result", {})
            message = start_result.get("message")
            chat_id = game_session.get("chat_id")
            if not chat_id:
                logger.error(f"No chat_id found for game {game_session.get('game_id')}")
                return
            bot_context = self._get_bot_context_safely("phase transition")
            if not bot_context:
                logger.error(f"Cannot send phase transition message for game {game_session.get('game_id')} - no bot context")
                return
            if message:
                await bot_context.bot.send_message(
                    chat_id=chat_id,
                    text=message
                )
            else:
                logger.info(f"No generic phase message for phase {new_phase}, proceeding to special-case handler.")
            # Handle special cases for specific phases
            if new_phase == "discussion":
                # Headline will be sent via pending notification loop to avoid duplicates
                await self._remind_drunk_to_teach(game_session, bot_context)
            elif new_phase == "voting":
                pass  # No longer send player voting interface here
            elif new_phase == "snipe_opportunity":
                await self._send_snipe_opportunity_message(game_session, bot_context)
            elif new_phase == "resolution" or new_phase == "round_results":
                logger.info(f"Sending round results for phase {new_phase}")
                await self._send_headline_resolution(game_session, bot_context)
            elif new_phase == "await_continue":
                await self._send_continue_end_options(game_session, bot_context)
            elif new_phase == "game_end":
                await self._send_game_end_results(game_session, bot_context)
            # --- CRITICAL: Handle PLAYER_VOTING phase ---
            elif new_phase == "player_voting":
                # Clear any previous player votes and prompt group for shadow-ban voting
                game_session["player_votes"] = {}
                await self._send_player_voting_interface(game_session, bot_context)
            # After handling the new phase specific operations, process results from the previous PLAYER_VOTING phase if applicable
            if transition_result.get("from_phase") == "player_voting":
                await self._process_player_voting_results(game_session, bot_context)
        except Exception as e:
            logger.error(f"Failed to handle phase transition: {e}")
            import traceback
            traceback.print_exc()
    
    async def _send_player_voting_interface(self, game_session: Dict, bot_context) -> None:
        """Send interface for players to vote each other out."""
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            # === NEW: skip voting if elimination cap reached ===
            if game_session.get("eliminations_total", 0) >= game_session.get("elimination_limit", 999):
                await bot_context.bot.send_message(
                    chat_id=game_session["chat_id"],
                    text="🚫 Elimination cap reached – no more shadow bans this round."
                )
                # Fast-forward phase transition
                await self._check_phase_transition(game_session)
                return
            
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
            headline_votes = dict(game_session["votes"])
            headline_text = current_headline.get("text", "Unknown headline")
            headline_is_real = current_headline.get("is_real", True)
            explanation = current_headline.get("explanation", "No explanation available")
            source = current_headline.get("source", "Unknown source")
            correct_answer = "TRUST" if headline_is_real else "FLAG"
            truth_status = "✅ REAL" if headline_is_real else "❌ FAKE"
            resolution_text = f"📊 **HEADLINE RESOLUTION**\n\n"
            resolution_text += f"📰 **Headline:** {headline_text}\n\n"
            resolution_text += f"�� **Result:** {truth_status}\n"
            resolution_text += f"✅ **Correct Answer:** {correct_answer}\n\n"
            resolution_text += f"💡 **Explanation:**\n{explanation}\n\n"
            resolution_text += f"🔗 **Source:** {source}\n\n"
            resolution_text += "🗳️ **Voting Results:**\n"
            if headline_votes:
                trust_voters = []
                flag_voters = []
                weighted_trust_votes = 0
                weighted_flag_votes = 0
                for voter_id, vote_data in headline_votes.items():
                    player_data = game_session["players"].get(voter_id, {})
                    username = player_data.get("username", f"Player {voter_id}")
                    role_info = game_session["player_roles"].get(voter_id, {})
                    role = role_info.get("role")
                    vote_weight = role.get_vote_weight() if role and hasattr(role, 'get_vote_weight') else 1
                    if isinstance(vote_data, dict):
                        vote_type = vote_data.get("vote_type")
                        if vote_type == "trust":
                            if vote_weight > 1:
                                trust_voters.append(f"{username} (x{vote_weight})")
                            else:
                                trust_voters.append(username)
                            weighted_trust_votes += vote_weight
                        elif vote_type == "flag":
                            if vote_weight > 1:
                                flag_voters.append(f"{username} (x{vote_weight})")
                            else:
                                flag_voters.append(username)
                            weighted_flag_votes += vote_weight
                if trust_voters:
                    resolution_text += f"🟢 **TRUSTED** ({len(trust_voters)} voters, {weighted_trust_votes} votes): {', '.join(trust_voters)}\n"
                else:
                    resolution_text += "🟢 **TRUSTED** (0 voters, 0 votes): No one\n"
                if flag_voters:
                    resolution_text += f"🔴 **FLAGGED** ({len(flag_voters)} voters, {weighted_flag_votes} votes): {', '.join(flag_voters)}\n"
                else:
                    resolution_text += "🔴 **FLAGGED** (0 voters, 0 votes): No one\n"
                majority_result = "TRUST" if weighted_trust_votes > weighted_flag_votes else "FLAG"
                resolution_text += f"\n⚖️ **Majority Decision:** {majority_result} (based on weighted votes)\n"
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
            # --- Send misinformation voting prompt immediately after resolution ---
            alive_players = [
                player_data for pid, player_data in game_session["players"].items()
                if pid not in game_session["eliminated_players"]
            ]
            # If the game is not over, send a clear status message to the chat
            if not game_session.get("game_over", False) and len(alive_players) > 1:
                # Inform players that the game continues
                continue_message = "⏩ No team has won yet. The game continues to the next round!"
                await bot_context.bot.send_message(
                    chat_id=game_session["chat_id"],
                    text=continue_message
                )
                logger.info(f"Game continues message sent to chat {game_session['chat_id']}")
                # No player voting phase in simplified flow
            # After broadcasting the resolution and any follow-up messages,
            # clear the votes so they do not carry over into the next round.
            game_session["votes"] = {}
            # Do NOT send snipe timing info or continue/end options here. Let phase handler do it.
        except Exception as e:
            logger.error(f"Failed to send headline resolution: {e}")
            import traceback
            traceback.print_exc()
    
    async def _send_snipe_timing_info(self, game_session: Dict, bot_context) -> None:
        """Send information about snipe timing to help players understand when snipes are available."""
        if not bot_context:
            return
            
        current_round = game_session["round_number"]
        chat_id = game_session["chat_id"]
        
        if self._is_snipe_round(current_round):
            # This is a snipe round - the snipe opportunity phase will follow
            snipe_info = (
                f"🎯 **Round {current_round}: Snipe Opportunity!**\n\n"
                f"⚡ **Fact Checkers** and **Scammers** can now use their snipe abilities!\n"
                f"🎯 Target your suspected enemies to shadow ban them\n"
                f"⚠️ **WARNING**: Wrong target = YOU get shadow banned!\n\n"
                f"⏰ **90 seconds** to decide...\n\n"
            )
        else:
            # This is NOT a snipe round - tell them when next snipe will be
            next_snipe_round = None
            for snipe_round in [2, 4]:
                if snipe_round > current_round:
                    next_snipe_round = snipe_round
                    break
                    
            if next_snipe_round:
                snipe_info = (
                    f"ℹ️ **Snipe Information**\n"
                    f"🚫 No snipe abilities this round\n"
                    f"⏭️ Next snipe opportunity: **Round {next_snipe_round}**\n"
                    f"📝 Remember: Snipes only available on rounds 2 and 4"
                )
            else:
                snipe_info = (
                    f"ℹ️ **Snipe Information**\n"
                    f"🚫 No more snipe opportunities this game\n"
                    f"📝 Snipe rounds (2 and 4) have passed"
                )
        
        try:
            await bot_context.bot.send_message(
                chat_id=chat_id,
                text=snipe_info
            )
            logger.info(f"Sent snipe timing info for round {current_round}")
        except Exception as e:
            logger.error(f"Failed to send snipe timing info: {e}")
    
    async def _send_continue_end_options(self, game_session: Dict, bot_context) -> None:
        """Send continue/end game options after resolution."""
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            current_round = game_session["round_number"]
            completed_round = current_round  # Now round_number always reflects the round just completed
            game_id = game_session["game_id"]
            win_progress = game_session["win_progress"]
            has_winner = (win_progress["fake_headlines_trusted"] >= 3 or 
                         win_progress["fake_headlines_flagged"] >= 3)
            if has_winner or current_round >= 5:
                end_message = (
                    f"🎯 **Round {completed_round} Complete**\n\n"
                    f"The game will automatically end now due to win conditions or maximum rounds reached."
                )
                await bot_context.bot.send_message(
                    chat_id=game_session["chat_id"],
                    text=end_message
                )
                return
            keyboard = [
                [
                    InlineKeyboardButton("▶️ Continue Game", callback_data=f"continue_game_{game_id}"),
                    InlineKeyboardButton("🛑 End Game", callback_data=f"end_game_{game_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            continue_message = (
                f"🎯 **Round {completed_round} Complete**\n\n"
                f"📊 **Current Score:**\n"
                f"• Fake headlines trusted: {win_progress['fake_headlines_trusted']}/3\n"
                f"• Fake headlines flagged: {win_progress['fake_headlines_flagged']}/3\n"
                f"• Rounds completed: {completed_round}/5\n\n"
                f"🤔 **What's next?**\n"
                f"Game Creator: Choose to continue or end the game."
            )
            await bot_context.bot.send_message(
                chat_id=game_session["chat_id"],
                text=continue_message,
                reply_markup=reply_markup
            )
            logger.info(f"Sent continue/end options for game {game_id}")
        except Exception as e:
            logger.error(f"Failed to send continue/end options: {e}")
    
    async def _send_game_end_results(self, game_session: Dict, bot_context) -> None:
        """Send final game results and role reveals."""
        try:
            # --- Persist per-game statistics ---
            from ..database.models import User as UserModel
            async with DatabaseSession() as session:
                winner = game_session.get("winner", "unknown")
                # Determine winner if still unknown to maintain accurate statistics
                if winner == "unknown":
                    truth_points = game_session.get("team_scores", {}).get("truth", 0)
                    scam_points = game_session.get("team_scores", {}).get("scam", 0)
                    if truth_points > scam_points:
                        winner = "truth_seekers"
                    elif scam_points > truth_points:
                        winner = "misinformers"
                    else:
                        winner = "draw"
                    # Update session for consistency across later operations
                    game_session["winner"] = winner
                winning_faction = None
                if winner == "misinformers":
                    winning_faction = "scammer_team"
                elif winner == "truth_seekers":
                    winning_faction = "truth_team"

                for player_id, role_info in game_session["player_roles"].items():
                    user_entry = await session.get(UserModel, player_id)
                    if not user_entry:
                        # Basic record if user somehow missing
                        player_data = game_session["players"].get(player_id, {})
                        user_entry = UserModel(
                            id=player_id,
                            username=player_data.get("username"),
                            first_name=player_data.get("username")
                        )
                        session.add(user_entry)

                    # Increment total games played
                    user_entry.total_games += 1

                    # Win tracking if faction won
                    player_faction = role_info.get("faction")
                    if winning_faction and player_faction == winning_faction:
                        user_entry.total_wins += 1
                        if winning_faction == "truth_team":
                            user_entry.truth_team_wins += 1
                        else:
                            user_entry.scammer_team_wins += 1

                    # Aggregate reputation earned
                    final_rp = game_session["player_reputation"].get(player_id, 3)
                    user_entry.total_reputation_earned += final_rp

                    # Update average reputation
                    if user_entry.total_games > 0:
                        user_entry.average_reputation = user_entry.total_reputation_earned / user_entry.total_games

                await session.commit()

            # Build final results message with win reason
            win_reason = game_session.get("win_reason", "Game completed")
            winner = game_session.get("winner")

            # --- Determine winner if it was never explicitly set ---
            if not winner or winner == "unknown":
                truth_points = game_session.get("team_scores", {}).get("truth", 0)
                scam_points = game_session.get("team_scores", {}).get("scam", 0)
                if truth_points > scam_points:
                    winner = "truth_seekers"
                    win_reason = win_reason or f"Truth Team leading {truth_points}-{scam_points} when game ended"
                elif scam_points > truth_points:
                    winner = "misinformers"
                    win_reason = win_reason or f"Scammers leading {scam_points}-{truth_points} when game ended"
                else:
                    winner = "draw"
                    win_reason = win_reason or "Scores were tied when the game ended"

            # --- Map winner keyword to display text/emoji ---
            if winner == "misinformers":
                winner_emoji = "🔴"
                winner_name = "**SCAMMERS**"
            elif winner == "truth_seekers":
                winner_emoji = "🔵"
                winner_name = "**TRUTH TEAM**"
            elif winner == "draw":
                winner_emoji = "🤝"
                winner_name = "**NO WINNER (DRAW)**"
            elif winner == "game_ended_early":
                winner_emoji = "🏁"
                winner_name = "**NO WINNER**"
            else:
                winner_emoji = "🎯"
                winner_name = "**UNKNOWN**"

            results_text = "🎉 **GAME OVER - FINAL RESULTS**\n\n"
            results_text += f"{winner_emoji} **WINNER:** {winner_name}\n"
            # Helper to escape underscores for Telegram Markdown
            def _esc(text: str) -> str:
                return text.replace("_", "\\_")

            results_text += f"📄 **Reason:** {_esc(win_reason)}\n\n"
            
            # Add win progress summary
            results_text += self._get_win_progress_display(game_session) + "\n\n"
            
            # Show all player roles
            results_text += "👥 **Role Reveals:**\n"
            for player_id, player_data in game_session["players"].items():
                username = _esc(player_data.get("username", f"Player {player_id}"))
                role_info = game_session["player_roles"].get(player_id, {})
                
                # Get role name from role object
                role = role_info.get("role")
                role_name = role.name if role else "Unknown"
                faction = _esc(role_info.get("faction", "Unknown"))
                
                status = "💀 Eliminated" if player_id in game_session["eliminated_players"] else "✅ Survived"
                current_rp = game_session["player_reputation"].get(player_id, 3)
                rp_status = "👻 Ghost Viewer" if current_rp == 0 else f"{current_rp} RP"
                results_text += f"• {username}: {role_name} ({faction}) - {status} - {rp_status}\n"
            
            # Show game statistics
            results_text += f"\n📊 **Game Stats:**\n"
            results_text += f"• Rounds played: {game_session['round_number']}\n"
            results_text += f"• Players eliminated: {len(game_session['eliminated_players'])}\n"
            
            # Add educational summary
            educational_summary = self._generate_educational_summary(game_session)
            if educational_summary:
                results_text += f"\n{educational_summary}"
            
            # TODO: Determine winning faction and show win/loss
            results_text += "\n🎮 Type /truthwars to start a new game!"
            
            await bot_context.bot.send_message(
                chat_id=game_session["chat_id"],
                text=results_text,
                parse_mode='Markdown'
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
        """Check if player can vote (not Ghost Viewer or Shadow Banned)."""
        # Check if player has enough reputation (not a Ghost Viewer)
        current_rp = game_session["player_reputation"].get(player_id, 3)
        if current_rp <= 0:
            return False
            
        # Check if player is shadow banned
        shadow_banned_players = game_session.get("shadow_banned_players", {})
        if shadow_banned_players.get(player_id, 0) > 0:
            return False
            
        return True
    
    def _can_player_use_ability(self, game_session: Dict, player_id: int) -> bool:
        """Check if player can use abilities (not Ghost Viewer or Shadow Banned)."""
        # Check if player has enough reputation (not a Ghost Viewer)
        current_rp = game_session["player_reputation"].get(player_id, 3)
        if current_rp <= 0:
            return False
            
        # Check if player is shadow banned
        shadow_banned_players = game_session.get("shadow_banned_players", {})
        if shadow_banned_players.get(player_id, 0) > 0:
            return False
            
        return True
    
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
            
            # Drunk role rotation happens silently - no public announcement
            # Players will only know when the drunk player shares tips or information
            logger.info(f"Drunk role rotated from {old_username} to {new_username} (silent rotation)")
            
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
        """Send the correct answer and educational content to the current drunk player."""
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
            
            # Get contextual educational tip based on headline
            educational_tip = await get_media_literacy_tip()
            
            correct_answer = "REAL" if headline_is_real else "FAKE"
            drunk_message = (
                f"🧍 **DRUNK INSIDE INFO**\n\n"
                f"📰 **Headline:** {headline_text}\n\n"
                f"🎯 **Correct Answer:** This headline is **{correct_answer}**\n\n"
                f"💡 **Explanation:** {explanation}\n\n"
                f"📚 **YOUR TEACHING MISSION:**\n"
                f"During discussion, share this media literacy tip with everyone:\n\n"
                f"🔍 **{educational_tip.get('category', 'General').replace('_', ' ').title()} Tip:**\n"
                f"💭 *\"{educational_tip.get('tip', 'Always verify sources before trusting information')}\"*\n\n"
                f"🎓 **Why this matters:** {educational_tip.get('explanation', 'Critical thinking helps identify misinformation')}\n\n"
                f"📢 **Remember:** Help others learn to spot fake news during the discussion!"
            )
            
            await bot_context.bot.send_message(
                chat_id=current_drunk_id,
                text=drunk_message
            )
            
            # Track educational content delivered
            game_session.setdefault("educational_content_delivered", []).append({
                "round": game_session["round_number"],
                "drunk_player": current_drunk_id,
                "tip_category": educational_tip.get("category"),
                "tip_content": educational_tip.get("tip")
            })
            
            logger.info(f"Sent correct answer and educational tip to drunk player {current_drunk_id}")
            
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
    
    def _get_bot_context_safely(self, operation_name: str = "operation") -> Optional[Any]:
        """
        Safely get bot context with proper error handling.
        
        Args:
            operation_name: Name of the operation for logging
            
        Returns:
            Bot context or None if not available
        """
        bot_context = getattr(self, '_bot_context', None)
        if not bot_context:
            logger.error(f"Bot context not available for {operation_name} - messages cannot be sent")
            # You could add recovery mechanisms here like:
            # - Queue the message for later
            # - Use a fallback messaging system
            # - Trigger bot context re-initialization
        return bot_context
    
    async def use_role_ability(self, game_id: str, user_id: int) -> Dict[str, Any]:
        """
        Use a player's role ability.
        
        Args:
            game_id: Game ID
            user_id: Player ID
            
        Returns:
            Dict: Result of ability usage
        """
        try:
            if game_id not in self.active_games:
                return {"success": False, "message": "Game not found"}
            
            game_session = self.active_games[game_id]
            
            # Check if player is in the game
            if user_id not in game_session["players"]:
                return {"success": False, "message": "You are not in this game"}
            
            # Get player's role
            role_info = game_session["player_roles"].get(user_id)
            if not role_info:
                return {"success": False, "message": "No role assigned"}
            
            role = role_info["role"]
            current_round = game_session["round_number"]
            
            # Check if player can use abilities (not Ghost Viewer)
            if not self._can_player_use_ability(game_session, user_id):
                return {"success": False, "message": "Ghost Viewers (0 RP) cannot use abilities"}
            
            # Check if player is shadow banned
            if self._is_player_shadow_banned(game_session, user_id):
                return {"success": False, "message": "Shadow banned players cannot use abilities"}
            
            # Check if ability was already used this round
            ability_usage_key = f"ability_used_round_{current_round}"
            if game_session.get(ability_usage_key, {}).get(user_id, False):
                return {"success": False, "message": "You have already used your ability this round"}
            
            # Check game phase - abilities can only be used during discussion phase
            current_phase = game_session["state_machine"].get_current_phase_type()
            if current_phase.value not in ["discussion", "headline_reveal"]:
                return {"success": False, "message": "Abilities can only be used during headline reveal or discussion phase"}
            
            # Use role-specific ability
            ability_result = await self._activate_role_ability(game_session, user_id, role)
            
            if ability_result["success"]:
                # Mark ability as used this round
                if ability_usage_key not in game_session:
                    game_session[ability_usage_key] = {}
                game_session[ability_usage_key][user_id] = True
                
                logger.info(f"Player {user_id} used role ability in game {game_id}, round {current_round}")
            
            return ability_result
            
        except Exception as e:
            logger.error(f"Failed to use role ability - game_id: {game_id}, user_id: {user_id}, error: {str(e)}")
            return {"success": False, "message": "Failed to use ability"}
    
    async def _activate_role_ability(self, game_session: Dict, user_id: int, role) -> Dict[str, Any]:
        """
        Activate the specific ability for a player's role.
        
        Args:
            game_session: Current game session
            user_id: Player ID
            role: Role object
            
        Returns:
            Dict: Result of ability activation
        """
        try:
            current_headline = game_session.get("current_headline")
            if not current_headline:
                return {"success": False, "message": "No active headline to use ability on"}
            
            bot_context = getattr(self, '_bot_context', None)
            if not bot_context:
                return {"success": False, "message": "Bot context not available"}
            
            # Handle Fact Checker ability
            if role.__class__.__name__ == "FactChecker":
                return await self._activate_fact_checker_ability(game_session, user_id, role)
            
            # Handle Drunk ability
            elif role.__class__.__name__ == "Drunk":
                return await self._activate_drunk_ability(game_session, user_id, role)
            
            # Handle Scammer ability (info about headline)
            elif role.__class__.__name__ == "Scammer":
                return await self._activate_scammer_ability(game_session, user_id, role)
            
            # Handle other roles (no active abilities, just show info)
            else:
                abilities_text = "\n".join([f"• {ability}" for ability in role.get_abilities()])
                
                await bot_context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"🎭 **Your Role:** {role.name}\n\n"
                        f"🔧 **Your Abilities:**\n{abilities_text}\n\n"
                        f"📋 **Description:**\n{role.get_description()}\n\n"
                        f"🎯 **Win Condition:**\n{role.get_win_condition()}"
                    )
                )
                
                return {"success": True, "message": "Role information sent"}
                
        except Exception as e:
            logger.error(f"Failed to activate role ability: {e}")
            return {"success": False, "message": "Failed to activate ability"}
    
    async def _activate_fact_checker_ability(self, game_session: Dict, user_id: int, role) -> Dict[str, Any]:
        """Activate Fact Checker's information ability."""
        try:
            current_round = game_session["round_number"]
            no_info_round = game_session.get("fact_checker_no_info_round")
            current_headline = game_session.get("current_headline")
            
            bot_context = getattr(self, '_bot_context', None)
            
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
                    chat_id=user_id,
                    text=no_info_message
                )
                
                return {"success": True, "message": "This is your no-info round - no intel available"}
                
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
                    chat_id=user_id,
                    text=fact_checker_message
                )
                
                return {"success": True, "message": "Fact checker intel sent"}
                
        except Exception as e:
            logger.error(f"Failed to activate fact checker ability: {e}")
            return {"success": False, "message": "Failed to get fact checker intel"}
    
    async def _activate_drunk_ability(self, game_session: Dict, user_id: int, role) -> Dict[str, Any]:
        """Activate Drunk's information ability."""
        try:
            current_headline = game_session.get("current_headline")
            bot_context = getattr(self, '_bot_context', None)
            
            headline_is_real = current_headline.get("is_real", True)
            headline_text = current_headline.get("text", "Unknown headline")
            explanation = current_headline.get("explanation", "No explanation available")
            
            # Get contextual educational tip based on headline
            from bot.ai.headline_generator import get_media_literacy_tip
            educational_tip = await get_media_literacy_tip()
            
            correct_answer = "REAL" if headline_is_real else "FAKE"
            drunk_message = (
                f"🧍 **DRUNK INSIDE INFO**\n\n"
                f"📰 **Headline:** {headline_text}\n\n"
                f"🎯 **Correct Answer:** This headline is **{correct_answer}**\n\n"
                f"💡 **Explanation:** {explanation}\n\n"
                f"📚 **YOUR TEACHING MISSION:**\n"
                f"During discussion, share this media literacy tip with everyone:\n\n"
                f"🔍 **{educational_tip.get('category', 'General').replace('_', ' ').title()} Tip:**\n"
                f"💭 *\"{educational_tip.get('tip', 'Always verify sources before trusting information')}\"*\n\n"
                f"🎓 **Why this matters:** {educational_tip.get('explanation', 'Critical thinking helps identify misinformation')}\n\n"
                f"📢 **Remember:** Help others learn to spot fake news during the discussion!"
            )
            
            await bot_context.bot.send_message(
                chat_id=user_id,
                text=drunk_message
            )
            
            return {"success": True, "message": "Drunk intel and educational mission sent"}
            
        except Exception as e:
            logger.error(f"Failed to activate drunk ability: {e}")
            return {"success": False, "message": "Failed to get drunk intel"}
    
    async def _activate_scammer_ability(self, game_session: Dict, user_id: int, role) -> Dict[str, Any]:
        """Activate Scammer's information ability."""
        try:
            bot_context = getattr(self, '_bot_context', None)
            if not bot_context:
                return {"success": False, "message": "Bot context unavailable"}

            # The Scammer can swap the headline only once per game
            if not hasattr(role, 'has_swapped_headline'):
                # Fallback safety – should be set in Role class
                role.has_swapped_headline = False

            if role.has_swapped_headline:
                await bot_context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        "😈 **HEADLINE SWAP**\n\n"
                        "❌ You have already used your headline-swap ability this game."
                    )
                )
                return {"success": False, "message": "Headline swap already used"}

            # --- Perform the headline swap ---
            # Fetch a new random headline (same helper used at round start)
            new_headline = await self.get_random_headline()

            if not new_headline:
                await bot_context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        "😈 **HEADLINE SWAP FAILED**\n\n"
                        "No alternative headline could be found. Try again later."
                    )
                )
                return {"success": False, "message": "No headlines available to swap"}

            # Update game session with new headline and reset votes
            game_session["current_headline"] = {
                "id": new_headline.id,
                "text": new_headline.text,
                "is_real": new_headline.is_real,
                "source": new_headline.source,
                "explanation": new_headline.explanation
            }

            # Clear any existing votes – players must vote on the new headline
            game_session["votes"] = {}

            # Queue notification for group chat to present the new headline
            game_session.setdefault("pending_notifications", []).append({
                "type": "headline_voting",
                "headline": {
                    "id": new_headline.id,
                    "text": new_headline.text,
                    "source": new_headline.source,
                    "is_real": new_headline.is_real,
                    "explanation": new_headline.explanation
                },
                "message": "📰 The headline has mysteriously changed! Read carefully and vote again!"
            })

            # Mark ability as used
            role.has_swapped_headline = True

            # Inform the Scammer privately
            await bot_context.bot.send_message(
                chat_id=user_id,
                text=(
                    "😈 **HEADLINE SWAP SUCCESSFUL**\n\n"
                    "You replaced the current headline with a new one."
                    " Players will now discuss and vote on it."
                )
            )

            return {"success": True, "message": "Headline swapped successfully"}

        except Exception as e:
            logger.error(f"Failed to activate scammer ability: {e}")
            return {"success": False, "message": "Failed to use headline swap"}
    
    def _is_player_shadow_banned(self, game_session: Dict, user_id: int) -> bool:
        """Check if player is currently shadow banned."""
        shadow_banned_players = game_session.get("shadow_banned_players", {})
        
        # Check if player is in shadow ban list with remaining rounds > 0
        rounds_remaining = shadow_banned_players.get(user_id, 0)
        return rounds_remaining > 0
    
    async def continue_game(self, game_id: str) -> Dict[str, Any]:
        """
        Continue the game to the next round.
        """
        try:
            if game_id not in self.active_games:
                return {"success": False, "message": "Game not found"}
            game_session = self.active_games[game_id]
            current_round = game_session["round_number"]
            win_progress = game_session["win_progress"]
            has_winner = (win_progress["fake_headlines_trusted"] >= 3 or 
                         win_progress["fake_headlines_flagged"] >= 3)
            if has_winner:
                return {"success": False, "message": "Game already has a winner"}
            if current_round >= 5:
                return {"success": False, "message": "Maximum rounds reached"}
            # --- Only allow continue if in await_continue phase ---
            if game_session["state_machine"].current_phase != PhaseType.AWAIT_CONTINUE:
                return {"success": False, "message": "Game is not waiting for continue. Please wait for the round to finish."}
            game_session["round_number"] += 1
            game_state = self._get_game_state(game_session)
            game_session["state_machine"].force_transition(PhaseType.HEADLINE_REVEAL, game_state)
            await self._start_news_phase(game_session)
            logger.info(f"Game {game_id} continued to round {game_session['round_number']}")
            return {"success": True, "message": f"Game continued to round {game_session['round_number']}"}
        except Exception as e:
            logger.error(f"Failed to continue game: {e}")
            return {"success": False, "message": "Failed to continue game"}
    
    async def end_game(self, game_id: str) -> Dict[str, Any]:
        """
        End the game immediately.
        
        Args:
            game_id: Game ID
            
        Returns:
            Dict: Result of end operation
        """
        try:
            if game_id not in self.active_games:
                return {"success": False, "message": "Game not found"}
            
            game_session = self.active_games[game_id]
            
            # Set game over status
            game_session["game_over"] = True
            game_session["winner"] = "game_ended_early"
            game_session["win_reason"] = "Game ended by creator"
            
            # Force transition to game end phase
            game_state = self._get_game_state(game_session)
            game_session["state_machine"].force_transition(PhaseType.GAME_END, game_state)
            
            # Send final results
            bot_context = getattr(self, '_bot_context', None)
            if bot_context:
                await self._send_game_end_results(game_session, bot_context)
            
            logger.info(f"Game {game_id} ended early by creator")
            
            return {"success": True, "message": "Game ended successfully"}
            
        except Exception as e:
            logger.error(f"Failed to end game {game_id}: {e}")
            return {"success": False, "message": "Failed to end game"}
    
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
                        if new_phase == "headline_reveal":
                            await self._start_news_phase(game_session)
                        elif new_phase == "round_results":
                            await self._resolve_voting(game_session)
                        # REMOVED: elif new_phase == "snipe_opportunity":
                        # REMOVED:     await self._send_snipe_opportunity_message(game_session, getattr(self, '_bot_context', None))
                
                # Wait 2 seconds before next check (more responsive)
                await asyncio.sleep(2)
                
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
    
    async def _send_snipe_opportunity_message(self, game_session: Dict, bot_context) -> None:
        """Send enhanced snipe opportunity message with clear instructions."""
        if not bot_context:
            return
            
        current_round = game_session["round_number"]
        chat_id = game_session["chat_id"]
        
        # Build public snipe notice (only Fact Checker may act, anonymity preserved)
        snipe_message = (
            f"🎯 **Round {current_round}: Fact-Checker's Secret Snipe**\n\n"
            f"🧠 The **Fact Checker** now has **90 seconds** to secretly target one player.\n"
            f"If the target is a 😈 *Scammer* they are instantly shadow-banned.\n"
            f"If the guess is wrong, the Fact Checker is shadow-banned instead.\n"
        )
        
        # Identify the Fact Checker with unused snipe
        fact_checker_id = None
        for pid, role_info in game_session["player_roles"].items():
            role = role_info.get("role")
            if role and getattr(role, "role_type", None).value == "fact_checker" and role.can_use_snipe():
                fact_checker_id = pid
                break

        if fact_checker_id is None:
            snipe_message += "ℹ️ Fact Checker has already used their snipe."
        else:
            snipe_message += "🤫 Fact Checker, check your private chat to select a target!"
        
        try:
            await bot_context.bot.send_message(
                chat_id=chat_id,
                text=snipe_message
            )
            # --- Send private prompt with inline buttons to the Fact Checker ---
            if fact_checker_id:
                try:
                    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                    keyboard = []
                    for pid, pdata in game_session["players"].items():
                        if pid == fact_checker_id or pid in game_session["eliminated_players"]:
                            continue
                        username = pdata.get("username", f"Player {pid}")
                        keyboard.append([
                            InlineKeyboardButton(username, callback_data=f"snipe_{pid}_{game_session['game_id']}")
                        ])
                    if keyboard:
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await bot_context.bot.send_message(
                            chat_id=fact_checker_id,
                            text="🎯 **Choose a player to snipe:** (one-time ability)",
                            reply_markup=reply_markup
                        )
                    else:
                        # No valid targets (e.g., single-player test games). Still notify the Fact Checker.
                        await bot_context.bot.send_message(
                            chat_id=fact_checker_id,
                            text="ℹ️ No eligible targets to snipe this round."
                        )
                except Exception as dm_err:
                    logger.error(f"Failed to send DM snipe prompt: {dm_err}")
            logger.info(f"Sent snipe opportunity message for round {current_round}")
        except Exception as e:
            logger.error(f"Failed to send snipe opportunity message: {e}")
    
    async def _remind_drunk_to_teach(self, game_session: Dict, bot_context) -> None:
        """Remind the drunk player to share educational tips during the discussion phase."""
        try:
            current_drunk_id = game_session["drunk_rotation"]["current_drunk_id"]
            if current_drunk_id:
                reminder_message = (
                    f"🧍 **Reminder:** You are the DRUNK for this round!\n\n"
                    f"💡 **Your job:** Share your source verification tips with the group during the discussion phase."
                )
                
                await bot_context.bot.send_message(
                    chat_id=current_drunk_id,
                    text=reminder_message
                )
                
            logger.info("Reminder sent to the drunk player to share educational tips")
        except Exception as e:
            logger.error(f"Failed to send reminder to drunk player: {e}")
    
    def _generate_educational_summary(self, game_session: Dict) -> str:
        """Generate a comprehensive summary of educational content covered during the game."""
        educational_content = game_session.get("educational_content_delivered", [])
        if not educational_content:
            return ""
        
        summary = "📚 **Educational Summary: What You Learned Today**\n\n"
        
        # Show tips by round
        summary += "🎓 **Media Literacy Tips Shared:**\n"
        for round_info in educational_content:
            category = round_info.get('tip_category', 'general').replace('_', ' ').title()
            tip = round_info.get('tip_content', 'Critical thinking is important')
            summary += f"• **Round {round_info['round']}** ({category}): {tip}\n"
        
        # Show categories covered
        categories_covered = set()
        for round_info in educational_content:
            categories_covered.add(round_info.get('tip_category', 'general'))
        
        if categories_covered:
            summary += f"\n🎯 **Concepts Covered:** {', '.join(cat.replace('_', ' ').title() for cat in categories_covered)}\n"
        
        # Add general reminder
        summary += (
            f"\n💡 **Remember these skills for real life:**\n"
            f"✅ Always check sources before sharing news\n"
            f"✅ Look for emotional language that might manipulate you\n"
            f"✅ Cross-reference important claims with multiple sources\n"
            f"✅ Be skeptical of headlines that seem too shocking to believe\n\n"
            f"🌟 **Keep practicing media literacy in your daily life!**"
        )
        
        return summary

    async def register_vote_only(self, game_id: str, user_id: int, vote_type: str, headline_id: str) -> dict:
        """Register a vote for a headline, but do NOT trigger phase transitions."""
        if game_id not in self.active_games:
            return {"success": False, "message": "Game not found"}
        game_session = self.active_games[game_id]
        # Only allow voting during discussion or voting phases
        current_phase = game_session["state_machine"].get_current_phase_type().value
        if current_phase not in ["discussion", "voting"]:
            return {"success": False, "message": "You can only vote during the discussion or voting phases."}
        if not self._can_player_vote(game_session, user_id):
            return {"success": False, "message": "Player cannot vote"}
        # Prevent duplicate votes: only first vote counts
        if user_id in game_session["votes"]:
            return {"success": False, "message": "You have already voted this round. Only your first vote counts."}
        # Register the vote
        game_session["votes"][user_id] = {
            "vote_type": vote_type,
            "headline_id": headline_id
        }
        # Log vote and eligible voters for debugging
        eligible_voters = [pid for pid in game_session["players"].keys() 
                          if pid not in game_session["eliminated_players"] 
                          and self._can_player_vote(game_session, pid)]
        logger.info(f"[register_vote_only] Vote received: voter_id={user_id}, vote_type={vote_type}, headline_id={headline_id}")
        logger.info(f"[register_vote_only] Total votes: {len(game_session['votes'])}, Eligible voters: {eligible_voters} (count: {len(eligible_voters)})")
        # Log headline vote to database
        current_headline = game_session.get("current_headline")
        is_correct = False
        if current_headline:
            headline_is_real = current_headline.get("is_real", True)
            is_correct = (headline_is_real and vote_type == "trust") or (not headline_is_real and vote_type == "flag")
        await self._log_headline_vote(
            game_id,
            user_id,
            headline_id,
            vote_type,
            is_correct
        )
        return {"success": True, "message": "Vote registered"}

    async def check_and_advance_phase(self, game_id: str) -> None:
        """Check if the phase should transition and advance if needed."""
        if game_id not in self.active_games:
            return
        game_session = self.active_games[game_id]
        await self._check_phase_transition(game_session)

    async def _send_player_voting_summary(self, game_session: Dict, bot_context) -> None:
        """Send a summary of player-voting results to the chat."""
        player_votes = game_session.get("player_votes", {})
        if not player_votes:
            await bot_context.bot.send_message(
                chat_id=game_session["chat_id"],
                text="No player-voting results to show."
            )
            return
        lines = ["🗳️ **Player Voting Results:**"]
        for voter_id, target_id in player_votes.items():
            voter_name = game_session["players"].get(voter_id, {}).get("username", str(voter_id))
            target_name = game_session["players"].get(target_id, {}).get("username", str(target_id))
            lines.append(f"{voter_name} voted for {target_name}")
        await bot_context.bot.send_message(
            chat_id=game_session["chat_id"],
            text="\n".join(lines)
        )
        # DO NOT clear player_votes here. It will be cleared after phase transition.

    async def _prepare_headline_set(self, game_session: Dict) -> None:
        """Prepare two headline pools (Set A and Set B) and choose one at random as per v3 rules.

        Set A = 3 real, 2 fake
        Set B = 2 real, 3 fake
        """
        try:
            # Fetch required headlines from DB
            async with DatabaseSession() as session:
                from sqlalchemy import select
                real_q = await session.execute(
                    select(Headline).where(Headline.is_real == True).order_by(func.random()).limit(3)
                )
                fake_q = await session.execute(
                    select(Headline).where(Headline.is_real == False).order_by(func.random()).limit(3)
                )
                real_headlines = [row[0] for row in real_q.fetchall()]
                fake_headlines = [row[0] for row in fake_q.fetchall()]
            if len(real_headlines) < 3 or len(fake_headlines) < 3:
                logger.warning("Not enough headlines in DB to build balanced sets; defaulting to random queue")
                return

            # Build sets
            set_a = real_headlines[:3] + fake_headlines[:2]
            set_b = real_headlines[:2] + fake_headlines[:3]

            import random as _r
            chosen_set = _r.choice([set_a, set_b])
            _r.shuffle(chosen_set)

            # Store in session as queue
            game_session["headline_queue"] = chosen_set
            logger.info(f"Prepared headline set with {len(chosen_set)} items for game {game_session['game_id']}")
        except Exception as e:
            logger.error(f"Failed to prepare headline set: {e}")

    async def _process_player_voting_results(self, game_session: Dict, bot_context) -> None:
        """Tally player-voting results, apply shadow ban, and announce outcome."""
        try:
            player_votes = game_session.get("player_votes", {})
            if not player_votes:
                return  # nothing to process
            # Build tally of votes per target
            tally: Dict[int, int] = {}
            for target_id in player_votes.values():
                tally[target_id] = tally.get(target_id, 0) + 1
            max_votes = max(tally.values())
            top_targets = [pid for pid, cnt in tally.items() if cnt == max_votes]
            # Send summary first
            await self._send_player_voting_summary(game_session, bot_context)
            # Determine outcome
            if len(top_targets) == 1:
                target_id = top_targets[0]
                # === NEW: enforce elimination cap ===
                if game_session.get("eliminations_total", 0) >= game_session.get("elimination_limit", 999):
                    await bot_context.bot.send_message(
                        chat_id=game_session["chat_id"],
                        text="🚫 Elimination cap reached – vote result ignored this round."
                    )
                    logger.info("Elimination cap reached – vote ignored")
                    game_session["player_votes"] = {}
                    return
                username = game_session["players"].get(target_id, {}).get("username", str(target_id))
                await self._apply_shadow_ban(game_session, target_id, rounds=99)
                await bot_context.bot.send_message(
                    chat_id=game_session["chat_id"],
                    text=f"🚫 **{username} has been shadow banned by majority vote!**"
                )
                logger.info(f"Player {target_id} shadow banned by group vote")
            else:
                await bot_context.bot.send_message(
                    chat_id=game_session["chat_id"],
                    text="⚖️ Vote was tied – no one is shadow banned this round."
                )
                logger.info("Player vote tie – no shadow ban applied")
            # Clear votes after processing
            game_session["player_votes"] = {}
        except Exception as e:
            logger.error(f"Failed to process player voting results: {e}")