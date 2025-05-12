import discord
from discord import app_commands, Interaction, ButtonStyle, SelectOption
from discord.ui import View, Button, Select, Modal, TextInput
from datetime import datetime, timedelta
import asyncio
import random
from typing import List
from utils.permissions import is_tournament_admin

from models.tournament import Tournament, TournamentFormat, Team, Player, Match, TeamStatus, MatchStatus
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
            
            if tournament.bracket_channel_id:
                channel = guild.get_channel(tournament.bracket_channel_id)
                await channel.send(
                    f"# 🏆 Tournament Bracket 🏆\n\n"
                    f"The bracket will be displayed here once the tournament begins.\n\n"
                    f"## Registered Teams\n"
                    f"Teams will be listed here after registration and approval."
                )
            
            if tournament.signup_channel_id:
                channel = guild.get_channel(tournament.signup_channel_id)
                team_info = ""
                if tournament.format == TournamentFormat.CHOOSE:
                    team_info = "You will also need to create or join a team after registration."
                
                await channel.send(
                    f"# ✒️ Tournament Sign-up ✒️\n\n"
                    f"Use the `/signup` command in this channel to register for the tournament.\n\n"
                    f"You will need:\n"
                    f"- Your Epic username\n"
                    f"- Your current {tournament.team_size}v{tournament.team_size} MMR\n"
                    f"- Your peak {tournament.team_size}v{tournament.team_size} MMR\n\n"
                    f"{team_info}"
                )
            
            # Send admin welcome message
            await admin_channel.send(
                f"# ⚙️ Tournament Admin Controls ⚙️\n\n"
                f"Welcome to the admin channel for **{tournament.name}**!\n\n"
                f"Use the following commands to manage the tournament:\n"
                f"- `/tournament approve` - Approve a team\n"
                f"- `/tournament deny` - Deny a team\n"
                f"- `/tournament start` - Start the tournament\n"
                f"- `/tournament bracket` - Update the bracket display\n"
                f"- `/tournament reminder` - Schedule a reminder\n"
                f"- `/tournament edit` - Edit tournament details\n\n"
                f"Pending team approvals will appear in this channel."
            )
            
            # Notify the creator
            await interaction.followup.send(
                f"Tournament **{tournament.name}** has been created successfully!", 
                ephemeral=True
            )
            
        except Exception as e:
            print(f"Error creating tournament: {e}")
            await interaction.followup.send(f"Error creating tournament: {e}", ephemeral=True)


# ---------------- Player Signup Views and Modals ----------------

class PlayerSignupModal(Modal):
    def __init__(self, tournament: Tournament):
        super().__init__(title=f"Sign up for {tournament.name}")
        self.tournament = tournament
        
        self.epic_username = TextInput(
            label="Epic Username",
            placeholder="Your Rocket League Epic username",
            required=True,
            max_length=100
        )
        self.add_item(self.epic_username)
        
        self.current_mmr = TextInput(
            label=f"Current {tournament.team_size}v{tournament.team_size} MMR",
            placeholder="Your current MMR (estimate if needed)",
            required=True,
            max_length=5
        )
        self.add_item(self.current_mmr)
        
        self.peak_mmr = TextInput(
            label=f"Peak {tournament.team_size}v{tournament.team_size} MMR",
            placeholder="Your highest MMR (estimate if needed)",
            required=True,
            max_length=5
        )
        self.add_item(self.peak_mmr)
    
    async def on_submit(self, interaction: Interaction):
        try:
            # Validate inputs
            current_mmr = int(self.current_mmr.value)
            peak_mmr = int(self.peak_mmr.value)
            
            if current_mmr < 0 or peak_mmr < 0:
                await interaction.response.send_message("MMR values cannot be negative.", ephemeral=True)
                return
            
            if peak_mmr < current_mmr:
                await interaction.response.send_message("Peak MMR cannot be lower than current MMR.", ephemeral=True)
                return
            
            # Check if already registered
            if self.tournament.is_player_registered(interaction.user.id):
                await interaction.response.send_message("You are already registered for this tournament.", ephemeral=True)
                return
            
            # Create player
            player = Player(
                user_id=interaction.user.id,
                username=str(interaction.user),
                epic_username=self.epic_username.value,
                current_mmr=current_mmr,
                peak_mmr=peak_mmr
            )
            
            # If CHOOSE format, ask to create/join team
            if self.tournament.format == TournamentFormat.CHOOSE:
                await interaction.response.send_message(
                    "Would you like to create a new team or join an existing team?",
                    view=TeamChoiceView(self.tournament, player),
                    ephemeral=True
                )
            else:
                # For BALANCE and RANDOM formats, create a temporary solo team
                team = Team(
                    name=f"{interaction.user.display_name}'s Team",
                    captain_id=interaction.user.id
                )
                team.add_player(player)
                
                # Add to tournament
                team_id = self.tournament.add_team(team)
                
                # Save tournament
                TournamentDatabase.save_tournament(self.tournament)
                
                # Send admin approval message
                await self.send_admin_approval(interaction, team)
                
                await interaction.response.send_message(
                    f"Thanks for signing up! Your registration is pending admin approval.",
                    ephemeral=True
                )
        
        except ValueError:
            await interaction.response.send_message("Please enter valid numbers for MMR values.", ephemeral=True)
        except Exception as e:
            print(f"Error in signup: {e}")
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
    
    async def send_admin_approval(self, interaction: Interaction, team: Team):
        # Get admin channel
        admin_channel = interaction.guild.get_channel(self.tournament.admin_channel_id)
        if not admin_channel:
            return
        
        # Create team info message
        player_list = "\n".join([
            f"- **{p.username}** (Epic: {p.epic_username}, MMR: {p.current_mmr}/{p.peak_mmr})"
            for p in team.players
        ])
        
        embed = discord.Embed(
            title=f"Team Registration: {team.name}",
            description=f"A new team has registered for {self.tournament.name}.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Players", value=player_list, inline=False)
        embed.add_field(name="Team Captain", value=f"<@{team.captain_id}>", inline=True)
        embed.add_field(name="Avg MMR", value=f"{team.calculate_average_mmr():.1f}", inline=True)
        
        # Send approval message with buttons
        await admin_channel.send(
            embed=embed,
            view=TeamApprovalView(self.tournament, team.id)
        )


