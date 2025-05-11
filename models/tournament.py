from enum import Enum
import uuid
from typing import List, Optional, Dict
from datetime import datetime

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
    
    def remove_player(self, user_id: int) -> bool:
        for i, player in enumerate(self.players):
            if player.user_id == user_id:
                self.players.pop(i)
                return True
        return False
    
    def calculate_average_mmr(self) -> float: # TODO placeholder until lanky's alg is used instead, though this works fairly well
        if not self.players:
            return 0
        
        total_current = sum(p.current_mmr for p in self.players)
        total_peak = sum(p.peak_mmr for p in self.players)
        
        # Weight current MMR 70%, peak MMR 30%
        return (total_current * 0.7 + total_peak * 0.3) / len(self.players)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "captain_id": self.captain_id,
            "password": self.password,
            "players": [p.to_dict() for p in self.players],
            "status": self.status.value,
            "seeding": self.seeding,
            "denial_reason": self.denial_reason
        }
    
    @classmethod
    def from_dict(cls, data):
        team = cls(
            name=data["name"],
            captain_id=data["captain_id"],
            password=data["password"]
        )
        team.id = data["id"]
        team.players = [Player.from_dict(p) for p in data["players"]]
        team.status = TeamStatus(data["status"])
        team.seeding = data["seeding"]
        team.denial_reason = data["denial_reason"]
        return team

class Match:
    def __init__(self, match_id: str, team1_id: str, team2_id: str, round_number: int, match_number: int):
        self.id = match_id
        self.team1_id = team1_id
        self.team2_id = team2_id
        self.round_number = round_number  # Round in tournament (1 = first round, etc)
        self.match_number = match_number  # Match number within the round
        self.status = MatchStatus.PENDING
        self.winner_id = None
        self.loser_id = None
        self.votes: Dict[int, str] = {}  # Map of user_id -> voted team_id
        self.channel_id = None
        self.created_at = datetime.now()
        self.lobby_name = None
        self.lobby_password = None
        self.checked_in = {team1_id: False, team2_id: False}