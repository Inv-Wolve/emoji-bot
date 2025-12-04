# 🎨 Emoji Bot - High-Quality Discord Emoji Manager

A powerful Discord bot for managing emojis with intelligent quality filtering, category-based search, and comprehensive backup features.

## ✨ Features

### 🔍 **Smart Emoji Discovery**
- **Search** - Find emojis by name or description
- **Browse by Category** - Anime, Pepe, Meme, Gaming, Brands, and more
- **Trending** - Discover the most popular emojis
- **Random** - Get random high-quality emojis

### 🎯 **Quality Filtering**
- **Favorites-Based Ranking** - Prioritize popular emojis
- **Adult Content Filter** - Automatic NSFW detection
- **File Quality Validation** - Reject corrupted or low-quality emojis
- **Smart Sorting** - Best emojis first

### 💾 **Backup & Restore**
- **Automatic Backups** - Never lose your emojis
- **Easy Restore** - One-command emoji restoration
- **Backup Management** - List and manage all backups

### ⚡ **Performance**
- **API Caching** - Fast responses with 1-hour cache
- **Bulk Upload** - Upload up to 100 emojis at once
- **Progress Tracking** - Real-time upload status

## 📋 Commands

### Emoji Management
- `/addemoji <url> <name>` - Add a single emoji from URL
- `/uploademojis <amount> [category] [animated] [min_favorites]` - Bulk upload quality emojis
- `/r <identifier>` - Quick emoji retrieval by name or ID

### Search & Discovery
- `/search <query> [category] [limit]` - Search for emojis
- `/trending [limit] [category]` - Show most popular emojis
- `/categories` - List all available categories
- `/random [count] [category]` - Get random emojis

### Backup Management
- `/backup <name>` - Create emoji backup
- `/backups` - List all backups
- `/uploadbackup <name>` - Restore from backup
- `/deleteallemojis` - Delete all emojis (auto-backup)

### Administration
- `/membersallow <true/false>` - Allow members to add emojis
- `/clearcache` - Clear API cache
- `/stats` - Show bot statistics

## 🚀 Setup

### Prerequisites
- Python 3.8 or higher
- Discord Bot Token

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd emojis-bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure the bot**

Create a `.env` file:
```env
BOT_TOKEN=your_discord_bot_token_here
```

4. **Configure settings** (optional)

Edit `config.json` to customize:
- API cache duration
- Quality filters (min favorites, file size)
- Adult content filtering
- Default limits

5. **Run the bot**
```bash
python main.py
```

## ⚙️ Configuration

### config.json
```json
{
  "api": {
    "base_url": "https://emoji.gg/api",
    "cache_ttl": 3600,
    "rate_limit_per_user": 10,
    "rate_limit_window": 60
  },
  "emoji_quality": {
    "min_favorites": 0,
    "min_file_size": 100,
    "max_file_size": 256000,
    "excluded_categories": [],
    "adult_filter_enabled": true
  },
  "defaults": {
    "upload_limit": 50,
    "search_limit": 10
  }
}
```

### Per-Server Settings
Settings are automatically saved per server in `settings.json`:
- Member emoji permissions
- Custom configurations

## 📊 Categories

Available emoji categories:
- 🎮 **Gaming** - Game-related emojis
- 😂 **Meme** - Popular meme emojis
- 🐸 **Pepe** - Pepe the Frog variations
- 🎨 **Anime** - Anime character emojis
- 🔵 **Blob** - Blob emoji variations
- 🏢 **Brands** - Brand logos and icons
- And many more!

Use `/categories` to see the full list with emoji counts.

## 🔒 Permissions

### Required Bot Permissions
- `Manage Emojis and Stickers` - To add/remove emojis
- `Send Messages` - To respond to commands
- `Embed Links` - To send rich embeds

### User Permissions
- **Administrators** - Full access to all commands
- **Manage Emojis** - Can use all emoji commands
- **Regular Members** - Can use commands if enabled by admin

## 📁 Project Structure

```
emojis-bot/
├── main.py                 # Bot entry point
├── config.json             # Configuration file
├── requirements.txt        # Python dependencies
├── adult_keywords.json     # NSFW filter keywords
├── settings.json           # Per-server settings
├── cogs/                   # Command modules
│   ├── emoji_management.py # Add/upload commands
│   ├── emoji_search.py     # Search/browse commands
│   ├── backup_management.py# Backup/restore commands
│   └── admin.py            # Admin commands
├── utils/                  # Utility modules
│   ├── config_manager.py   # Configuration handler
│   ├── emoji_cache.py      # API caching system
│   ├── emoji_filter.py     # Quality filtering
│   └── logger.py           # Logging system
├── emoji_backups/          # Backup storage
└── logs/                   # Log files
```

## 🎯 Usage Examples

### Upload 20 anime emojis with minimum 5 favorites
```
/uploademojis amount:20 category:anime min_favorites:5
```

### Search for thinking emojis
```
/search query:think limit:10
```

### Get top 10 trending emojis
```
/trending limit:10
```

### Create a backup before making changes
```
/backup name:before_cleanup
```

### Browse random meme emojis
```
/random count:10 category:meme
```

## 🐛 Troubleshooting

### Bot not responding
- Check bot token in `.env`
- Verify bot has required permissions
- Check logs in `logs/emoji_bot.log`

### Emojis not uploading
- Ensure bot has `Manage Emojis and Stickers` permission
- Check server emoji limit (50 static + 50 animated for non-boosted)
- Verify emoji URLs are accessible

### Cache issues
- Use `/clearcache` to force refresh
- Check `config.json` cache_ttl setting

## 📝 Logs

Logs are stored in `logs/emoji_bot.log` with automatic rotation:
- Max file size: 5MB
- Backup count: 3 files
- Format: `YYYY-MM-DD HH:MM:SS - LEVEL - MESSAGE`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## 📜 License

This project is licensed under the MIT License.

## 🙏 Credits

- Emoji data provided by [emoji.gg](https://emoji.gg)
- Built with [discord.py](https://github.com/Rapptz/discord.py)

## 📞 Support

For issues or questions:
1. Check the logs in `logs/emoji_bot.log`
2. Review the configuration in `config.json`
3. Open an issue on GitHub

---

**Made with ❤️ for Discord communities**
