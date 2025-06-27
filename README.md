# Telegram Bot Game

A Telegram bot-based game built with Python using the python-telegram-bot library.

## Project Overview

This project implements a game through a Telegram bot interface, allowing users to interact and play directly within Telegram.

## Features (Planned)

- User registration and profiles
- Game state management
- Interactive gameplay through Telegram commands
- Score tracking and leaderboards
- Admin commands for game management

## Project Structure

```
truthchecker/
├── bot/                    # Main bot application
│   ├── __init__.py
│   ├── main.py            # Bot entry point
│   ├── handlers/          # Command and message handlers
│   ├── game/              # Game logic modules
│   ├── database/          # Database models and operations
│   └── utils/             # Utility functions
├── config/                # Configuration files
├── docs/                  # Documentation
├── tests/                 # Test files
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## Getting Started

### Prerequisites

- Python 3.8+
- Telegram Bot Token (from @BotFather)
- PostgreSQL or SQLite for data storage

### Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and configure your settings
4. Run the bot: `python bot/main.py`

## Development Status

🚧 **Project is in early development phase**

Currently implementing:
- [ ] Basic bot setup and configuration
- [ ] User registration system
- [ ] Game framework architecture
- [ ] Database schema design

## Documentation

- [Project Planning](docs/PLANNING.md) - Overall project roadmap
- [Bot Architecture](docs/ARCHITECTURE.md) - Technical architecture details
- [Game Design](docs/GAME_DESIGN.md) - Game mechanics and rules
- [API Documentation](docs/API.md) - Bot commands and responses

## Contributing

This project follows clean code principles:
- Write simple, readable code
- Keep files small and focused (<200 lines)
- Test after every meaningful change
- Use clear, consistent naming
- Include comprehensive comments

## License

[Add your preferred license here] 