"""
Truth Wars Refined Role System

This module defines the new role system for the refined Truth Wars game,
focusing on media literacy education with reputation-based gameplay.
"""

import random
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from enum import Enum


class RoleType(Enum):
    """Define the different role types in Truth Wars."""
    FACT_CHECKER = "fact_checker"
    SCAMMER = "scammer"
    INFLUENCER = "influencer"
    NORMIE = "normie"


class Role(ABC):
    """
    Abstract base class for all Truth Wars roles.
    
    Each role has specific abilities and win conditions in the new
    reputation-based game system.
    """
    
    def __init__(self, role_type: RoleType, faction: str):
        """Initialize role with type and faction."""
        self.role_type = role_type
        self.faction = faction
        self.has_used_snipe = False  # Track if snipe ability used
        self.is_shadow_banned = False  # Track shadow ban status
        
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the display name of this role."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get detailed description of the role."""
        pass
    
    @abstractmethod
    def get_win_condition(self) -> str:
        """Get the win condition for this role."""
        pass
    
    @abstractmethod
    def get_abilities(self) -> List[str]:
        """Get list of abilities available to this role."""
        pass
    
    def can_use_snipe(self) -> bool:
        """Check if this role can use snipe ability."""
        return getattr(self, 'snipe_ability', False) and not self.has_used_snipe
    
    def use_snipe(self, target_user_id: int, game_state: Dict, sniper_id: int) -> Dict[str, Any]:
        """
        Use the snipe ability to shadow ban a target.
        
        Args:
            target_user_id: The player to target
            game_state: Current game state
            sniper_id: The player using the snipe ability
            
        Returns:
            Dict with result of snipe attempt
        """
        if not self.can_use_snipe():
            return {"success": False, "message": "Cannot use snipe ability"}
            
        # Mark snipe as used
        self.has_used_snipe = True
        
        # Check if target is correct (implemented in subclasses)
        return self._execute_snipe(target_user_id, game_state, sniper_id)
    
    def _execute_snipe(self, target_user_id: int, game_state: Dict, sniper_id: int) -> Dict[str, Any]:
        """Execute the snipe attempt (implemented in subclasses)."""
        return {"success": False, "message": "Snipe not implemented for this role"}


class FactChecker(Role):
    """
    🧠 Fact Checker Role
    
    - Receives correct answer every round except one (random)
    - One-time snipe ability to shadow ban suspected Scammer
    - Must be subtle to avoid being targeted
    - Win condition: Truth team wins
    """
    
    def __init__(self):
        super().__init__(RoleType.FACT_CHECKER, "truth_seekers")
        self.snipe_ability = True
        self.no_info_round = None  # Will be set randomly (1-5)
        # v3: allow up to 3 peeks per game, not in consecutive rounds
        self.peeks_left: int = 3
        self.last_peek_round: int = 0  # Round number when the last peek was used (0 = never)
        
    @property
    def name(self) -> str:
        return "🧠 Fact Checker"
    
    def get_description(self) -> str:
        return (
            "🧠 **Fact Checker**\n\n"
            "🎯 **Your Mission:**\n"
            "• Help your team identify fake news\n"
            "• Guide discussions subtly without revealing your role\n"
            "• Use your snipe ability wisely\n\n"
            "🔍 *Special Abilities:*\n"
            "• You receive the correct answer for most headlines\n"
            "• **WARNING**: One round will have NO INFO - be careful!\n"
            "• One-time **SNIPE** ability to shadow ban a suspected Scammer\n\n"
            "⚠️ **Risk**: If you snipe the wrong person, YOU get shadow banned!\n\n"
            "🏆 **You win when**: Truth team identifies 3 fake headlines correctly"
        )
    
    def get_win_condition(self) -> str:
        return "Help your team flag 3 fake headlines correctly"
    
    def get_abilities(self) -> List[str]:
        """Get list of abilities available to Fact Checker."""
        abilities = [
            "Receive correct answer for most headlines (except one random round)",
            "One-time SNIPE ability to shadow ban suspected Scammer"
        ]
        if not self.has_used_snipe:
            abilities.append("SNIPE ability available")
        else:
            abilities.append("SNIPE ability used")
        return abilities
    
    def set_no_info_round(self, round_num: int) -> None:
        """Set which round this Fact Checker won't receive info."""
        self.no_info_round = round_num
    
    def should_receive_info(self, current_round: int) -> bool:
        """Check if Fact Checker should receive info this round."""
        return current_round != self.no_info_round
    
    def _execute_snipe(self, target_user_id: int, game_state: Dict, sniper_id: int) -> Dict[str, Any]:
        """Execute snipe attempt against suspected Scammer."""
        target_role = game_state.get("player_roles", {}).get(target_user_id, {}).get("role")
        
        # Success if target is actually a Scammer
        if target_role and target_role.role_type == RoleType.SCAMMER:
            return {
                "success": True,
                "message": "Successful snipe! Target was a Scammer.",
                "effect": "shadow_ban_target",
                "target": target_user_id
            }
        else:
            return {
                "success": False,
                "message": "Wrong target! You are now shadow banned.",
                "effect": "shadow_ban_self",
                "target": None,
                "sniper_id": sniper_id
            }

    # === Truth Wars v3 additions ===
    def can_peek_headline(self, current_round: int) -> bool:
        """Determine if the Fact Checker can peek at the headline truth this round.

        - Must have peeks remaining.
        - Cannot peek in two consecutive rounds (ensure a gap of at least 1 round).
        """
        if self.peeks_left <= 0:
            return False
        # If never peeked before, allowed
        if self.last_peek_round == 0:
            return True
        # Enforce non-consecutive rule
        return (current_round - self.last_peek_round) > 1

    def record_peek(self, current_round: int) -> None:
        """Call when the Fact Checker performs a peek.

        Decrements remaining peeks and records the round number.
        """
        if self.peeks_left > 0:
            self.peeks_left -= 1
            self.last_peek_round = current_round


