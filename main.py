import discord
from discord.ext import commands
import os
import requests
import zipfile
import requests
from io import BytesIO
from datetime import datetime
import json
import re
from dotenv import load_dotenv
load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents)

BOT_TOKEN = os.getenv('BOT_TOKEN')

API_URL = "https://emoji.gg/api"
SETTINGS_FILE = "settings.json"

BACKUP_FOLDER = "emoji_backups"

if not os.path.exists(BACKUP_FOLDER):
    os.makedirs(BACKUP_FOLDER)


if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "r") as f:
        settings = json.load(f)
else:
    settings = {}

def save_settings():
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)

def can_members_add_emojis(server_id):
    return settings.get(str(server_id), {}).get("members_allow", False)

def set_members_allow(server_id, allow):
    if str(server_id) not in settings:
        settings[str(server_id)] = {}
    settings[str(server_id)]["members_allow"] = allow
    save_settings()

def get_emojis(include_animated=True):
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            emojis = response.json()
            if include_animated:
                emoji_urls = [emoji["image"] for emoji in emojis]
            else:
                emoji_urls = [emoji["image"] for emoji in emojis if not emoji["image"].endswith(".gif")]
            print(f"Fetched {len(emoji_urls)} emojis from Emoji.gg.")
            return emoji_urls
        else:
            print(f"Failed to fetch emojis. Status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching emojis: {e}")
        return []

@bot.hybrid_command(name="membersallow")
@commands.has_permissions(administrator=True)
async def members_allow(ctx, allow: bool):
    server_id = ctx.guild.id
    set_members_allow(server_id, allow)
    status = "allowed" if allow else "not allowed"
    await ctx.send(f"Emoji additions by regular members are now {status}.")

@bot.hybrid_command(name="addemoji")
async def add_emoji(ctx, emoji_url: str, name: str):
    server_id = ctx.guild.id
    member_allowed = can_members_add_emojis(server_id)

    if not member_allowed and not ctx.author.guild_permissions.manage_emojis:
        await ctx.send("You are not allowed to add emojis to this server.", ephemeral=True)
        return

    existing_emojis = [emoji.name for emoji in ctx.guild.emojis]
    if name in existing_emojis:
        await ctx.send(f"An emoji with the name '{name}' already exists in this server.")
        return

    try:
        response = requests.get(emoji_url, stream=True)
        if response.status_code == 200:
            emoji_bytes = response.content
            guild = ctx.guild
            new_emoji = await guild.create_custom_emoji(name=name, image=emoji_bytes)
            await ctx.send(f"Emoji {new_emoji} added successfully!")
        else:
            await ctx.send("Failed to download the emoji. Please check the URL.")
    except discord.Forbidden:
        await ctx.send("I don't have the `Manage Emojis and Stickers` permission.")
    except discord.HTTPException as e:
        await ctx.send(f"Failed to add the emoji: {e}")
    except Exception as e:
        print(f"Error adding emoji: {e}")
        await ctx.send("An error occurred while adding the emoji.")

@bot.hybrid_command(name="uploademojis")
async def upload_emojis(ctx, amount: int, include_animated: bool = True):
    server_id = ctx.guild.id
    emoji_urls = get_emojis(include_animated)
    member_allowed = can_members_add_emojis(server_id)

    if not member_allowed and not ctx.author.guild_permissions.manage_emojis:
        await ctx.send("You are not allowed to add emojis to this server.", ephemeral=True)
        return

    new_downloads = 0
    existing_emojis = [emoji.name for emoji in ctx.guild.emojis]

    for url in emoji_urls[:amount]:
        emoji_name = url.split("/")[-1].split(".")[0]
        if emoji_name in existing_emojis:
            continue  

        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                emoji_bytes = response.content
                await ctx.guild.create_custom_emoji(name=emoji_name, image=emoji_bytes)
                new_downloads += 1
            else:
                await ctx.send(f"Failed to download {emoji_name}.")
        except discord.Forbidden:
            await ctx.send("I don't have the `Manage Emojis and Stickers` permission.")
            break
        except Exception as e:
            print(f"Error downloading {url}: {e}")

    await ctx.send(f"Uploaded {new_downloads} new emojis to the server.")

