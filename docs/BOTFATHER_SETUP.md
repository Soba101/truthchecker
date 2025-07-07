# BotFather Configuration Guide

## How to Fix Commands Showing @botusername

When commands show as `/ability@realorfahke_bot` instead of `/ability`, follow these steps:

### 1. CRITICAL: Configure Commands in BotFather

**This is the most important step!** The commands MUST be set in BotFather to display cleanly.

1. **Open Telegram and message @BotFather**
2. **Send `/setcommands`**
3. **Select your bot from the list** 
4. **Copy and paste EXACTLY this command list:**

```
start - Welcome message and introduction
help - Complete guide and instructions
truthwars - Start Truth Wars game (groups only)
status - Check current game status
ability - View your role and abilities
vote - Vote to eliminate a player
stats - View your game statistics
leaderboard - See top players
play - Browse other games
```

**IMPORTANT:** Make sure there are no extra spaces or formatting. Each line should be exactly: `command - description`

### 2. CRITICAL: Configure Bot Privacy Settings

1. **Send `/setprivacy` to @BotFather**
2. **Select your bot**
3. **Choose `Disable`** - This is REQUIRED for clean commands in groups
4. You should see: `Privacy mode is disabled for YourBot`

### 3. CRITICAL: Configure Bot Domain (Optional but Recommended)

1. **Send `/setdomain` to @BotFather**
2. **Select your bot**
3. **Send your domain** (or just press /cancel if you don't have one)

### 4. Set Bot Description

1. **Send `/setdescription` to @BotFather**
2. **Select your bot**
3. **Enter:** `Truth Wars - Learn to spot fake news while playing a fun social game!`

### 5. Set Bot About Text

1. **Send `/setabouttext` to @BotFather**
2. **Select your bot**
3. **Enter:** `Educational game bot that teaches media literacy through social gameplay`

### 6. Set Bot Profile Photo (Optional)

1. **Send `/setuserpic` to @BotFather**
2. **Select your bot**
3. **Send a square image** for your bot's profile picture

## Why This Happens

- **Group Disambiguation**: Telegram shows @username in groups with multiple bots
- **Command Menu**: Without proper BotFather setup, the command menu doesn't work cleanly
- **Bot Privacy**: Privacy settings affect how commands are processed

## Expected Results

After configuration:
- ✅ Clean command menu when typing `/`
- ✅ Commands work both as `/ability` and `/ability@botusername`
- ✅ Better user experience in groups
- ✅ Professional bot appearance

## Verification Steps

After completing ALL the above steps:

1. **Restart your bot** - Stop and start your bot to apply changes
2. **Clear Telegram cache** - Close and reopen Telegram completely
3. **Test in private chat:**
   - Message your bot directly
   - Type `/` - you should see a clean command menu
   - Commands should appear as `/ability` not `/ability@botusername`
4. **Test in group chat:**
   - Add bot to a test group
   - Type `/` - clean commands should appear
   - Commands work both as `/ability` and `/ability@botusername`
5. **Wait if needed** - Changes can take up to 10-15 minutes to propagate

## Troubleshooting

If commands still show @username:

### Quick Fixes:
1. **Verify all BotFather steps were completed correctly**
2. **Check privacy is DISABLED (not enabled)**
3. **Restart your bot completely**
4. **Clear Telegram app cache/restart Telegram**
5. **Wait 15 minutes for changes to propagate**

### Advanced Fixes:
1. **Delete and recreate command list in BotFather**
2. **Remove bot from group and re-add it**
3. **Check if there are multiple bots in the group (causes @username display)**
4. **Verify bot token is correct in your code**

## Common Mistakes

❌ **Wrong:** Having privacy mode enabled  
✅ **Correct:** Privacy mode disabled

❌ **Wrong:** Not setting commands in BotFather  
✅ **Correct:** Commands properly configured in BotFather

❌ **Wrong:** Extra spaces in command format  
✅ **Correct:** Exact format: `command - description`

❌ **Wrong:** Not restarting bot after changes  
✅ **Correct:** Always restart bot after BotFather changes

## Technical Notes

- Bot code automatically handles both `/command` and `/command@botusername`
- BotFather configuration controls visual appearance
- Privacy disabled = bot can read all group messages
- Command menu only appears when properly configured
- Multiple bots in one group will force @username display 