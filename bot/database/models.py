"""
Database Models for Refined Truth Wars System

This module defines all SQLAlchemy models for the refined Truth Wars game system.
Each model represents a table in the database with relationships supporting:
- Reputation-based gameplay (3 RP system)
- Trust/Flag voting on headlines  
- Shadow ban mechanics via snipe abilities
- Educational media literacy tracking
- Round-based fixed structure (5 rounds)
- Role rotation and strategic depth
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, ForeignKey, Text, JSON, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .database import Base


# Use String for UUID storage since we're using SQLite
def generate_uuid():
    """Generate a UUID string for SQLite compatibility."""
    return str(uuid.uuid4())


# Enums for consistent data types
class GameStatus(enum.Enum):
    WAITING = "waiting"
    ACTIVE = "active" 
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class GamePhase(enum.Enum):
    LOBBY = "lobby"
    ROLE_ASSIGNMENT = "role_assignment"
    ROUND_START = "round_start"
    DISCUSSION = "discussion"
    VOTING = "voting"
    RESOLUTION = "resolution"
    GAME_END = "game_end"


class PlayerFaction(enum.Enum):
    TRUTH_TEAM = "truth_team"
    SCAMMER_TEAM = "scammer_team"


class VoteType(enum.Enum):
    TRUST = "trust"
    FLAG = "flag"


class SnipeResult(enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"


class User(Base):
    """
    User model representing a Telegram user with enhanced media literacy tracking.
    
    This stores user information, game statistics, and learning progress.
    """
    __tablename__ = "users"
    
    # Primary key is Telegram user ID
    id = Column(BigInteger, primary_key=True, doc="Telegram user ID")
    
    # User information
    username = Column(String(255), nullable=True, doc="Telegram username")
    first_name = Column(String(255), nullable=True, doc="User's first name")
    last_name = Column(String(255), nullable=True, doc="User's last name")
    
    # Account status
    is_active = Column(Boolean, default=True, doc="Whether user account is active")
    is_admin = Column(Boolean, default=False, doc="Whether user has admin privileges")
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), doc="Account creation timestamp")
    last_seen_at = Column(DateTime, default=func.now(), doc="Last activity timestamp")
    
    # Enhanced game statistics for refined system
    total_games = Column(Integer, default=0, doc="Total number of games played")
    total_wins = Column(Integer, default=0, doc="Total number of games won")
    truth_team_wins = Column(Integer, default=0, doc="Wins as Truth team member")
    scammer_team_wins = Column(Integer, default=0, doc="Wins as Scammer team member")
    
    # Reputation system stats
    total_reputation_earned = Column(Integer, default=0, doc="Total RP earned across all games")
    average_reputation = Column(Float, default=3.0, doc="Average RP maintained per game")
    
    # Headline voting accuracy
    headlines_voted_on = Column(Integer, default=0, doc="Total headlines voted on")
    correct_votes = Column(Integer, default=0, doc="Number of correct Trust/Flag votes")
    fake_headlines_correctly_flagged = Column(Integer, default=0, doc="Fake headlines correctly identified")
    real_headlines_correctly_trusted = Column(Integer, default=0, doc="Real headlines correctly trusted")
    
    # Role performance tracking
    times_as_fact_checker = Column(Integer, default=0, doc="Times played as Fact Checker")
    times_as_scammer = Column(Integer, default=0, doc="Times played as Scammer")
    times_as_influencer = Column(Integer, default=0, doc="Times played as Influencer")
    times_as_normie = Column(Integer, default=0, doc="Times played as Normie")
    
    # Snipe system stats
    successful_snipes = Column(Integer, default=0, doc="Successful snipe attempts")
    failed_snipes = Column(Integer, default=0, doc="Failed snipe attempts")
    times_shadow_banned = Column(Integer, default=0, doc="Times shadow banned by snipes")
    
    # Learning progress
    media_literacy_level = Column(Integer, default=1, doc="Current media literacy level (1-10)")
    educational_tips_seen = Column(JSON, default=list, doc="List of educational tips user has seen")
    learning_streak = Column(Integer, default=0, doc="Current streak of correct votes")
    best_learning_streak = Column(Integer, default=0, doc="Best learning streak achieved")
    
    # Relationships
    game_players = relationship("GamePlayer", back_populates="user", cascade="all, delete-orphan")
    reputation_history = relationship("PlayerReputationHistory", back_populates="user", cascade="all, delete-orphan")
    headline_votes = relationship("HeadlineVote", back_populates="voter", cascade="all, delete-orphan")
    snipe_actions_given = relationship("SnipeAction", foreign_keys="SnipeAction.sniper_id", back_populates="sniper", cascade="all, delete-orphan")
    snipe_actions_received = relationship("SnipeAction", foreign_keys="SnipeAction.target_id", back_populates="target", cascade="all, delete-orphan")
    
    @property
    def win_rate(self) -> float:
        """Calculate user's win rate as a percentage."""
        if self.total_games == 0:
            return 0.0
        return (self.total_wins / self.total_games) * 100
    
    @property
    def headline_accuracy(self) -> float:
        """Calculate user's headline voting accuracy as a percentage."""
        if self.headlines_voted_on == 0:
            return 0.0
        return (self.correct_votes / self.headlines_voted_on) * 100
    
    @property
    def snipe_success_rate(self) -> float:
        """Calculate user's snipe success rate as a percentage."""
        total_snipes = self.successful_snipes + self.failed_snipes
        if total_snipes == 0:
            return 0.0
        return (self.successful_snipes / total_snipes) * 100
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, ml_level={self.media_literacy_level})>"


