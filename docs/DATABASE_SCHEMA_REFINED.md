# 🗄️ Truth Wars Refined Database Schema

## 📋 **Overview**
This document defines the complete database schema for the refined Truth Wars game system, supporting reputation tracking, Trust/Flag voting, shadow ban mechanics, and educational features. This schema reflects the actual implementation in the current codebase.

## 📊 **Core Game Tables**

### **games** (Enhanced)
```sql
-- Enhanced games table for refined system
id (String Primary Key) -- UUID as string for SQLite compatibility
game_type (VARCHAR) -- Always "truth_wars"
status (ENUM) -- 'waiting', 'active', 'completed', 'cancelled'
chat_id (BIGINT) -- Telegram chat ID
chat_type (VARCHAR) -- 'group' for Truth Wars
max_players (INT DEFAULT 8) -- Maximum players (5-8)
min_players (INT DEFAULT 5) -- Minimum to start
total_rounds (INT DEFAULT 5) -- Always 5 for refined system
current_round (INT DEFAULT 1) -- Current round (1-5)
fake_headlines_trusted (INT DEFAULT 0) -- Scammer win condition tracker
fake_headlines_flagged (INT DEFAULT 0) -- Truth team win condition tracker
winning_faction (ENUM) -- 'truth_team', 'scammer_team'
win_condition_met (VARCHAR) -- How game was won
settings (JSON) -- Game configuration
game_metadata (JSON) -- Additional metadata
created_at (TIMESTAMP)
started_at (TIMESTAMP)
completed_at (TIMESTAMP)
```

### **game_players** (Enhanced)
```sql
-- Enhanced player participation tracking
id (String Primary Key) -- UUID as string
game_id (Foreign Key → games.id)
user_id (BIGINT) -- Telegram user ID
current_reputation (INT DEFAULT 3) -- Current RP (0-3+)
starting_reputation (INT DEFAULT 3) -- RP at game start
reputation_lost (INT DEFAULT 0) -- Total RP lost during game
reputation_gained (INT DEFAULT 0) -- Total RP gained during game
is_ghost_viewer (BOOLEAN DEFAULT FALSE) -- 0 RP status
became_ghost_at_round (INT) -- Round when became Ghost Viewer
is_shadow_banned (BOOLEAN DEFAULT FALSE) -- Current shadow ban status
shadow_ban_expires_round (INT) -- Round when shadow ban expires
shadow_ban_count (INT DEFAULT 0) -- Times shadow banned this game
is_active (BOOLEAN DEFAULT TRUE) -- Still in game
is_winner (BOOLEAN DEFAULT FALSE) -- Player's faction won
headlines_voted_correctly (INT DEFAULT 0) -- Correct headline votes
headlines_voted_incorrectly (INT DEFAULT 0) -- Incorrect headline votes
joined_at (TIMESTAMP)
left_at (TIMESTAMP)
player_data (JSON) -- Player-specific game state
```

### **truth_wars_games** (Game-Specific Data)
```sql
-- Truth Wars specific game data
game_id (Foreign Key → games.id, Primary Key)
current_phase (ENUM) -- 'lobby', 'role_assignment', 'round_start', 'discussion', 'voting', 'resolution', 'game_end'
phase_end_time (TIMESTAMP) -- When current phase ends
discussion_duration (INT DEFAULT 120) -- Discussion time (2 min)
voting_duration (INT DEFAULT 45) -- Voting time (45 sec)
resolution_duration (INT DEFAULT 30) -- Resolution time (30 sec)
drunk_rotation_order (JSON) -- Order of Drunk role rotation
current_drunk_player_id (BIGINT) -- Current Drunk player
educational_tips_shared (JSON) -- Tips shared this game
snipes_available_this_round (BOOLEAN DEFAULT FALSE) -- Snipes available
snipes_used_this_round (INT DEFAULT 0) -- Snipes used this round
next_snipe_round (INT DEFAULT 2) -- Next snipe round
truth_score (INT DEFAULT 0) -- Truth Team points (v3 scoring)
scam_score (INT DEFAULT 0) -- Scammer Team points (v3 scoring)
current_headline_id (String Foreign Key → headlines.id) -- Active headline
difficulty_progression (JSON) -- Difficulty per round ['easy', 'medium', 'medium', 'hard', 'hard']
settings (JSON) -- Game-specific settings
```

