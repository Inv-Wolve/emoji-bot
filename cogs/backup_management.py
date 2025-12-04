import discord
from discord.ext import commands
from discord import app_commands
import os
import zipfile
import requests
from io import BytesIO
from datetime import datetime
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger(__name__)

BACKUP_FOLDER = "emoji_backups"

class BackupManagement(commands.Cog):
    """Commands for backing up and restoring emojis."""
    
    def __init__(self, bot):
        self.bot = bot
        self.backup_folder = Path(BACKUP_FOLDER)
        self.backup_folder.mkdir(exist_ok=True)
    
    @app_commands.command(name="backup", description="Backup all server emojis")
    @app_commands.describe(name="Name for this backup")
    @commands.has_permissions(manage_emojis=True)
    async def backup_emojis(self, interaction: discord.Interaction, name: str):
        """Create a backup of all server emojis."""
        await interaction.response.defer()
        
        guild = interaction.guild
        emojis = guild.emojis
        
        if not emojis:
            await interaction.followup.send("❌ No custom emojis to back up in this server.")
            return
        
        try:
            # Create server backup folder
            server_backup_folder = self.backup_folder / str(guild.id)
            server_backup_folder.mkdir(exist_ok=True)
            
            # Create zip file
            zip_path = server_backup_folder / f"{name}_backup.zip"
            
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for emoji in emojis:
                    try:
                        response = requests.get(emoji.url, stream=True, timeout=10)
                        if response.status_code == 200:
                            emoji_data = BytesIO(response.content)
                            ext = "gif" if emoji.animated else "png"
                            emoji_filename = f"{emoji.name}_{emoji.id}.{ext}"
                            zipf.writestr(emoji_filename, emoji_data.getvalue())
                    except Exception as e:
                        logger.error(f"Error backing up emoji {emoji.name}: {e}")
            
            # Get file size
            file_size = zip_path.stat().st_size / 1024  # KB
            
            embed = discord.Embed(
                title="✅ Backup Complete",
                description=f"Backed up **{len(emojis)}** emojis",
                color=discord.Color.green()
            )
            embed.add_field(name="Backup Name", value=f"`{name}`", inline=True)
            embed.add_field(name="File Size", value=f"{file_size:.2f} KB", inline=True)
            embed.add_field(name="Emojis", value=str(len(emojis)), inline=True)
            
            await interaction.followup.send(embed=embed)
            logger.info(f"Created backup '{name}' for guild {guild.id}")
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            await interaction.followup.send("❌ An error occurred while creating the backup.")
    
    @app_commands.command(name="backups", description="List all available backups")
    @commands.has_permissions(manage_emojis=True)
    async def list_backups(self, interaction: discord.Interaction):
        """List all backups for this server."""
        guild = interaction.guild
        server_backup_folder = self.backup_folder / str(guild.id)
        
        if not server_backup_folder.exists():
            await interaction.response.send_message(
                "❌ No backups found for this server.",
                ephemeral=True
            )
            return
        
        backup_files = list(server_backup_folder.glob("*.zip"))
        
        if not backup_files:
            await interaction.response.send_message(
                "❌ No backup files found for this server.",
                ephemeral=True
            )
            return
        
        # Create embed
        embed = discord.Embed(
            title="💾 Server Backups",
            description=f"Found {len(backup_files)} backup(s)",
            color=discord.Color.blue()
        )
        
        for backup_file in backup_files[:10]:  # Show max 10
            backup_name = backup_file.stem.replace("_backup", "")
            file_size = backup_file.stat().st_size / 1024  # KB
            modified_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
            
            embed.add_field(
                name=f"📦 {backup_name}",
                value=f"Size: {file_size:.2f} KB\nCreated: {modified_time.strftime('%Y-%m-%d %H:%M')}",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="uploadbackup", description="Restore emojis from a backup")
    @app_commands.describe(name="Name of the backup to restore")
    @commands.has_permissions(manage_emojis=True)
    async def upload_backup(self, interaction: discord.Interaction, name: str):
        """Restore emojis from a backup."""
        await interaction.response.defer()
        
        guild = interaction.guild
        server_backup_folder = self.backup_folder / str(guild.id)
        backup_path = server_backup_folder / f"{name}_backup.zip"
        
        if not backup_path.exists():
            await interaction.followup.send(
                f"❌ No backup found with the name `{name}`."
            )
            return
        
        try:
            uploaded = 0
            failed = 0
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                file_list = [f for f in zipf.namelist() if f.endswith(('.png', '.gif'))]
                
                embed = discord.Embed(
                    title="📥 Restoring Backup",
                    description=f"Restoring {len(file_list)} emojis...",
                    color=discord.Color.blue()
                )
                status_msg = await interaction.followup.send(embed=embed)
                
                for file_name in file_list:
                    emoji_data = zipf.read(file_name)
                    emoji_name = file_name.split("_")[0]
                    
                    try:
                        await guild.create_custom_emoji(name=emoji_name, image=emoji_data)
                        uploaded += 1
                        
                        # Update progress every 5 emojis
                        if uploaded % 5 == 0:
                            embed.description = f"Progress: {uploaded}/{len(file_list)} restored"
                            await status_msg.edit(embed=embed)
                            
                    except discord.Forbidden:
                        await interaction.followup.send(
                            "❌ I don't have permission to upload emojis."
                        )
                        break
                    except Exception as e:
                        logger.error(f"Error uploading emoji {emoji_name}: {e}")
                        failed += 1
            
            # Final summary
            embed.title = "✅ Restore Complete"
            embed.description = (
                f"**Restored:** {uploaded} emojis\n"
                f"**Failed:** {failed}"
            )
            embed.color = discord.Color.green()
            await status_msg.edit(embed=embed)
            
            logger.info(f"Restored {uploaded} emojis from backup '{name}' to guild {guild.id}")
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            await interaction.followup.send("❌ An error occurred while restoring the backup.")
    
    @app_commands.command(name="deleteallemojis", description="Delete all server emojis (creates backup)")
    @commands.has_permissions(manage_emojis=True)
    async def delete_all_emojis(self, interaction: discord.Interaction):
        """Delete all emojis from the server (with automatic backup)."""
        guild = interaction.guild
        emojis = guild.emojis
        
        if not emojis:
            await interaction.response.send_message(
                "❌ No custom emojis to delete in this server.",
                ephemeral=True
            )
            return
        
        # Create confirmation view
        view = ConfirmView()
        embed = discord.Embed(
            title="⚠️ Delete All Emojis",
            description=f"This will delete **{len(emojis)}** emojis from this server.\nA backup will be created automatically.",
            color=discord.Color.red()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await view.wait()
        
        if not view.value:
            await interaction.edit_original_response(
                content="❌ Deletion cancelled.",
                embed=None,
                view=None
            )
            return
        
        await interaction.edit_original_response(
            content="Creating backup and deleting emojis...",
            embed=None,
            view=None
        )
        
        try:
            # Create automatic backup
            server_backup_folder = self.backup_folder / str(guild.id)
            server_backup_folder.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_path = server_backup_folder / f"{guild.id}_backup_{timestamp}.zip"
            
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for emoji in emojis:
                    try:
                        response = requests.get(emoji.url, stream=True, timeout=10)
                        if response.status_code == 200:
                            emoji_data = BytesIO(response.content)
                            ext = "gif" if emoji.animated else "png"
                            emoji_filename = f"{emoji.name}_{emoji.id}.{ext}"
                            zipf.writestr(emoji_filename, emoji_data.getvalue())
                    except Exception as e:
                        logger.error(f"Error backing up emoji {emoji.name}: {e}")
            
            # Delete emojis
            deleted_count = 0
            for emoji in emojis:
                try:
                    await emoji.delete()
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting emoji {emoji.name}: {e}")
            
            await interaction.edit_original_response(
                content=f"✅ Deleted {deleted_count} emojis. Backup saved as `{timestamp}`."
            )
            logger.info(f"Deleted {deleted_count} emojis from guild {guild.id}")
            
        except Exception as e:
            logger.error(f"Error deleting emojis: {e}")
            await interaction.edit_original_response(
                content="❌ An error occurred while deleting emojis."
            )

class ConfirmView(discord.ui.View):
    """Confirmation view for destructive actions."""
    
    def __init__(self):
        super().__init__(timeout=30)
        self.value = None
    
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()

async def setup(bot):
    await bot.add_cog(BackupManagement(bot))
