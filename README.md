# Truth Wars - Telegram Bot Game

A sophisticated Telegram bot implementing the "Truth Wars" game - an educational multiplayer experience that teaches media literacy through interactive gameplay. Players vote on headlines to determine if they're real or fake while taking on special roles with unique abilities.

## 🎮 Game Overview

Truth Wars combines social deduction with media literacy education:
- **5-10 players** engage in a **5-round fixed structure**
- **Trust/Flag voting** on real and fake headlines
- **Reputation system** (3 RP → Ghost Viewer when depleted)
- **Role-based gameplay** with Fact Checkers, Scammers, Influencers, and rotating Drunk educators
- **Snipe abilities** for strategic shadow banning
- **Educational content** delivery through gameplay

## ✨ Key Features

- **Educational Focus**: Learn to identify misinformation through gameplay
- **Reputation System**: 3 Reputation Points system with Ghost Viewer mechanics
- **Role Rotation**: Dynamic Drunk role rotation among Normies for education
- **Strategic Depth**: One-time Snipe ability (Rounds 1–4) adds high-stakes moments
- **Progress Tracking**: Comprehensive statistics and learning analytics
- **Cross-Platform**: Works in any Telegram group chat

## 🏗️ Project Structure

```
truthchecker/
├── bot/                    # Main bot application
│   ├── ai/                # AI headline generation
│   ├── database/          # Async SQLAlchemy models & sessions
│   ├── game/              # Core game logic (roles, state machine, manager)
│   ├── handlers/          # Telegram command/message handlers
│   ├── utils/             # Config & logging helpers
│   └── main.py            # Bot entry point
├── docs/                  # Documentation (architecture, game design, etc.)
├── deploy/                # Deployment scripts / configs
├── tests/                 # Pytest test suite
├── run_bot.py             # Simple launcher helper
├── requirements.txt       # Python dependencies
├── game.db                # SQLite dev database
├── SETUP_GUIDE.md         # Quick setup instructions
├── BOTFATHER_SETUP.md     # BotFather configuration helper
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Telegram Bot Token** (from [@BotFather](https://t.me/BotFather))
- **Group Chat** (Truth Wars requires multiple players)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd truthchecker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your bot token and settings
   ```

4. **Start the bot**
   ```bash
   python run_bot.py
   ```

### Essential Configuration (.env file)

```bash
# Required: Get this from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional: Database (defaults to SQLite)
DATABASE_URL=sqlite+aiosqlite:///game.db

# Optional: Environment settings
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## 🎯 Game Commands

### Basic Commands
- `/start` - Welcome message and bot introduction
- `/help` - Complete game guide and instructions
- `/stats` - View your personal game statistics
- `/leaderboard` - See top players and rankings

### Game Commands (Groups Only)
- `/truthwars` - Start a new Truth Wars game
- `/status` - Check current game status and round info
- `/ability` - View your current role and special abilities
- `/vote` - Cast Trust/Flag votes on headlines

## 🛠️ Technology Stack

- **Framework**: [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) 21.5
- **Database**: SQLite with [SQLAlchemy](https://sqlalchemy.org/) 2.0 (async)
- **Configuration**: [Pydantic](https://pydantic.dev/) with environment variables
- **Logging**: [Structlog](https://structlog.org/) for structured logging
- **Testing**: [Pytest](https://pytest.org/) with async support

## 📊 Development Status

🟢 **Core Features Complete**
- ✅ Full game implementation with 5-round structure
- ✅ Reputation system (3 RP → Ghost Viewer)
- ✅ Trust/Flag voting on headlines
- ✅ Role system with special abilities
- ✅ Snipe mechanics for shadow banning
- ✅ Educational content delivery via Drunk role
- ✅ Comprehensive statistics tracking
- ✅ Database schema with full relationship mapping

🟡 **In Progress**
- 🔄 Additional headline content and difficulty balancing
- 🔄 Advanced analytics and learning insights
- 🔄 Performance optimizations for larger groups

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=bot

# Test database models specifically
python test_db_models.py
```

## 📖 Documentation

Comprehensive documentation is available in the `docs/` directory:
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Game Design Document](docs/TRUTH_WARS_REFINED_GAME_DESIGN.md)
- [Database Schema](docs/DATABASE_SCHEMA_REFINED.md)
- [Development Progress](docs/DEVELOPMENT_PROGRESS.md)

## 🤝 Contributing

This project follows clean code principles:
- **Write simple, readable code** with clear documentation
- **Keep files focused** (<200 lines when possible)
- **Test thoroughly** after every meaningful change
- **Use clear, consistent naming** throughout
- **Include explanatory comments** for complex logic

## 🎓 Educational Goals

Truth Wars is designed to teach:
- **Source Verification**: How to check news source credibility
- **Bias Recognition**: Identifying language bias and loaded terms
- **Red Flag Detection**: Spotting common misinformation patterns
- **Critical Thinking**: Evaluating claims and evidence
- **Media Literacy**: Understanding how information spreads

## 📝 License

MIT License

## 🆘 Support

- **Setup Issues**: Check [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Bot Configuration**: See [BOTFATHER_SETUP.md](BOTFATHER_SETUP.md)
- **Game Rules**: Use `/help` command in Telegram
- **Technical Issues**: Check the logs and error messages