### **player_roles** (Enhanced Role System)
```sql
-- Enhanced player roles for refined Truth Wars system
id (String Primary Key) -- UUID as string
game_player_id (Foreign Key → game_players.id)
role_name (VARCHAR) -- 'fact_checker', 'scammer', 'influencer', 'drunk', 'normie'
faction (ENUM) -- 'truth_team', 'scammer_team'
is_original_drunk (BOOLEAN DEFAULT FALSE) -- Original Drunk assignment
drunk_rotation_position (INT) -- Position in rotation
snipe_ability_used_rounds (JSON) -- Rounds when snipe used
snipe_ability_available (BOOLEAN DEFAULT TRUE) -- Can use snipe
fact_checker_blind_round (INT) -- Round when FC doesn't get info
influencer_vote_weight (INT DEFAULT 1) -- Vote weight (2 for Influencer)
educational_tips_shared (JSON) -- Tips shared while Drunk
media_literacy_content (JSON) -- Role-specific educational content
assigned_at (TIMESTAMP)
became_drunk_at (TIMESTAMP)
```

## 🎯 **Enhanced User & Educational Tables**

### **users** (Enhanced User Tracking)
```sql
-- Enhanced user model with media literacy tracking
id (BIGINT Primary Key) -- Telegram user ID
username (VARCHAR)
first_name (VARCHAR)
last_name (VARCHAR)
is_active (BOOLEAN DEFAULT TRUE)
is_admin (BOOLEAN DEFAULT FALSE)
created_at (TIMESTAMP)
last_seen_at (TIMESTAMP)

-- Enhanced game statistics
total_games (INT DEFAULT 0)
total_wins (INT DEFAULT 0)
truth_team_wins (INT DEFAULT 0)
scammer_team_wins (INT DEFAULT 0)

-- Reputation system stats
total_reputation_earned (INT DEFAULT 0)
average_reputation (FLOAT DEFAULT 3.0)

-- Headline voting accuracy
headlines_voted_on (INT DEFAULT 0)
correct_votes (INT DEFAULT 0)
fake_headlines_correctly_flagged (INT DEFAULT 0)
real_headlines_correctly_trusted (INT DEFAULT 0)

-- Role performance tracking
times_as_fact_checker (INT DEFAULT 0)
times_as_scammer (INT DEFAULT 0)
times_as_influencer (INT DEFAULT 0)
times_as_drunk (INT DEFAULT 0)
times_as_normie (INT DEFAULT 0)

-- Snipe system stats
successful_snipes (INT DEFAULT 0)
failed_snipes (INT DEFAULT 0)
times_shadow_banned (INT DEFAULT 0)

-- Learning progress
media_literacy_level (INT DEFAULT 1) -- Current level (1-10)
educational_tips_seen (JSON) -- Tips seen
learning_streak (INT DEFAULT 0) -- Current streak
best_learning_streak (INT DEFAULT 0) -- Best streak
```

