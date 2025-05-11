from datetime import datetime, timedelta

import discord
from discord import Interaction, ButtonStyle, Button, SelectOption
from discord.ui import Modal, TextInput, View, Select

from models.tournament import TournamentFormat, Tournament, Player, Team, TeamStatus
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
            view=TeamApprovalView(self.tournament, team.id) # will add later
        )


class TeamChoiceView(View):
    def __init__(self, tournament: Tournament, player: Player):
        super().__init__()
        self.tournament = tournament
        self.player = player  # Store the player object directly
    
    @discord.ui.button(label="Create Team", style=ButtonStyle.primary, row=0)
    async def create_team_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_modal(CreateTeamModal(self.tournament, self.player)) # will add later
    
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
            view=TeamSelectView(self.tournament, self.player, available_teams), # will add later
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
                view=TeamApprovalView(self.tournament, team.id) # will add later
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
            await interaction.response.send_modal(TeamPasswordModal(self.tournament, team, self.player)) # will add later
        else:
            # Join team without password
            await self.join_team(interaction, team)