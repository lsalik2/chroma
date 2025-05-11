from datetime import datetime, timedelta

import discord
from discord import Interaction, ButtonStyle, Button
from discord.ui import Modal, TextInput, View

from models.tournament import TournamentFormat

# Constants
CHANNEL_EMOJI_MAP = {
    "announcements": "📢",
    "rules": "📃",
    "bracket": "🏆",
    "sign_up": "✒️",
    "lobby": "🗣️",
    "questions": "❓",
}

PASSWORDS = [
    "Vex", "Drift", "Flux", "Nova", "Blitz", "Zyn", "Wisp", "Rune",
    "Axe", "Glint", "Crux", "Jynx", "Nyx", "Fang", "Hex", "Void",
    "Echo", "Pyre", "Grim", "Keen", "Raze", "Obel", "Shiv", "Zeph",
    "Talon", "Nox"
]


# ---------------- Tournament Creation Views and Modals ----------------

class TournamentCreateModal(Modal):
    def __init__(self):
        super().__init__(title="Create Tournament")
        
        self.name = TextInput(
            label="Tournament Name",
            placeholder="Enter tournament name",
            required=True,
            max_length=100
        )
        self.add_item(self.name)
        
        self.team_size = TextInput(
            label="Team Size",
            placeholder="Number of players per team (e.g. 2 for 2v2)",
            required=True,
            max_length=1
        )
        self.add_item(self.team_size)
        
        self.max_teams = TextInput(
            label="Max Teams (Optional)",
            placeholder="Leave empty for no limit",
            required=False,
            max_length=3
        )
        self.add_item(self.max_teams)
        
        self.registration_deadline = TextInput(
            label="Registration Deadline (days)",
            placeholder="Days until registration closes",
            required=False,
            max_length=2,
            default="7"
        )
        self.add_item(self.registration_deadline)
        
        self.prize_info = TextInput(
            label="Prizes (Optional)",
            placeholder="Describe tournament prizes",
            required=False,
            max_length=1000,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.prize_info)

    async def on_submit(self, interaction: Interaction):
        # Validate inputs
        try:
            team_size = int(self.team_size.value)
            if team_size <= 0 or team_size > 4:
                await interaction.response.send_message("Team size must be between 1 and 4.", ephemeral=True)
                return
            
            max_teams = None
            if self.max_teams.value:
                max_teams = int(self.max_teams.value)
                if max_teams <= 0:
                    await interaction.response.send_message("Max teams must be a positive number.", ephemeral=True)
                    return
            
            deadline_days = 7
            if self.registration_deadline.value:
                deadline_days = int(self.registration_deadline.value)
                if deadline_days <= 0:
                    await interaction.response.send_message("Registration deadline must be a positive number of days.", ephemeral=True)
                    return
            
            # Store the form data in a variable to pass to the next view
            tournament_data = {
                "name": self.name.value,
                "team_size": team_size,
                "max_teams": max_teams,
                "registration_deadline": datetime.now() + timedelta(days=deadline_days),
                "prize_info": self.prize_info.value if self.prize_info.value else None
            }
            
            # Move to format selection
            await interaction.response.send_message(
                "Select the tournament format:",
                view=TournamentFormatView(tournament_data),
                ephemeral=True
            )
        
        except ValueError:
            await interaction.response.send_message("Please enter valid numbers for team size, max teams, and registration deadline.", ephemeral=True)


class TournamentFormatView(View):
    def __init__(self, tournament_data):
        super().__init__()
        self.tournament_data = tournament_data
    
    @discord.ui.button(label="CHOOSE", style=ButtonStyle.primary, row=0)
    async def choose_button(self, interaction: Interaction, button: Button):
        self.tournament_data["format"] = TournamentFormat.CHOOSE
        await interaction.response.send_message(
            "Select which channels to create for this tournament:",
            view=TournamentChannelsView(self.tournament_data),
            ephemeral=True
        )