### **headlines** (Enhanced Content Database)
```sql
-- Enhanced headlines with educational value
id (String Primary Key) -- UUID as string
text (TEXT) -- The headline text
is_real (BOOLEAN) -- True for real news, False for fake
source (VARCHAR) -- Publication/source name
source_url (VARCHAR) -- Original article URL
source_credibility_rating (INT) -- Source credibility (1-10)
publication_date (TIMESTAMP) -- When published
category (VARCHAR DEFAULT 'general') -- Topic category
difficulty (VARCHAR DEFAULT 'medium') -- 'easy', 'medium', 'hard'
explanation (TEXT) -- Educational explanation
detection_tips (JSON) -- Specific detection tips
bias_indicators (JSON) -- Language bias markers
red_flags (JSON) -- Red flags for fake news
verification_sources (JSON) -- Sources to verify claims
teaches_concepts (JSON) -- Media literacy concepts taught
common_misconceptions (JSON) -- Misconceptions addressed
times_used (INT DEFAULT 0) -- Usage count
times_trusted (INT DEFAULT 0) -- Trust votes received
times_flagged (INT DEFAULT 0) -- Flag votes received
correct_votes (INT DEFAULT 0) -- Correct votes received
created_at (TIMESTAMP)
last_used (TIMESTAMP)
created_by (VARCHAR) -- Creator/curator
```

## 🔗 **Voting & Analytics Tables**

### **headline_votes** (Trust/Flag Voting Records)
```sql
-- Trust/Flag voting records for refined system
id (String Primary Key) -- UUID as string
game_id (Foreign Key → games.id)
user_id (BIGINT Foreign Key → users.id)
headline_id (Foreign Key → headlines.id)
vote (ENUM) -- 'trust', 'flag'
is_correct (BOOLEAN) -- Whether vote was correct
vote_weight (INT DEFAULT 1) -- Vote weight (2 for Influencer)
round_number (INT) -- Round when vote cast
voter_reputation_before (INT) -- RP before vote
voter_reputation_after (INT) -- RP after vote
timestamp (TIMESTAMP)
vote_confidence (INT) -- Confidence level (1-5) if collected
changed_vote (BOOLEAN DEFAULT FALSE) -- Whether vote was changed
reasoning_provided (TEXT) -- Player's reasoning
used_fact_check_info (BOOLEAN DEFAULT FALSE) -- FC info available
```

### **player_reputation_history** (RP Change Tracking)
```sql
-- Track reputation changes over time
id (String Primary Key) -- UUID as string
user_id (BIGINT Foreign Key → users.id)
game_player_id (Foreign Key → game_players.id)
round_number (INT)
reputation_before (INT)
reputation_after (INT)
change_amount (INT) -- +1, -1, etc.
change_reason (VARCHAR) -- 'correct_vote', 'incorrect_vote', 'scammer_bonus'
headline_id (Foreign Key → headlines.id)
player_vote (ENUM) -- 'trust', 'flag'
headline_truth (BOOLEAN) -- Whether headline was real
timestamp (TIMESTAMP)
```

### **round_results** (Round Outcome Tracking)
```sql
-- Results of each round
id (String Primary Key) -- UUID as string
game_id (Foreign Key → games.id)
headline_id (Foreign Key → headlines.id)
round_number (INT) -- Round number (1-5)
headline_was_real (BOOLEAN)
total_trust_votes (INT)
total_flag_votes (INT)
weighted_trust_votes (INT) -- Including Influencer weight
weighted_flag_votes (INT)
majority_vote (ENUM) -- 'trust', 'flag'
majority_was_correct (BOOLEAN)
fake_headline_trusted (BOOLEAN DEFAULT FALSE)
fake_headline_flagged (BOOLEAN DEFAULT FALSE)
contributes_to_scammer_win (BOOLEAN DEFAULT FALSE)
contributes_to_truth_win (BOOLEAN DEFAULT FALSE)
fact_checker_influence (BOOLEAN DEFAULT FALSE)
drunk_tip_shared (TEXT) -- Educational tip shared
players_learned_something (JSON) -- Players who learned
players_voted_correctly (JSON) -- Correct voters
players_lost_reputation (JSON) -- Players who lost RP
new_ghost_viewers (JSON) -- New Ghost Viewers
round_started_at (TIMESTAMP)
round_ended_at (TIMESTAMP)
```

## 🎯 **Shadow Ban & Snipe System Tables**