class Game(Base):
    """
    Enhanced game model for refined Truth Wars system.
    
    This stores game metadata supporting the fixed 5-round structure.
    """
    __tablename__ = "games"
    
    # Primary key - using String for SQLite compatibility
    id = Column(String(36), primary_key=True, default=generate_uuid, doc="Unique game ID")
    
    # Game configuration
    game_type = Column(String(50), nullable=False, default="truth_wars", doc="Type of game")
    status = Column(Enum(GameStatus), default=GameStatus.WAITING, doc="Current game status")
    
    # Player configuration for refined system
    max_players = Column(Integer, default=8, doc="Maximum number of players (5-8)")
    min_players = Column(Integer, default=5, doc="Minimum number of players to start")
    
    # Refined game structure
    total_rounds = Column(Integer, default=5, doc="Total number of rounds (fixed at 5)")
    current_round = Column(Integer, default=1, doc="Current round number")
    
    # Win conditions tracking
    fake_headlines_trusted = Column(Integer, default=0, doc="Number of fake headlines trusted by majority")
    fake_headlines_flagged = Column(Integer, default=0, doc="Number of fake headlines flagged by majority")
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), doc="Game creation timestamp")
    started_at = Column(DateTime, nullable=True, doc="Game start timestamp")
    completed_at = Column(DateTime, nullable=True, doc="Game completion timestamp")
    
    # Game settings and metadata
    settings = Column(JSON, nullable=True, doc="Game-specific settings and configuration")
    game_metadata = Column(JSON, nullable=True, doc="Additional game metadata")
    
    # Chat information
    chat_id = Column(BigInteger, nullable=True, doc="Telegram chat ID where game is played")
    chat_type = Column(String(20), default="group", doc="Type of chat (group for Truth Wars)")
    
    # Winner tracking
    winning_faction = Column(Enum(PlayerFaction), nullable=True, doc="Faction that won the game")
    win_condition_met = Column(String(100), nullable=True, doc="How the game was won")
    
    # Relationships
    players = relationship("GamePlayer", back_populates="game", cascade="all, delete-orphan")
    truth_wars_data = relationship("TruthWarsGame", back_populates="game", uselist=False, cascade="all, delete-orphan")
    round_results = relationship("RoundResult", back_populates="game", cascade="all, delete-orphan")
    headline_votes = relationship("HeadlineVote", back_populates="game", cascade="all, delete-orphan")
    snipe_actions = relationship("SnipeAction", back_populates="game", cascade="all, delete-orphan")
    
    @property
    def current_players(self) -> int:
        """Get current number of active players in the game."""
        return len([p for p in self.players if p.is_active])
    
    @property
    def truth_team_won(self) -> bool:
        """Check if Truth team won (3 fake headlines flagged)."""
        return self.fake_headlines_flagged >= 3
    
    @property
    def scammer_team_won(self) -> bool:
        """Check if Scammer team won (3 fake headlines trusted)."""
        return self.fake_headlines_trusted >= 3
    
    @property
    def is_game_over(self) -> bool:
        """Check if game has ended due to win condition or round limit."""
        return (self.truth_team_won or 
                self.scammer_team_won or 
                self.current_round > self.total_rounds or
                self.status == GameStatus.COMPLETED)
    
    def __repr__(self) -> str:
        return f"<Game(id={self.id}, round={self.current_round}/{self.total_rounds}, status={self.status.value})>"


