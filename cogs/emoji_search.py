import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EmojiSearch(commands.Cog):
    """Commands for searching and browsing emojis."""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.emoji_cache = bot.emoji_cache
        self.emoji_filter = bot.emoji_filter
    
    @app_commands.command(name="search", description="Search for emojis by name or description")
    @app_commands.describe(
        query="Search query",
        category="Filter by category name",
        limit="Maximum number of results (default: 10)"
    )
    async def search(
        self,
        interaction: discord.Interaction,
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ):
        """Search for emojis."""
        await interaction.response.defer()
        
        try:
            # Get emojis from cache
            api_url = self.config.get("api.base_url")
            emojis = await self.emoji_cache.get_emojis(api_url)
            
            if not emojis:
                await interaction.followup.send("❌ Failed to fetch emojis from API.")
                return
            
            # Get category ID if provided
            category_id = None
            if category:
                categories = await self.emoji_cache.get_categories(api_url)
                for cat in categories:
                    if cat.get("name", "").lower() == category.lower():
                        category_id = cat.get("id")
                        break
            
            # Filter and search
            filtered_emojis = self.emoji_filter.filter_emojis(
                emojis,
                category=category_id,
                search_query=query,
                adult_filter=True
            )
            
            if not filtered_emojis:
                await interaction.followup.send(
                    f"❌ No emojis found matching `{query}`."
                )
                return
            
            # Sort by favorites
            sorted_emojis = self.emoji_filter.sort_emojis(filtered_emojis, sort_by="favorites")
            results = sorted_emojis[:limit]
            
            # Create embed
            embed = discord.Embed(
                title=f"🔍 Search Results for '{query}'",
                description=f"Found {len(filtered_emojis)} emojis (showing top {len(results)})",
                color=discord.Color.blue()
            )
            
            for emoji_data in results[:10]:  # Show max 10 in embed
                name = emoji_data.get("title", "Unknown")
                url = emoji_data.get("image", "")
                faves = emoji_data.get("faves", 0)
                animated = "🎬" if url.endswith(".gif") else "🖼️"
                
                embed.add_field(
                    name=f"{animated} {name}",
                    value=f"❤️ {faves} favorites\n[View]({url})",
                    inline=True
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in search command: {e}")
            await interaction.followup.send("❌ An error occurred while searching.")
    
    @app_commands.command(name="trending", description="Show the most popular emojis")
    @app_commands.describe(
        limit="Number of emojis to show (default: 10)",
        category="Filter by category name"
    )
    async def trending(
        self,
        interaction: discord.Interaction,
        limit: int = 10,
        category: Optional[str] = None
    ):
        """Show trending (most favorited) emojis."""
        await interaction.response.defer()
        
        try:
            # Get emojis from cache
            api_url = self.config.get("api.base_url")
            emojis = await self.emoji_cache.get_emojis(api_url)
            
            if not emojis:
                await interaction.followup.send("❌ Failed to fetch emojis from API.")
                return
            
            # Get category ID if provided
            category_id = None
            if category:
                categories = await self.emoji_cache.get_categories(api_url)
                for cat in categories:
                    if cat.get("name", "").lower() == category.lower():
                        category_id = cat.get("id")
                        break
            
            # Get trending emojis
            trending_emojis = self.emoji_filter.get_trending_emojis(
                emojis,
                limit=limit,
                category=category_id
            )
            
            if not trending_emojis:
                await interaction.followup.send("❌ No trending emojis found.")
                return
            
            # Create embed
            embed = discord.Embed(
                title="🔥 Trending Emojis",
                description=f"Top {len(trending_emojis)} most popular emojis",
                color=discord.Color.gold()
            )
            
            for i, emoji_data in enumerate(trending_emojis[:10], 1):
                name = emoji_data.get("title", "Unknown")
                url = emoji_data.get("image", "")
                faves = emoji_data.get("faves", 0)
                animated = "🎬" if url.endswith(".gif") else "🖼️"
                
                embed.add_field(
                    name=f"#{i} {animated} {name}",
                    value=f"❤️ {faves} favorites\n[View]({url})",
                    inline=True
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in trending command: {e}")
            await interaction.followup.send("❌ An error occurred.")
    
    @app_commands.command(name="categories", description="List all available emoji categories")
    async def categories(self, interaction: discord.Interaction):
        """List all available categories."""
        await interaction.response.defer()
        
        try:
            api_url = self.config.get("api.base_url")
            categories = await self.emoji_cache.get_categories(api_url)
            
            if not categories:
                await interaction.followup.send("❌ Failed to fetch categories.")
                return
            
            # Get emoji counts per category
            emojis = await self.emoji_cache.get_emojis(api_url)
            category_counts = {}
            for emoji in emojis:
                cat_id = emoji.get("category")
                category_counts[cat_id] = category_counts.get(cat_id, 0) + 1
            
            # Create embed
            embed = discord.Embed(
                title="📂 Emoji Categories",
                description=f"Total: {len(categories)} categories",
                color=discord.Color.purple()
            )
            
            # Sort categories by emoji count
            sorted_categories = sorted(
                categories,
                key=lambda c: category_counts.get(c.get("id"), 0),
                reverse=True
            )
            
            category_text = ""
            for cat in sorted_categories[:20]:  # Show top 20
                cat_name = cat.get("name", "Unknown")
                cat_id = cat.get("id")
                count = category_counts.get(cat_id, 0)
                category_text += f"**{cat_name}** - {count} emojis\n"
            
            embed.description = category_text
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in categories command: {e}")
            await interaction.followup.send("❌ An error occurred.")
    
    @app_commands.command(name="random", description="Get random high-quality emojis")
    @app_commands.describe(
        count="Number of random emojis (default: 5)",
        category="Filter by category name"
    )
    async def random(
        self,
        interaction: discord.Interaction,
        count: int = 5,
        category: Optional[str] = None
    ):
        """Get random emojis."""
        await interaction.response.defer()
        
        try:
            # Get emojis from cache
            api_url = self.config.get("api.base_url")
            emojis = await self.emoji_cache.get_emojis(api_url)
            
            if not emojis:
                await interaction.followup.send("❌ Failed to fetch emojis from API.")
                return
            
            # Get category ID if provided
            category_id = None
            if category:
                categories = await self.emoji_cache.get_categories(api_url)
                for cat in categories:
                    if cat.get("name", "").lower() == category.lower():
                        category_id = cat.get("id")
                        break
            
            # Filter emojis
            filtered_emojis = self.emoji_filter.filter_emojis(
                emojis,
                category=category_id,
                adult_filter=True
            )
            
            if not filtered_emojis:
                await interaction.followup.send("❌ No emojis found.")
                return
            
            # Get random emojis
            random_emojis = self.emoji_filter.sort_emojis(filtered_emojis, sort_by="random")
            results = random_emojis[:count]
            
            # Create embed
            embed = discord.Embed(
                title="🎲 Random Emojis",
                description=f"Here are {len(results)} random emojis",
                color=discord.Color.random()
            )
            
            for emoji_data in results[:10]:
                name = emoji_data.get("title", "Unknown")
                url = emoji_data.get("image", "")
                faves = emoji_data.get("faves", 0)
                animated = "🎬" if url.endswith(".gif") else "🖼️"
                
                embed.add_field(
                    name=f"{animated} {name}",
                    value=f"❤️ {faves} favorites\n[View]({url})",
                    inline=True
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in random command: {e}")
            await interaction.followup.send("❌ An error occurred.")

async def setup(bot):
    await bot.add_cog(EmojiSearch(bot))
