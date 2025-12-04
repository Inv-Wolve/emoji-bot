import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from utils.logger import setup_logger
from utils.config_manager import ConfigManager
from utils.emoji_cache import EmojiCache
from utils.emoji_filter import EmojiFilter

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logger()

# Bot configuration
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents)

# Initialize utilities
bot.config = ConfigManager()
bot.emoji_cache = EmojiCache(ttl=bot.config.get("api.cache_ttl", 3600))
bot.emoji_filter = EmojiFilter(bot.config)

BOT_TOKEN = os.getenv('BOT_TOKEN')

@bot.event
async def on_ready():
    """Called when the bot is ready."""
    logger.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info(f'Connected to {len(bot.guilds)} guilds')
    
    try:
        # Sync slash commands
        await bot.tree.sync()
        logger.info("Slash commands synchronized successfully")
    except Exception as e:
        logger.error(f"Error synchronizing commands: {e}")

async def load_cogs():
    """Load all cogs."""
    cogs = [
        'cogs.emoji_management',
        'cogs.emoji_search',
        'cogs.backup_management',
        'cogs.admin'
    ]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f"Loaded cog: {cog}")
        except Exception as e:
            logger.error(f"Failed to load cog {cog}: {e}")

async def main():
    """Main entry point."""
    async with bot:
        await load_cogs()
        await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())