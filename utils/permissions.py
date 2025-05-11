import discord
from utils.config_storage import ConfigStorage

def is_tournament_admin(member: discord.Member) -> bool:
    """Check if a member has tournament admin permissions"""
    
    # Server owner always has permissions
    if member.id == member.guild.owner_id:
        return True
    
    # Discord administrators always have permission
    if member.guild_permissions.administrator:
        return True
    
    # Check for the tournament admin role
    admin_role_id = ConfigStorage.get_tournament_admin_role(member.guild.id)
    
    if admin_role_id:
        # Check if the member has the role
        return any(role.id == admin_role_id for role in member.roles)
    
    # If no admin role is set, fall back to Discord administrators only
    return False