class GamePlayer(Base):
    """
    Enhanced game player model with reputation tracking.
    
    This links users to games and stores reputation and Ghost Viewer status.
    """
    __tablename__ = "game_players"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid, doc="Unique player record ID")
    
    # Foreign keys
    game_id = Column(String(36), ForeignKey("games.id"), nullable=False, doc="Game ID")
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, doc="User ID")
    
    # Reputation system (core mechanic of refined system)
    current_reputation = Column(Integer, default=3, doc="Current Reputation Points (0-3)")
    starting_reputation = Column(Integer, default=3, doc="Reputation at game start")
    reputation_lost = Column(Integer, default=0, doc="Total RP lost during game")
    reputation_gained = Column(Integer, default=0, doc="Total RP gained during game")
    
    # Ghost Viewer status (when reputation = 0)
    is_ghost_viewer = Column(Boolean, default=False, doc="Whether player is a Ghost Viewer (0 RP)")
    became_ghost_at_round = Column(Integer, nullable=True, doc="Round when player became Ghost Viewer")
    
    # Shadow ban tracking
    is_shadow_banned = Column(Boolean, default=False, doc="Whether player is currently shadow banned")
    shadow_ban_expires_round = Column(Integer, nullable=True, doc="Round when shadow ban expires")
    shadow_ban_count = Column(Integer, default=0, doc="Number of times shadow banned this game")
    
    # Player status
    is_active = Column(Boolean, default=True, doc="Whether player is still in the game")
    is_winner = Column(Boolean, default=False, doc="Whether player's faction won")
    
    # Game performance
    headlines_voted_correctly = Column(Integer, default=0, doc="Number of correct headline votes")
    headlines_voted_incorrectly = Column(Integer, default=0, doc="Number of incorrect headline votes")
    
    # Timestamps
    joined_at = Column(DateTime, default=func.now(), doc="When player joined the game")
    left_at = Column(DateTime, nullable=True, doc="When player left the game")
    
    # Player-specific game data
    player_data = Column(JSON, nullable=True, doc="Player-specific game state and data")
    
    # Relationships
    game = relationship("Game", back_populates="players")
    user = relationship("User", back_populates="game_players")
    role = relationship("PlayerRole", back_populates="game_player", uselist=False, cascade="all, delete-orphan")
    reputation_history = relationship("PlayerReputationHistory", back_populates="game_player", cascade="all, delete-orphan")
    
    @property
    def can_vote(self) -> bool:
        """Check if player can vote (Ghost Viewers can vote, shadow banned cannot speak but can vote)."""
        return self.is_active
    
    @property
    def can_speak(self) -> bool:
        """Check if player can speak in chat (shadow banned players cannot)."""
        return self.is_active and not self.is_shadow_banned
    
    @property
    def voting_accuracy(self) -> float:
        """Calculate this player's voting accuracy in current game."""
        total_votes = self.headlines_voted_correctly + self.headlines_voted_incorrectly
        if total_votes == 0:
            return 0.0
        return (self.headlines_voted_correctly / total_votes) * 100
    
    def __repr__(self) -> str:
        return f"<GamePlayer(user_id={self.user_id}, RP={self.current_reputation}, ghost={self.is_ghost_viewer})>"


