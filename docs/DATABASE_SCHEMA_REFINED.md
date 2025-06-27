# 🗄️ Truth Wars Refined Database Schema

## 📋 **Overview**
This document defines the complete database schema for the refined Truth Wars game system, supporting reputation tracking, Trust/Flag voting, shadow ban mechanics, and educational features.

## 📊 **Core Game Tables**

### **games** (Enhanced)
```sql
-- Enhanced games table for refined system
id (Primary Key)
game_type (VARCHAR) -- "truth_wars"
chat_id (BIGINT) -- Telegram chat ID
creator_user_id (BIGINT) -- Game creator
status (ENUM) -- 'waiting', 'active', 'completed', 'cancelled'
current_round (INT DEFAULT 0) -- Current round (1-5)
max_rounds (INT DEFAULT 5) -- Always 5 for refined system
current_phase (VARCHAR) -- Current game phase
phase_start_time (TIMESTAMP) -- When current phase started
settings (JSON) -- Game configuration
created_at (TIMESTAMP)
started_at (TIMESTAMP)
ended_at (TIMESTAMP)
winner_faction (VARCHAR) -- 'truth_seekers', 'misinformers', or 'draw'
win_condition_met (VARCHAR) -- How game was won
fake_headlines_trusted (INT DEFAULT 0) -- Scammer win condition tracker
fake_headlines_flagged (INT DEFAULT 0) -- Truth team win condition tracker
```

### **game_players** (Enhanced)
```sql
-- Enhanced player participation tracking
id (Primary Key)
game_id (Foreign Key → games.id)
user_id (BIGINT) -- Telegram user ID
user_name (VARCHAR) -- Display name
joined_at (TIMESTAMP)
current_reputation (INT DEFAULT 3) -- Current RP (0-3+)
is_ghost_viewer (BOOLEAN DEFAULT FALSE) -- 0 RP status
is_shadow_banned (BOOLEAN DEFAULT FALSE) -- Current shadow ban status
shadow_ban_rounds_remaining (INT DEFAULT 0) -- Rounds left in shadow ban
role_type (VARCHAR) -- Current role: fact_checker, scammer, drunk, influencer, normie
faction (VARCHAR) -- truth_seekers, misinformers
is_drunk_this_round (BOOLEAN DEFAULT FALSE) -- Rotating drunk status
role_assigned_at (TIMESTAMP)
final_reputation (INT) -- End-game RP
```

## 🎯 **New Refined System Tables**

### **player_reputation_history**
```sql
-- Track reputation changes over time
id (Primary Key)
game_id (Foreign Key → games.id)
user_id (BIGINT)
round_number (INT)
reputation_before (INT)
reputation_after (INT)
change_amount (INT) -- +1, -1, etc.
change_reason (VARCHAR) -- 'correct_vote', 'incorrect_vote', 'scammer_bonus'
headline_id (Foreign Key → headlines.id) -- What headline caused change
vote_choice (VARCHAR) -- 'trust' or 'flag'
headline_was_real (BOOLEAN)
timestamp (TIMESTAMP)
```

### **headline_votes**
```sql
-- Record all Trust/Flag votes
id (Primary Key)
game_id (Foreign Key → games.id)
user_id (BIGINT)
headline_id (Foreign Key → headlines.id)
round_number (INT)
vote_choice (VARCHAR) -- 'trust' or 'flag'
vote_weight (INT DEFAULT 1) -- 2 for Influencer, 1 for others
voted_at (TIMESTAMP)
was_correct (BOOLEAN) -- Whether vote matched headline truth
reputation_change (INT) -- RP change from this vote
```

### **round_results**
```sql
-- Store outcome of each round
id (Primary Key)
game_id (Foreign Key → games.id)
round_number (INT)
headline_id (Foreign Key → headlines.id)
headline_was_real (BOOLEAN)
total_trust_votes (INT)
total_flag_votes (INT)
total_vote_weight_trust (INT) -- Including Influencer 2x weight
total_vote_weight_flag (INT)
majority_choice (VARCHAR) -- 'trust' or 'flag'
was_majority_correct (BOOLEAN)
scammer_bonus_awarded (BOOLEAN) -- If Scammers got +1 RP
players_gained_rp (INT) -- Count of players who gained RP
players_lost_rp (INT) -- Count of players who lost RP
ghost_viewers_created (INT) -- Players who hit 0 RP this round
phase_started_at (TIMESTAMP)
voting_ended_at (TIMESTAMP)
```

### **shadow_ban_history**
```sql
-- Track shadow ban events
id (Primary Key)
game_id (Foreign Key → games.id)
target_user_id (BIGINT) -- Who was shadow banned
sniper_user_id (BIGINT) -- Who performed the snipe
sniper_role (VARCHAR) -- fact_checker or scammer
target_role (VARCHAR) -- What role was targeted
round_number (INT)
was_successful (BOOLEAN) -- TRUE if correct target, FALSE if wrong
shadow_ban_duration (INT DEFAULT 1) -- Rounds of shadow ban
snipe_reason (VARCHAR) -- 'successful_snipe' or 'failed_snipe_self_ban'
sniped_at (TIMESTAMP)
```

### **snipe_actions**
```sql
-- Log all snipe attempts (successful and failed)
id (Primary Key)
game_id (Foreign Key → games.id)
sniper_user_id (BIGINT)
target_user_id (BIGINT)
round_number (INT)
sniper_role (VARCHAR) -- fact_checker or scammer
target_role (VARCHAR) -- What the target actually was
intended_target_role (VARCHAR) -- What sniper thought target was
result (VARCHAR) -- 'success', 'failed_wrong_target', 'already_used'
shadow_ban_applied_to (BIGINT) -- Who got shadow banned (sniper or target)
attempted_at (TIMESTAMP)
```

