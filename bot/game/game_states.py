"""
Truth Wars Game State Machine

This module defines the different phases of a Truth Wars game and manages
transitions between them. Each phase has specific logic and timing.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum

from ..utils.logging_config import get_logger

# Setup logger
logger = get_logger(__name__)


class PhaseType(Enum):
    """Enumeration of all possible game phases."""
    LOBBY = "lobby"
    ROLE_ASSIGNMENT = "role_assignment"
    NEWS = "news"
    DISCUSSION = "discussion"
    VOTING = "voting"
    RESOLUTION = "resolution"
    GAME_END = "game_end"


class GamePhase(ABC):
    """
    Abstract base class for all game phases.
    
    Each phase handles specific game logic and determines when to transition
    to the next phase.
    """
    
    def __init__(self, phase_type: PhaseType, duration_seconds: Optional[int] = None):
        """
        Initialize a game phase.
        
        Args:
            phase_type: Type of this phase
            duration_seconds: How long this phase lasts (None for manual transition)
        """
        self.phase_type = phase_type
        self.duration_seconds = duration_seconds
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
    def start(self) -> Dict[str, Any]:
        """
        Start this phase.
        
        Returns:
            Dict: Phase start information
        """
        self.start_time = datetime.utcnow()
        if self.duration_seconds:
            self.end_time = self.start_time + timedelta(seconds=self.duration_seconds)
            
        logger.info(f"Phase started: {self.phase_type.value}, duration: {self.duration_seconds}")
        return self._on_start()
    
    def end(self) -> Dict[str, Any]:
        """
        End this phase.
        
        Returns:
            Dict: Phase end information
        """
        logger.info(f"Phase ended: {self.phase_type.value}")
        return self._on_end()
    
    def is_expired(self) -> bool:
        """Check if this phase has expired based on time."""
        if not self.end_time:
            return False
        return datetime.utcnow() >= self.end_time
    
    def time_remaining(self) -> Optional[int]:
        """Get seconds remaining in this phase."""
        if not self.end_time:
            return None
        remaining = (self.end_time - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))
    
    @abstractmethod
    def _on_start(self) -> Dict[str, Any]:
        """Phase-specific start logic."""
        pass
    
    @abstractmethod  
    def _on_end(self) -> Dict[str, Any]:
        """Phase-specific end logic."""
        pass
    
    @abstractmethod
    def can_transition(self, game_state: Dict) -> Tuple[bool, Optional[PhaseType]]:
        """
        Check if phase can transition to next phase.
        
        Args:
            game_state: Current game state
            
        Returns:
            Tuple: (can_transition, next_phase_type)
        """
        pass
    
    @abstractmethod
    def handle_action(self, action_type: str, player_id: int, data: Any, game_state: Dict) -> Dict:
        """
        Handle a player action during this phase.
        
        Args:
            action_type: Type of action
            player_id: Player performing action
            data: Action data
            game_state: Current game state
            
        Returns:
            Dict: Action result
        """
        pass


class LobbyPhase(GamePhase):
    """
    Lobby phase where players join the game.
    
    This phase waits for enough players to join before allowing the game to start.
    """
    
    def __init__(self):
        super().__init__(PhaseType.LOBBY)
    
    def _on_start(self) -> Dict[str, Any]:
        """Initialize lobby."""
        return {
            "message": "🎮 **Truth Wars Lobby**\n\nWaiting for players to join...\nMinimum: 1 player, Maximum: 10 players",
            "lobby_open": True
        }
    
    def _on_end(self) -> Dict[str, Any]:
        """Close lobby."""
        return {
            "message": "Lobby closed. Starting role assignment...",
            "lobby_open": False
        }
    
    def can_transition(self, game_state: Dict) -> Tuple[bool, Optional[PhaseType]]:
        """Check if enough players have joined to start."""
        player_count = len(game_state.get("active_players", []))
        
        # Can start with 1+ players (testing), auto-start with 10
        if player_count >= 10:
            return True, PhaseType.ROLE_ASSIGNMENT
        elif player_count >= 1 and game_state.get("force_start", False):
            return True, PhaseType.ROLE_ASSIGNMENT
            
        return False, None
    
    def handle_action(self, action_type: str, player_id: int, data: Any, game_state: Dict) -> Dict:
        """Handle lobby actions."""
        if action_type == "join":
            return {"success": True, "message": "Player joined lobby"}
        elif action_type == "start":
            # Only game creator can force start
            if player_id == game_state.get("creator_id"):
                return {"success": True, "force_start": True}
            else:
                return {"success": False, "message": "Only game creator can start"}
        else:
            return {"success": False, "message": "Invalid action for lobby phase"}


class RoleAssignmentPhase(GamePhase):
    """
    Role assignment phase where players receive their secret roles.
    
    This phase assigns roles and sends private messages to players with their role info.
    """
    
    def __init__(self):
        super().__init__(PhaseType.ROLE_ASSIGNMENT, duration_seconds=60)
    
    def _on_start(self) -> Dict[str, Any]:
        """Start role assignment."""
        return {
            "message": "🎭 **Assigning Roles...**\n\nCheck your private messages for your role!",
            "roles_being_assigned": True
        }
    
    def _on_end(self) -> Dict[str, Any]:
        """Finish role assignment."""
        return {
            "message": "Roles assigned! The game begins...",
            "roles_assigned": True
        }
    
    def can_transition(self, game_state: Dict) -> Tuple[bool, Optional[PhaseType]]:
        """Transition when all roles are assigned or time expires."""
        all_assigned = game_state.get("all_roles_assigned", False)
        # For now, transition immediately after a short delay to allow role messages to be sent
        return all_assigned or self.is_expired(), PhaseType.NEWS
    
    def handle_action(self, action_type: str, player_id: int, data: Any, game_state: Dict) -> Dict:
        """Role assignment phase doesn't accept player actions."""
        return {"success": False, "message": "Cannot take actions during role assignment"}


