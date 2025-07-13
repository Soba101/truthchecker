# 🗂️ Truth Wars – Project Documentation

Welcome!  This guide explains every moving part of the **Truth Wars Telegram Bot** so a new developer can be productive fast.

---

## 1. Project Purpose
Truth Wars is a **5-round social-deduction game** that teaches media-literacy through interactive gameplay. Players debate headlines (real or fake) and vote **Trust** or **Flag** to determine authenticity. Special roles create strategic depth while the bot manages game flow, scoring, and educational content delivery.

**Key Learning Goals:**
- Source verification and credibility assessment
- Bias recognition and critical thinking
- Red flag identification in misinformation
- Understanding how information spreads

## 2. Game Rules Summary (v3)

### Player Roles & Counts
| Role | Count | Special Abilities |
|------|-------|-------------------|
| 🧠 **Fact Checker** | 1 | • **3 peeks** per game (not consecutive rounds)<br/>• **1 snipe** ability (Rounds 1-4 only) |
| 😈 **Scammer** | 1 (5-6p) / 2 (7-10p) | • Always knows headline truth<br/>• Tries to mislead majority votes |
| 🧍 **Misinformed Users** | remaining | • No special powers<br/>• Regular players ("normies") |
| 🎭 **Influencer** | 1 (7-10p only) | • **Vote counts as 2 votes**<br/>• No other abilities |

### Scoring System
| Majority Vote Outcome | Points Awarded |
|----------------------|----------------|
| Fake headline **flagged** | +1 **Truth Team** |
| Real headline **trusted** | +1 **Truth Team** |
| Fake headline **trusted** | +1 **Scammers** |
| Real headline **flagged** | +1 **Scammers** |

**Win Conditions:** First team to 3 points OR all Scammers shadow-banned.

### Round Structure (5 rounds max)
1. **Headline Reveal** + Drunk gets private hint
2. **Discussion Phase** (3 min) + optional Fact Checker peek
3. **Trust/Flag Vote** (with Influencer 2x weight)
4. **Fact Checker Snipe** (Rounds 1-4 only)
5. **Shadow-Ban Vote** (Rounds 2-5)
6. **Scoring Update** + results announcement
7. **Next Round** or game end

## 3. Tech Stack
| Layer | Choice | Notes |
|-------|--------|-------|
| Language | Python 3.10+ | Async/await throughout |
| Bot Framework | `python-telegram-bot` 21.x | Uses `Application` + async handlers |
| DB | SQLite (dev) via SQLAlchemy 2.0 | Easy to swap to Postgres |
| AI | OpenAI Chat API | Generates extra headlines |
| Config | `dotenv` + custom Settings class | Located in `bot/utils/config.py` |
| Logging | `structlog` | JSON logs for cloud shipping |
| Tests | `pytest` + `pytest-asyncio` | ≈90% coverage for core logic |

## 4. Directory Tour
```
truthchecker/
│
├─ bot/                   # Main application package
│  ├─ ai/                 # Headline generation helpers
│  │  ├─ ai_headline_seeder.py   # Seeds default headline set
│  │  └─ headline_generator.py   # OpenAI + DB fallback logic
│  │
│  ├─ database/           # Persistence layer
│  │  ├─ database.py      # Async engine/session creator
│  │  ├─ models.py        # SQLAlchemy models (Game, Player, Vote, etc.)
│  │  └─ seed_data.py     # Seed fixtures for dev
│  │
│  ├─ game/               # Core gameplay logic
│  │  ├─ roles.py                 # Role definitions & utilities
│  │  ├─ refined_game_states.py   # Finite-state machine for 5-round flow
│  │  ├─ game_manager.py          # Legacy manager (kept for reference)
│  │  └─ truth_wars_manager.py    # High-level orchestrator (current)
│  │
│  ├─ handlers/           # Telegram update handlers
│  │  ├─ command_handlers.py      # /start, /truthwars, /help, /stats
│  │  ├─ message_handlers.py      # Text messages, rate limit, shadow-ban filter
│  │  ├─ truth_wars_handlers.py   # Inline button callbacks, vote handling
│  │  └─ error_handlers.py        # Global error logging
│  │
│  ├─ utils/              # Helpers
│  │  ├─ config.py            # Settings loader (env vars → Settings)
│  │  └─ logging_config.py    # structlog setup
│  │
│  └─ main.py             # `python -m bot.main` entrypoint
│
├─ docs/                  # All documentation & design specs
├─ tests/                 # Pytest suite (unit + integration)
├─ deploy/                # Docker, CI scripts (optional)
├─ run_bot.py             # Shortcut runner (reads .env)
└─ requirements.txt       # Locked versions
```