## 📰 **Headlines & Content Tables**

### **headlines** (Enhanced)
```sql
-- Database of real and fake headlines
id (Primary Key)
text (TEXT) -- The headline text
is_real (BOOLEAN) -- TRUE for real news, FALSE for fake
source (VARCHAR) -- Publication/source name
source_credibility (ENUM) -- 'high', 'medium', 'low', 'satirical', 'fake'
category (VARCHAR) -- 'health', 'politics', 'science', 'technology', etc.
difficulty (ENUM) -- 'easy', 'medium', 'hard'
explanation (TEXT) -- Why it's real/fake and how to verify
fact_check_url (VARCHAR) -- Link to fact-checking source
red_flags (JSON) -- Array of red flags to look for
verification_tips (JSON) -- Array of verification techniques
created_at (TIMESTAMP)
last_used_at (TIMESTAMP)
usage_count (INT DEFAULT 0) -- How many times used in games
correct_vote_rate (DECIMAL) -- % of players who vote correctly
```

### **headline_usage**
```sql
-- Track which headlines were used in which games
id (Primary Key)
game_id (Foreign Key → games.id)
headline_id (Foreign Key → headlines.id)
round_number (INT)
presented_at (TIMESTAMP)
total_players (INT)
correct_votes (INT)
incorrect_votes (INT)
accuracy_rate (DECIMAL) -- % who voted correctly
```

## 🎓 **Educational & Analytics Tables**

### **media_literacy_scores** (Enhanced)
```sql
-- Track learning progress per player
id (Primary Key)
user_id (BIGINT)
assessment_date (TIMESTAMP)
games_played (INT)
total_headlines_seen (INT)
correct_identifications (INT)
accuracy_rate (DECIMAL)
improvement_rate (DECIMAL) -- Compared to previous assessment
strong_categories (JSON) -- Categories player is good at
weak_categories (JSON) -- Categories player struggles with
learning_badges (JSON) -- Achievements earned
```

### **learning_analytics**
```sql
-- Aggregate learning data
id (Primary Key)
user_id (BIGINT)
game_id (Foreign Key → games.id)
headlines_correct (INT)
headlines_incorrect (INT)
reputation_gained (INT)
reputation_lost (INT)
role_played (VARCHAR)
faction (VARCHAR)
game_outcome (VARCHAR) -- 'won', 'lost'
key_learnings (JSON) -- What they learned this game
improvement_areas (JSON) -- What to work on
recorded_at (TIMESTAMP)
```

### **drunk_role_assignments**
```sql
-- Track rotating "Drunk" role assignments
id (Primary Key)
game_id (Foreign Key → games.id)
user_id (BIGINT)
round_number (INT)
was_drunk_this_round (BOOLEAN)
shared_tips (TEXT) -- Media literacy tips they shared
tip_quality_rating (INT) -- 1-5 rating of their tips
assigned_at (TIMESTAMP)
```

## 🔗 **Relationship Indexes & Constraints**

### **Key Indexes**
```sql
-- Performance indexes for common queries
CREATE INDEX idx_games_chat_status ON games(chat_id, status);
CREATE INDEX idx_game_players_game_user ON game_players(game_id, user_id);
CREATE INDEX idx_reputation_history_game_round ON player_reputation_history(game_id, round_number);
CREATE INDEX idx_headline_votes_game_round ON headline_votes(game_id, round_number);
CREATE INDEX idx_headlines_real_difficulty ON headlines(is_real, difficulty);
CREATE INDEX idx_shadow_ban_game_round ON shadow_ban_history(game_id, round_number);
```

### **Data Constraints**
```sql
-- Ensure data integrity
ALTER TABLE player_reputation_history ADD CONSTRAINT chk_reputation_range 
    CHECK (reputation_after >= 0 AND reputation_after <= 10);

ALTER TABLE headline_votes ADD CONSTRAINT chk_vote_choice 
    CHECK (vote_choice IN ('trust', 'flag'));

ALTER TABLE round_results ADD CONSTRAINT chk_round_number 
    CHECK (round_number >= 1 AND round_number <= 5);

ALTER TABLE headlines ADD CONSTRAINT chk_difficulty 
    CHECK (difficulty IN ('easy', 'medium', 'hard'));
```

## 📈 **Migration Strategy**

### **From Current to Refined Schema**
```sql
-- Migration steps for existing data
1. Backup existing tables
2. Add new columns to existing tables
3. Create new refined system tables  
4. Migrate game data to new structure
5. Update foreign key relationships
6. Populate headlines database
7. Initialize reputation tracking
```

### **Data Seeding Requirements**
```sql
-- Essential data to seed
1. Headlines database (50+ real/fake headlines)
2. Source credibility ratings
3. Category classifications
4. Educational explanations
5. Verification tip templates
```

## 🎯 **Key Features Supported**

✅ **Reputation System**: Track 3 RP per player with detailed history  
✅ **Trust/Flag Voting**: Record all votes with weight and accuracy  
✅ **Shadow Ban Mechanics**: Track snipe actions and ban duration  
✅ **5-Round Structure**: Support fixed game length with round progression  
✅ **Educational Analytics**: Monitor learning progress and improvement  
✅ **Role Rotation**: Track "Drunk" role assignments each round  
✅ **Win Condition Tracking**: Monitor fake headlines trusted/flagged  
✅ **Media Literacy Scoring**: Assess and improve player skills over time  

This schema supports **all the refined game mechanics** while maintaining **educational focus** and providing rich **analytics for learning assessment**! 🎓✨ 