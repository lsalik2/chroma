import os
import json

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