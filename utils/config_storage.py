import json
import os
from typing import Dict, Optional, Any

# Directory for storing configuration data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
CONFIG_DIR = os.path.join(DATA_DIR, 'config')

# Ensure directories exist
os.makedirs(CONFIG_DIR, exist_ok=True)


class ConfigStorage:
    """
    Stores and retrieves configuration settings for each guild
    """
    
    @staticmethod
    def get_guild_config(guild_id: int) -> Dict[str, Any]:
        """Get configuration for a guild"""
        file_path = os.path.join(CONFIG_DIR, f"{guild_id}.json")
        
        if not os.path.exists(file_path):
            # Create default config
            default_config = {
                "guild_id": guild_id,
                "tournament_admin_role": None,
                "timezone": "UTC",
                "created_at": "",
                "last_updated": ""
            }
            
            ConfigStorage.save_guild_config(guild_id, default_config)
            return default_config
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading guild config: {e}")
            return {"guild_id": guild_id}
    
    @staticmethod
    def save_guild_config(guild_id: int, config: Dict[str, Any]) -> bool:
        """Save configuration for a guild"""
        file_path = os.path.join(CONFIG_DIR, f"{guild_id}.json")
        
        try:
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving guild config: {e}")
            return False
    