class Scammer(Role):
    """
    😈 Scammer Role
    
    - Knows which headlines are real/fake
    - Goal: Manipulate others into wrong votes
    - One-time snipe ability to target Fact Checker
    - Win condition: Get 3 fake headlines trusted
    """
    
    def __init__(self):
        super().__init__(RoleType.SCAMMER, "misinformers")
        # v3: Scammer no longer has snipe ability
        self.snipe_ability = False
        # New: one-time headline swap ability
        self.has_swapped_headline: bool = False
        
    @property
    def name(self) -> str:
        return "😈 Scammer"
    
    def get_description(self) -> str:
        return (
            "😈 **Scammer**\n\n"
            "🎯 **Your Mission:**\n"
            "• Manipulate others into trusting fake headlines\n"
            "• Blend in with Truth Seekers\n"
            "• Target the Fact Checker with your snipe\n\n"
            "🔍 **Special Abilities:**\n"
            "• You know which headlines are REAL or FAKE\n"
            "• One-time **HEADLINE SWAP** ability – replace the current headline with a new random one (use wisely!)\n"
            "• +1 RP bonus when majority votes incorrectly\n\n"
            "⚠️ **Risk**: Swapping the headline may backfire if the new headline benefits the Truth Seekers!\n\n"
            "🏆 **You win when**: 3 fake headlines are trusted by majority"
        )
    
    def get_win_condition(self) -> str:
        return "Get 3 fake headlines trusted by the majority"
    
    def get_abilities(self) -> List[str]:
        """Get list of abilities available to Scammer."""
        abilities = [
            "Know which headlines are REAL or FAKE",
            "Manipulate others into trusting fake headlines",
            "One-time HEADLINE SWAP ability to replace the current headline"
        ]
        if not self.has_swapped_headline:
            abilities.append("HEADLINE SWAP available (unused)")
        else:
            abilities.append("HEADLINE SWAP used")
        return abilities
    
    def _execute_snipe(self, target_user_id: int, game_state: Dict, sniper_id: int) -> Dict[str, Any]:
        """Execute snipe attempt against suspected Fact Checker."""
        target_role = game_state.get("player_roles", {}).get(target_user_id, {}).get("role")
        
        # Success if target is actually the Fact Checker
        if target_role and target_role.role_type == RoleType.FACT_CHECKER:
            return {
                "success": True,
                "message": "Successful snipe! Target was the Fact Checker.",
                "effect": "shadow_ban_target",
                "target": target_user_id
            }
        else:
            return {
                "success": False,
                "message": "Wrong target! You are now shadow banned.",
                "effect": "shadow_ban_self",
                "target": None,
                "sniper_id": sniper_id
            }


class Influencer(Role):
    """
    🎭 Influencer Role (7+ players only)
    
    - Vote counts double (2x weight)
    - Regular player otherwise
    - Significant impact on voting outcomes
    """
    
    def __init__(self):
        super().__init__(RoleType.INFLUENCER, "truth_seekers")
        
    @property
    def name(self) -> str:
        return "🎭 Influencer"
    
    def get_description(self) -> str:
        return (
            "🎭 **Influencer**\n\n"
            "🎯 **Your Mission:**\n"
            "• Use your influence responsibly\n"
            "• Your vote carries extra weight\n"
            "• Help guide the group to truth\n\n"
            "🔍 **Special Abilities:**\n"
            "• Your vote counts as **2 votes** instead of 1\n"
            "• Significant impact on voting outcomes\n"
            "• No other special knowledge or abilities\n\n"
            "💪 **Responsibility**: Your extra influence can swing close votes!\n\n"
            "🏆 **You win when**: Truth team flags 3 fake headlines correctly"
        )
    
    def get_win_condition(self) -> str:
        return "Use your influence to help the truth team win"
    
    def get_abilities(self) -> List[str]:
        """Get list of abilities available to Influencer."""
        return [
            "Vote counts as 2 votes instead of 1",
            "Significant impact on voting outcomes",
            "Help guide the group to truth"
        ]
    
    def get_vote_weight(self) -> int:
        """Get the vote weight for this role."""
        return 2


