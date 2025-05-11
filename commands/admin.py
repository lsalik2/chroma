import discord
from discord import app_commands, Interaction, Role
from utils.config_storage import ConfigStorage

@app_commands.command(name="setup", description="Configure the bot settings")
@app_commands.describe(
    tournament_admin_role="The role that can manage tournaments"
)
async def setup_command(
    interaction: Interaction,
    tournament_admin_role: Role = None
):
    """Set up bot configuration including admin roles"""
    
    # Check if user has administrator permissions or is the server owner
    is_admin = False
    
    # Check if user is server owner
    if interaction.user.id == interaction.guild.owner_id:
        is_admin = True
    # Check if user has administrator permissions
    elif interaction.user.guild_permissions.administrator:
        is_admin = True
    
    if not is_admin:
        await interaction.response.send_message(
            "You need administrator permissions to use this setup command.",
            ephemeral=True
        )
        return
    
    guild_id = interaction.guild.id
    config = ConfigStorage.get_guild_config(guild_id)
    
    # Update tournament admin role if provided
    if tournament_admin_role:
        ConfigStorage.set_tournament_admin_role(guild_id, tournament_admin_role.id)
        await interaction.response.send_message(
            f"Tournament admin role set to **{tournament_admin_role.name}**.\n\n"
            f"Users with this role can now create and manage tournaments.",
            ephemeral=True
        )
    else:
        # Display current settings
        current_admin_role_id = config.get("tournament_admin_role")
        current_admin_role = None
        
        if current_admin_role_id:
            current_admin_role = interaction.guild.get_role(current_admin_role_id)
        
        embed = discord.Embed(
            title="Bot Configuration",
            description="Current configuration settings:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Tournament Admin Role",
            value=f"{current_admin_role.mention if current_admin_role else 'Not set'}",
            inline=False
        )
        
        embed.add_field(
            name="How to Update",
            value=f"Use `/setup tournament_admin_role:@role` to update the tournament admin role.",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

def register_admin(tree):
    tree.add_command(setup_command)