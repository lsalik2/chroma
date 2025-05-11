import os
import discord
from discord import app_commands
from dotenv import load_dotenv

# Import command and view setup functions
from commands import setup_commands
from views import setup_views
from utils import start_tournament_scheduler

# --------------------- Section: Setup and Intents ---------------------
intents = discord.Intents.default() # TODO gotta change the administrator requirement when inviting bot, need to look at what permissions exactly it will need
intents.members = True  # Need members intent for tournament functionality
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
    
    # Start the tournament scheduler
    print("Starting tournament scheduler...")
    client.tournament_scheduler = await start_tournament_scheduler(client)
    print("Tournament scheduler started")
    
    activity = discord.Activity(
        type=discord.ActivityType.listening, 
        name="/chroma | /tournament"
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
    
    # Create data directories if they don't exist
    os.makedirs('data/tournaments', exist_ok=True)
    
    setup_commands(tree)       # Register commands
    setup_views(tree, client)  # Register context menu views

    client.run(token)

if __name__ == "__main__":
    main()