@bot.hybrid_command(name="sendemojis")
async def send_emojis(ctx, amount: int, include_animated: bool = True):
    emoji_urls = get_emojis(include_animated)
    sent_emojis = 0

    for url in emoji_urls[:amount]:
        await ctx.send(url)
        sent_emojis += 1

    await ctx.send(f"Sent {sent_emojis} emojis.")

@bot.hybrid_command(name="r")
async def retrieve_emoji(ctx, identifier: str):
    found_emoji = None
    for emoji in ctx.guild.emojis:
        if identifier.isdigit() and emoji.id == int(identifier):
            found_emoji = emoji
            break
        elif emoji.name == identifier:
            found_emoji = emoji
            break

    if found_emoji:
        await ctx.send(str(found_emoji))
    else:
        await ctx.send(f"No emoji found with identifier '{identifier}'.", ephemeral=True)








BACKUP_FOLDER = "emoji_backups"

if not os.path.exists(BACKUP_FOLDER):
    os.makedirs(BACKUP_FOLDER)

@bot.hybrid_command(name="deleteallemojis")
@commands.has_permissions(manage_emojis=True)
async def delete_all_emojis(ctx):
    guild = ctx.guild
    emojis = guild.emojis

    if not emojis:
        await ctx.send("No custom emojis to delete in this server.")
        return

    server_backup_folder = os.path.join(BACKUP_FOLDER, str(guild.id))
    if not os.path.exists(server_backup_folder):
        os.makedirs(server_backup_folder)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = os.path.join(server_backup_folder, f"{guild.id}_backup_{timestamp}.zip")

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for emoji in emojis:
            try:
                response = requests.get(emoji.url, stream=True)
                if response.status_code == 200:
                    emoji_data = BytesIO(response.content)
                    emoji_filename = f"{emoji.name}_{emoji.id}.png" if not emoji.animated else f"{emoji.name}_{emoji.id}.gif"
                    zipf.writestr(emoji_filename, emoji_data.getvalue())
                else:
                    print(f"Failed to download emoji: {emoji.name} ({emoji.url})")
            except Exception as e:
                print(f"Error downloading emoji {emoji.name}: {e}")

    deleted_count = 0
    for emoji in emojis:
        try:
            await emoji.delete()
            deleted_count += 1
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete some emojis.")
        except Exception as e:
            print(f"Error deleting emoji {emoji.name}: {e}")

    await ctx.send(f"Deleted {deleted_count} emojis. A backup has been saved.")

