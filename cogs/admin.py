import discord
from discord.ext import commands
from discord import app_commands
from utils.logger import setup_logger

logger = setup_logger(__name__)

class Admin(commands.Cog):
    """Administrative commands for bot management."""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.emoji_cache = bot.emoji_cache
    
    @app_commands.command(name="membersallow", description="Allow/disallow regular members to add emojis")
    @app_commands.describe(allow="True to allow, False to disallow")
    @commands.has_permissions(administrator=True)
    async def members_allow(self, interaction: discord.Interaction, allow: bool):
        """Configure whether regular members can add emojis."""
        server_id = interaction.guild.id
        self.config.set_members_allow(server_id, allow)
        
        status = "allowed" if allow else "not allowed"
        await interaction.response.send_message(
            f"✅ Emoji additions by regular members are now **{status}**."
        )
        logger.info(f"Set members_allow to {allow} for guild {server_id}")
    
    @app_commands.command(name="clearcache", description="Clear the emoji cache and force refresh from API")
    @commands.has_permissions(administrator=True)
    async def clear_cache(self, interaction: discord.Interaction):
        """Clear the emoji cache."""
        self.emoji_cache.clear_cache()
        await interaction.response.send_message(
            "✅ Cache cleared. Next API request will fetch fresh data."
        )
        logger.info(f"Cache cleared by {interaction.user} in guild {interaction.guild.id}")
    
    @app_commands.command(name="stats", description="Show bot statistics")
    async def stats(self, interaction: discord.Interaction):
        """Show bot statistics."""
        cache_stats = self.emoji_cache.get_cache_stats()
        
        embed = discord.Embed(
            title="📊 Bot Statistics",
            color=discord.Color.blue()
        )
        
        # Cache stats
        emojis_cached = cache_stats["emojis"]["cached"]
        emoji_count = cache_stats["emojis"]["count"]
        emoji_age = cache_stats["emojis"]["age_seconds"]
        
        cache_status = "✅ Active" if emojis_cached else "❌ Empty"
        cache_info = f"{cache_status}\n"
        if emojis_cached:
            cache_info += f"Emojis: {emoji_count}\n"
            cache_info += f"Age: {int(emoji_age)}s"
        
        embed.add_field(
            name="🗄️ Cache Status",
            value=cache_info,
            inline=True
        )
        
        # Server stats
        embed.add_field(
            name="🏠 Servers",
            value=str(len(self.bot.guilds)),
            inline=True
        )
        
        # Bot stats
        embed.add_field(
            name="🤖 Bot Info",
            value=f"Latency: {round(self.bot.latency * 1000)}ms",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))