class NewsPhase(GamePhase):
    """
    News phase where a headline is presented for discussion.
    
    This phase displays a headline and gives players time to read and react.
    """
    
    def __init__(self):
        super().__init__(PhaseType.NEWS, duration_seconds=30)
    
    def _on_start(self) -> Dict[str, Any]:
        """Present the headline."""
        return {
            "message": "📰 **Breaking News Alert!**\n\nA new headline has appeared. Take a moment to read and consider...",
            "headline_presented": True
        }
    
    def _on_end(self) -> Dict[str, Any]:
        """Move to discussion."""
        return {
            "message": "💬 **Discussion Phase**\n\nDiscuss whether this headline is REAL or FAKE!\nUse your abilities and share your thoughts.",
            "discussion_starting": True
        }
    
    def can_transition(self, game_state: Dict) -> Tuple[bool, Optional[PhaseType]]:
        """Always transition to discussion after time limit."""
        return self.is_expired(), PhaseType.DISCUSSION
    
    def handle_action(self, action_type: str, player_id: int, data: Any, game_state: Dict) -> Dict:
        """Limited actions during news phase."""
        if action_type == "quick_reaction":
            # Allow players to react with emojis
            return {"success": True, "reaction": data.get("emoji", "🤔")}
        else:
            return {"success": False, "message": "Limited actions during news phase"}


class DiscussionPhase(GamePhase):
    """
    Discussion phase where players debate and use abilities.
    
    This is the main social deduction phase where players try to identify
    misinformers and determine if the headline is real or fake.
    """
    
    def __init__(self):
        super().__init__(PhaseType.DISCUSSION, duration_seconds=300)  # 5 minutes
    
    def _on_start(self) -> Dict[str, Any]:
        """Start discussion."""
        return {
            "message": "💬 **Discussion Time!**\n\n• Share your thoughts about the headline\n• Vote TRUST or FLAG when you're ready\n• Use your role abilities\n• Watch for suspicious behavior\n\n⏰ 5 minutes to discuss (or until everyone votes)!",
            "discussion_active": True
        }
    
    def _on_end(self) -> Dict[str, Any]:
        """End discussion, move to voting."""
        return {
            "message": "⏰ **Time's Up!**\n\n🗳️ **Voting Phase**\nTime to vote someone out. Who do you think is spreading misinformation?",
            "voting_starting": True
        }
    
    def can_transition(self, game_state: Dict) -> Tuple[bool, Optional[PhaseType]]:
        """Transition when time expires, all players ready, or all players have voted."""
        all_ready = game_state.get("all_players_ready", False)
        all_voted = game_state.get("all_players_voted", False)
        return all_ready or all_voted or self.is_expired(), PhaseType.VOTING
    
    def handle_action(self, action_type: str, player_id: int, data: Any, game_state: Dict) -> Dict:
        """Handle discussion phase actions."""
        if action_type == "chat":
            return {"success": True, "message": data.get("message", "")}
        elif action_type == "use_ability":
            # This would integrate with role system
            return {"success": True, "ability_used": True}
        elif action_type == "ready":
            return {"success": True, "player_ready": True}
        elif action_type == "vote_headline":
            # Handle headline voting during discussion phase
            vote_type = data.get("vote_type")
            headline_id = data.get("headline_id")
            if vote_type in ["trust", "flag"] and headline_id:
                return {"success": True, "vote_type": vote_type, "headline_id": headline_id}
            else:
                return {"success": False, "message": "Invalid headline vote"}
        else:
            return {"success": False, "message": "Invalid action for discussion phase"}


