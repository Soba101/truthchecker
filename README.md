# Truth Wars - Educational Telegram Bot Game

A sophisticated Telegram bot implementing the "Truth Wars" game - an educational multiplayer social deduction experience that teaches media literacy through interactive gameplay. Players vote on headlines to determine if they're real or fake while taking on special roles with unique abilities in a strategic battle between Truth Seekers and Misinformers.

## 🎮 Game Overview

Truth Wars combines social deduction with media literacy education in an engaging 5-round format:

- **5-8 players** engage in a **fixed 5-round structure** (optimized for 45-minute games)
- **Trust/Flag voting** on carefully curated real and fake headlines
- **Dynamic reputation system** starting with 3 RP, becoming Ghost Viewer at 0 RP
- **Role-based gameplay** with strategic abilities:
  - **Fact Checker** (Truth Team) - Gets insider info, can snipe suspected Scammers
  - **Scammer** (Misinformation Team) - Spreads doubt, can snipe suspected Fact Checkers  
  - **Influencer** (Truth Team) - Double-weighted votes (2x voting power)
  - **Normies** (Various Teams) - Standard players, learn through gameplay
- **Snipe abilities** for strategic shadow banning (Rounds 1-4 only)
- **Educational content** seamlessly integrated through gameplay mechanics
- **Win conditions**: First faction to 3 points OR highest combined reputation after 5 rounds

## ✨ Key Features

### 🎯 **Educational Focus**
- **Real-world headlines** from credible news sources
- **Carefully crafted fake news** with common misinformation patterns
- **Detailed explanations** after each vote revealing truth and teaching detection techniques
- **Media literacy concepts** taught through the rotating Drunk role
- **Progressive difficulty** from easy to hard headlines across 5 rounds

### 🏆 **Reputation System**
- **3 Reputation Points** starting system - lose 1 for incorrect votes, gain 1 for correct votes
- **Ghost Viewer mechanics** - 0 RP players can vote but cannot speak during discussions
- **Strategic depth** - Shadow banned players lose voice but retain voting power
- **Comprehensive tracking** - All reputation changes logged with detailed reasoning

### 🎭 **Role-Based Strategy**
- **Faction warfare** between Truth Seekers and Misinformers
- **One-time snipe abilities** (Rounds 1-4) create high-stakes tactical moments
- **Educational role rotation** - Drunk role rotates among Normies for peer teaching
- **Influencer mechanics** - Double-weighted votes can swing close decisions
- **Blind rounds** - Fact Checker occasionally doesn't get insider information

### 📊 **Progress Tracking**
- **Individual statistics** - Win rates, accuracy, role performance
- **Learning analytics** - Media literacy improvement over time
- **Game history** - Detailed records of all games and decisions
- **Leaderboards** - Top players by wins, accuracy, and learning progress

## 🏗️ Project Structure

```
truthchecker/
├── bot/                    # Main bot application
│   ├── ai/                # AI headline generation & content curation
│   │   ├── headline_generator.py
│   │   └── ai_headline_seeder.py
│   ├── database/          # Async SQLAlchemy models & database management
│   │   ├── models.py      # Complete game data models
│   │   ├── database.py    # Database session management
│   │   └── seed_data.py   # Initial data population
│   ├── game/              # Core game logic & state management
│   │   ├── truth_wars_manager.py      # Central game orchestrator
│   │   ├── refined_game_states.py     # Phase-based state machine
│   │   └── roles.py                   # Role system & abilities
│   ├── handlers/          # Telegram command/message handlers
│   │   ├── command_handlers.py        # Basic bot commands
│   │   ├── truth_wars_handlers.py     # Game-specific handlers
│   │   ├── message_handlers.py        # Chat message processing
│   │   └── error_handlers.py          # Error handling & recovery
│   ├── utils/             # Shared utilities & configuration
│   │   ├── config.py      # Environment configuration
│   │   └── logging_config.py          # Structured logging setup
│   └── main.py            # Bot entry point & application setup
├── docs/                  # Comprehensive documentation
│   ├── ARCHITECTURE.md              # Technical architecture overview
│   ├── DATABASE_SCHEMA_REFINED.md   # Complete database schema
│   ├── BOTFATHER_SETUP.md           # Bot configuration guide
│   ├── PROJECT_DOCUMENTATION.md     # Development documentation
│   ├── ROADMAP.md                   # Future development plans
│   ├── SETUP_GUIDE.md               # Quick setup instructions
│   ├── TRUTH_WARSV2.md              # Game design evolution
│   ├── TRUTH_WARSV3.md              # Current game design
│   └── V3_IMPLEMENTATION.md         # Implementation details
├── tests/                 # Comprehensive test suite
│   ├── test_example.py    # Basic functionality tests
│   └── test_truthwars_v3.py         # Game logic tests
├── deploy/                # Deployment configurations
├── run_bot.py             # Simple launcher script
├── requirements.txt       # Python dependencies
├── game.db                # SQLite development database
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (3.9+ recommended)
- **Telegram Bot Token** (from [@BotFather](https://t.me/BotFather))
- **Group Chat** (Truth Wars requires 5-8 players)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/truthchecker.git
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

# Optional: Database configuration (defaults to SQLite)
DATABASE_URL=sqlite+aiosqlite:///game.db

# Optional: Environment settings
ENVIRONMENT=development
LOG_LEVEL=INFO

# Optional: AI/Content settings
OPENAI_API_KEY=your_openai_key_here  # For AI headline generation
CONTENT_MODERATION=true
```

