import discord
from discord.ext import commands
from discord import app_commands
import requests
from typing import Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EmojiManagement(commands.Cog):
    """Commands for adding and managing emojis."""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.emoji_cache = bot.emoji_cache
        self.emoji_filter = bot.emoji_filter
    
    def _can_manage_emojis(self, ctx: commands.Context) -> bool:
        """Check if user can manage emojis."""
        if ctx.author.guild_permissions.manage_emojis:
            return True
        return self.config.can_members_add_emojis(ctx.guild.id)
    
    @app_commands.command(name="addemoji", description="Add a custom emoji to the server")
    @app_commands.describe(
        emoji_url="URL of the emoji image",
        name="Name for the emoji"
    )
    async def add_emoji(self, interaction: discord.Interaction, emoji_url: str, name: str):
        """Add a single emoji from a URL."""
        if not self._can_manage_emojis_interaction(interaction):
            await interaction.response.send_message(
                "❌ You don't have permission to add emojis to this server.",
                ephemeral=True
            )
            return
        
        # Check if emoji with this name already exists
        existing_emojis = [emoji.name for emoji in interaction.guild.emojis]
        if name in existing_emojis:
            await interaction.response.send_message(
                f"❌ An emoji with the name `{name}` already exists in this server.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            # Download emoji
            response = requests.get(emoji_url, stream=True, timeout=10)
            if response.status_code != 200:
                await interaction.followup.send(
                    f"❌ Failed to download emoji. Status code: {response.status_code}"
                )
                return
            
            emoji_bytes = response.content
            
            # Validate file size
            if len(emoji_bytes) > 256000:  # 256KB limit
                await interaction.followup.send(
                    "❌ Emoji file is too large (max 256KB)."
                )
                return
            
            # Create emoji
            new_emoji = await interaction.guild.create_custom_emoji(
                name=name,
                image=emoji_bytes
            )
            
            await interaction.followup.send(
                f"✅ Successfully added emoji {new_emoji} (`{name}`)"
            )
            logger.info(f"Added emoji {name} to guild {interaction.guild.id}")
            
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I don't have the `Manage Emojis and Stickers` permission."
            )
        except discord.HTTPException as e:
            await interaction.followup.send(
                f"❌ Failed to add emoji: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error adding emoji: {e}")
            await interaction.followup.send(
                "❌ An error occurred while adding the emoji."
            )
    
    @app_commands.command(name="uploademojis", description="Upload multiple emojis from emoji.gg")
    @app_commands.describe(
        amount="Number of emojis to upload",
        category="Filter by category name (e.g., 'anime', 'pepe', 'meme')",
        include_animated="Include animated GIF emojis",
        min_favorites="Minimum number of favorites (quality filter)"
    )
    async def upload_emojis(
        self,
        interaction: discord.Interaction,
        amount: int,
        category: Optional[str] = None,
        include_animated: bool = True,
        min_favorites: Optional[int] = None
    ):
        """Upload multiple high-quality emojis from emoji.gg."""
        if not self._can_manage_emojis_interaction(interaction):
            await interaction.response.send_message(
                "❌ You don't have permission to add emojis to this server.",
                ephemeral=True
            )
            return
        
        if amount < 1 or amount > 100:
            await interaction.response.send_message(
                "❌ Amount must be between 1 and 100.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            # Get emojis from cache
            api_url = self.config.get("api.base_url")
            emojis = await self.emoji_cache.get_emojis(api_url)
            
            if not emojis:
                await interaction.followup.send("❌ Failed to fetch emojis from API.")
                return
            
            # Get category ID if category name provided
            category_id = None
            if category:
                categories = await self.emoji_cache.get_categories(api_url)
                for cat in categories:
                    if cat.get("name", "").lower() == category.lower():
                        category_id = cat.get("id")
                        break
                
                if category_id is None:
                    await interaction.followup.send(
                        f"❌ Category `{category}` not found. Use `/categories` to see available categories."
                    )
                    return
            
            # Filter emojis
            filtered_emojis = self.emoji_filter.filter_emojis(
                emojis,
                category=category_id,
                include_animated=include_animated,
                adult_filter=True,
                min_favorites=min_favorites
            )
            
            if not filtered_emojis:
                await interaction.followup.send("❌ No emojis found matching your criteria.")
                return
            
            # Sort by favorites (best quality first)
            sorted_emojis = self.emoji_filter.sort_emojis(filtered_emojis, sort_by="favorites")
            
            # Get existing emoji names
            existing_emojis = [emoji.name for emoji in interaction.guild.emojis]
            
            # Upload emojis
            uploaded = 0
            skipped = 0
            failed = 0
            
            embed = discord.Embed(
                title="📤 Uploading Emojis",
                description=f"Uploading up to {amount} emojis...",
                color=discord.Color.blue()
            )
            status_msg = await interaction.followup.send(embed=embed)
            
            for emoji_data in sorted_emojis:
                if uploaded >= amount:
                    break
                
                emoji_name = emoji_data.get("title", "").replace(" ", "_")
                emoji_url = emoji_data.get("image")
                
                # Skip if already exists
                if emoji_name in existing_emojis:
                    skipped += 1
                    continue
                
                try:
                    # Download emoji
                    response = requests.get(emoji_url, stream=True, timeout=10)
                    if response.status_code != 200:
                        failed += 1
                        continue
                    
                    emoji_bytes = response.content
                    
                    # Create emoji
                    await interaction.guild.create_custom_emoji(
                        name=emoji_name,
                        image=emoji_bytes
                    )
                    uploaded += 1
                    existing_emojis.append(emoji_name)
                    
                    # Update progress every 5 emojis
                    if uploaded % 5 == 0:
                        embed.description = f"Progress: {uploaded}/{amount} uploaded, {skipped} skipped, {failed} failed"
                        await status_msg.edit(embed=embed)
                    
                except discord.Forbidden:
                    await interaction.followup.send(
                        "❌ I don't have the `Manage Emojis and Stickers` permission."
                    )
                    break
                except discord.HTTPException:
                    failed += 1
                except Exception as e:
                    logger.error(f"Error uploading emoji {emoji_name}: {e}")
                    failed += 1
            
            # Final summary
            embed.title = "✅ Upload Complete"
            embed.description = (
                f"**Uploaded:** {uploaded} emojis\n"
                f"**Skipped:** {skipped} (already exist)\n"
                f"**Failed:** {failed}"
            )
            embed.color = discord.Color.green()
            await status_msg.edit(embed=embed)
            
            logger.info(f"Uploaded {uploaded} emojis to guild {interaction.guild.id}")
            
        except Exception as e:
            logger.error(f"Error in upload_emojis: {e}")
            await interaction.followup.send(
                "❌ An error occurred while uploading emojis."
            )
    
    @app_commands.command(name="r", description="Retrieve an emoji by name or ID")
    @app_commands.describe(identifier="Emoji name or ID")
    async def retrieve_emoji(self, interaction: discord.Interaction, identifier: str):
        """Quickly retrieve and display an emoji."""
        found_emoji = None
        
        for emoji in interaction.guild.emojis:
            if identifier.isdigit() and emoji.id == int(identifier):
                found_emoji = emoji
                break
            elif emoji.name.lower() == identifier.lower():
                found_emoji = emoji
                break
        
        if found_emoji:
            await interaction.response.send_message(str(found_emoji))
        else:
            await interaction.response.send_message(
                f"❌ No emoji found with identifier `{identifier}`.",
                ephemeral=True
            )
    
    def _can_manage_emojis_interaction(self, interaction: discord.Interaction) -> bool:
        """Check if user can manage emojis (for interactions)."""
        if interaction.user.guild_permissions.manage_emojis:
            return True
        return self.config.can_members_add_emojis(interaction.guild.id)

async def setup(bot):
    await bot.add_cog(EmojiManagement(bot))