class TruthWarsGame(Base):
    """
    Enhanced Truth Wars specific game data for refined system.
    
    This stores refined game state, round tracking, and educational features.
    """
    __tablename__ = "truth_wars_games"
    
    # Primary key - links to main game record
    game_id = Column(String(36), ForeignKey("games.id"), primary_key=True, doc="Main game ID")
    
    # Refined game state
    current_phase = Column(Enum(GamePhase), default=GamePhase.LOBBY, doc="Current game phase")
    phase_end_time = Column(DateTime, nullable=True, doc="When current phase ends")
    
    # Phase timing configuration (optimized for faster gameplay)
    discussion_duration = Column(Integer, default=120, doc="Discussion time in seconds (2 min)")
    voting_duration = Column(Integer, default=45, doc="Voting time in seconds (45 sec)")
    resolution_duration = Column(Integer, default=30, doc="Resolution viewing time (30 sec)")
    
    # Educational features
    educational_tips_shared = Column(JSON, default=list, doc="Tips shared by Drunk players this game")
    
    # Snipe system tracking (every 2 rounds)
    snipes_available_this_round = Column(Boolean, default=False, doc="Whether snipes are available this round")
    snipes_used_this_round = Column(Integer, default=0, doc="Number of snipes used this round")
    next_snipe_round = Column(Integer, default=2, doc="Next round when snipes will be available")
    
    # === v3 team score tracking ===
    truth_score = Column(Integer, default=0, doc="Points for Truth Team (first to 3 wins)")
    scam_score = Column(Integer, default=0, doc="Points for Scammer Team (first to 3 wins)")
    
    # Content and difficulty progression
    current_headline_id = Column(String(36), ForeignKey("headlines.id"), nullable=True, doc="Active headline ID")
    difficulty_progression = Column(JSON, default=lambda: ["easy", "medium", "medium", "hard", "hard"], doc="Difficulty for each round")
    
    # Game configuration
    settings = Column(JSON, default=dict, doc="Game-specific settings")
    
    # Relationships
    game = relationship("Game", back_populates="truth_wars_data")
    current_headline = relationship("Headline", foreign_keys=[current_headline_id])
    
    @property
    def current_difficulty(self) -> str:
        """Get difficulty level for current round."""
        if not self.difficulty_progression or len(self.difficulty_progression) < self.game.current_round:
            return "medium"
        return self.difficulty_progression[self.game.current_round - 1]
    
    def __repr__(self) -> str:
        return f"<TruthWarsGame(game_id={self.game_id}, phase={self.current_phase.value}, snipes_round={self.next_snipe_round})>"


class PlayerRole(Base):
    """
    Enhanced player roles for refined Truth Wars system.
    
    This tracks role assignments, faction membership, and ability usage.
    """
    __tablename__ = "player_roles"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid, doc="Unique role record ID")
    
    # Foreign keys
    game_player_id = Column(String(36), ForeignKey("game_players.id"), nullable=False, doc="Game player ID")
    
    # Role information for refined system
    role_name = Column(String(50), nullable=False, doc="Role name (fact_checker, scammer, influencer, normie)")
    faction = Column(Enum(PlayerFaction), nullable=False, doc="Player faction (truth_team, scammer_team)")
    
    # Ability tracking for refined system
    snipe_ability_used_rounds = Column(JSON, default=list, doc="Rounds when snipe ability was used")
    snipe_ability_available = Column(Boolean, default=True, doc="Whether snipe ability can be used")
    
    # Role-specific data
    fact_checker_blind_round = Column(Integer, nullable=True, doc="Round when Fact Checker doesn't get truth")
    influencer_vote_weight = Column(Integer, default=1, doc="Current vote weight (2 for Influencer)")
    
    # Educational content tracking (for Drunk role)
    educational_tips_shared = Column(JSON, default=list, doc="Educational tips shared while Drunk")
    media_literacy_content = Column(JSON, default=dict, doc="Media literacy content associated with role")
    
    # Timestamps
    assigned_at = Column(DateTime, default=func.now(), doc="When role was assigned")
    
    # Relationships
    game_player = relationship("GamePlayer", back_populates="role")
    
    @property
    def can_use_snipe(self) -> bool:
        """Check if player can use snipe ability this round."""
        return (self.snipe_ability_available and 
                not self.game_player.is_shadow_banned and
                self.game_player.current_reputation > 0)
    
    @property
    def is_currently_drunk(self) -> bool:
        """Check if this player is currently the Drunk."""
        if not hasattr(self, 'game_player') or not self.game_player.game.truth_wars_data:
            return False
        return self.game_player.user_id == self.game_player.game.truth_wars_data.current_drunk_player_id
    
    def __repr__(self) -> str:
        return f"<PlayerRole(role={self.role_name}, faction={self.faction.value}, can_snipe={self.can_use_snipe})>"