## 🎯 Game Commands

### Basic Commands
- `/start` - Welcome message and bot introduction
- `/help` - Complete game guide and instructions  
- `/stats` - View your personal game statistics and learning progress
- `/leaderboard` - See top players by wins, accuracy, and media literacy

### Game Commands (Groups Only)
- `/truthwars` - Start a new Truth Wars game lobby
- `/status` - Check current game status, round info, and player roles
- `/ability` - View your current role, abilities, and use special powers
- `/vote` - Cast elimination votes during player voting phase (if enabled)

### Interactive Elements
- **Trust/Flag Buttons** - Vote on headlines during voting phases
- **Snipe Targeting** - Use special abilities to shadow ban opponents
- **Join/Start Game** - Lobby management through inline keyboards
- **Continue Game** - Progress through rounds via button presses

## 🛠️ Technology Stack

- **Bot Framework**: [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) 21.5+
- **Database**: SQLite with [SQLAlchemy](https://sqlalchemy.org/) 2.0 (async ORM)
- **Configuration**: [Pydantic](https://pydantic.dev/) with environment variable validation
- **Logging**: [Structlog](https://structlog.org/) for structured, contextual logging
- **Testing**: [Pytest](https://pytest.org/) with async support and fixtures
- **Data Storage**: JSON fields for flexible game state and analytics
- **Content**: Curated real/fake headlines with educational explanations

## 📊 Development Status

### 🟢 **Core Features Complete**
- ✅ **Full game implementation** with optimized 5-round structure
- ✅ **Reputation system** with 3 RP starting points and Ghost Viewer mechanics
- ✅ **Trust/Flag voting** with weighted votes and accuracy tracking
- ✅ **Complete role system** with Fact Checker, Scammer, Influencer, Drunk, Normie
- ✅ **Snipe mechanics** for strategic shadow banning (Rounds 1-4)
- ✅ **Educational content delivery** via rotating Drunk role with media literacy tips
- ✅ **Comprehensive statistics** tracking individual and game performance
- ✅ **Database schema** with complete relationship mapping and analytics support
- ✅ **Error handling** and recovery mechanisms for robust gameplay
- ✅ **Performance optimization** for concurrent game management

### 🟡 **In Progress**
- 🔄 **Advanced analytics dashboard** for learning insights and improvement tracking
- 🔄 **Additional headline content** with expanded categories and difficulty progression
- 🔄 **Multi-language support** for international accessibility
- 🔄 **Tournament mode** for competitive educational events

### 🔴 **Future Enhancements**
- 📋 **Admin controls** for game moderation and content management
- 📋 **Custom headline submission** system with community curation
- 📋 **Integration with fact-checking APIs** for real-time content verification
- 📋 **Advanced AI opponent** for single-player practice mode

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests with coverage
pytest --cov=bot --cov-report=html

# Run specific test categories
pytest tests/test_game_logic.py          # Game mechanics
pytest tests/test_database.py           # Database operations  
pytest tests/test_handlers.py           # Command handlers
pytest tests/test_integration.py        # End-to-end scenarios

# Run with verbose output
pytest -v --tb=short

# Test database models specifically
python -m pytest tests/test_models.py -v
```

## 📖 Documentation

Comprehensive documentation is available in the `docs/` directory:

### 🏛️ **Architecture & Design**
- [**Architecture Overview**](docs/ARCHITECTURE.md) - Technical system architecture
- [**Database Schema**](docs/DATABASE_SCHEMA_REFINED.md) - Complete data model documentation
- [**Project Documentation**](docs/PROJECT_DOCUMENTATION.md) - Development guide and code structure

### 🎮 **Game Design**
- [**Truth Wars v3 Design**](docs/TRUTH_WARSV3.md) - Current game mechanics and rules
- [**Implementation Guide**](docs/V3_IMPLEMENTATION.md) - Technical implementation details
- [**Design Evolution**](docs/TRUTH_WARSV2.md) - Game design history and decisions

### 🚀 **Setup & Configuration**
- [**Setup Guide**](docs/SETUP_GUIDE.md) - Step-by-step installation instructions
- [**BotFather Setup**](docs/BOTFATHER_SETUP.md) - Telegram bot configuration
- [**Development Roadmap**](docs/ROADMAP.md) - Future development plans

## 🤝 Contributing

This project follows clean code principles and educational best practices:

### 📋 **Code Standards**
- **Write simple, readable code** with clear documentation and comments
- **Keep files focused** and modular (<200 lines when possible)
- **Test thoroughly** after every meaningful change with automated tests
- **Use clear, consistent naming** throughout the codebase
- **Include explanatory comments** for complex logic and game mechanics

### 🎯 **Development Workflow**
1. **Fork the repository** and create a feature branch
2. **Write tests** for new functionality before implementation
3. **Implement changes** following existing code patterns
4. **Update documentation** to reflect changes
5. **Run full test suite** to ensure no regressions
6. **Submit pull request** with detailed description

### 🧪 **Testing Requirements**
- **Unit tests** for all new functions and classes
- **Integration tests** for game flow and database operations
- **Performance tests** for concurrent game handling
- **Edge case testing** for error conditions and recovery

## 🎓 Educational Goals

Truth Wars is designed to teach essential media literacy skills through engaging gameplay:

### 📰 **Content Evaluation**
- **Source Verification** - How to research and verify news source credibility
- **Fact-Checking Techniques** - Using multiple sources and verification tools
- **Publication Date Awareness** - Understanding timing and context of news
- **Author Credibility** - Evaluating journalist expertise and bias

### 🔍 **Critical Analysis**
- **Bias Recognition** - Identifying language bias, loaded terms, and framing
- **Logical Fallacy Detection** - Spotting common reasoning errors
- **Evidence Assessment** - Evaluating quality and relevance of supporting evidence
- **Emotional Manipulation** - Recognizing appeals to fear, anger, and prejudice

### 🚩 **Red Flag Detection**
- **Sensationalist Headlines** - Identifying clickbait and exaggerated claims
- **Suspicious Sources** - Recognizing fake news websites and unreliable publishers
- **Fabricated Content** - Detecting doctored images, false quotes, and manufactured stories
- **Conspiracy Theories** - Understanding common patterns and logical flaws

### 🧠 **Meta-Cognitive Skills**
- **Information Seeking** - Developing habits of verification and cross-referencing
- **Confirmation Bias Awareness** - Recognizing and countering personal biases
- **Media Ecosystem Understanding** - Learning how information spreads and mutates
- **Digital Citizenship** - Responsible sharing and consumption of online content

## 🔧 Technical Features

### 🎯 **Game Engine**
- **Async architecture** for concurrent game management
- **State machine implementation** for reliable phase transitions
- **Comprehensive error handling** with graceful degradation
- **Performance optimization** for large group chats

### 📊 **Analytics & Learning**
- **Individual progress tracking** across multiple game sessions
- **Learning effectiveness measurement** through accuracy improvement
- **Content performance analysis** for headline difficulty optimization
- **Behavioral pattern recognition** for personalized learning paths

### 🔒 **Security & Privacy**
- **Input validation** and sanitization for all user inputs
- **Rate limiting** to prevent abuse and spam
- **Minimal data collection** with focus on educational analytics
- **Secure token management** for bot authentication

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support & Troubleshooting

### 📚 **Quick References**
- **Setup Issues**: Check [Setup Guide](docs/SETUP_GUIDE.md) for detailed instructions
- **Bot Configuration**: See [BotFather Setup](docs/BOTFATHER_SETUP.md) for Telegram configuration
- **Game Rules**: Use `/help` command in Telegram for complete game guide
- **Technical Issues**: Check logs for error messages and debugging information

### 🐛 **Common Issues**
- **Bot not responding**: Verify token and network connectivity
- **Commands showing @username**: Configure privacy settings in BotFather
- **Database errors**: Check file permissions and disk space
- **Group chat issues**: Ensure bot has proper administrator permissions

### 📞 **Getting Help**
- **Documentation**: Comprehensive guides in the `docs/` directory
- **Error Logs**: Enable debug logging for detailed error information
- **Community**: Join our development discussions and issue tracking
- **Support**: Submit detailed bug reports with reproduction steps

---

**Truth Wars** - *Teaching media literacy through engaging social gameplay* 🎓📰🎮
