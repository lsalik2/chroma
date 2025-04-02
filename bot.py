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