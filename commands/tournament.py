from datetime import datetime, timedelta

import discord
from discord import Interaction, ButtonStyle, Button, SelectOption
from discord.ui import Modal, TextInput, View, Select

from models.tournament import TournamentFormat, Tournament
from utils.tournament_db import TournamentDatabase

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
            # TODO now that I think about it, this is probably a terrible idea
            #      eventually this probably should be changed to default to anyone with admin permissions
            #      for now I'll leave it as is since I don't think anyone is gonna have a role named admin that's not an admin
            #      and no one is gonna go source-code diving to find this flaw (hopefully lol)
            if not admin_role:
                for role in guild.roles:
                    if "admin" in role.name.lower():
                        admin_role = role
                        admin_overwrites[admin_role] = discord.PermissionOverwrite(
                            read_messages=True,
                            send_messages=True
                        )
                        break
            
            # Add creator to admin channel permissions
            admin_overwrites[interaction.user] = discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True
            )
            
            # Also add permissions for users with administrator permissions
            for member in guild.members:
                if member.guild_permissions.administrator:
                    admin_overwrites[member] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True
                    )
            
            admin_channel = await guild.create_text_channel(
                name=f"⚙️admin-{tournament.name.lower().replace(' ', '-')}",
                category=category,
                overwrites=admin_overwrites
            )
            
            tournament.admin_channel_id = admin_channel.id
            
            # Save the tournament to database
            TournamentDatabase.save_tournament(tournament)
            
            # Send welcome messages
            if tournament.announcement_channel_id:
                channel = guild.get_channel(tournament.announcement_channel_id)
                prize_text = ""
                if tournament.prize_info:
                    prize_text = f"**Prizes:**\n{tournament.prize_info}"
                
                await channel.send(
                    f"# 🏆 Welcome to {tournament.name}! 🏆\n\n"
                    f"**Team Size:** {tournament.team_size}v{tournament.team_size}\n"
                    f"**Format:** {tournament.format.value.capitalize()}\n"
                    f"**Registration Deadline:** <t:{int(tournament.registration_deadline.timestamp())}:F>\n"
                    f"**Max Teams:** {tournament.max_teams if tournament.max_teams else 'No limit'}\n\n"
                    f"{prize_text}"
                )
            
            if tournament.rules_channel_id:
                channel = guild.get_channel(tournament.rules_channel_id)
                prize_section = ""
                if tournament.prize_info:
                    prize_section = f"## Prizes\n{tournament.prize_info}"
                
                team_formation = "Players choose their own teams"
                if tournament.format != TournamentFormat.CHOOSE:
                    team_formation = "Teams will be automatically formed by the bot"
                
                await channel.send( # TODO add a dynamic rules list or something?
                    f"# 📜 Tournament Rules and Format 📜\n\n"
                    f"## Format\n"
                    f"- **Tournament Name:** {tournament.name}\n"
                    f"- **Team Size:** {tournament.team_size}v{tournament.team_size}\n"
                    f"- **Teams:** {tournament.format.value.capitalize()} format\n"
                    f"- **Registration Deadline:** <t:{int(tournament.registration_deadline.timestamp())}:F>\n\n"
                    f"## Team Formation\n"
                    f"- {team_formation}\n"
                    f"- All players must register with their Epic username and MMR\n"
                    f"- Teams must be approved by admins before participating\n\n"
                    f"## Match Rules\n"
                    f"- Standard Rocket League rules apply\n"
                    f"- Matches are best-of-3\n"
                    f"- No toxic behavior or cheating\n"
                    f"- Admins have final say in all disputes\n\n"
                    f"{prize_section}"
                )


        except Exception as e:
            print(f"Error creating tournament: {e}")
            await interaction.followup.send(f"Error creating tournament: {e}", ephemeral=True)