## 5. Key Environment Variables (`.env`)
| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather | **Required** |
| `DATABASE_URL` | SQLAlchemy URL | `sqlite+aiosqlite:///game.db` |
| `OPENAI_API_KEY` | Needed for AI headlines | '' (disabled) |
| `AI_HEADLINE_ENABLED` | Toggle AI generation | `false` |
| `AI_HEADLINE_USAGE_PERCENTAGE` | % of AI vs DB headlines | `50` |
| `MAX_CONCURRENT_GAMES` | Throttle to avoid spam | `100` |
| `GAME_SESSION_TIMEOUT` | Seconds of idle before cleanup | `3600` |
| `ADMIN_USER_IDS` | Comma-sep list of Telegram IDs | '' |
| `RATE_LIMIT_PER_USER` | Commands per user per window | `10` |
| `RATE_LIMIT_WINDOW` | Rate limit window in seconds | `60` |
| `SENTRY_DSN` | Error tracking | '' |
| `PROMETHEUS_PORT` | Metrics port | `8000` |

Full list & parsing logic: `bot/utils/config.py`.

## 6. Database Models (detailed)
| Table | Key Fields | Purpose |
|-------|-----------|---------|
| `players` | `id`, `tg_id`, `name`, `role`, `reputation` | Tracks each user across games |
| `games` | `id`, `chat_id`, `round_no`, `state`, `truth_score`, `scam_score` | One row per active game |
| `headlines` | `id`, `text`, `is_real`, `difficulty`, `source` | Source pool for headlines |
| `votes` | `id`, `game_id`, `player_id`, `round_no`, `choice` | Trust/Flag voting history |
| `shadow_bans` | `id`, `player_id`, `round_no`, `reason` | Snipe & ban tracking |
| `snipe_actions` | `id`, `game_id`, `shooter_id`, `target_id`, `success` | Fact-Checker snipe log |
| `player_reputation` | `id`, `player_id`, `game_id`, `change`, `reason` | RP change tracking |
| `round_results` | `id`, `game_id`, `round_no`, `headline_id`, `majority_vote` | Round outcome log |

**Key Relationships:**
- `Game` → many `Player` (via game_id)
- `Game` → many `Vote` (per round)
- `Player` → many `ShadowBan` (tracking bans)
- `Player` → many `SnipeAction` (as shooter/target)

## 7. Gameplay Flow (Technical)
1. **Command `/truthwars`** → `command_handlers.py` → `TruthWarsManager.start_game()`
2. **Lobby Phase** → Collect players, assign roles via `roles.py`
3. **State Machine** → `refined_game_states.py` drives phase transitions:
   ```txt
   LOBBY → ROLE_ASSIGNMENT → HEADLINE_REVEAL → DISCUSSION → VOTING → RESULTS
        ↘ (Rounds 1-4) SNIPE_PHASE → SHADOW_BAN_VOTE ↙
   ```
4. **Vote Handling** → `truth_wars_handlers.py` processes inline button callbacks
5. **Scoring** → `truth_wars_manager.py` calculates points, updates DB
6. **Shadow Ban** → `message_handlers.py` filters messages from banned players

## 8. Core Classes & Methods
| File | Class | Key Methods |
|------|-------|-------------|
| `roles.py` | `Role`, `RoleSet` | `assign_roles()`, `get_role_description()` |
| `refined_game_states.py` | `TruthWarsState` | `advance_phase()`, `can_transition()` |
| `truth_wars_manager.py` | `TruthWarsManager` | `start_game()`, `process_vote()`, `handle_snipe()` |
| `headline_generator.py` | `HeadlineGenerator` | `get_headline()`, `generate_ai_headline()` |
| `database.py` | `DatabaseSessionManager` | `get_session()`, `create_tables()` |