class Headline(Base):
    """
    Enhanced headlines for refined Truth Wars system.
    
    This stores headlines with credibility ratings and educational value.
    """
    __tablename__ = "headlines"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid, doc="Unique headline ID")
    
    # Headline content
    text = Column(Text, nullable=False, doc="The headline text")
    is_real = Column(Boolean, nullable=False, doc="Whether headline is real or fake")
    
    # Enhanced source information
    source = Column(String(255), nullable=True, doc="News source name")
    source_url = Column(String(500), nullable=True, doc="Original article URL")
    source_credibility_rating = Column(Integer, nullable=True, doc="Source credibility (1-10)")
    publication_date = Column(DateTime, nullable=True, doc="When article was published")
    
    # Classification with refined categories
    category = Column(String(50), default="general", doc="Topic category (politics, health, tech, etc.)")
    difficulty = Column(String(20), default="medium", doc="Difficulty level (easy, medium, hard)")
    
    # Enhanced educational content
    explanation = Column(Text, nullable=True, doc="Detailed explanation of why headline is real/fake")
    detection_tips = Column(JSON, default=list, doc="Specific tips for identifying this type of misinformation")
    bias_indicators = Column(JSON, default=list, doc="Language bias markers present")
    red_flags = Column(JSON, default=list, doc="Red flags that indicate this is fake news")
    verification_sources = Column(JSON, default=list, doc="Sources to verify similar claims")
    
    # Media literacy teaching points
    teaches_concepts = Column(JSON, default=list, doc="Media literacy concepts this headline teaches")
    common_misconceptions = Column(JSON, default=list, doc="Common misconceptions this addresses")
    
    # Usage and performance tracking
    times_used = Column(Integer, default=0, doc="How many times headline was used")
    times_trusted = Column(Integer, default=0, doc="How many times voted as 'trusted'")
    times_flagged = Column(Integer, default=0, doc="How many times voted as 'flagged'")
    correct_votes = Column(Integer, default=0, doc="Number of correct votes received")
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), doc="When headline was added")
    last_used = Column(DateTime, nullable=True, doc="When headline was last used")
    created_by = Column(String(100), nullable=True, doc="Who created/curated this headline")
    
    # Relationships
    headline_usage = relationship("HeadlineUsage", back_populates="headline", cascade="all, delete-orphan")
    votes = relationship("HeadlineVote", back_populates="headline", cascade="all, delete-orphan")
    
    @property
    def trust_rate(self) -> float:
        """Calculate percentage of players who trusted this headline."""
        total_votes = self.times_trusted + self.times_flagged
        if total_votes == 0:
            return 0.0
        return (self.times_trusted / total_votes) * 100
    
    @property
    def accuracy_rate(self) -> float:
        """Calculate percentage of correct votes for this headline."""
        total_votes = self.times_trusted + self.times_flagged
        if total_votes == 0:
            return 0.0
        return (self.correct_votes / total_votes) * 100
    
    def __repr__(self) -> str:
        return f"<Headline(id={self.id}, real={self.is_real}, difficulty={self.difficulty}, accuracy={self.accuracy_rate:.1f}%)>"


# New models for refined system features

class PlayerReputationHistory(Base):
    """
    Track reputation changes throughout games for analysis and learning.
    
    This provides detailed tracking of how players gain/lose RP.
    """
    __tablename__ = "player_reputation_history"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid, doc="Unique record ID")
    
    # Foreign keys
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, doc="User ID")
    game_player_id = Column(String(36), ForeignKey("game_players.id"), nullable=False, doc="Game player ID")
    
    # Reputation change details
    round_number = Column(Integer, nullable=False, doc="Round when change occurred")
    reputation_before = Column(Integer, nullable=False, doc="RP before this change")
    reputation_after = Column(Integer, nullable=False, doc="RP after this change")
    change_amount = Column(Integer, nullable=False, doc="RP change (+/- amount)")
    
    # Reason for change
    change_reason = Column(String(100), nullable=False, doc="Why RP changed (correct_vote, incorrect_vote, etc.)")
    headline_id = Column(String(36), ForeignKey("headlines.id"), nullable=True, doc="Related headline if applicable")
    
    # Context
    player_vote = Column(Enum(VoteType), nullable=True, doc="What the player voted")
    headline_truth = Column(Boolean, nullable=True, doc="Whether headline was real")
    
    # Timestamp
    timestamp = Column(DateTime, default=func.now(), doc="When change occurred")
    
    # Relationships
    user = relationship("User", back_populates="reputation_history")
    game_player = relationship("GamePlayer", back_populates="reputation_history")
    headline = relationship("Headline")
    
    def __repr__(self) -> str:
        return f"<ReputationHistory(user_id={self.user_id}, round={self.round_number}, change={self.change_amount})>"