class VotingPhase(GamePhase):
    """
    Voting phase where players vote to eliminate someone.
    
    Players vote for who they think is a misinformer. The player with the most
    votes is eliminated.
    """
    
    def __init__(self):
        super().__init__(PhaseType.VOTING, duration_seconds=120)  # 2 minutes
    
    def _on_start(self) -> Dict[str, Any]:
        """Start voting."""
        return {
            "message": "🗳️ **Voting Phase**\n\nVote for the player you think is spreading misinformation!\n\n⏰ 2 minutes to vote!",
            "voting_active": True,
            "votes": {}
        }
    
    def _on_end(self) -> Dict[str, Any]:
        """End voting."""
        return {
            "message": "⏰ **Voting Complete!**\n\nCounting votes...",
            "voting_complete": True
        }
    
    def can_transition(self, game_state: Dict) -> Tuple[bool, Optional[PhaseType]]:
        """Transition when all votes cast or time expires."""
        all_voted = game_state.get("all_players_voted", False)
        return all_voted or self.is_expired(), PhaseType.RESOLUTION
    
    def handle_action(self, action_type: str, player_id: int, data: Any, game_state: Dict) -> Dict:
        """Handle voting actions."""
        if action_type == "vote":
            target_id = data.get("target_id")
            if target_id and target_id != player_id:  # Can't vote for yourself
                return {"success": True, "vote_cast": target_id}
            else:
                return {"success": False, "message": "Invalid vote target"}
        else:
            return {"success": False, "message": "Only voting allowed in this phase"}


class ResolutionPhase(GamePhase):
    """
    Resolution phase where vote results are revealed and players eliminated.
    
    This phase reveals who was voted out, shows their role, and checks win conditions.
    """
    
    def __init__(self):
        super().__init__(PhaseType.RESOLUTION, duration_seconds=45)
    
    def _on_start(self) -> Dict[str, Any]:
        """Start resolution."""
        return {
            "message": "⚖️ **Resolution Phase**\n\nRevealing results...",
            "resolving": True
        }
    
    def _on_end(self) -> Dict[str, Any]:
        """End resolution."""
        return {
            "message": "Resolution complete. Preparing next round...",
            "resolution_complete": True
        }
    
    def can_transition(self, game_state: Dict) -> Tuple[bool, Optional[PhaseType]]:
        """Check win conditions or continue to next round."""
        if game_state.get("game_over", False):
            return True, PhaseType.GAME_END
        elif self.is_expired():
            return True, PhaseType.NEWS  # Next round
        else:
            return False, None
    
    def handle_action(self, action_type: str, player_id: int, data: Any, game_state: Dict) -> Dict:
        """No actions during resolution."""
        return {"success": False, "message": "No actions allowed during resolution"}


class GameEndPhase(GamePhase):
    """
    Game end phase where final results are shown.
    
    This phase reveals all roles and shows educational content about the headlines used.
    """
    
    def __init__(self):
        super().__init__(PhaseType.GAME_END)
    
    def _on_start(self) -> Dict[str, Any]:
        """Show game end results."""
        return {
            "message": "🎉 **Game Over!**\n\nRevealing all roles and showing final results...",
            "game_ended": True
        }
    
    def _on_end(self) -> Dict[str, Any]:
        """Complete the game."""
        return {
            "message": "Thanks for playing Truth Wars! 🎮\n\nType /truthwars to start a new game.",
            "ready_for_new_game": True
        }
    
    def can_transition(self, game_state: Dict) -> Tuple[bool, Optional[PhaseType]]:
        """Game end is final phase."""
        return False, None
    
    def handle_action(self, action_type: str, player_id: int, data: Any, game_state: Dict) -> Dict:
        """Limited actions at game end."""
        if action_type == "new_game":
            return {"success": True, "start_new_game": True}
        else:
            return {"success": False, "message": "Game has ended"}


