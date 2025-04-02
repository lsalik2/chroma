import os
import discord
from discord import app_commands

# --------------------- Section: Token Loading ---------------------
with open(".env", "r") as f:
    token_line = f.read().strip()
    TOKEN = token_line.split('=')[1]

# --------------------- Section: Options Choices ---------------------
FORMAT_OPTIONS = [
    app_commands.Choice(name="Normal", value=0),
    app_commands.Choice(name="Bold", value=1),
    app_commands.Choice(name="Underline", value=4)
]

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

# --------------------- Section: Setup and Intents ---------------------
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# --------------------- Section: Start-up Functions and Debugs ---------------------
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
    
    # Custom status to let users know about the bot
    activity = discord.Activity(
        type=discord.ActivityType.listening, 
        name="/color commands"
    )
    await client.change_presence(activity=activity)

    print('Bot is ready!')

# --------------------- Section: /color Command ---------------------
@tree.command(name="color", description="Create a colorful ANSI code block")
@app_commands.describe(
    message="The message to colorize",
    format="Text formatting",
    background_color="The background color",
    text_color="The color of the text"
)
@app_commands.choices(
    format=FORMAT_OPTIONS,
    background_color=BACKGROUND_COLORS,
    text_color=TEXT_COLORS
)
async def color_command(
    interaction: discord.Interaction, 
    message: str, 
    format: app_commands.Choice[int],
    background_color: app_commands.Choice[int],
    text_color: app_commands.Choice[int]
):
    
    """Command to create a colorful ANSI-formatted code block"""
    # Create ANSI formatted text
    ansi_code = f"[{format.value};{text_color.value};{background_color.value}m"
    reset_code = "[0m"
    
    # Format the response with the ANSI code block
    response = f"Here's your colorized message:\n```ansi\n{ansi_code}{message}{reset_code}\n```"
    
    # Send the response as ephemeral (only visible to the command user)
    await interaction.response.send_message(response, ephemeral=True)

# --------------------- Section: Run the Client ---------------------
if __name__ == "__main__":
    client.run(TOKEN)