class HeadlineVote(Base):
    """
    Trust/Flag voting records for refined system.
    
    This tracks all Trust/Flag votes with detailed context.
    """
    __tablename__ = "headline_votes"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid, doc="Unique vote ID")
    
    # Foreign keys
    game_id = Column(String(36), ForeignKey("games.id"), nullable=False, doc="Game ID")
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, doc="Voter ID")
    headline_id = Column(String(36), ForeignKey("headlines.id"), nullable=False, doc="Headline ID")
    
    # Vote details for refined system
    vote = Column(Enum(VoteType), nullable=False, doc="TRUST or FLAG vote")
    is_correct = Column(Boolean, nullable=False, doc="Whether vote was correct")
    vote_weight = Column(Integer, default=1, doc="Vote weight (2 for Influencer, 1 for others)")
    
    # Game context
    round_number = Column(Integer, nullable=False, doc="Round when vote was cast")
    voter_reputation_before = Column(Integer, nullable=False, doc="Voter's RP before this vote")
    voter_reputation_after = Column(Integer, nullable=False, doc="Voter's RP after this vote")
    
    # Vote timing and behavior
    timestamp = Column(DateTime, default=func.now(), doc="When vote was cast")
    vote_confidence = Column(Integer, nullable=True, doc="Player's confidence level (1-5) if collected")
    changed_vote = Column(Boolean, default=False, doc="Whether player changed their vote")
    
    # Educational tracking
    reasoning_provided = Column(Text, nullable=True, doc="Player's reasoning for their vote")
    used_fact_check_info = Column(Boolean, default=False, doc="Whether Fact Checker info was available")
    
    # Relationships
    game = relationship("Game", back_populates="headline_votes")
    voter = relationship("User", back_populates="headline_votes")
    headline = relationship("Headline", back_populates="votes")
    
    def __repr__(self) -> str:
        return f"<HeadlineVote(voter={self.user_id}, vote={self.vote.value}, correct={self.is_correct})>"


class RoundResult(Base):
    """
    Results of each round in refined Truth Wars system.
    
    This tracks win condition progress and educational outcomes.
    """
    __tablename__ = "round_results"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid, doc="Unique round result ID")
    
    # Foreign keys
    game_id = Column(String(36), ForeignKey("games.id"), nullable=False, doc="Game ID")
    headline_id = Column(String(36), ForeignKey("headlines.id"), nullable=False, doc="Headline used")
    
    # Round information
    round_number = Column(Integer, nullable=False, doc="Round number (1-5)")
    headline_was_real = Column(Boolean, nullable=False, doc="Whether headline was real")
    
    # Voting results
    total_trust_votes = Column(Integer, nullable=False, doc="Total TRUST votes")
    total_flag_votes = Column(Integer, nullable=False, doc="Total FLAG votes")
    weighted_trust_votes = Column(Integer, nullable=False, doc="Trust votes including Influencer weight")
    weighted_flag_votes = Column(Integer, nullable=False, doc="Flag votes including Influencer weight")
    
    # Outcome
    majority_vote = Column(Enum(VoteType), nullable=False, doc="Majority vote result")
    majority_was_correct = Column(Boolean, nullable=False, doc="Whether majority was correct")
    
    # Win condition tracking
    fake_headline_trusted = Column(Boolean, default=False, doc="Did a fake headline get trusted?")
    fake_headline_flagged = Column(Boolean, default=False, doc="Did a fake headline get flagged?")
    contributes_to_scammer_win = Column(Boolean, default=False, doc="Does this help Scammers win?")
    contributes_to_truth_win = Column(Boolean, default=False, doc="Does this help Truth team win?")
    
    # Educational metrics
    fact_checker_influence = Column(Boolean, default=False, doc="Did Fact Checker info influence outcome?")
    players_learned_something = Column(JSON, default=list, doc="Players who indicated they learned")
    players_voted_correctly = Column(JSON, default=list, doc="List of player IDs who voted correctly")
    players_lost_reputation = Column(JSON, default=list, doc="List of player IDs who lost RP")
    new_ghost_viewers = Column(JSON, default=list, doc="Player IDs who became Ghost Viewers")
    round_started_at = Column(DateTime, nullable=False, doc="When round started")
    round_ended_at = Column(DateTime, default=func.now(), doc="When round ended")
    
    # Relationships
    game = relationship("Game", back_populates="round_results")
    headline = relationship("Headline")
    
    @property
    def participation_rate(self) -> float:
        """Calculate what percentage of players voted."""
        total_votes = self.total_trust_votes + self.total_flag_votes
        if not hasattr(self.game, 'players') or len(self.game.players) == 0:
            return 0.0
        active_players = len([p for p in self.game.players if p.is_active])
        if active_players == 0:
            return 0.0
        return (total_votes / active_players) * 100
    
    def __repr__(self) -> str:
        return f"<RoundResult(game_id={self.game_id}, round={self.round_number}, majority={self.majority_vote.value})>"