### **snipe_actions** (Snipe Attempt Tracking)
```sql
-- Track snipe attempts and results
id (String Primary Key) -- UUID as string
game_id (Foreign Key → games.id)
sniper_id (BIGINT Foreign Key → users.id)
target_id (BIGINT Foreign Key → users.id)
round_number (INT)
snipe_result (ENUM) -- 'success', 'failed', 'blocked'
sniper_role (VARCHAR) -- Role of sniper
target_role (VARCHAR) -- Role of target
sniper_reputation (INT) -- Sniper's RP when used
target_reputation (INT) -- Target's RP when sniped
snipe_reasoning (TEXT) -- Why this target
was_revenge_snipe (BOOLEAN DEFAULT FALSE)
target_was_suspicious (BOOLEAN DEFAULT FALSE)
target_shadow_banned (BOOLEAN DEFAULT FALSE)
sniper_revealed (BOOLEAN DEFAULT FALSE)
affected_game_outcome (BOOLEAN DEFAULT FALSE)
timestamp (TIMESTAMP)
```

### **shadow_ban_history** (Shadow Ban Event Tracking)
```sql
-- Track shadow ban events
id (String Primary Key) -- UUID as string
game_id (Foreign Key → games.id)
snipe_action_id (Foreign Key → snipe_actions.id)
banned_player_id (BIGINT Foreign Key → users.id)
round_banned (INT) -- When shadow ban started
round_expires (INT) -- When shadow ban expires
ban_duration_rounds (INT) -- Duration in rounds
messages_blocked (INT DEFAULT 0) -- Messages blocked count
could_still_vote (BOOLEAN DEFAULT TRUE) -- Voting allowed
affected_voting_behavior (BOOLEAN DEFAULT FALSE)
banned_at (TIMESTAMP)
expires_at (TIMESTAMP)
```

## 📚 **Educational & Analytics Tables**

### **headline_usage** (Content Performance Tracking)
```sql
-- Track headline usage for optimization
id (String Primary Key) -- UUID as string
headline_id (Foreign Key → headlines.id)
game_id (Foreign Key → games.id)
round_result_id (Foreign Key → round_results.id)
round_number (INT)
difficulty_level (VARCHAR)
player_count (INT)
correct_vote_percentage (FLOAT)
engagement_score (FLOAT)
discussion_quality (INT) -- Quality rating (1-5)
players_learned (INT DEFAULT 0)
misconceptions_corrected (JSON)
educational_goals_met (JSON)
was_too_easy (BOOLEAN DEFAULT FALSE)
was_too_hard (BOOLEAN DEFAULT FALSE)
needs_better_explanation (BOOLEAN DEFAULT FALSE)
used_at (TIMESTAMP)
```

### **media_literacy_analytics** (Learning Outcomes)
```sql
-- Track learning outcomes and educational effectiveness
id (String Primary Key) -- UUID as string
user_id (BIGINT Foreign Key → users.id)
game_id (Foreign Key → games.id) -- Optional
concepts_learned (JSON)
skills_improved (JSON)
misconceptions_corrected (JSON)
before_accuracy (FLOAT)
after_accuracy (FLOAT)
improvement_percentage (FLOAT)
learning_source (VARCHAR) -- 'drunk_tip', 'discussion', etc.
educational_content_id (VARCHAR)
learning_session_duration (INT) -- Minutes
knowledge_retained_after_game (BOOLEAN)
applied_in_subsequent_games (BOOLEAN)
engagement_level (INT) -- 1-5 rating
asked_questions (BOOLEAN DEFAULT FALSE)
shared_with_others (BOOLEAN DEFAULT FALSE)
learning_occurred_at (TIMESTAMP)
measured_at (TIMESTAMP)
```

### **drunk_role_assignments** (Educational Role Rotation)
```sql
-- Track Drunk role rotation and educational content
id (String Primary Key) -- UUID as string
game_id (Foreign Key → games.id)
player_id (BIGINT Foreign Key → users.id)
round_assigned (INT)
round_rotation_ends (INT)
was_original_drunk (BOOLEAN DEFAULT FALSE)
rotation_position (INT)
tips_shared (JSON) -- Educational tips shared
concepts_taught (JSON) -- Media literacy concepts
player_engagement (JSON) -- How others engaged
educational_effectiveness (FLOAT)
players_who_learned (JSON)
questions_answered (INT DEFAULT 0)
assigned_at (TIMESTAMP)
rotation_completed_at (TIMESTAMP)
```

