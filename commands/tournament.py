from datetime import datetime, timedelta

import discord
from discord import Interaction, ButtonStyle, Button, SelectOption
from discord.ui import Modal, TextInput, View, Select

from models.tournament import TournamentFormat, Tournament

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
    
    @discord.ui.button(label="BALANCE", style=ButtonStyle.primary, row=0)
    async def balance_button(self, interaction: Interaction, button: Button):
        self.tournament_data["format"] = TournamentFormat.BALANCE
        await interaction.response.send_message(
            "Select which channels to create for this tournament:",
            view=TournamentChannelsView(self.tournament_data),
            ephemeral=True
        )
    
    @discord.ui.button(label="RANDOM", style=ButtonStyle.primary, row=0)
    async def random_button(self, interaction: Interaction, button: Button):
        self.tournament_data["format"] = TournamentFormat.RANDOM
        await interaction.response.send_message(
            "Select which channels to create for this tournament:",
            view=TournamentChannelsView(self.tournament_data),
            ephemeral=True
        )


class TournamentChannelsView(View):
    def __init__(self, tournament_data):
        super().__init__()
        self.tournament_data = tournament_data
        
        # Add checkboxes for each channel type
        self.channels_select = Select(
            placeholder="Select channels to create...",
            min_values=0,
            max_values=6,
            options=[
                SelectOption(
                    label=f"{emoji} {name.capitalize()}",
                    value=name,
                    description=f"{emoji} {name.capitalize()} channel"
                )
                for name, emoji in CHANNEL_EMOJI_MAP.items()
            ]
        )
        self.channels_select.callback = self.on_select
        self.add_item(self.channels_select)
    
    async def on_select(self, interaction: Interaction):
        # Store selected channels
        self.tournament_data["channels"] = self.channels_select.values
        
        # Confirm selection
        channels_text = "\n".join([f"{CHANNEL_EMOJI_MAP[channel]} {channel.capitalize()}" for channel in self.channels_select.values])
        
        await interaction.response.send_message(
            f"Selected channels:\n{channels_text}\n\nCreate tournament with these settings?",
            view=TournamentConfirmView(self.tournament_data),
            ephemeral=True
        )


class TournamentConfirmView(View):
    def __init__(self, tournament_data):
        super().__init__()
        self.tournament_data = tournament_data
    
    @discord.ui.button(label="Confirm", style=ButtonStyle.green, row=0)
    async def confirm_button(self, interaction: Interaction, button: Button):
        # Create the tournament
        await self.create_tournament(interaction)
    
    @discord.ui.button(label="Cancel", style=ButtonStyle.red, row=0)
    async def cancel_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_message("Tournament creation cancelled.", ephemeral=True)
    
    async def create_tournament(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        data = self.tournament_data
        
        # Create Tournament object
        tournament = Tournament(
            name=data["name"],
            format=data["format"],
            creator_id=interaction.user.id,
            team_size=data["team_size"],
            max_teams=data["max_teams"],
            registration_deadline=data["registration_deadline"],
            prize_info=data["prize_info"]
        )
        
        # Create Discord channels
        try:
            guild = interaction.guild
            
            # Create category
            category = await guild.create_category(name=f"🏆 {tournament.name}")
            tournament.category_id = category.id
            
            # Create selected channels
            for channel_name in data["channels"]:
                emoji = CHANNEL_EMOJI_MAP[channel_name]
                
                # Determine permissions based on channel type
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=True)
                }
                
                # Read-only channels
                if channel_name in ["announcements", "rules", "bracket"]:
                    overwrites[guild.default_role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=False
                    )
                
                # Create the channel
                channel = await guild.create_text_channel(
                    name=f"{emoji}{channel_name}",
                    category=category,
                    overwrites=overwrites
                )
                
                # Store channel ID
                if channel_name == "announcements":
                    tournament.announcement_channel_id = channel.id
                elif channel_name == "rules":
                    tournament.rules_channel_id = channel.id
                elif channel_name == "bracket":
                    tournament.bracket_channel_id = channel.id
                elif channel_name == "sign_up":
                    tournament.signup_channel_id = channel.id
                elif channel_name == "lobby":
                    tournament.lobby_channel_id = channel.id
                elif channel_name == "questions":
                    tournament.questions_channel_id = channel.id
            
            # Create admin channel (always created)
            admin_overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
            }
            
            # Try to find the tournament admin role
            from utils.config_storage import ConfigStorage
            admin_role_id = ConfigStorage.get_tournament_admin_role(guild.id)
            admin_role = None
            
            if admin_role_id:
                admin_role = guild.get_role(admin_role_id)
                if admin_role:
                    admin_overwrites[admin_role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True
                    )
            
            # If no tournament admin role is set, fall back to any role with "admin" in the name
            if not admin_role:
                for role in guild.roles:
                    if "admin" in role.name.lower():
                        admin_role = role
                        admin_overwrites[admin_role] = discord.PermissionOverwrite(
                            read_messages=True,
                            send_messages=True
                        )
                        break

        except Exception as e:
            print(f"Error creating tournament: {e}")
            await interaction.followup.send(f"Error creating tournament: {e}", ephemeral=True)