class ShadowBanHistory(Base):
    """
    Track shadow ban events from snipe system.
    
    This provides analysis of snipe effectiveness and player behavior.
    """
    __tablename__ = "shadow_ban_history"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid, doc="Unique shadow ban record ID")
    
    # Foreign keys
    game_id = Column(String(36), ForeignKey("games.id"), nullable=False, doc="Game ID")
    snipe_action_id = Column(String(36), ForeignKey("snipe_actions.id"), nullable=False, doc="Related snipe action")
    banned_player_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, doc="Player who was shadow banned")
    
    # Shadow ban details
    round_banned = Column(Integer, nullable=False, doc="Round when shadow ban started")
    round_expires = Column(Integer, nullable=False, doc="Round when shadow ban expires")
    ban_duration_rounds = Column(Integer, nullable=False, doc="Duration in rounds")
    
    # Impact tracking
    messages_blocked = Column(Integer, default=0, doc="Number of messages blocked during ban")
    could_still_vote = Column(Boolean, default=True, doc="Whether player could still vote")
    affected_voting_behavior = Column(Boolean, default=False, doc="Whether ban affected their voting")
    
    # Timestamps
    banned_at = Column(DateTime, default=func.now(), doc="When shadow ban started")
    expires_at = Column(DateTime, nullable=True, doc="When shadow ban expires")
    
    # Relationships
    game = relationship("Game")
    snipe_action = relationship("SnipeAction", back_populates="shadow_ban_result")
    banned_player = relationship("User")
    
    def __repr__(self) -> str:
        return f"<ShadowBanHistory(player={self.banned_player_id}, rounds={self.round_banned}-{self.round_expires})>"


class SnipeAction(Base):
    """
    Track snipe attempts and results in refined system.
    
    This records all snipe attempts for strategic analysis.
    """
    __tablename__ = "snipe_actions"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid, doc="Unique snipe action ID")
    
    # Foreign keys
    game_id = Column(String(36), ForeignKey("games.id"), nullable=False, doc="Game ID")
    sniper_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, doc="Player who used snipe")
    target_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, doc="Player who was targeted")
    
    # Snipe details
    round_number = Column(Integer, nullable=False, doc="Round when snipe was used")
    snipe_result = Column(Enum(SnipeResult), nullable=False, doc="Result of snipe attempt")
    
    # Context
    sniper_role = Column(String(50), nullable=False, doc="Role of the sniper")
    target_role = Column(String(50), nullable=False, doc="Role of the target")
    sniper_reputation = Column(Integer, nullable=False, doc="Sniper's RP when snipe was used")
    target_reputation = Column(Integer, nullable=False, doc="Target's RP when sniped")
    
    # Strategic context
    snipe_reasoning = Column(Text, nullable=True, doc="Why sniper chose this target")
    was_revenge_snipe = Column(Boolean, default=False, doc="Whether this was retaliation")
    target_was_suspicious = Column(Boolean, default=False, doc="Whether target was acting suspiciously")
    
    # Results
    target_shadow_banned = Column(Boolean, default=False, doc="Whether target was shadow banned")
    sniper_revealed = Column(Boolean, default=False, doc="Whether failed snipe revealed sniper")
    affected_game_outcome = Column(Boolean, default=False, doc="Whether snipe significantly affected game")
    
    # Timestamp
    timestamp = Column(DateTime, default=func.now(), doc="When snipe was used")
    
    # Relationships
    game = relationship("Game", back_populates="snipe_actions")
    sniper = relationship("User", foreign_keys=[sniper_id], back_populates="snipe_actions_given")
    target = relationship("User", foreign_keys=[target_id], back_populates="snipe_actions_received")
    shadow_ban_result = relationship("ShadowBanHistory", back_populates="snipe_action", uselist=False)
    
    def __repr__(self) -> str:
        return f"<SnipeAction(sniper={self.sniper_id}, target={self.target_id}, result={self.snipe_result.value})>"


