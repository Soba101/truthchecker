# 📅 Truth Wars – Telegram Bot Development Roadmap (1 Jun → 10 Jul 2025)

> Note: This file is named ROADMAP.md. All references in documentation should use this filename for consistency.
> Sprint-level plan for **Telegram bot development** over five weeks. Focus on bot functionality, commands, handlers, and Telegram-specific features.

| Date | Version | Sprint / Codename | Key Deliverables |
|------|---------|------------------|------------------|
| **1 Jun 2025** | **3.1** | Bot Foundation & Setup | • Upgrade `python-telegram-bot` to latest version <br/>• Configure BotFather settings (commands, descriptions, privacy mode) <br/>• Set up bot webhook vs polling configuration <br/>• **Implement `/start` welcome flow with game explanation** |
| **5 Jun 2025** | **3.2** | Command System Enhancement | • Expand `/help` command with interactive inline keyboard <br/>• Add `/rules` command with game rules breakdown <br/>• Implement `/stats` personal statistics display <br/>• **Create admin commands: `/flush`, `/broadcast`, `/maintenance`** |
| **10 Jun 2025** | **3.3** | Game Setup & Lobby System | • Enhance `/truthwars` command with better lobby management <br/>• Add `/join` and `/leave` commands for flexible participation <br/>• Implement lobby countdown timer with live updates <br/>• **Create inline keyboard for game difficulty selection** |
| **15 Jun 2025** | **3.4** | Multi-Chat Support | • Enable bot to handle multiple concurrent games across chats <br/>• Add `/newgame <room_code>` for private lobbies <br/>• Implement chat-specific game state isolation <br/>• **Create `/rooms` command to list active games** |
| **20 Jun 2025** | **3.5** | Enhanced Voting & UI | • Redesign Trust/Flag voting buttons with emojis <br/>• Add vote confirmation messages and vote changing <br/>• Implement real-time vote counter display <br/>• **Create `/vote_status` command to check current votes** |
| **25 Jun 2025** | **3.6** | Role System & Abilities | • Enhance role assignment notifications with custom messages <br/>• Implement `/ability` command to check role powers <br/>• Add private DM notifications for special role actions <br/>• **Create `/snipe` command with target selection inline keyboard** |
| **30 Jun 2025** | **4.0-RC** | Bot Polish & Testing | • Comprehensive message formatting and emoji consistency <br/>• Error handling for all edge cases (network, API limits) <br/>• Rate limiting and spam protection <br/>• **Complete BotFather optimization (description, commands, about)** |
| **5 Jul 2025** | **4.1** | Advanced Features | • Implement `/leaderboard` with pagination <br/>• Add `/history` command to view past games <br/>• Create game replay system with `/replay <game_id>` <br/>• **Implement bot notifications for game events** |
| **9 Jul 2025** | **5.0** | Production Launch | • Switch to production bot token <br/>• Configure webhook for production environment <br/>• Submit bot to Telegram Bot Directory <br/>• **Launch announcement in bot channels and groups** |
| **10 Jul 2025** | **5.1** | Monitoring & Maintenance | • Monitor Telegram API rate limits and errors <br/>• Implement automatic error reporting to admins <br/>• Add bot health check via `/ping` command <br/>• **Set up log monitoring for bot performance** |

---

## 📈 Post-10 Jul 2025 – Telegram Bot Backlog
* **Inline Query Support** - Allow users to share game stats via `@truthwarsbot`
* **Bot Payments Integration** - Premium features or donations via Telegram Payments
* **Group Admin Integration** - Respect group permissions and admin controls
* **Callback Query Optimization** - Reduce button response time
* **Multi-language Support** - Internationalization for global users
* **Bot API Webhooks** - Advanced webhook handling for better performance

---