class Normie(Role):
    """
    🧍 Normie Role (Misinformed User)
    
    - Regular player with no special abilities
    - Must learn to identify fake news through discussion
    """
    
    def __init__(self):
        super().__init__(RoleType.NORMIE, "truth_seekers")
        
    @property
    def name(self) -> str:
        return "🧍 Misinformed User"
    
    def get_description(self) -> str:
        return (
            "🧍 **Misinformed User (\"Normie\")**\n\n"
            "🎯 **Your Mission:**\n"
            "• Learn to identify fake news through discussion\n"
            "• Listen to others and develop critical thinking\n"
            "• Vote based on your best judgment\n\n"
            "🔍 **Abilities:**\n"
            "• No special knowledge or abilities\n"
            "• Rely on discussion and critical thinking\n\n"
            "📚 **Learning**: This is your chance to develop real media literacy skills!\n\n"
            "🏆 **You win when**: Truth team flags 3 fake headlines correctly"
        )
    
    def get_win_condition(self) -> str:
        return "Help the truth team identify fake news"

    def get_abilities(self) -> List[str]:
        """Get list of abilities available to Normie."""
        return [
            "No special knowledge or abilities",
            "Learn to identify fake news through discussion",
            "Participate in voting and discussion"
        ]


def assign_refined_roles(player_ids: List[int]) -> Dict[int, Role]:
    """
    Assign roles according to the refined Truth Wars system.
    
    Args:
        player_ids: List of player IDs to assign roles to
        
    Returns:
        Dict mapping player_id to Role instance
    """
    player_count = len(player_ids)
    role_assignments = {}
    
    # Shuffle player list for random assignment
    shuffled_players = player_ids.copy()
    random.shuffle(shuffled_players)
    
    if player_count == 5:
        # 5 players: 1 Fact Checker, 1 Scammer, 3 Normies
        role_assignments[shuffled_players[0]] = FactChecker()
        role_assignments[shuffled_players[1]] = Scammer()
        role_assignments[shuffled_players[2]] = Normie()
        role_assignments[shuffled_players[3]] = Normie()
        role_assignments[shuffled_players[4]] = Normie()
        
    elif player_count == 6:
        # 6 players: 1 Fact Checker, 1 Scammer, 4 Normies
        role_assignments[shuffled_players[0]] = FactChecker()
        role_assignments[shuffled_players[1]] = Scammer()
        role_assignments[shuffled_players[2]] = Normie()
        role_assignments[shuffled_players[3]] = Normie()
        role_assignments[shuffled_players[4]] = Normie()
        role_assignments[shuffled_players[5]] = Normie()
        
    elif player_count >= 7:
        # 7+ players: 1 Fact Checker, 2 Scammers, 1 Influencer, rest Normies
        role_assignments[shuffled_players[0]] = FactChecker()
        role_assignments[shuffled_players[1]] = Scammer()
        role_assignments[shuffled_players[2]] = Scammer()
        role_assignments[shuffled_players[3]] = Influencer()
        # Fill remaining slots with Normies
        for i in range(4, player_count):
            role_assignments[shuffled_players[i]] = Normie()
    
    else:
        # Less than 5 players - for testing only
        # Just assign basic roles
        for i, player_id in enumerate(shuffled_players):
            if i == 0:
                role_assignments[player_id] = FactChecker()
            elif i == 1:
                role_assignments[player_id] = Scammer()
            else:
                role_assignments[player_id] = Normie()
    
    # Set random no-info round for Fact Checker
    for role in role_assignments.values():
        if isinstance(role, FactChecker):
            role.set_no_info_round(random.randint(1, 5))
    
    return role_assignments


def get_role_by_type(role_type: RoleType) -> Role:
    """
    Create a role instance by type.
    
    Args:
        role_type: The type of role to create
        
    Returns:
        Role instance
    """
    if role_type == RoleType.FACT_CHECKER:
        return FactChecker()
    elif role_type == RoleType.SCAMMER:
        return Scammer()
    elif role_type == RoleType.INFLUENCER:
        return Influencer()
    elif role_type == RoleType.NORMIE:
        return Normie()
    else:
        raise ValueError(f"Unknown role type: {role_type}")


# Legacy compatibility - keeping old function name but using new logic
def assign_roles(player_ids: List[int]) -> Dict[int, Role]:
    """Legacy function name - redirects to refined role assignment."""
    return assign_refined_roles(player_ids)


def create_role_instance(role_name: str) -> Role:
    """Legacy function - create role by string name."""
    role_map = {
        "fact_checker": RoleType.FACT_CHECKER,
        "scammer": RoleType.SCAMMER,
        "influencer": RoleType.INFLUENCER,
        "normie": RoleType.NORMIE,
        "misinformed_user": RoleType.NORMIE
    }
    
    role_type = role_map.get(role_name.lower())
    if role_type:
        return get_role_by_type(role_type)
    else:
        raise ValueError(f"Unknown role name: {role_name}") 