class TeamChoiceView(View):
    def __init__(self, tournament: Tournament, player: Player):
        super().__init__()
        self.tournament = tournament
        self.player = player  # Store the player object directly
    
    @discord.ui.button(label="Create Team", style=ButtonStyle.primary, row=0)
    async def create_team_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_modal(CreateTeamModal(self.tournament, self.player))
    
    @discord.ui.button(label="Join Team", style=ButtonStyle.primary, row=0)
    async def join_team_button(self, interaction: Interaction, button: Button):
        # Get available teams
        available_teams = [
            team for team in self.tournament.teams.values()
            if team.status != TeamStatus.DENIED and len(team.players) < self.tournament.team_size
        ]
        
        if not available_teams:
            await interaction.response.send_message("No teams available to join. Please create a new team.", ephemeral=True)
            return
        
        # Show team selection
        await interaction.response.send_message(
            "Select a team to join:",
            view=TeamSelectView(self.tournament, self.player, available_teams),
            ephemeral=True
        )


class CreateTeamModal(Modal):
    def __init__(self, tournament: Tournament, player: Player):
        super().__init__(title="Create a Team")
        self.tournament = tournament
        self.player = player  # Store the player object directly
        
        self.team_name = TextInput(
            label="Team Name",
            placeholder="Enter your team name",
            required=True,
            max_length=100
        )
        self.add_item(self.team_name)
        
        self.team_password = TextInput(
            label="Team Password (Optional)",
            placeholder="Password for others to join your team",
            required=False,
            max_length=50
        )
        self.add_item(self.team_password)
    
    async def on_submit(self, interaction: Interaction):
        # Check for existing teams with the same name
        existing_teams = []
        for team in self.tournament.teams.values():
            if team.name.lower() == self.team_name.value.lower():
                existing_teams.append(team)
        
        # Check if any existing team with the same name is not denied
        active_team_exists = False
        for team in existing_teams:
            if team.status != TeamStatus.DENIED:
                active_team_exists = True
                break
        
        if active_team_exists:
            await interaction.response.send_message("A team with this name already exists. Please choose a different name.", ephemeral=True)
            return
        
        # If we found only denied teams with this name, remove them to avoid conflicts
        for team in existing_teams:
            if team.status == TeamStatus.DENIED:
                del self.tournament.teams[team.id]
        
        # Create team
        team = Team(
            name=self.team_name.value,
            captain_id=interaction.user.id,
            password=self.team_password.value if self.team_password.value else None
        )
        team.add_player(self.player)  # Use the stored player object
        
        # Add to tournament
        team_id = self.tournament.add_team(team)
        
        # Save tournament
        TournamentDatabase.save_tournament(self.tournament)
        
        # Send admin approval message
        admin_channel = interaction.guild.get_channel(self.tournament.admin_channel_id)
        if admin_channel:
            embed = discord.Embed(
                title=f"Team Registration: {team.name}",
                description=f"A new team has registered for {self.tournament.name}.",
                color=discord.Color.blue()
            )
            
            player_list = f"- **{self.player.username}** (Epic: {self.player.epic_username}, MMR: {self.player.current_mmr}/{self.player.peak_mmr})"
            embed.add_field(name="Players", value=player_list, inline=False)
            embed.add_field(name="Team Captain", value=f"<@{team.captain_id}>", inline=True)
            embed.add_field(name="Avg MMR", value=f"{team.calculate_average_mmr():.1f}", inline=True)
            
            await admin_channel.send(
                embed=embed,
                view=TeamApprovalView(self.tournament, team.id)
            )
        
        await interaction.response.send_message(
            f"Team **{team.name}** has been created! Your registration is pending admin approval.\n\n"
            f"Team Password: {team.password if team.password else 'None (anyone can join)'}\n\n"
            f"Share this password with your teammates so they can join your team.",
            ephemeral=True
        )


class TeamSelectView(View):
    def __init__(self, tournament: Tournament, player: Player, available_teams: List[Team]):
        super().__init__()
        self.tournament = tournament
        self.player = player  # Store the player object directly
        self.available_teams = available_teams
        
        # Add team selection dropdown
        options = []
        for team in available_teams:
            captain = f"<@{team.captain_id}>"
            players = f"{len(team.players)}/{tournament.team_size}"
            
            options.append(
                SelectOption(
                    label=team.name[:100],  # Max 100 chars
                    value=team.id,
                    description=f"Captain: {captain[:100]}, Players: {players}"
                )
            )
        
        self.teams_select = Select(
            placeholder="Select a team to join...",
            min_values=1,
            max_values=1,
            options=options[:25]  # Max 25 options
        )
        self.teams_select.callback = self.on_team_select
        self.add_item(self.teams_select)
    
    async def on_team_select(self, interaction: Interaction):
        team_id = self.teams_select.values[0]
        team = self.tournament.get_team(team_id)
        
        if not team:
            await interaction.response.send_message("Team not found.", ephemeral=True)
            return
        
        # Check if team requires a password
        if team.password:
            await interaction.response.send_modal(TeamPasswordModal(self.tournament, team, self.player))
        else:
            # Join team without password
            await self.join_team(interaction, team)
    
    async def join_team(self, interaction: Interaction, team: Team):
        # Check if team is full
        if len(team.players) >= self.tournament.team_size:
            await interaction.response.send_message("This team is already full.", ephemeral=True)
            return
        
        # Add player to team
        if not team.add_player(self.player):  # Use the stored player object
            await interaction.response.send_message("You are already on this team.", ephemeral=True)
            return
        
        # Save tournament
        TournamentDatabase.save_tournament(self.tournament)
        
        # Notify team captain
        try:
            captain = await interaction.client.fetch_user(team.captain_id)
            await captain.send(f"**{self.player.username}** has joined your team **{team.name}** for the tournament **{self.tournament.name}**!")
        except:
            pass  # Ignore if DM fails
        
        # Send admin approval message update
        admin_channel = interaction.guild.get_channel(self.tournament.admin_channel_id)
        if admin_channel:
            player_list = "\n".join([
                f"- **{p.username}** (Epic: {p.epic_username}, MMR: {p.current_mmr}/{p.peak_mmr})"
                for p in team.players
            ])
            
            embed = discord.Embed(
                title=f"Team Update: {team.name}",
                description=f"A new player has joined team {team.name}.",
                color=discord.Color.blue()
            )
            embed.add_field(name="Players", value=player_list, inline=False)
            embed.add_field(name="Team Captain", value=f"<@{team.captain_id}>", inline=True)
            embed.add_field(name="Avg MMR", value=f"{team.calculate_average_mmr():.1f}", inline=True)
            
            await admin_channel.send(embed=embed)
        
        await interaction.response.send_message(
            f"You have joined team **{team.name}**! Your registration is pending admin approval.",
            ephemeral=True
        )