class GameStateMachine:
    """
    Manages transitions between game phases.
    
    This coordinates the entire game flow and handles phase transitions.
    """
    
    def __init__(self):
        """Initialize the state machine."""
        self.current_phase: Optional[GamePhase] = None
        self.phase_history: List[PhaseType] = []
        
    def start_game(self) -> Dict[str, Any]:
        """Start a new game in lobby phase."""
        self.current_phase = LobbyPhase()
        result = self.current_phase.start()
        self.phase_history.append(PhaseType.LOBBY)
        
        logger.info("Game started in lobby phase")
        return result
    
    def get_current_phase_type(self) -> Optional[PhaseType]:
        """Get the current phase type."""
        return self.current_phase.phase_type if self.current_phase else None
    
    def get_time_remaining(self) -> Optional[int]:
        """Get seconds remaining in current phase."""
        return self.current_phase.time_remaining() if self.current_phase else None
    
    def can_transition(self, game_state: Dict) -> bool:
        """Check if current phase can transition."""
        if not self.current_phase:
            return False
            
        can_transition, _ = self.current_phase.can_transition(game_state)
        return can_transition
    
    def transition_phase(self, game_state: Dict) -> Optional[Dict[str, Any]]:
        """
        Transition to the next phase if possible.
        
        Args:
            game_state: Current game state
            
        Returns:
            Optional[Dict]: Transition result or None if no transition
        """
        if not self.current_phase:
            return None
            
        can_transition, next_phase_type = self.current_phase.can_transition(game_state)
        
        if not can_transition or not next_phase_type:
            return None
            
        # End current phase
        end_result = self.current_phase.end()
        
        # Create next phase
        phase_classes = {
            PhaseType.LOBBY: LobbyPhase,
            PhaseType.ROLE_ASSIGNMENT: RoleAssignmentPhase,
            PhaseType.NEWS: NewsPhase,
            PhaseType.DISCUSSION: DiscussionPhase,
            PhaseType.VOTING: VotingPhase,
            PhaseType.RESOLUTION: ResolutionPhase,
            PhaseType.GAME_END: GameEndPhase
        }
        
        if next_phase_type not in phase_classes:
            logger.error(f"Unknown phase type: {next_phase_type}")
            return None
            
        # Transition to new phase
        self.current_phase = phase_classes[next_phase_type]()
        start_result = self.current_phase.start()
        self.phase_history.append(next_phase_type)
        
        logger.info(f"Phase transition: {self.phase_history[-2]} -> {next_phase_type}")
        
        return {
            "transition": True,
            "from_phase": self.phase_history[-2].value,
            "to_phase": next_phase_type.value,
            "end_result": end_result,
            "start_result": start_result
        }
    
    def handle_action(self, action_type: str, player_id: int, data: Any, game_state: Dict) -> Dict:
        """
        Handle a player action in the current phase.
        
        Args:
            action_type: Type of action
            player_id: Player ID
            data: Action data
            game_state: Current game state
            
        Returns:
            Dict: Action result
        """
        if not self.current_phase:
            return {"success": False, "message": "No active game phase"}
            
        return self.current_phase.handle_action(action_type, player_id, data, game_state)
    
    def force_transition(self, next_phase_type: PhaseType, game_state: Dict) -> Dict[str, Any]:
        """
        Force transition to a specific phase (for admin/debugging).
        
        Args:
            next_phase_type: Phase to transition to
            game_state: Current game state
            
        Returns:
            Dict: Transition result
        """
        # End current phase if exists
        if self.current_phase:
            self.current_phase.end()
            
        # Create and start new phase
        phase_classes = {
            PhaseType.LOBBY: LobbyPhase,
            PhaseType.ROLE_ASSIGNMENT: RoleAssignmentPhase,
            PhaseType.NEWS: NewsPhase,
            PhaseType.DISCUSSION: DiscussionPhase,
            PhaseType.VOTING: VotingPhase,
            PhaseType.RESOLUTION: ResolutionPhase,
            PhaseType.GAME_END: GameEndPhase
        }
        
        self.current_phase = phase_classes[next_phase_type]()
        result = self.current_phase.start()
        self.phase_history.append(next_phase_type)
        
        logger.warning(f"Forced phase transition to: {next_phase_type}")
        return result 