## 🔗 **Key Indexes & Performance**

### **Essential Indexes**
```sql
-- Performance indexes for common queries
CREATE INDEX idx_games_chat_status ON games(chat_id, status);
CREATE INDEX idx_game_players_game_user ON game_players(game_id, user_id);
CREATE INDEX idx_reputation_history_game_round ON player_reputation_history(user_id, round_number);
CREATE INDEX idx_headline_votes_game_round ON headline_votes(game_id, round_number);
CREATE INDEX idx_headlines_real_difficulty ON headlines(is_real, difficulty);
CREATE INDEX idx_shadow_ban_game_round ON shadow_ban_history(game_id, round_banned);
CREATE INDEX idx_snipe_actions_game_round ON snipe_actions(game_id, round_number);
CREATE INDEX idx_users_total_games ON users(total_games, total_wins);
```

### **Data Constraints**
```sql
-- Ensure data integrity
ALTER TABLE game_players ADD CONSTRAINT chk_reputation_range 
    CHECK (current_reputation >= 0 AND current_reputation <= 10);

ALTER TABLE headline_votes ADD CONSTRAINT chk_vote_type 
    CHECK (vote IN ('trust', 'flag'));

ALTER TABLE round_results ADD CONSTRAINT chk_round_number 
    CHECK (round_number >= 1 AND round_number <= 5);

ALTER TABLE headlines ADD CONSTRAINT chk_difficulty 
    CHECK (difficulty IN ('easy', 'medium', 'hard'));

ALTER TABLE snipe_actions ADD CONSTRAINT chk_snipe_result
    CHECK (snipe_result IN ('success', 'failed', 'blocked'));
```

## 📈 **Enum Definitions (Actual Implementation)**

### **Game Status**
- `waiting` - Game lobby, waiting for players
- `active` - Game in progress
- `completed` - Game finished
- `cancelled` - Game cancelled

### **Game Phase**
- `lobby` - Player joining phase
- `role_assignment` - Roles being assigned
- `round_start` - Round beginning
- `discussion` - Discussion phase (2 min)
- `voting` - Trust/Flag voting (45 sec)
- `resolution` - Results and education (30 sec)
- `game_end` - Game completed

### **Player Faction**
- `truth_team` - Truth Seekers faction
- `scammer_team` - Misinformers faction

### **Vote Type**
- `trust` - Trust the headline (think it's real)
- `flag` - Flag the headline (think it's fake)

### **Snipe Result**
- `success` - Snipe successful, target shadow banned
- `failed` - Snipe failed, sniper shadow banned
- `blocked` - Snipe attempt blocked/invalid

## 🎯 **Key Features Supported**

✅ **Reputation System**: 3 RP starting system with detailed tracking  
✅ **Trust/Flag Voting**: Complete vote recording with weights and accuracy  
✅ **Shadow Ban Mechanics**: Snipe abilities with duration tracking  
✅ **5-Round Structure**: Fixed game length with round progression  
✅ **Educational Analytics**: Learning progress and improvement tracking  
✅ **Role Rotation**: Drunk role rotation among Normies  
✅ **v3 Team Scoring**: First-to-3-points win condition tracking  
✅ **Media Literacy Integration**: Comprehensive educational content system

## 🔄 **Migration & Compatibility**

### **SQLite Compatibility**
- UUIDs stored as String(36) for SQLite compatibility
- JSON fields for flexible data storage
- Async SQLAlchemy with aiosqlite driver
- Proper indexing for query performance

### **Production Scalability**
- PostgreSQL-compatible schema design
- Relationship integrity via foreign keys
- Comprehensive constraint system
- Analytics-ready structure for reporting