class TeamPasswordModal(Modal):
    def __init__(self, tournament: Tournament, team: Team, player: Player):
        super().__init__(title=f"Join {team.name}")
        self.tournament = tournament
        self.team = team
        self.player = player  # Store the player object directly
        
        self.password = TextInput(
            label="Team Password",
            placeholder="Enter the team password",
            required=True
        )
        self.add_item(self.password)
    
    async def on_submit(self, interaction: Interaction):
        # Check password
        if self.password.value != self.team.password:
            await interaction.response.send_message("Incorrect password.", ephemeral=True)
            return
        
        # Check if team is full
        if len(self.team.players) >= self.tournament.team_size:
            await interaction.response.send_message("This team is already full.", ephemeral=True)
            return
        
        # Add player to team
        if not self.team.add_player(self.player):  # Use the stored player object
            await interaction.response.send_message("You are already on this team.", ephemeral=True)
            return
        
        # Save tournament
        TournamentDatabase.save_tournament(self.tournament)
        
        # Notify team captain
        try:
            captain = await interaction.client.fetch_user(self.team.captain_id)
            await captain.send(f"**{self.player.username}** has joined your team **{self.team.name}** for the tournament **{self.tournament.name}**!")
        except:
            pass  # Ignore if DM fails
        
        # Send admin approval message update
        admin_channel = interaction.guild.get_channel(self.tournament.admin_channel_id)
        if admin_channel:
            player_list = "\n".join([
                f"- **{p.username}** (Epic: {p.epic_username}, MMR: {p.current_mmr}/{p.peak_mmr})"
                for p in self.team.players
            ])
            
            embed = discord.Embed(
                title=f"Team Update: {self.team.name}",
                description=f"A new player has joined team {self.team.name}.",
                color=discord.Color.blue()
            )
            embed.add_field(name="Players", value=player_list, inline=False)
            embed.add_field(name="Team Captain", value=f"<@{self.team.captain_id}>", inline=True)
            embed.add_field(name="Avg MMR", value=f"{self.team.calculate_average_mmr():.1f}", inline=True)
            
            await admin_channel.send(embed=embed)
        
        await interaction.response.send_message(
            f"You have joined team **{self.team.name}**! Your registration is pending admin approval.",
            ephemeral=True
        )


# ---------------- Admin Views and Controls ----------------

class TeamApprovalView(View):
    def __init__(self, tournament: Tournament, team_id: str):
        super().__init__(timeout=None)  # No timeout for admin buttons
        self.tournament = tournament
        self.team_id = team_id
    
    @discord.ui.button(label="Approve", style=ButtonStyle.green, row=0)
    async def approve_button(self, interaction: Interaction, button: Button):
        team = self.tournament.get_team(self.team_id)
        if not team:
            await interaction.response.send_message("Team not found.", ephemeral=True)
            return
        
        # Approve the team
        self.tournament.approve_team(self.team_id)
        TournamentDatabase.save_tournament(self.tournament)
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(
            content=f"**Team {team.name} has been approved!**",
            view=self
        )
        
        # Notify team members
        for player in team.players:
            try:
                user = await interaction.client.fetch_user(player.user_id)
                await user.send(f"Your team **{team.name}** has been approved for the tournament **{self.tournament.name}**!")
            except:
                pass  # Ignore if DM fails
    
    @discord.ui.button(label="Deny", style=ButtonStyle.red, row=0)
    async def deny_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_modal(TeamDenialModal(self.tournament, self.team_id))


class TeamDenialModal(Modal):
    def __init__(self, tournament: Tournament, team_id: str):
        super().__init__(title="Deny Team")
        self.tournament = tournament
        self.team_id = team_id
        
        self.reason = TextInput(
            label="Reason for Denial",
            placeholder="Why is this team being denied?",
            required=True,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.reason)
    
    async def on_submit(self, interaction: Interaction):
        team = self.tournament.get_team(self.team_id)
        if not team:
            await interaction.response.send_message("Team not found.", ephemeral=True)
            return
        
        # Deny the team
        self.tournament.deny_team(self.team_id, self.reason.value)
        TournamentDatabase.save_tournament(self.tournament)
        
        # Update the message
        for item in interaction.message.components:
            for child in item.children:
                child.disabled = True
        
        await interaction.response.edit_message(
            content=f"**Team {team.name} has been denied.**\nReason: {self.reason.value}",
            view=None
        )
        
        # Notify team members
        for player in team.players:
            try:
                user = await interaction.client.fetch_user(player.user_id)
                await user.send(
                    f"Your team **{team.name}** has been denied for the tournament **{self.tournament.name}**.\n\n"
                    f"Reason: {self.reason.value}\n\n"
                    f"You can sign up again by using the `/signup` command in the tournament sign-up channel and addressing the reason for denial."
                )
            except:
                pass  # Ignore if DM fails


# ---------------- Tournament Bracket Management ----------------

class StartTournamentView(View):
    def __init__(self, tournament: Tournament):
        super().__init__()
        self.tournament = tournament
    
    @discord.ui.button(label="Start Tournament", style=ButtonStyle.green, row=0)
    async def start_button(self, interaction: Interaction, button: Button):
        # Check if there are enough teams
        approved_teams = self.tournament.get_approved_teams()
        if len(approved_teams) < 2:
            await interaction.response.send_message("Need at least 2 approved teams to start the tournament.", ephemeral=True)
            return
        
        # Create the bracket
        matches = self.tournament.create_matches()
        
        # Set started_at time
        self.tournament.started_at = datetime.now()
        
        # Save the tournament
        TournamentDatabase.save_tournament(self.tournament)

        # Disable the button
        button.disabled = True
        await interaction.response.edit_message(view=self)
        
        # Update bracket channel
        await update_bracket_display(interaction, self.tournament)
        
        # Create match channels for pending matches
        for match in self.tournament.get_pending_matches():
            await create_match_channel(interaction, self.tournament, match)
        
        ## Announce the start
        if self.tournament.announcement_channel_id:
            channel = interaction.guild.get_channel(self.tournament.announcement_channel_id)
            if channel:
                await channel.send(
                    f"# 🏆 Tournament Has Started! 🏆\n\n"
                    f"The tournament has officially begun! Check the bracket channel for match details.\n\n"
                    f"Players in first-round matches should check their match channels for lobby information."
                )


async def update_bracket_display(interaction: Interaction, tournament: Tournament):
    """Update the bracket display in the bracket channel"""
    if not tournament.bracket_channel_id:
        return
    
    channel = interaction.guild.get_channel(tournament.bracket_channel_id)
    if not channel:
        return
    
    # Get all teams
    approved_teams = tournament.get_approved_teams()
    
    # Create team list message
    team_list = "# Registered Teams\n\n"
    for team in sorted(approved_teams, key=lambda t: t.seeding):
        player_names = ", ".join([p.username for p in team.players])
        team_list += f"**Seed #{team.seeding}: {team.name}** - {player_names}\n"
    
    # Send team list
    await channel.send(team_list)
    
    # Create bracket visualization
    bracket_msg = await create_bracket_visualization(tournament)
    
    # Send bracket
    await channel.send("# Tournament Bracket\n\n" + bracket_msg)


