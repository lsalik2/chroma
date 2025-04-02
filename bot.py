import os
import discord
from discord import app_commands

# Load Discord bot token
with open(".env", "r") as f:
    token_line = f.read().strip()
    TOKEN = token_line.split('=')[1]

# Format options
FORMAT_OPTIONS = [
    app_commands.Choice(name="Normal", value=0),
    app_commands.Choice(name="Bold", value=1),
    app_commands.Choice(name="Underline", value=4)
]

# Text color options
TEXT_COLORS = [
    app_commands.Choice(name="Grey", value=30),
    app_commands.Choice(name="Red", value=31),
    app_commands.Choice(name="Green", value=32),
    app_commands.Choice(name="Yellow", value=33),
    app_commands.Choice(name="Blue", value=34),
    app_commands.Choice(name="Pink", value=35),
    app_commands.Choice(name="Cyan", value=36),
    app_commands.Choice(name="White", value=37)
]

# Background color options
BACKGROUND_COLORS = [
    app_commands.Choice(name="Dark Blue", value=40),
    app_commands.Choice(name="Orange", value=41),
    app_commands.Choice(name="Dark Grey", value=42),
    app_commands.Choice(name="Grey", value=43),
    app_commands.Choice(name="Light Grey", value=44),
    app_commands.Choice(name="Indigo", value=45),
    app_commands.Choice(name="Silver", value=46),
    app_commands.Choice(name="White", value=47)
]

# Discord client setup
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    """When bot is connected and ready, triggers event"""
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    
    # Force sync commands globally (this is important!)
    try:
        print("Syncing commands globally...")
        await tree.sync()
        print("Command sync completed successfully")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    
    print('Bot is ready!')

    # Custom status to let users know about the bot
    activity = discord.Activity(
        type=discord.ActivityType.listening, 
        name="/color commands"
    )
    await client.change_presence(activity=activity)

# Run the client
if __name__ == "__main__":
    client.run(TOKEN)