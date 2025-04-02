import os
import discord
from discord import app_commands

# Load Discord bot token
TOKEN = os.getenv('DISCORD_TOKEN')

# Format options
FORMAT_OPTIONS = [
    app_commands.Choice(name="Normal", value=0),
    app_commands.Choice(name="Bold", value=1),
    app_commands.Choice(name="Underline", value=4)
]