async def create_bracket_visualization(tournament: Tournament) -> str: # TODO eventually transform this into a nicer looking pillow image creation process
    """Create a text-based visualization of the tournament bracket"""
    max_rounds = 0
    for match in tournament.matches.values():
        max_rounds = max(max_rounds, match.round_number)
    
    # Group matches by round
    matches_by_round = {}
    for i in range(1, max_rounds + 1):
        matches_by_round[i] = tournament.get_matches_by_round(i)
    
    # Build the bracket
    bracket = "```\n"
    
    for round_num in range(1, max_rounds + 1):
        round_matches = sorted(matches_by_round[round_num], key=lambda m: m.match_number)
        bracket += f"Round {round_num}:\n"
        
        for match in round_matches:
            team1_name = "TBD"
            team2_name = "TBD"
            
            if match.team1_id:
                team1 = tournament.get_team(match.team1_id)
                if team1:
                    team1_name = team1.name
            
            if match.team2_id:
                team2 = tournament.get_team(match.team2_id)
                if team2:
                    team2_name = team2.name
                else:
                    team2_name = "BYE"  # Mark as bye match
            
            status = ""
            if match.winner_id:
                winner_name = "Unknown"
                if match.winner_id == match.team1_id:
                    winner_name = team1_name
                    status = "✓ vs "
                else:
                    winner_name = team2_name
                    status = " vs ✓"
                bracket += f"  Match {match.match_number}: {team1_name}{status}{team2_name}\n"
            else:
                bracket += f"  Match {match.match_number}: {team1_name} vs {team2_name}\n"
        
        bracket += "\n"
    
    bracket += "```"
    return bracket


async def create_match_channel(interaction: Interaction, tournament: Tournament, match: Match):
    """Create a channel for a match"""
    if not match.team1_id or not match.team2_id:
        return  # Skip if not both teams are set
    
    team1 = tournament.get_team(match.team1_id)
    team2 = tournament.get_team(match.team2_id)
    
    if not team1 or not team2:
        return  # Skip if teams not found
    
    # Generate a random lobby name and password
    # TODO there is a minimally small change of duplicate lobby names, might need to add a check for this eventually
    lobby_name = f"{team1.name[:3].upper()}-{team2.name[:3].upper()}-{random.randint(100, 999)}" 
    lobby_password = random.choice(PASSWORDS).lower()
    
    match.lobby_name = lobby_name
    match.lobby_password = lobby_password
    
    # Create channel permissions
    guild = interaction.guild
    category = guild.get_channel(tournament.category_id)
    
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
    }
    
    # Add tournament admin role
    from utils.config_storage import ConfigStorage
    admin_role_id = ConfigStorage.get_tournament_admin_role(guild.id)
    
    if admin_role_id:
        admin_role = guild.get_role(admin_role_id)
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True
            )
    
    # If no tournament admin role, fall back to checking for roles with "admin" in the name
    if not admin_role_id:
        for role in guild.roles:
            if "admin" in role.name.lower():
                admin_role = role
                overwrites[admin_role] = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True
                )
                break
    
    # Add Discord administrators
    for member in guild.members:
        if member.guild_permissions.administrator:
            overwrites[member] = discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True
            )
    
    # Add teams
    for player in team1.players + team2.players:
        member = guild.get_member(player.user_id)
        if member:
            overwrites[member] = discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True
            )
    
    # Create channel
    match_name = f"match-{team1.name.lower().replace(' ', '-')}-vs-{team2.name.lower().replace(' ', '-')}"
    if len(match_name) > 90:  # Keep within Discord's limit
        match_name = f"match-{match.id[-8:]}"
    
    channel = await guild.create_text_channel(
        name=match_name,
        category=category,
        overwrites=overwrites
    )
    
    match.channel_id = channel.id
    
    # Save the tournament
    TournamentDatabase.save_tournament(tournament)
    
    # Create match check-in message
    embed = discord.Embed(
        title=f"Match: {team1.name} vs {team2.name}",
        description="Please check in for your match by clicking the button below.",
        color=discord.Color.blue()
    )
    
    team1_players = "\n".join([f"<@{p.user_id}>" for p in team1.players])
    team2_players = "\n".join([f"<@{p.user_id}>" for p in team2.players])
    
    embed.add_field(name=f"Team {team1.name}", value=team1_players, inline=True)
    embed.add_field(name=f"Team {team2.name}", value=team2_players, inline=True)
    
    # Mention all players
    mentions = " ".join([f"<@{p.user_id}>" for p in team1.players + team2.players])
    
    # Send initial message with check-in buttons
    message = await channel.send(
        content=f"{mentions} Your match is ready!",
        embed=embed,
        view=MatchCheckInView(tournament, match.id)
    )


