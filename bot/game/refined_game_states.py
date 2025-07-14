"""
Truth Wars Refined Game State Machine

This module manages the refined game state transitions for Truth Wars,
implementing the new 5-round structure with Trust/Flag voting system.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
import inspect

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class PhaseType(Enum):
    """Define the different phases in refined Truth Wars."""
    LOBBY = "lobby"
    ROLE_ASSIGNMENT = "role_assignment"
    HEADLINE_REVEAL = "headline_reveal"
    DISCUSSION = "discussion"
    VOTING = "voting"
    ROUND_RESULTS = "round_results"
    PLAYER_VOTING = "player_voting"  # New phase for player accusation voting
    SNIPE_OPPORTUNITY = "snipe_opportunity"
    AWAIT_CONTINUE = "await_continue"
    GAME_END = "game_end"


class RefinedGameStateMachine:
    """
    State machine for managing refined Truth Wars game flow.
    
    Handles the 5-round structure with:
    - Headline presentation and discussion
    - Trust/Flag voting system
    - Reputation tracking
    - Shadow ban mechanics
    - Snipe opportunities every 2 rounds
    """
    
    def __init__(self):
        """Initialize the game state machine."""
        self.current_phase = PhaseType.LOBBY
        self.phase_start_time = datetime.now(timezone.utc)
        self.round_number = 0
        self.max_rounds = 5
        self.phase_durations = {
            PhaseType.LOBBY: 180,  # 3 minutes to join (reduced from 5)
            PhaseType.ROLE_ASSIGNMENT: 45,  # 45 seconds to read roles (reduced from 60)
            PhaseType.HEADLINE_REVEAL: 1,  # reduced to 1 second to immediately enter discussion phase
            PhaseType.DISCUSSION: 120,  # 2 minutes for discussion (reduced from 3)
            PhaseType.VOTING: 45,  # 45 seconds for Trust/Flag voting (reduced from 60)
            PhaseType.ROUND_RESULTS: 15,  # 15 seconds to see results (reduced from 45)
            PhaseType.SNIPE_OPPORTUNITY: 60,  # 1 minute for snipe attempts (reduced from 90)
            PhaseType.PLAYER_VOTING: 45,  # 45 seconds for shadow ban voting
            PhaseType.AWAIT_CONTINUE: 30,  # 30 seconds to continue (new phase for post-results pause)
            PhaseType.GAME_END: 60  # 1 minute to see final results (reduced from 120)
        }
        
        # Track game state for win conditions
        self.fake_headlines_trusted = 0
        self.fake_headlines_flagged = 0
        # v3: Fact Checker can snipe once per game in rounds 1-4
        self.snipe_rounds = [1, 2, 3, 4]
        
    def start_game(self) -> Dict[str, Any]:
        """
        Start the game from lobby.
        
        Returns:
            Dict: Transition result
        """
        if self.current_phase != PhaseType.LOBBY:
            return {"success": False, "message": "Game already started"}
        
        self.current_phase = PhaseType.LOBBY
        self.phase_start_time = datetime.now(timezone.utc)
        
        return {
            "success": True,
            "phase": self.current_phase.value,
            "message": "Game lobby started",
            "time_limit": self.phase_durations[self.current_phase]
        }
    
    def can_transition(self, game_state: Dict[str, Any]) -> bool:
        """
        Check if current phase can transition to next.
        
        Args:
            game_state: Current game state with player data
            
        Returns:
            bool: True if phase can transition
        """
        # Check time-based transitions
        time_elapsed = (datetime.now(timezone.utc) - self.phase_start_time).total_seconds()
        phase_time_limit = self.phase_durations.get(self.current_phase, 300)
        
        if self.current_phase == PhaseType.LOBBY:
            # Can start if creator forces start or time limit reached
            return game_state.get("force_start", False) or time_elapsed >= phase_time_limit
            
        elif self.current_phase == PhaseType.ROLE_ASSIGNMENT:
            # Transition when all roles assigned and time passed
            return (game_state.get("all_roles_assigned", False) and 
                   time_elapsed >= 20)  # Minimum 20 seconds to read roles
                   
        elif self.current_phase == PhaseType.HEADLINE_REVEAL:
            # Always transition after time limit
            return time_elapsed >= phase_time_limit
            
        elif self.current_phase == PhaseType.DISCUSSION:
            # Transition after 3 minutes OR when all eligible players have voted
            all_voted = game_state.get("all_eligible_voted", False)
            return all_voted or time_elapsed >= phase_time_limit
            
        elif self.current_phase == PhaseType.VOTING:
            # Transition when all eligible players voted or time up
            return (game_state.get("all_eligible_voted", False) or 
                   time_elapsed >= phase_time_limit)
        elif self.current_phase == PhaseType.PLAYER_VOTING:
            # Transition when all eligible players have voted or time is up
            return (game_state.get("all_eligible_voted", False) or
                    time_elapsed >= phase_time_limit)
                   
        elif self.current_phase == PhaseType.ROUND_RESULTS:
            # Always transition after showing results
            return time_elapsed >= phase_time_limit
            
        elif self.current_phase == PhaseType.SNIPE_OPPORTUNITY:
            # Transition when snipe used or time up
            return time_elapsed >= phase_time_limit
            
        elif self.current_phase == PhaseType.AWAIT_CONTINUE:
            # Transition when awaiting continue
            return time_elapsed >= phase_time_limit
            
        elif self.current_phase == PhaseType.GAME_END:
            # Game stays in end state
            return False
            
        return False
    
    def transition_phase(self, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Transition to the next phase.
        
        Args:
            game_state: Current game state
            
        Returns:
            Optional[Dict]: Transition result or None if no transition
        """
        if not self.can_transition(game_state):
            return None
            
        previous_phase = self.current_phase
        
        if self.current_phase == PhaseType.LOBBY:
            self.current_phase = PhaseType.ROLE_ASSIGNMENT
            
        elif self.current_phase == PhaseType.ROLE_ASSIGNMENT:
            self.current_phase = PhaseType.HEADLINE_REVEAL
            self.round_number = 1
            
        elif self.current_phase == PhaseType.HEADLINE_REVEAL:
            self.current_phase = PhaseType.DISCUSSION
            
        elif self.current_phase == PhaseType.DISCUSSION:
            self.current_phase = PhaseType.VOTING
            
        elif self.current_phase == PhaseType.VOTING:
            self.current_phase = PhaseType.ROUND_RESULTS
            
        elif self.current_phase == PhaseType.ROUND_RESULTS:
            # Simplified flow: resolve results then either snipe (rounds 2 & 4) or move to next headline
            if self._should_end_game(game_state):
                self.current_phase = PhaseType.GAME_END
            elif self.round_number in self.snipe_rounds:
                self.current_phase = PhaseType.SNIPE_OPPORTUNITY
            else:
                if self.round_number < self.max_rounds:
                    self.round_number += 1
                    self.current_phase = PhaseType.HEADLINE_REVEAL
                else:
                    self.current_phase = PhaseType.GAME_END
            # Return transition result immediately
            return {
                "success": True,
                "from_phase": previous_phase.value,
                "to_phase": self.current_phase.value,
                "round_number": self.round_number,
                "time_limit": self.phase_durations.get(self.current_phase, 300)
            }
        
        elif self.current_phase == PhaseType.SNIPE_OPPORTUNITY:
            # After snipe phase, proceed to group shadow-ban voting unless game ends
            if self._should_end_game(game_state):
                self.current_phase = PhaseType.GAME_END
            else:
                # === NEW: If a snipe already occurred this round, skip player voting ===
                if game_state.get("snipe_used_this_round", False):
                    if self.round_number < self.max_rounds:
                        self.round_number += 1
                        self.current_phase = PhaseType.HEADLINE_REVEAL
                    else:
                        self.current_phase = PhaseType.GAME_END
                else:
                    self.current_phase = PhaseType.PLAYER_VOTING
        
        elif self.current_phase == PhaseType.PLAYER_VOTING:
            # After player-voting phase, either continue with next round or end
            if self._should_end_game(game_state):
                self.current_phase = PhaseType.GAME_END
            elif self.round_number < self.max_rounds:
                self.round_number += 1
                self.current_phase = PhaseType.HEADLINE_REVEAL
            else:
                self.current_phase = PhaseType.GAME_END
        
        elif self.current_phase == PhaseType.AWAIT_CONTINUE:
            # After results, check if game should end
            if self._should_end_game(game_state):
                self.current_phase = PhaseType.GAME_END
            elif self.round_number < self.max_rounds:
                self.round_number += 1
                self.current_phase = PhaseType.HEADLINE_REVEAL
            else:
                self.current_phase = PhaseType.GAME_END
        
        # Update phase start time
        self.phase_start_time = datetime.now(timezone.utc)
        
        # Log transition
        logger.info(f"Phase transition: {previous_phase.value} -> {self.current_phase.value}, Round: {self.round_number}")
        
        return {
            "success": True,
            "from_phase": previous_phase.value,
            "to_phase": self.current_phase.value,
            "round_number": self.round_number,
            "time_limit": self.phase_durations.get(self.current_phase, 300)
        }
    
    def force_transition(self, target_phase: PhaseType, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Force transition to a specific phase.
        
        Args:
            target_phase: Phase to transition to
            game_state: Current game state
            
        Returns:
            Dict: Transition result
        """
        previous_phase = self.current_phase
        self.current_phase = target_phase
        self.phase_start_time = datetime.now(timezone.utc)
        
        logger.info(f"Forced phase transition: {previous_phase.value} -> {target_phase.value}")
        
        return {
            "success": True,
            "from_phase": previous_phase.value,
            "to_phase": target_phase.value,
            "round_number": self.round_number,
            "forced": True
        }
    
    def get_current_phase_type(self) -> PhaseType:
        """Get current phase type."""
        return self.current_phase
    
    def get_time_remaining(self) -> int:
        """
        Get seconds remaining in current phase.
        
        Returns:
            int: Seconds remaining (0 if expired)
        """
        if self.current_phase not in self.phase_durations:
            return 0
            
        elapsed = (datetime.now(timezone.utc) - self.phase_start_time).total_seconds()
        remaining = self.phase_durations[self.current_phase] - elapsed
        
        return max(0, int(remaining))
    
    def handle_action(self, action: str, player_id: int, data: Any, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle player action in current phase.
        
        Args:
            action: Action type
            player_id: Player performing action
            data: Action data
            game_state: Current game state
            
        Returns:
            Dict: Action result
        """
        if self.current_phase == PhaseType.VOTING:
            if action == "vote_headline":
                return self._handle_headline_vote(player_id, data, game_state)
                
        elif self.current_phase == PhaseType.SNIPE_OPPORTUNITY:
            if action == "snipe_player":
                return self._handle_snipe_attempt(player_id, data, game_state)
        
        elif self.current_phase == PhaseType.DISCUSSION:
            if action == "send_message":
                return self._handle_discussion_message(player_id, data, game_state)
            elif action == "vote_headline":
                return self._handle_headline_vote(player_id, data, game_state)
        
        elif self.current_phase == PhaseType.PLAYER_VOTING:
            if action == "vote_player":
                return self._handle_player_vote(player_id, data, game_state)
        
        return {"success": False, "message": f"Action '{action}' not available in {self.current_phase.value} phase"}
    
    def _handle_headline_vote(self, player_id: int, vote_data: Dict, game_state: Dict) -> Dict[str, Any]:
        """Handle Trust/Flag vote on headline."""
        # Check if player is eligible to vote
        if player_id in game_state.get("eliminated_players", []):
            return {"success": False, "message": "Eliminated players cannot vote"}
        
        # Check if player has 0 reputation (Ghost Viewer)
        player_reputation = game_state.get("player_reputation", {}).get(player_id, 3)
        if player_reputation <= 0:
            return {"success": False, "message": "Ghost Viewers (0 RP) cannot vote"}
        
        # Check if player is shadow banned
        if game_state.get("shadow_banned_players", {}).get(player_id, False):
            return {"success": False, "message": "Shadow banned players cannot vote"}
        
        vote_choice = vote_data.get("vote_type")  # "trust" or "flag"
        if vote_choice not in ["trust", "flag"]:
            return {"success": False, "message": "Vote must be 'trust' or 'flag'"}
        
        return {
            "success": True,
            "message": f"Vote recorded: {vote_choice}",
            "vote": vote_choice,
            "player_id": player_id
        }
    
    def _handle_snipe_attempt(self, player_id: int, snipe_data: Dict, game_state: Dict) -> Dict[str, Any]:
        """Handle snipe attempt during snipe opportunity phase."""
        target_id = snipe_data.get("target_id")
        
        if not target_id:
            return {"success": False, "message": "Must specify target for snipe"}
        
        # Check if player can snipe
        player_role = game_state.get("player_roles", {}).get(player_id, {}).get("role")
        if not player_role or not player_role.can_use_snipe():
            return {"success": False, "message": "You cannot use snipe ability"}
        
        # Execute snipe through role (include sniper_id for logging/penalties)
        snipe_result = player_role.use_snipe(target_id, game_state, sniper_id=player_id)
        
        return snipe_result
    
    def _handle_discussion_message(self, player_id: int, message_data: Dict, game_state: Dict) -> Dict[str, Any]:
        """Handle message during discussion phase."""
        # Check if player is shadow banned
        if game_state.get("shadow_banned_players", {}).get(player_id, False):
            return {"success": False, "message": "You are shadow banned and cannot speak this round"}
        
        message = message_data.get("message", "")
        if len(message.strip()) == 0:
            return {"success": False, "message": "Message cannot be empty"}
        
        if len(message) > 500:
            return {"success": False, "message": "Message too long (max 500 characters)"}
        
        return {
            "success": True,
            "message": "Message sent",
            "content": message,
            "player_id": player_id
        }
    
    def _handle_player_vote(self, player_id: int, vote_data: Dict, game_state: Dict) -> Dict[str, Any]:
        """Handle vote for shadow-ban during PLAYER_VOTING phase."""
        target_id = vote_data.get("target_id")
        if not target_id:
            return {"success": False, "message": "Must specify a player to vote"}
        # Eligibility checks (similar to headline vote)
        if player_id in game_state.get("eliminated_players", []):
            return {"success": False, "message": "Eliminated players cannot vote"}
        if game_state.get("player_reputation", {}).get(player_id, 3) <= 0:
            return {"success": False, "message": "Ghost Viewers (0 RP) cannot vote"}
        if game_state.get("shadow_banned_players", {}).get(player_id, False):
            return {"success": False, "message": "Shadow banned players cannot vote"}
        return {
            "success": True,
            "message": f"Vote recorded for target {target_id}",
            "target_id": target_id,
            "player_id": player_id
        }
    
    def _should_end_game(self, game_state: Dict[str, Any]) -> bool:
        """
        Check if game should end based on win conditions.
        
        Args:
            game_state: Current game state
            
        Returns:
            bool: True if game should end
        """
        # CRITICAL FIX: Comprehensive win condition logging
        rounds_completed = game_state.get("rounds_completed", 0)
        fake_trusted = game_state.get("fake_headlines_trusted", 0)
        fake_flagged = game_state.get("fake_headlines_flagged", 0)
        
        logger.info(f"Win condition check: rounds_completed={rounds_completed}, "
                   f"fake_trusted={fake_trusted}, fake_flagged={fake_flagged}, "
                   f"state_machine_round={self.round_number}, max_rounds={self.max_rounds}")
        
        # CRITICAL FIX: Check for 5 rounds completed (mandatory end condition)
        if rounds_completed >= 5:
            logger.info(f"Game should end: 5 rounds completed ({rounds_completed})")
            return True
        
        # Check if we've reached max rounds (fallback check)
        if self.round_number >= self.max_rounds:
            logger.info(f"Game should end: max rounds reached ({self.round_number}/{self.max_rounds})")
            return True
        
        # Check Scammer win condition: 3 fake headlines trusted
        if fake_trusted >= 3:
            logger.info(f"Game should end: 3 fake headlines trusted ({fake_trusted})")
            return True
        
        # Check Truth Team win condition: 3 fake headlines flagged
        if fake_flagged >= 3:
            logger.info(f"Game should end: 3 fake headlines flagged ({fake_flagged})")
            return True
        
        # Check if all players of one faction are shadow banned/eliminated
        # BUT only if there are players from both factions (multi-player mode)
        total_players = len(game_state.get("player_roles", {}))
        
        # In single-player mode, don't end game based on faction balance
        if total_players == 1:
            return False
        
        active_truth_seekers = 0
        active_scammers = 0
        
        for player_id, role_info in game_state.get("player_roles", {}).items():
            if player_id in game_state.get("eliminated_players", []):
                continue
            if game_state.get("shadow_banned_players", {}).get(player_id, False):
                continue
            if game_state.get("player_reputation", {}).get(player_id, 3) <= 0:
                continue
                
            role = role_info.get("role")
            if role and role.faction == "truth_seekers":
                active_truth_seekers += 1
            elif role and role.faction == "misinformers":
                active_scammers += 1
        
        # Game ends if one faction has no active players (only in multi-player)
        if active_truth_seekers == 0 or active_scammers == 0:
            logger.info(f"Game should end: faction elimination (truth_seekers={active_truth_seekers}, scammers={active_scammers})")
            return True
        
        logger.info("Game continues: no win conditions met")
        return False
    
    def get_game_status(self) -> Dict[str, Any]:
        """
        Get comprehensive game status.
        
        Returns:
            Dict: Current game status
        """
        return {
            "current_phase": self.current_phase.value,
            "round_number": self.round_number,
            "max_rounds": self.max_rounds,
            "time_remaining": self.get_time_remaining(),
            "fake_headlines_trusted": self.fake_headlines_trusted,
            "fake_headlines_flagged": self.fake_headlines_flagged,
            "snipe_available": self.round_number in self.snipe_rounds
        }
    
    def update_win_condition_counters(self, headline_was_fake: bool, majority_trusted: bool) -> None:
        """
        Update win condition counters after a round.
        
        Args:
            headline_was_fake: Whether the headline was fake
            majority_trusted: Whether majority voted to trust it
        """
        if headline_was_fake:
            if majority_trusted:
                self.fake_headlines_trusted += 1
                logger.info(f"Fake headline trusted! Count: {self.fake_headlines_trusted}/3")
            else:
                self.fake_headlines_flagged += 1
                logger.info(f"Fake headline flagged! Count: {self.fake_headlines_flagged}/3")
    
    def get_phase_description(self) -> str:
        """
        Get user-friendly description of current phase.
        
        Returns:
            str: Phase description
        """
        descriptions = {
            PhaseType.LOBBY: "⏳ **Waiting for players to join...**\nPlayers can join the game and the creator can start when ready.",
            
            PhaseType.ROLE_ASSIGNMENT: "🎭 **Role Assignment**\nPlayers are receiving their secret roles and learning their objectives.",
            
            PhaseType.HEADLINE_REVEAL: f"📰 **Round {self.round_number}: Headline Reveal**\nA new headline has been presented. Study it carefully!",
            
            PhaseType.DISCUSSION: f"💬 **Round {self.round_number}: Discussion Phase**\nDebate whether the headline is REAL or FAKE. All players must participate!",
            
            PhaseType.VOTING: f"🗳️ **Round {self.round_number}: Voting Time**\nVote whether to TRUST or FLAG this headline!",
            
            PhaseType.ROUND_RESULTS: f"📊 **Round {self.round_number}: Results**\nSee how everyone voted and learn the truth about the headline.",
            
            PhaseType.SNIPE_OPPORTUNITY: f"🎯 **Round {self.round_number}: Snipe Opportunity**\nSpecial roles can use their snipe abilities to shadow ban suspected enemies!",
            
            PhaseType.PLAYER_VOTING: f"🗳️ **Round {self.round_number}: Player Voting**\nVote to shadow ban suspected enemies!",
            
            PhaseType.AWAIT_CONTINUE: "⏸️ **Awaiting Continue**\nPress continue to proceed to the next round or end the game.",
            
            PhaseType.GAME_END: "🏁 **Game Over**\nSee final results and learn who was on which team!"
        }
        
        return descriptions.get(self.current_phase, "Unknown phase") 