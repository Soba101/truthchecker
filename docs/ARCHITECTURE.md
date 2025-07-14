# Truth Wars Telegram Bot - Technical Architecture

> **Note (2025-07):** The *Drunk* role has been removed from gameplay. Any references below are for historical context only and do not reflect current gameplay.

## Overview

This document outlines the technical architecture of the Truth Wars Telegram bot - an educational social deduction game that teaches media literacy through gameplay. The bot implements a sophisticated 5-round game system with reputation tracking, role-based abilities, and shadow ban mechanics.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram API  │    │   Truth Wars    │    │    Database     │
│                 │────│      Bot        │────│                 │
│  - Commands     │    │ - Game Manager  │    │ - Game State    │
│  - Callbacks    │    │ - Role System   │    │ - Player Data   │
│  - Messages     │    │ - State Machine │    │ - Reputation    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Game Architecture

### 1. Truth Wars Game System

#### Game Manager (`truth_wars_manager.py`)
- **Central orchestrator** for all game sessions
- Manages game lifecycle from lobby to completion
- Handles player actions and state transitions
- Implements win condition logic and scoring
- Coordinates between database, roles, and bot interface

#### Game State Machine (`refined_game_states.py`)
- **Phase-based game progression** through 7 distinct phases:
  1. **LOBBY** - Player joining and game setup
  2. **ROLE_ASSIGNMENT** - Secret role distribution
  3. **HEADLINE_REVEAL** - News headline presentation
  4. **DISCUSSION** - Player debate and analysis (2 minutes)
  5. **VOTING** - Trust/Flag voting on headlines
  6. **SNIPE_OPPORTUNITY** - Special ability usage (rounds 1-4)
  7. **ROUND_RESULTS** - Resolution and educational content

#### Role System (`roles.py`)
- **Dynamic role assignments** based on player count
- **5-6 Players**: Fact Checker, Scammer, Normies
- **7+ Players**: Fact Checker, 2x Scammers, Influencer, Normies
- **Special abilities**: Snipe powers, double voting, educational content
- **Faction-based gameplay**: Truth Seekers vs Misinformers

## 2. Database Architecture

### Core Tables

#### **games** - Game Session Management
```sql
id (UUID Primary Key)
game_type (VARCHAR) -- Always "truth_wars"
chat_id (BIGINT) -- Telegram chat ID
status (ENUM) -- waiting, active, completed
current_round (INT) -- Current round (1-5)
created_at, started_at, completed_at (TIMESTAMP)
winning_faction (ENUM) -- truth_team, scammer_team
```

#### **game_players** - Player Participation
```sql
id (UUID Primary Key)
game_id (Foreign Key)
user_id (BIGINT) -- Telegram user ID
current_reputation (INT) -- Current RP (0-3+)
is_ghost_viewer (BOOLEAN) -- 0 RP status
is_shadow_banned (BOOLEAN) -- Current shadow ban
is_active (BOOLEAN) -- Still in game
```

#### **truth_wars_games** - Game-Specific Data
```sql
game_id (Foreign Key)
current_phase (ENUM) -- Current game phase
truth_score (INT) -- Truth Team points (0-3)
scam_score (INT) -- Scammer Team points (0-3)
discussion_duration (INT) -- Phase timing
snipes_available_this_round (BOOLEAN)
```

#### **player_roles** - Role Assignment
```sql
id (UUID Primary Key)
game_player_id (Foreign Key)
role_name (VARCHAR) -- fact_checker, scammer, influencer, normie
faction (ENUM) -- truth_team, scammer_team
snipe_ability_used_rounds (JSON) -- Track ability usage
```

### Educational & Analytics Tables

#### **headlines** - News Content Database
```sql
id (UUID Primary Key)
text (TEXT) -- The headline text
is_real (BOOLEAN) -- True for real news
difficulty (ENUM) -- easy, medium, hard
explanation (TEXT) -- Educational content
fact_check_url (VARCHAR) -- Verification source
```

#### **headline_votes** - Trust/Flag Voting
```sql
id (UUID Primary Key)
game_id, user_id, headline_id (Foreign Keys)
vote (ENUM) -- trust, flag
is_correct (BOOLEAN) -- Whether vote was right
vote_weight (INT) -- 2 for Influencer, 1 for others
round_number (INT) -- When vote was cast
```

#### **snipe_actions** - Shadow Ban System
```sql
id (UUID Primary Key)
game_id, sniper_id, target_id (Foreign Keys)
round_number (INT) -- When snipe was used
snipe_result (ENUM) -- success, failed, self_ban
target_shadow_banned (BOOLEAN) -- Result
```

## 3. Bot Interface Architecture

### Command Handlers (`handlers/command_handlers.py`)
- **`/start`** - Welcome and bot introduction
- **`/help`** - Complete game guide and instructions
- **`/stats`** - Personal game statistics and progress
- **`/leaderboard`** - Top players by wins/accuracy
- **`/play`** - Game selection menu

### Truth Wars Handlers (`handlers/truth_wars_handlers.py`)
- **`/truthwars`** - Create new game lobby (group chats only)
- **`/status`** - Check current game phase and progress
- **`/ability`** - View role info and use special abilities
- **`/vote`** - Vote to eliminate players during elimination phase

### Message Handlers (`handlers/message_handlers.py`)
- **Shadow ban enforcement** - Automatically delete messages from banned players
- **Custom keyboard handling** - Process menu button presses
- **Educational discussions** - Allow free-form chat during discussion phases

### Callback Handlers
- **Join/Start game buttons** - Lobby management
- **Trust/Flag voting** - Headline evaluation interface
- **Snipe targeting** - Special ability usage
- **Continue game** - Round progression

## 4. Game Flow Architecture

### Round Structure (5 Rounds Total)

