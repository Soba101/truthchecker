# Truth Wars Bot - Quick Setup Guide

## 🚀 Getting Started

This guide will help you set up and run the **Truth Wars** Telegram bot - now fully playable! 

**Status: ✅ READY TO PLAY** - The bot includes complete gameplay with Trust/Flag voting, role assignment, and educational content.

### Prerequisites

- Python 3.8 or higher
- A Telegram account
- Basic command line knowledge

### Step 1: Get a Bot Token

1. Open Telegram and search for `@BotFather`
2. Start a conversation and type `/newbot`
3. Follow the instructions to create your bot
4. Save the bot token (it looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Clone and Setup Project

```bash
# Navigate to your project directory
cd truthchecker

# Install Python dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy the environment template
cp env.example .env

# Edit the .env file with your settings
# At minimum, set your TELEGRAM_BOT_TOKEN
```

**Required Configuration (.env file):**
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_URL=sqlite:///game_bot.db
DEBUG=true
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### Step 4: Run the Bot

```bash
# Run the bot directly
python run_bot.py

# Or run via the bot module
python -m bot.main
```

### Step 5: Test the Bot

1. Find your bot on Telegram (using the username you gave it)
2. Start a conversation
3. Type `/start` to see the welcome message
4. Try other commands like `/help`, `/play`, `/stats`

## 🎮 Available Commands

### Core Commands
- `/start` - Welcome message and introduction
- `/help` - Detailed help and command list
- `/stats` - View your statistics
- `/leaderboard` - See top players

### Truth Wars Game Commands
- `/truthwars` - Create a new Truth Wars game (group chats only)
- `/status` - Check current game status and trigger events
- `/vote` - Vote to eliminate players (during elimination phases)
- `/ability` - View your role abilities

### Game Flow
1. **Create Game**: Use `/truthwars` in a group chat
2. **Join Game**: Click the "Join Game" button (creator must join too)
3. **Start Game**: Creator clicks "Start Game" (minimum 1 player for testing)
4. **Get Role**: Check your private messages for secret role assignment
5. **Play Game**: Headlines will appear - vote Trust or Flag!
6. **Learn**: See explanations and improve your media literacy skills

## 🔧 Development Setup

### Project Structure

```
truthchecker/
├── bot/                    # Main bot application
│   ├── handlers/          # Command and message handlers
│   ├── game/              # Game logic (framework ready)
│   ├── database/          # Database models and operations
│   └── utils/             # Configuration and utilities
├── docs/                  # Documentation
├── tests/                 # Test files
├── requirements.txt       # Python dependencies
├── env.example           # Environment template
└── run_bot.py            # Easy bot runner script
```

### Running Tests

```bash
# Install test dependencies (already in requirements.txt)
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=bot
```

### Development Workflow

1. **Make Changes**: Edit code in the `bot/` directory
2. **Test Changes**: Run tests with `pytest tests/`
3. **Run Bot**: Test with `python run_bot.py`
4. **Check Logs**: Monitor console output for errors

## 📊 Database Setup

The bot uses SQLite by default for development:
- Database file: `game_bot.db` (created automatically)
- Tables created automatically on first run
- No manual setup required

For production, switch to PostgreSQL:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/gamebot
```

## 🎯 Next Steps

### Immediate (After Setup)
- ✅ Verify bot responds to `/start` command
- ✅ Test Truth Wars game creation with `/truthwars`
- ✅ Check role assignment in private messages
- ✅ Test Trust/Flag voting on headlines

### Playing Truth Wars
1. **Add bot to a group chat** (required for multiplayer)
2. **Use `/truthwars`** to create a game lobby
3. **Click "Join Game"** for each player (including creator)
4. **Click "Start Game"** when ready (creator only)
5. **Check private messages** for your secret role
6. **Vote on headlines** using Trust/Flag buttons
7. **Learn media literacy** from explanations!

### Game Features Already Working
✅ **Complete Truth Wars Implementation**:
- Role assignment (Fact Checker, Scammer, Normie, etc.)
- Trust/Flag voting on real/fake headlines
- Automatic game progression
- Educational content with explanations
- Database persistence and player tracking

## 🐛 Troubleshooting

### Common Issues

**Bot doesn't respond:**
- Check your bot token is correct
- Verify the bot is running (no errors in console)
- Make sure you're messaging the right bot

**Database errors:**
- Check file permissions for SQLite database
- Verify DATABASE_URL in .env file
- Try deleting `game_bot.db` to recreate

**Import errors:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version is 3.8+
- Verify you're in the correct directory

**Rate limiting:**
- Telegram limits bot requests
- Wait a few minutes if you see rate limit errors
- Consider adding delays in development

### Getting Help

1. Check the logs for specific error messages
2. Review the documentation in `docs/`
3. Look at the example tests in `tests/`
4. Ensure your environment matches the requirements

## 🔄 Making Changes

### Adding New Commands
1. Add handler function in `bot/handlers/command_handlers.py`
2. Register handler in `bot/main.py`
3. Add tests in `tests/`
4. Update documentation

### Adding Game Logic
1. Create game class in `bot/game/`
2. Integrate with `GameManager`
3. Add database models if needed
4. Write comprehensive tests

### Configuration Changes
1. Add new settings to `bot/utils/config.py`
2. Update `env.example` file
3. Document in relevant docs

---

**🎉 You're ready to start developing your Telegram bot game!**

For detailed planning and architecture information, see the documentation in the `docs/` folder. 