class HeadlineUsage(Base):
    """
    Track headline usage across games for content curation.
    
    This helps optimize headline difficulty and educational value.
    """
    __tablename__ = "headline_usage"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid, doc="Unique usage record ID")
    
    # Foreign keys
    headline_id = Column(String(36), ForeignKey("headlines.id"), nullable=False, doc="Headline ID")
    game_id = Column(String(36), ForeignKey("games.id"), nullable=False, doc="Game ID")
    round_result_id = Column(String(36), ForeignKey("round_results.id"), nullable=False, doc="Round result ID")
    
    # Usage context
    round_number = Column(Integer, nullable=False, doc="Round when headline was used")
    difficulty_level = Column(String(20), nullable=False, doc="Difficulty setting when used")
    player_count = Column(Integer, nullable=False, doc="Number of players in game")
    
    # Performance metrics
    correct_vote_percentage = Column(Float, nullable=False, doc="Percentage who voted correctly")
    engagement_score = Column(Float, nullable=True, doc="Player engagement during this headline")
    discussion_quality = Column(Integer, nullable=True, doc="Quality of discussion (1-5)")
    
    # Educational effectiveness
    players_learned = Column(Integer, default=0, doc="Number of players who indicated learning")
    misconceptions_corrected = Column(JSON, default=list, doc="Misconceptions addressed")
    educational_goals_met = Column(JSON, default=list, doc="Educational objectives achieved")
    
    # Content optimization data
    was_too_easy = Column(Boolean, default=False, doc="Whether headline was too easy")
    was_too_hard = Column(Boolean, default=False, doc="Whether headline was too hard")
    needs_better_explanation = Column(Boolean, default=False, doc="Whether explanation needs improvement")
    
    # Timestamp
    used_at = Column(DateTime, default=func.now(), doc="When headline was used")
    
    # Relationships
    headline = relationship("Headline", back_populates="headline_usage")
    game = relationship("Game")
    round_result = relationship("RoundResult")
    
    def __repr__(self) -> str:
        return f"<HeadlineUsage(headline_id={self.headline_id}, round={self.round_number}, accuracy={self.correct_vote_percentage:.1f}%)>"


class MediaLiteracyAnalytics(Base):
    """
    Track learning outcomes and educational effectiveness.
    
    This measures how well the game teaches media literacy.
    """
    __tablename__ = "media_literacy_analytics"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid, doc="Unique analytics record ID")
    
    # Foreign keys
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, doc="User ID")
    game_id = Column(String(36), ForeignKey("games.id"), nullable=True, doc="Game ID (if game-specific)")
    
    # Learning metrics
    concepts_learned = Column(JSON, default=list, doc="Media literacy concepts learned")
    skills_improved = Column(JSON, default=list, doc="Skills that showed improvement")
    misconceptions_corrected = Column(JSON, default=list, doc="Misconceptions that were corrected")
    
    # Performance tracking
    before_accuracy = Column(Float, nullable=True, doc="Accuracy before learning intervention")
    after_accuracy = Column(Float, nullable=True, doc="Accuracy after learning intervention")
    improvement_percentage = Column(Float, nullable=True, doc="Percentage improvement")
    
    # Learning context
    learning_source = Column(String(50), nullable=False, doc="How learning occurred (discussion, etc.)")
    educational_content_id = Column(String(100), nullable=True, doc="Specific educational content ID")
    learning_session_duration = Column(Integer, nullable=True, doc="Duration of learning session in minutes")
    
    # Knowledge retention
    knowledge_retained_after_game = Column(Boolean, nullable=True, doc="Whether knowledge was retained")
    applied_in_subsequent_games = Column(Boolean, nullable=True, doc="Whether learning was applied later")
    
    # Engagement metrics
    engagement_level = Column(Integer, nullable=True, doc="Engagement level during learning (1-5)")
    asked_questions = Column(Boolean, default=False, doc="Whether user asked follow-up questions")
    shared_with_others = Column(Boolean, default=False, doc="Whether user shared learning with others")
    
    # Timestamps
    learning_occurred_at = Column(DateTime, default=func.now(), doc="When learning occurred")
    measured_at = Column(DateTime, default=func.now(), doc="When improvement was measured")
    
    # Relationships
    user = relationship("User")
    game = relationship("Game")
    
    def __repr__(self) -> str:
        return f"<MediaLiteracyAnalytics(user_id={self.user_id}, improvement={self.improvement_percentage:.1f}%)>" 