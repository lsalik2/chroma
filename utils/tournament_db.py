import os
import json
from typing import Optional, List

from models.tournament import Tournament

# Directory for storing tournament data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
TOURNAMENTS_DIR = os.path.join(DATA_DIR, 'tournaments')

# Ensure directories exist
os.makedirs(TOURNAMENTS_DIR, exist_ok=True)

class TournamentDatabase:
    @staticmethod
    def save_tournament(tournament: Tournament) -> bool:
        """Save tournament data to file"""
        try:
            # Convert tournament to dict
            tournament_dict = tournament.to_dict()
            
            # Create tournament file path
            file_path = os.path.join(TOURNAMENTS_DIR, f"{tournament.id}.json")
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(tournament_dict, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error saving tournament: {e}")
            return False
    
    @staticmethod
    def load_tournament(tournament_id: str) -> Optional[Tournament]:
        """Load tournament from file by ID"""
        try:
            file_path = os.path.join(TOURNAMENTS_DIR, f"{tournament_id}.json")
            
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, 'r') as f:
                tournament_dict = json.load(f)
                
            return Tournament.from_dict(tournament_dict)
        except Exception as e:
            print(f"Error loading tournament: {e}")
            return None
    
    @staticmethod
    def get_active_tournaments() -> List[Tournament]:
        """Get all active tournaments"""
        tournaments = []
        
        try:
            for filename in os.listdir(TOURNAMENTS_DIR):
                if filename.endswith('.json'):
                    tournament_id = filename[:-5]  # Remove .json extension
                    tournament = TournamentDatabase.load_tournament(tournament_id)
                    
                    if tournament and tournament.is_active:
                        tournaments.append(tournament)
        except Exception as e:
            print(f"Error loading active tournaments: {e}")
        
        return tournaments
    
    @staticmethod
    def get_guild_tournaments(guild_id: int) -> List[Tournament]:
        """Get all tournaments for a specific guild"""
        # This would require adding guild_id to the Tournament model
        # For now, just return all tournaments
        return TournamentDatabase.get_active_tournaments()
    
    @staticmethod
    def delete_tournament(tournament_id: str) -> bool:
        """Delete a tournament by ID"""
        try:
            file_path = os.path.join(TOURNAMENTS_DIR, f"{tournament_id}.json")
            
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            
            return False
        except Exception as e:
            print(f"Error deleting tournament: {e}")
            return False
    
    @staticmethod
    def get_tournament_by_match(match_id: str) -> Optional[Tournament]:
        """Find tournament containing a specific match"""
        try:
            for filename in os.listdir(TOURNAMENTS_DIR):
                if filename.endswith('.json'):
                    tournament_id = filename[:-5]
                    tournament = TournamentDatabase.load_tournament(tournament_id)
                    
                    if tournament and match_id in tournament.matches:
                        return tournament
        except Exception as e:
            print(f"Error finding tournament by match: {e}")
        
        return None