## 9. Important Implementation Details

### Vote Weight Calculation
```python
# Influencer votes count as 2
vote_weight = 2 if player.role == Role.INFLUENCER else 1
```

### Snipe Mechanics
- **Who:** Only Fact Checker
- **When:** Rounds 1-4 only (not Round 5)
- **Limit:** Once per game
- **Success:** If target is Scammer → shadow ban, else nothing

### Shadow Ban Enforcement
- Implemented in `message_handlers.py`
- Banned players' messages are deleted
- Private notification sent to banned player
- Affects discussion phase only (can still vote)

### Headline Selection
- Two pools: Set A (3 real/2 fake) or Set B (2 real/3 fake)
- Random set selection at game start
- AI generation + DB fallback system

## 10. Running Locally
```bash
pip install -r requirements.txt
cp .env.example .env  # add TELEGRAM_BOT_TOKEN
python run_bot.py     # launches polling bot
```

**For webhook mode:**
```bash
# Use ngrok for local webhook testing
ngrok http 8000
# Set TELEGRAM_WEBHOOK_URL in .env
```

## 11. Testing Strategy
```bash
pytest                    # run all tests
pytest -k "test_voting"   # filter by keyword
pytest --cov=bot         # with coverage
```

**Key Test Files:**
- `tests/test_truthwars_v3.py` – Full 5-round game simulation
- `tests/test_example.py` – Unit tests for core functions
- Integration tests for role assignment, voting, snipe mechanics

## 12. Deployment Checklist
- [ ] **Environment Variables:** All required vars set in production
- [ ] **Database:** Migrate to Postgres for production load
- [ ] **Webhook:** Configure production webhook URL
- [ ] **BotFather:** Update bot description, commands, privacy settings
- [ ] **Monitoring:** Sentry for errors, Prometheus for metrics
- [ ] **Rate Limiting:** Configure appropriate limits for production

## 13. Common Maintenance Tasks
| Action | Command |
|--------|---------|
| Add headlines | `python bot/ai/ai_headline_seeder.py data.csv` |
| Run migrations | `alembic revision --autogenerate && alembic upgrade head` |
| Seed dev DB | `python bot/database/seed_data.py` |
| Debug logs | Set `LOG_LEVEL=DEBUG` in `.env` |
| Admin cleanup | `/admin cleanup` (Telegram, admin only) |
| Check bot health | `/ping` command |

## 14. Troubleshooting Guide
| Problem | Solution |
|---------|----------|
| Bot not responding | Check `TELEGRAM_BOT_TOKEN` and network connectivity |
| Database locked | Switch to Postgres or check SQLite file permissions |
| High memory usage | Monitor concurrent games, adjust `MAX_CONCURRENT_GAMES` |
| Spam/abuse | Tune `RATE_LIMIT_PER_USER` and `RATE_LIMIT_WINDOW` |
| Vote buttons not working | Check callback query handlers in `truth_wars_handlers.py` |
| Shadow ban not working | Verify message filtering in `message_handlers.py` |

## 15. Game Balance & Tuning
**Current Balance Settings:**
- Fact Checker: 3 peeks per game
- Snipe: Once per game, Rounds 1-4 only
- Discussion: 3 minutes per round
- Win condition: First to 3 points

**Tuning Knobs (in code):**
- Reduce peeks to 2 if Truth Team dominates
- Adjust Drunk hint accuracy (currently 100%)
- Modify discussion timer length
- Change win condition threshold

## 16. Future Enhancements
See `docs/TRUTH_WARS_ROADMAP.md` for detailed timeline.

**Immediate Priorities:**
- Multi-lobby support for concurrent games
- Enhanced statistics and analytics
- Improved onboarding flow
- Advanced admin tools

**Long-term Vision:**
- Tournament mode
- Classroom integration
- Advanced difficulty presets
- Multi-language support

**Note (2025-07):** The *Drunk* role has been deprecated and removed from the implementation. References to it below are historical.

---

*Document last updated: **July 2025** – update this line when you edit.* 