#### 1. **Headline Reveal Phase** (30 seconds)
- AI-generated or curated headline presented
- Difficulty progression: Easy → Medium → Hard
- Educational context provided

#### 2. **Discussion Phase** (2 minutes)
- Players debate headline authenticity
- Fact Checker gets special information (except 1 blind round)
- [Historical: Drunk player shares media literacy tips]
- Shadow banned players cannot speak

#### 3. **Voting Phase** (45 seconds)
- Trust/Flag buttons for each player
- Influencer votes count as 2 votes
- Ghost Viewers (0 RP) can still vote
- Real-time vote tallying

#### 4. **Snipe Phase** (30 seconds, rounds 1-4)
- Fact Checkers and Scammers can use snipe abilities
- Target elimination or self-shadow ban
- Strategic ability usage

#### 5. **Resolution Phase** (30 seconds)
- Reveal headline truth and voting results
- Update player reputations (+1 correct, -1 incorrect)
- Educational explanation and fact-checking tips
- Team scoring: Truth/Scam teams get points

### Win Conditions
1. **First to 3 Points**: Truth Team or Scammer Team reaches 3 points
2. **5 Rounds Complete**: Highest total faction RP wins
3. **All Opposition Eliminated**: Via shadow bans and 0 RP

## 5. Reputation System Architecture

### 3 RP Starting System
- All players start with **3 Reputation Points**
- **Correct votes**: +1 RP (max varies by game state)
- **Incorrect votes**: -1 RP (minimum 0)
- **0 RP = Ghost Viewer**: Can vote but cannot speak

### Special RP Mechanics
- **Scammer bonus**: +1 RP when fake headlines are trusted
- **Influencer weight**: Votes count as 2 points
- **Shadow ban immunity**: 0 RP players cannot be shadow banned

## 6. Shadow Ban System Architecture

### Snipe Abilities
- **Available rounds**: 1, 2, 3, 4 (not round 5)
- **Fact Checker snipe**: Target suspected Scammers
- **Scammer snipe**: Target suspected Fact Checkers
- **Consequences**: Successful = target shadow banned, Failed = self shadow banned

### Shadow Ban Effects
- **Cannot speak** during discussion phases
- **Can still vote** on headlines
- **Duration**: 1 round (may be extended)
- **Visual feedback**: Messages automatically deleted

## 7. Educational Features Architecture

### Drunk Role Rotation
- **Rotates among Normies** each round
- **Provides media literacy tips** during discussion
- **Encourages learning** through peer teaching
- **Tracks educational effectiveness**

### Fact-Checking Integration
- **Real headlines** from credible sources
- **Fake headlines** with common red flags
- **Detailed explanations** after each vote
- **Verification techniques** teaching
- **Source credibility** education

## 8. Performance & Scalability

### Database Optimization
- **Indexed queries** on game_id, user_id, round_number
- **Connection pooling** via AsyncSession
- **Efficient state updates** with minimal queries
- **Cleanup routines** for completed games

### Bot Response Optimization
- **Async handlers** for concurrent game management
- **Efficient message routing** based on chat context
- **Cached game state** in memory for active games
- **Batch operations** for multi-player updates

### Memory Management
- **Active games dictionary** for fast access
- **Automatic cleanup** on game completion
- **Periodic garbage collection** of old game data
- **Resource limits** on concurrent games

## 9. Error Handling & Monitoring

### Comprehensive Error Handling
- **Telegram API errors** (rate limits, blocked users)
- **Database connection issues** with retry logic
- **Game state corruption** recovery
- **User input validation** and sanitization

### Logging Strategy
- **Structured logging** with user/game context
- **Game events tracking** for analytics
- **Performance monitoring** of phase transitions
- **Error reporting** with stack traces

## 10. Security Considerations

### Input Validation
- **Command parameter sanitization**
- **SQL injection prevention** via ORM
- **User permission checks** for game actions
- **Rate limiting** on command usage

### Data Protection
- **User privacy** - minimal data collection
- **Secure token management** for bot authentication
- **Audit trails** for administrative actions
- **GDPR compliance** considerations

## 11. Development Architecture

### Code Organization
```
bot/
├── main.py                    # Bot entry point and setup
├── handlers/                  # Telegram command/message handlers
│   ├── command_handlers.py
│   ├── truth_wars_handlers.py
│   └── message_handlers.py
├── game/                      # Game logic and state management
│   ├── truth_wars_manager.py
│   ├── refined_game_states.py
│   └── roles.py
├── database/                  # Data persistence layer
│   ├── models.py
│   ├── database.py
│   └── seed_data.py
├── ai/                        # Content generation
│   └── headline_generator.py
└── utils/                     # Shared utilities
    ├── config.py
    └── logging_config.py
```

### Testing Strategy
- **Unit tests** for game logic components
- **Integration tests** for database operations
- **Game flow tests** simulating complete sessions
- **Performance tests** for concurrent game handling

## 12. Future Scalability

### Horizontal Scaling Potential
- **Stateless handler design** enables multiple bot instances
- **Database sharding** by chat_id for large deployments
- **Redis caching** for cross-instance game state
- **Load balancing** for high-volume chats

### Feature Extensibility
- **Plugin architecture** for new game modes
- **Configurable game parameters** via admin interface
- **Multi-language support** framework
- **Advanced analytics** and reporting

---

**Last Updated**: July 2025
**Version**: 3.0 - Truth Wars Refined Implementation
**Architecture**: Specialized Educational Social Deduction Game Bot

**Note (2025-07):** The *Drunk* role has been removed from the codebase. Any references below remain for historical context only and do not reflect current gameplay. 

## Local Setup & Environment

- The bot requires a .env file with all necessary environment variables. If .env.example is not present, create .env manually using the variables described in the documentation and config.py. 