@bot.hybrid_command(name="backup")
@commands.has_permissions(manage_emojis=True)
async def backup_emojis(ctx, name: str):
    guild = ctx.guild
    emojis = guild.emojis

    if not emojis:
        await ctx.send("No custom emojis to back up in this server.")
        return

    server_backup_folder = os.path.join(BACKUP_FOLDER, str(guild.id))
    if not os.path.exists(server_backup_folder):
        os.makedirs(server_backup_folder)

    zip_path = os.path.join(server_backup_folder, f"{name}_backup.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for emoji in emojis:
            try:
                response = requests.get(emoji.url, stream=True)
                if response.status_code == 200:
                    emoji_data = BytesIO(response.content)
                    emoji_filename = f"{emoji.name}_{emoji.id}.png" if not emoji.animated else f"{emoji.name}_{emoji.id}.gif"
                    zipf.writestr(emoji_filename, emoji_data.getvalue())
                else:
                    print(f"Failed to download emoji: {emoji.name} ({emoji.url})")
            except Exception as e:
                print(f"Error downloading emoji {emoji.name}: {e}")

    await ctx.send(f"All emojis have been backed up under the name '{name}'.")

@bot.hybrid_command(name="uploadbackup")
@commands.has_permissions(manage_emojis=True)
async def upload_backup(ctx, backup_name: str):
    guild = ctx.guild
    server_backup_folder = os.path.join(BACKUP_FOLDER, str(guild.id))

    if not os.path.exists(server_backup_folder):
        await ctx.send("No backup folder found for this server.")
        return

    backup_path = os.path.join(server_backup_folder, f"{backup_name}_backup.zip")
    if not os.path.exists(backup_path):
        await ctx.send(f"No backup found with the name '{backup_name}'.")
        return

    try:
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            for file_name in zipf.namelist():
                if file_name.endswith(".png") or file_name.endswith(".gif"):
                    emoji_data = zipf.read(file_name)
                    emoji_image = BytesIO(emoji_data)
                    emoji_name = file_name.split("_")[0]
                    
                    try:
                        await guild.create_custom_emoji(name=emoji_name, image=emoji_image.read())
                        print(f"Uploaded emoji {emoji_name}")
                    except discord.Forbidden:
                        await ctx.send("I don't have permission to upload some emojis.")
                    except Exception as e:
                        print(f"Error uploading emoji {emoji_name}: {e}")
            
        await ctx.send(f"Emojis from backup '{backup_name}' have been uploaded.")
    except Exception as e:
        await ctx.send(f"Failed to upload emojis from the backup: {e}")
        print(f"Error uploading from backup {backup_name}: {e}")

@bot.hybrid_command(name="backups")
@commands.has_permissions(manage_emojis=True)
async def list_backups(ctx):
    guild = ctx.guild
    server_backup_folder = os.path.join(BACKUP_FOLDER, str(guild.id))

    if not os.path.exists(server_backup_folder):
        await ctx.send("No backups found for this server.")
        return

    backup_files = [f for f in os.listdir(server_backup_folder) if f.endswith(".zip")]
    if not backup_files:
        await ctx.send("No backup files found for this server.")
        return

    backup_list = "\n".join([f.split("_backup")[0] for f in backup_files])
    await ctx.send(f"Available backups:\n{backup_list}")



@bot.hybrid_command(name="copy")
@commands.has_permissions(manage_emojis=True)
async def copy_emoji(ctx, emoji_name_or_id: str, guild_name_or_id: str):
    emoji = None
    try:
        emoji = discord.utils.get(ctx.guild.emojis, name=emoji_name_or_id) or discord.utils.get(ctx.guild.emojis, id=int(emoji_name_or_id))
    except ValueError:
        pass  

    if emoji:
        target_guild = None
        for guild in bot.guilds:
            if str(guild.id) == guild_name_or_id or guild.name.lower() == guild_name_or_id.lower():
                if target_guild:
                    await ctx.send("You have multiple guilds with that name! Please specify a guild ID.")
                    return
                target_guild = guild

        if not target_guild:
            await ctx.send(f"Could not find a guild matching '{guild_name_or_id}'")
            return

        if not target_guild.me.guild_permissions.manage_emojis:
            await ctx.send("I don't have permission to manage emojis in that guild.")
            return

        try:
            emoji_url = emoji.url
            emoji_bytes = await emoji.url.read()
            emoji_name = emoji.name
            await target_guild.create_custom_emoji(name=emoji_name, image=emoji_bytes)
            await ctx.send(f"Successfully copied the emoji '{emoji_name}' to {target_guild.name}.")

        except discord.Forbidden:
            await ctx.send(f"I do not have permission to upload emojis to {target_guild.name}.")
        except Exception as e:
            await ctx.send(f"An error occurred while copying the emoji: {e}")

    else:
        target_guild = None
        for guild in bot.guilds:
            if str(guild.id) == guild_name_or_id or guild.name.lower() == guild_name_or_id.lower():
                target_guild = guild
                break
        
        if not target_guild:
            await ctx.send(f"Could not find a guild matching '{guild_name_or_id}'", ephemeral=True)
            return
        
        if target_guild not in bot.guilds:
            await ctx.send(f"I am not in that server. Please invite me to the server using the following link:\n[Click here to invite me to {target_guild.name}](https://discord.com/oauth2/authorize?client_id=1307048148908114011&permissions=137439215648&integration_type=0&scope=bot)", ephemeral=True)








@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    try:
        await bot.tree.sync()
        print("Commands synchronized successfully.")
    except Exception as e:
        print(f"Error synchronizing commands: {e}")

bot.run(BOT_TOKEN)