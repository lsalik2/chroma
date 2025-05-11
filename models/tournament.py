from enum import Enum
import uuid
from typing import List, Optional

class TournamentFormat(Enum):
    CHOOSE = "choose"   # Players choose their team
    BALANCE = "balance" # Bot balances teams
    RANDOM = "random"   # Bot creates random teams

class TeamStatus(Enum):
    PENDING = "pending"   # Awaiting admin approval
    APPROVED = "approved" # Approved and part of tournament
    DENIED = "denied"     # Denied by admin

class MatchStatus(Enum):
    PENDING = "pending"     # Match not started
    IN_PROGRESS = "playing" # Match in progress
    COMPLETED = "completed" # Match completed
    FORFEIT = "forfeit"     # Match forfeited

class Player:
    def __init__(self, user_id: int, username: str, epic_username: str, current_mmr: int, peak_mmr: int):
        self.user_id = user_id
        self.username = username
        self.epic_username = epic_username
        self.current_mmr = current_mmr
        self.peak_mmr = peak_mmr

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "epic_username": self.epic_username,
            "current_mmr": self.current_mmr,
            "peak_mmr": self.peak_mmr
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            epic_username=data["epic_username"],
            current_mmr=data["current_mmr"],
            peak_mmr=data["peak_mmr"]
        )

class Team:
    def __init__(self, name: str, captain_id: int, password: Optional[str] = None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.captain_id = captain_id
        self.password = password
        self.players: List[Player] = []
        self.status = TeamStatus.PENDING
        self.seeding = 0  # Will be set when tournament starts
        self.denial_reason = None
    
    def add_player(self, player: Player) -> bool:
        # Check if player already exists
        if any(p.user_id == player.user_id for p in self.players):
            return False
        
        self.players.append(player)
        return True