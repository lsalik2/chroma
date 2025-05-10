import os
import discord
from discord import app_commands
from dotenv import load_dotenv

# Import command and view setup functions
from commands import setup_commands
from views import setup_views

# --------------------- Section: Setup and Intents ---------------------
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# --------------------- Section: Start-up Functions and Debugs ---------------------
@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    try:
        print("Syncing commands globally...")
        await tree.sync()
        print("Command sync completed successfully")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    activity = discord.Activity(
        type=discord.ActivityType.listening, 
        name="/chroma"
    )
    await client.change_presence(activity=activity)
    print('Bot is ready!')

# --------------------- Section: Token Loading ---------------------
def main():
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables")
        return
    
    setup_commands(tree)       # Register commands
    setup_views(tree, client)  # Register context menu views

    client.run(token)

    client.run(token)

if __name__ == "__main__":
    main()