class MatchCheckInView(View):
    def __init__(self, tournament: Tournament, match_id: str):
        super().__init__(timeout=None)
        self.tournament = tournament
        self.match_id = match_id
    
    @discord.ui.button(label="Check-in Team 1", style=ButtonStyle.primary, row=0, custom_id="checkin_team1")
    async def team1_button(self, interaction: Interaction, button: Button):
        match = self.tournament.get_match(self.match_id)
        if not match:
            await interaction.response.send_message("Match not found.", ephemeral=True)
            return
        
        team1 = self.tournament.get_team(match.team1_id)
        
        # Check if user is on team1
        is_on_team = False
        for player in team1.players:
            if player.user_id == interaction.user.id:
                is_on_team = True
                break
        
        if not is_on_team:
            await interaction.response.send_message("You are not on this team.", ephemeral=True)
            return
        
        # Mark team as checked in
        match.checked_in[match.team1_id] = True
        TournamentDatabase.save_tournament(self.tournament)
        
        # Disable the button
        button.disabled = True
        await interaction.response.edit_message(view=self)
        
        # Check if both teams are checked in
        if all(match.checked_in.values()):
            await self.both_teams_checked_in(interaction)
        else:
            # Start timeout for other team
            await interaction.followup.send(f"Team {team1.name} has checked in! Waiting for the other team...")
    
    @discord.ui.button(label="Check-in Team 2", style=ButtonStyle.primary, row=0, custom_id="checkin_team2")
    async def team2_button(self, interaction: Interaction, button: Button):
        match = self.tournament.get_match(self.match_id)
        if not match:
            await interaction.response.send_message("Match not found.", ephemeral=True)
            return
        
        team2 = self.tournament.get_team(match.team2_id)
        
        # Check if user is on team2
        is_on_team = False
        for player in team2.players:
            if player.user_id == interaction.user.id:
                is_on_team = True
                break
        
        if not is_on_team:
            await interaction.response.send_message("You are not on this team.", ephemeral=True)
            return
        
        # Mark team as checked in
        match.checked_in[match.team2_id] = True
        TournamentDatabase.save_tournament(self.tournament)
        
        # Disable the button
        button.disabled = True
        await interaction.response.edit_message(view=self)
        
        # Check if both teams are checked in
        if all(match.checked_in.values()):
            await self.both_teams_checked_in(interaction)
        else:
            # Start timeout for other team
            await interaction.followup.send(f"Team {team2.name} has checked in! Waiting for the other team...")
    
    async def both_teams_checked_in(self, interaction: Interaction):
        match = self.tournament.get_match(self.match_id)
        team1 = self.tournament.get_team(match.team1_id)
        team2 = self.tournament.get_team(match.team2_id)
        
        # Post lobby info
        embed = discord.Embed(
            title="Match Ready!",
            description="Both teams have checked in. Please join the Rocket League lobby with the information below:",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Lobby Name", value=match.lobby_name, inline=True)
        embed.add_field(name="Password", value=match.lobby_password, inline=True)
        embed.add_field(name="Format", value=f"Best of 3", inline=True)
        
        # Update match status
        match.status = MatchStatus.IN_PROGRESS
        TournamentDatabase.save_tournament(self.tournament)
        
        # Send match report view
        message = await interaction.followup.send(
            embed=embed,
            view=MatchReportView(self.tournament, match.id)
        )


class MatchReportView(View):
    def __init__(self, tournament: Tournament, match_id: str):
        super().__init__(timeout=None)
        self.tournament = tournament
        self.match_id = match_id
    
    @discord.ui.button(label="Report Team 1 Win", style=ButtonStyle.primary, row=0)
    async def team1_win_button(self, interaction: Interaction, button: Button):
        await self.report_result(interaction, is_team1_win=True)
    
    @discord.ui.button(label="Report Team 2 Win", style=ButtonStyle.primary, row=0)
    async def team2_win_button(self, interaction: Interaction, button: Button):
        await self.report_result(interaction, is_team1_win=False)
    
    async def report_result(self, interaction: Interaction, is_team1_win: bool):
        match = self.tournament.get_match(self.match_id)
        if not match:
            await interaction.response.send_message("Match not found.", ephemeral=True)
            return
        
        team1 = self.tournament.get_team(match.team1_id)
        team2 = self.tournament.get_team(match.team2_id)
        
        # Check if user is part of the match
        is_participant = False
        for player in team1.players + team2.players:
            if player.user_id == interaction.user.id:
                is_participant = True
                break

        is_admin = is_tournament_admin(interaction.user)
        
        if not is_participant and not is_admin:
            await interaction.response.send_message("You are not a participant in this match.", ephemeral=True)
            return
        
        # Record vote
        winner_id = match.team1_id if is_team1_win else match.team2_id
        match.record_vote(interaction.user.id, winner_id)
        
        # Check if there's a majority
        team1_player_ids = [p.user_id for p in team1.players]
        team2_player_ids = [p.user_id for p in team2.players]
        
        result = match.determine_result(team1_player_ids, team2_player_ids)
        
        # Save votes
        TournamentDatabase.save_tournament(self.tournament)
        
        if result:
            # We have a winner
            winner_team = team1 if result == match.team1_id else team2
            loser_team = team2 if result == match.team1_id else team1
            
            # Display winner
            embed = discord.Embed(
                title="Match Result",
                description=f"**{winner_team.name}** has won the match against **{loser_team.name}**!",
                color=discord.Color.gold()
            )
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            # Update match and advance winner
            next_match = self.tournament.advance_match(match.id, result)
            
            # Update bracket display
            try:
                await update_bracket_display(interaction, self.tournament)
            except Exception as e:
                print(f"Error updating bracket: {e}")
            
            # If next match is ready (both teams assigned), create its channel
            if next_match and next_match.team1_id and next_match.team2_id:
                await create_match_channel(interaction, self.tournament, next_match)
            
            # Check if tournament is complete (only one match in the last round)
            final_round = max(match.round_number for match in self.tournament.matches.values())
            final_matches = [m for m in self.tournament.matches.values() if m.round_number == final_round]
            
            if len(final_matches) == 1 and final_matches[0].status == MatchStatus.COMPLETED:
                # Tournament complete
                self.tournament.ended_at = datetime.now()
                self.tournament.winner_id = final_matches[0].winner_id
                TournamentDatabase.save_tournament(self.tournament)
                
                # Announce winner
                if self.tournament.announcement_channel_id:
                    channel = interaction.guild.get_channel(self.tournament.announcement_channel_id)
                    if channel:
                        winner = self.tournament.get_team(self.tournament.winner_id)
                        if winner:
                            player_mentions = " ".join([f"<@{p.user_id}>" for p in winner.players])
                            
                            prize_text = ""
                            if self.tournament.prize_info:
                                prize_text = f"**Prizes:**\n{self.tournament.prize_info}"
                            
                            await channel.send(
                                f"# 🏆 Tournament Champion! 🏆\n\n"
                                f"Congratulations to **{winner.name}** for winning the tournament!\n\n"
                                f"Team members: {player_mentions}\n\n"
                                f"{prize_text}"
                            )
        else:
            # No majority yet
            team1_votes = sum(1 for team in match.votes.values() if team == match.team1_id)
            team2_votes = sum(1 for team in match.votes.values() if team == match.team2_id)
            
            await interaction.response.send_message(
                f"Vote recorded! Current votes: {team1.name}: {team1_votes}, {team2.name}: {team2_votes}",
                ephemeral=True
            )


# ---------------- Reminder Scheduling ----------------

class ReminderScheduleModal(Modal):
    def __init__(self, tournament: Tournament):
        super().__init__(title="Schedule Reminder")
        self.tournament = tournament
        
        self.reminder_days = TextInput(
            label="Days from now",
            placeholder="0",
            required=True,
            max_length=2
        )
        self.add_item(self.reminder_days)
        
        self.reminder_hours = TextInput(
            label="Hours from now",
            placeholder="0",
            required=True,
            max_length=2
        )
        self.add_item(self.reminder_hours)
        
        self.reminder_minutes = TextInput(
            label="Minutes from now",
            placeholder="0",
            required=True,
            max_length=2
        )
        self.add_item(self.reminder_minutes)
        
        self.message = TextInput(
            label="Reminder Message",
            placeholder="Tournament starts soon!",
            required=True,
            max_length=1000,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.message)
    
    async def on_submit(self, interaction: Interaction):
        try:
            days = int(self.reminder_days.value or 0)
            hours = int(self.reminder_hours.value or 0)
            minutes = int(self.reminder_minutes.value or 0)
            
            if days < 0 or hours < 0 or minutes < 0:
                await interaction.response.send_message("Time values cannot be negative.", ephemeral=True)
                return
            
            if days == 0 and hours == 0 and minutes < 1:
                await interaction.response.send_message("Reminder must be at least 1 minute in the future.", ephemeral=True)
                return
            
            # Calculate when to send reminder
            now = datetime.now()
            reminder_time = now + timedelta(days=days, hours=hours, minutes=minutes)
            
            # Store reminder info
            self.tournament.reminders.append({
                "time": reminder_time.isoformat(),
                "message": self.message.value
            })
            
            # Save tournament
            TournamentDatabase.save_tournament(self.tournament)
            
            # Acknowledge
            await interaction.response.send_message(
                f"Reminder scheduled for <t:{int(reminder_time.timestamp())}:F>.",
                ephemeral=True
            )
            
            # Start a background task to handle the reminder
            asyncio.create_task(self.send_reminder_later(interaction, reminder_time, self.message.value))
        
        except ValueError:
            await interaction.response.send_message("Please enter valid numbers for time values.", ephemeral=True)
    
    async def send_reminder_later(self, interaction: Interaction, reminder_time: datetime, message: str):
        """Background task to send the reminder at the specified time"""
        # Calculate seconds to wait
        now = datetime.now()
        wait_seconds = (reminder_time - now).total_seconds()
        
        if wait_seconds <= 0:
            return
        
        # Wait until it's time
        await asyncio.sleep(wait_seconds)
        
        # Double-check that the tournament still exists and is active
        tournament = TournamentDatabase.load_tournament(self.tournament.id)
        if not tournament or not tournament.is_active:
            return
        
        # Send the reminder
        if tournament.announcement_channel_id:
            channel = interaction.guild.get_channel(tournament.announcement_channel_id)
            if channel:
                # Get all player mentions
                mentions = []
                for team in tournament.teams.values():
                    if team.status == TeamStatus.APPROVED:
                        for player in team.players:
                            mentions.append(f"<@{player.user_id}>")
                
                mentions_text = " ".join(mentions)
                
                await channel.send(
                    f"# 📢 Tournament Reminder 📢\n\n"
                    f"{message}\n\n"
                    f"{mentions_text}"
                )


# ---------------- Main Commands ----------------

@app_commands.command(name="tournament", description="Create and manage tournaments")
@app_commands.describe(
    action="The tournament action to perform",
    tournament_id="Tournament ID (for specific tournament commands)"
)
@app_commands.choices(
    action=[
        app_commands.Choice(name="create", value="create"),
        app_commands.Choice(name="list", value="list"),
        app_commands.Choice(name="start", value="start"),
        app_commands.Choice(name="approve", value="approve"),
        app_commands.Choice(name="deny", value="deny"),
        app_commands.Choice(name="bracket", value="bracket"),
        app_commands.Choice(name="reminder", value="reminder"),
        app_commands.Choice(name="edit", value="edit"),
        app_commands.Choice(name="delete", value="delete"),
    ]
)
async def tournament_command(
    interaction: Interaction, 
    action: app_commands.Choice[str],
    tournament_id: str = None
):
    # Directly allow server owner
    is_server_owner = interaction.user.id == interaction.guild.owner_id
    
    # Check permissions (admin commands)
    admin_actions = ["create", "start", "approve", "deny", "bracket", "reminder", "edit", "delete"]
    
    if action.value in admin_actions and not is_server_owner:
        from utils.permissions import is_tournament_admin
        if not is_tournament_admin(interaction.user):
            await interaction.response.send_message(
                "You need tournament admin permissions to use this command. Please contact a server administrator.",
                ephemeral=True
            )
            return
    
    # Handle different actions
    if action.value == "create":
        await create_tournament(interaction)
    elif action.value == "list":
        await list_tournaments(interaction)
    elif action.value == "start":
        await start_tournament(interaction, tournament_id)
    elif action.value == "approve":
        await approve_team(interaction, tournament_id)
    elif action.value == "deny":
        await deny_team(interaction, tournament_id)
    elif action.value == "bracket":
        await update_bracket(interaction, tournament_id)
    elif action.value == "reminder":
        await schedule_reminder(interaction, tournament_id)
    elif action.value == "edit":
        await edit_tournament(interaction, tournament_id)
    elif action.value == "delete":
        await delete_tournament(interaction, tournament_id)


async def create_tournament(interaction: Interaction):
    """Start the tournament creation process"""
    await interaction.response.send_modal(TournamentCreateModal())


async def list_tournaments(interaction: Interaction):
    """List all active tournaments"""
    tournaments = TournamentDatabase.get_active_tournaments()
    
    if not tournaments:
        await interaction.response.send_message("No active tournaments found.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="Active Tournaments",
        description="Here are the currently active tournaments:",
        color=discord.Color.blue()
    )
    
    for tournament in tournaments:
        status = "Registration" if not tournament.started_at else "In Progress"
        if tournament.ended_at:
            status = "Completed"
        
        # Get team count
        approved_teams = len(tournament.get_approved_teams())
        pending_teams = len(tournament.get_pending_teams())
        
        embed.add_field(
            name=tournament.name,
            value=(
                f"**Status:** {status}\n"
                f"**Format:** {tournament.format.value.capitalize()}\n"
                f"**Team Size:** {tournament.team_size}v{tournament.team_size}\n"
                f"**Teams:** {approved_teams} approved, {pending_teams} pending\n"
                f"**ID:** `{tournament.id}`"
            ),
            inline=False
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def start_tournament(interaction: Interaction, tournament_id: str = None):
    """Start a tournament"""
    # If no tournament ID provided, check for admin channel
    if not tournament_id:
        tournament = TournamentDatabase.get_tournament_by_channel(interaction.channel_id)
        if not tournament:
            # Show list of tournaments to select from
            await interaction.response.send_message(
                "Please specify which tournament to start:",
                view=TournamentSelectView(interaction.user.id, "start"),
                ephemeral=True
            )
            return
        tournament_id = tournament.id
    
    tournament = TournamentDatabase.load_tournament(tournament_id)
    if not tournament:
        await interaction.response.send_message("Tournament not found.", ephemeral=True)
        return
    
    # Check if already started
    if tournament.started_at:
        await interaction.response.send_message("This tournament has already started.", ephemeral=True)
        return
    
    # Confirm start
    await interaction.response.send_message(
        f"Are you sure you want to start tournament **{tournament.name}**?",
        view=StartTournamentView(tournament),
        ephemeral=True
    )


async def approve_team(interaction: Interaction, tournament_id: str = None):
    """Approve a team for participation"""
    # If no tournament ID provided, check for admin channel
    if not tournament_id:
        tournament = TournamentDatabase.get_tournament_by_channel(interaction.channel_id)
        if not tournament:
            # Show list of tournaments to select from
            await interaction.response.send_message(
                "Please specify which tournament to manage:",
                view=TournamentSelectView(interaction.user.id, "approve"),
                ephemeral=True
            )
            return
        tournament_id = tournament.id
    
    tournament = TournamentDatabase.load_tournament(tournament_id)
    if not tournament:
        await interaction.response.send_message("Tournament not found.", ephemeral=True)
        return
    
    # Get pending teams
    pending_teams = tournament.get_pending_teams()
    
    if not pending_teams:
        await interaction.response.send_message("No pending teams to approve.", ephemeral=True)
        return
    
    # Show team selection
    await interaction.response.send_message(
        "Select a team to approve:",
        view=TeamApprovalSelectView(tournament),
        ephemeral=True
    )


class TeamApprovalSelectView(View):
    def __init__(self, tournament: Tournament):
        super().__init__()
        self.tournament = tournament
        
        # Add team selection dropdown
        options = []
        for team in tournament.get_pending_teams():
            options.append(
                SelectOption(
                    label=team.name[:100],  # Max 100 chars
                    value=team.id,
                    description=f"Players: {len(team.players)}/{tournament.team_size}"
                )
            )
        
        if not options:
            options.append(SelectOption(label="No pending teams", value="none"))
        
        self.teams_select = Select(
            placeholder="Select a team to approve...",
            min_values=1,
            max_values=1,
            options=options[:25]  # Max 25 options
        )
        self.teams_select.callback = self.on_team_select
        self.add_item(self.teams_select)
    
    async def on_team_select(self, interaction: Interaction):
        team_id = self.teams_select.values[0]
        
        if team_id == "none":
            await interaction.response.send_message("No pending teams available.", ephemeral=True)
            return
        
        team = self.tournament.get_team(team_id)
        
        if not team:
            await interaction.response.send_message("Team not found.", ephemeral=True)
            return
        
        # Approve the team
        self.tournament.approve_team(team_id)
        TournamentDatabase.save_tournament(self.tournament)
        
        # Notify team members
        for player in team.players:
            try:
                user = await interaction.client.fetch_user(player.user_id)
                await user.send(f"Your team **{team.name}** has been approved for the tournament **{self.tournament.name}**!")
            except:
                pass  # Ignore if DM fails
        
        await interaction.response.send_message(f"Team **{team.name}** has been approved!", ephemeral=True)


async def deny_team(interaction: Interaction, tournament_id: str = None):
    """Deny a team from participation"""
    # If no tournament ID provided, check for admin channel
    if not tournament_id:
        tournament = TournamentDatabase.get_tournament_by_channel(interaction.channel_id)
        if not tournament:
            # Show list of tournaments to select from
            await interaction.response.send_message(
                "Please specify which tournament to manage:",
                view=TournamentSelectView(interaction.user.id, "deny"),
                ephemeral=True
            )
            return
        tournament_id = tournament.id
    
    tournament = TournamentDatabase.load_tournament(tournament_id)
    if not tournament:
        await interaction.response.send_message("Tournament not found.", ephemeral=True)
        return
    
    # Get pending teams
    pending_teams = tournament.get_pending_teams()
    
    if not pending_teams:
        await interaction.response.send_message("No pending teams to deny.", ephemeral=True)
        return
    
    # Show team selection
    await interaction.response.send_message(
        "Select a team to deny:",
        view=TeamDenialSelectView(tournament),
        ephemeral=True
    )


class TeamDenialSelectView(View):
    def __init__(self, tournament: Tournament):
        super().__init__()
        self.tournament = tournament
        
        # Add team selection dropdown
        options = []
        for team in tournament.get_pending_teams():
            options.append(
                SelectOption(
                    label=team.name[:100],  # Max 100 chars
                    value=team.id,
                    description=f"Players: {len(team.players)}/{tournament.team_size}"
                )
            )
        
        if not options:
            options.append(SelectOption(label="No pending teams", value="none"))
        
        self.teams_select = Select(
            placeholder="Select a team to deny...",
            min_values=1,
            max_values=1,
            options=options[:25]  # Max 25 options
        )
        self.teams_select.callback = self.on_team_select
        self.add_item(self.teams_select)
    
    async def on_team_select(self, interaction: Interaction):
        team_id = self.teams_select.values[0]
        
        if team_id == "none":
            await interaction.response.send_message("No pending teams available.", ephemeral=True)
            return
        
        team = self.tournament.get_team(team_id)
        
        if not team:
            await interaction.response.send_message("Team not found.", ephemeral=True)
            return
        
        # Show denial modal
        await interaction.response.send_modal(TeamDenialModal(self.tournament, team_id))


async def update_bracket(interaction: Interaction, tournament_id: str = None):
    """Update the tournament bracket display"""
    # If no tournament ID provided, check for admin channel
    if not tournament_id:
        tournament = TournamentDatabase.get_tournament_by_channel(interaction.channel_id)
        if not tournament:
            # Show list of tournaments to select from
            await interaction.response.send_message(
                "Please specify which tournament to update bracket for:",
                view=TournamentSelectView(interaction.user.id, "bracket"),
                ephemeral=True
            )
            return
        tournament_id = tournament.id
    
    tournament = TournamentDatabase.load_tournament(tournament_id)
    if not tournament:
        await interaction.response.send_message("Tournament not found.", ephemeral=True)
        return
    
    # Check if tournament has started
    if not tournament.started_at:
        await interaction.response.send_message("The tournament hasn't started yet.", ephemeral=True)
        return
    
    # Check if bracket channel exists
    if not tournament.bracket_channel_id:
        await interaction.response.send_message("This tournament doesn't have a bracket channel.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Update bracket display
        await update_bracket_display(interaction, tournament)
        await interaction.followup.send("Tournament bracket has been updated!", ephemeral=True)
    except Exception as e:
        print(f"Error updating bracket: {e}")
        await interaction.followup.send(f"Error updating bracket: {e}", ephemeral=True)


async def schedule_reminder(interaction: Interaction, tournament_id: str = None):
    """Schedule a tournament reminder"""
    # If no tournament ID provided, check for admin channel
    if not tournament_id:
        tournament = TournamentDatabase.get_tournament_by_channel(interaction.channel_id)
        if not tournament:
            # Show list of tournaments to select from
            await interaction.response.send_message(
                "Please specify which tournament to schedule a reminder for:",
                view=TournamentSelectView(interaction.user.id, "reminder"),
                ephemeral=True
            )
            return
        tournament_id = tournament.id
    
    tournament = TournamentDatabase.load_tournament(tournament_id)
    if not tournament:
        await interaction.response.send_message("Tournament not found.", ephemeral=True)
        return
    
    # Check if announcements channel exists
    if not tournament.announcement_channel_id:
        await interaction.response.send_message("This tournament doesn't have an announcements channel for reminders.", ephemeral=True)
        return
    
    # Show reminder modal
    await interaction.response.send_modal(ReminderScheduleModal(tournament))


async def edit_tournament(interaction: Interaction, tournament_id: str = None): # TODO add so that editing name, deadline, etc. also changes their values in the respective parts of the code
    """Edit tournament details"""
    # If no tournament ID provided, check for admin channel
    if not tournament_id:
        tournament = TournamentDatabase.get_tournament_by_channel(interaction.channel_id)
        if not tournament:
            # Show list of tournaments to select from
            await interaction.response.send_message(
                "Please specify which tournament to edit:",
                view=TournamentSelectView(interaction.user.id, "edit"),
                ephemeral=True
            )
            return
        tournament_id = tournament.id
    
    tournament = TournamentDatabase.load_tournament(tournament_id)
    if not tournament:
        await interaction.response.send_message("Tournament not found.", ephemeral=True)
        return
    
    # Show edit options
    await interaction.response.send_message(
        f"Select what to edit for tournament **{tournament.name}**:",
        view=TournamentEditView(tournament),
        ephemeral=True
    )


class TournamentEditView(View):
    def __init__(self, tournament: Tournament):
        super().__init__()
        self.tournament = tournament
    
    @discord.ui.button(label="Edit Name", style=ButtonStyle.primary, row=0)
    async def edit_name_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_modal(TournamentEditNameModal(self.tournament))
    
    @discord.ui.button(label="Edit Deadline", style=ButtonStyle.primary, row=0)
    async def edit_deadline_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_modal(TournamentEditDeadlineModal(self.tournament))
    
    @discord.ui.button(label="Edit Prizes", style=ButtonStyle.primary, row=1)
    async def edit_prizes_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_modal(TournamentEditPrizesModal(self.tournament))
    
    @discord.ui.button(label="Edit Team", style=ButtonStyle.primary, row=1)
    async def edit_team_button(self, interaction: Interaction, button: Button):
        # Show team selection for editing
        options = []
        for team in self.tournament.teams.values():
            options.append(
                SelectOption(
                    label=team.name[:100],  # Max 100 chars
                    value=team.id,
                    description=f"Status: {team.status.value.capitalize()}"
                )
            )
        
        if not options:
            await interaction.response.send_message("No teams available to edit.", ephemeral=True)
            return
        
        select = Select(
            placeholder="Select a team to edit...",
            min_values=1,
            max_values=1,
            options=options[:25]  # Max 25 options
        )
        
        async def team_select_callback(team_interaction: Interaction):
            team_id = select.values[0]
            team = self.tournament.get_team(team_id)
            
            if not team:
                await team_interaction.response.send_message("Team not found.", ephemeral=True)
                return
            
            await team_interaction.response.send_message(
                f"Editing team **{team.name}**:",
                view=TeamEditView(self.tournament, team_id),
                ephemeral=True
            )
        
        select.callback = team_select_callback
        
        team_select_view = View()
        team_select_view.add_item(select)
        
        await interaction.response.send_message(
            "Select a team to edit:",
            view=team_select_view,
            ephemeral=True
        )


class TournamentEditNameModal(Modal):
    def __init__(self, tournament: Tournament):
        super().__init__(title="Edit Tournament Name")
        self.tournament = tournament
        
        self.name = TextInput(
            label="New Tournament Name",
            placeholder="Enter new tournament name",
            required=True,
            max_length=100,
            default=tournament.name
        )
        self.add_item(self.name)
    
    async def on_submit(self, interaction: Interaction):
        old_name = self.tournament.name
        self.tournament.name = self.name.value
        
        # Save the tournament
        TournamentDatabase.save_tournament(self.tournament)
        
        await interaction.response.send_message(
            f"Tournament name changed from **{old_name}** to **{self.tournament.name}**.",
            ephemeral=True
        )


class TournamentEditDeadlineModal(Modal):
    def __init__(self, tournament: Tournament):
        super().__init__(title="Edit Registration Deadline")
        self.tournament = tournament
        
        self.deadline_days = TextInput(
            label="Days from now",
            placeholder="0",
            required=True,
            max_length=2,
            default="7"
        )
        self.add_item(self.deadline_days)
    
    async def on_submit(self, interaction: Interaction):
        try:
            days = int(self.deadline_days.value)
            if days < 0:
                await interaction.response.send_message("Days cannot be negative.", ephemeral=True)
                return
            
            old_deadline = self.tournament.registration_deadline
            new_deadline = datetime.now() + timedelta(days=days)
            self.tournament.registration_deadline = new_deadline
            
            # Save the tournament
            TournamentDatabase.save_tournament(self.tournament)
            
            await interaction.response.send_message(
                f"Registration deadline changed from <t:{int(old_deadline.timestamp())}:F> to <t:{int(new_deadline.timestamp())}:F>.",
                ephemeral=True
            )
        except ValueError:
            await interaction.response.send_message("Please enter a valid number for days.", ephemeral=True)


class TournamentEditPrizesModal(Modal):
    def __init__(self, tournament: Tournament):
        super().__init__(title="Edit Tournament Prizes")
        self.tournament = tournament
        
        self.prize_info = TextInput(
            label="Prize Information",
            placeholder="Describe tournament prizes",
            required=False,
            max_length=1000,
            style=discord.TextStyle.paragraph,
            default=tournament.prize_info or ""
        )
        self.add_item(self.prize_info)
    
    async def on_submit(self, interaction: Interaction):
        old_prizes = self.tournament.prize_info or "None"
        self.tournament.prize_info = self.prize_info.value if self.prize_info.value else None
        
        # Save the tournament
        TournamentDatabase.save_tournament(self.tournament)
        
        await interaction.response.send_message(
            f"Tournament prizes updated.\n\nOld prizes: {old_prizes}\nNew prizes: {self.tournament.prize_info or 'None'}",
            ephemeral=True
        )


class TeamEditView(View):
    def __init__(self, tournament: Tournament, team_id: str):
        super().__init__()
        self.tournament = tournament
        self.team_id = team_id
    
    @discord.ui.button(label="Change Name", style=ButtonStyle.primary, row=0)
    async def change_name_button(self, interaction: Interaction, button: Button):
        team = self.tournament.get_team(self.team_id)
        if not team:
            await interaction.response.send_message("Team not found.", ephemeral=True)
            return
        
        await interaction.response.send_modal(TeamEditNameModal(self.tournament, team))