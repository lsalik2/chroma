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
    
    def record_vote(self, user_id: int, team_id: str) -> None:
        self.votes[user_id] = team_id
    
    def determine_result(self, team1_players: List[int], team2_players: List[int]) -> Optional[str]:
        """Determine the winner based on votes"""
        team1_votes = sum(1 for team in self.votes.values() if team == self.team1_id)
        team2_votes = sum(1 for team in self.votes.values() if team == self.team2_id)
        
        total_players = len(team1_players) + len(team2_players)
        majority = total_players // 2 + 1
        
        if team1_votes >= majority:
            return self.team1_id
        elif team2_votes >= majority:
            return self.team2_id
        
        return None  # No majority yet
    
    def to_dict(self):
        return {
            "id": self.id,
            "team1_id": self.team1_id,
            "team2_id": self.team2_id,
            "round_number": self.round_number,
            "match_number": self.match_number,
            "status": self.status.value,
            "winner_id": self.winner_id,
            "loser_id": self.loser_id,
            "votes": self.votes,
            "channel_id": self.channel_id,
            "created_at": self.created_at.isoformat(),
            "lobby_name": self.lobby_name,
            "lobby_password": self.lobby_password,
            "checked_in": self.checked_in
        }
    
    @classmethod
    def from_dict(cls, data):
        match = cls(
            match_id=data["id"],
            team1_id=data["team1_id"],
            team2_id=data["team2_id"],
            round_number=data["round_number"],
            match_number=data["match_number"]
        )
        match.status = MatchStatus(data["status"])
        match.winner_id = data["winner_id"]
        match.loser_id = data["loser_id"]
        match.votes = data["votes"]
        match.channel_id = data["channel_id"]
        match.created_at = datetime.fromisoformat(data["created_at"])
        match.lobby_name = data["lobby_name"]
        match.lobby_password = data["lobby_password"]
        match.checked_in = data["checked_in"]
        return match

class Tournament:
    def __init__(
        self, 
        name: str, 
        format: TournamentFormat, 
        creator_id: int,
        team_size: int, 
        max_teams: Optional[int] = None,
        registration_deadline: Optional[datetime] = None,
        prize_info: Optional[str] = None
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.format = format
        self.creator_id = creator_id
        self.team_size = team_size
        self.max_teams = max_teams
        self.registration_deadline = registration_deadline
        self.prize_info = prize_info
        self.teams: Dict[str, Team] = {}  # team_id -> Team
        self.matches: Dict[str, Match] = {}  # match_id -> Match
        self.created_at = datetime.now()
        self.started_at = None
        self.ended_at = None
        self.is_active = True
        self.bracket_channel_id = None
        self.announcement_channel_id = None
        self.admin_channel_id = None
        self.signup_channel_id = None
        self.rules_channel_id = None
        self.lobby_channel_id = None
        self.questions_channel_id = None
        self.category_id = None
        self.reminders = []  # List of scheduled reminder times
        self.winner_id = None
    
    def add_team(self, team: Team) -> str:
        """Add a team to the tournament and return team ID"""
        self.teams[team.id] = team
        return team.id
    
    def get_team(self, team_id: str) -> Optional[Team]:
        """Get a team by ID"""
        return self.teams.get(team_id)
    
    def get_team_by_name(self, team_name: str) -> Optional[Team]:
        """Get a team by name (only returns approved or pending teams)"""
        for team in self.teams.values():
            # Only consider approved or pending teams
            if team.status != TeamStatus.DENIED and team.name.lower() == team_name.lower():
                return team
        return None
    
    def get_player_team(self, user_id: int) -> Optional[Team]:
        """Get the team a player is on (only returns approved or pending teams)"""
        for team in self.teams.values():
            # Only consider approved or pending teams
            if team.status != TeamStatus.DENIED:
                if any(p.user_id == user_id for p in team.players):
                    return team
        return None
    
    def is_player_registered(self, user_id: int) -> bool:
        """Check if a player is already in any APPROVED or PENDING team"""
        for team in self.teams.values():
            # Only consider players in approved or pending teams as "registered"
            if team.status != TeamStatus.DENIED:
                for player in team.players:
                    if player.user_id == user_id:
                        return True
        return False
    
    def approve_team(self, team_id: str) -> bool:
        """Approve a team for participation"""
        if team_id in self.teams:
            self.teams[team_id].status = TeamStatus.APPROVED
            return True
        return False
    
    def deny_team(self, team_id: str, reason: str) -> bool:
        """Deny a team from participating"""
        if team_id in self.teams:
            self.teams[team_id].status = TeamStatus.DENIED
            self.teams[team_id].denial_reason = reason
            return True
        return False
    
    def get_approved_teams(self) -> List[Team]:
        """Get all approved teams"""
        return [t for t in self.teams.values() if t.status == TeamStatus.APPROVED]
    
    def get_pending_teams(self) -> List[Team]:
        """Get all pending teams"""
        return [t for t in self.teams.values() if t.status == TeamStatus.PENDING]
    
    def calculate_seedings(self) -> None: # TODO maybe condense calculate_average_mmr into here
        """Calculate team seedings based on MMR"""
        approved_teams = self.get_approved_teams()
        
        # Sort teams by average MMR (highest to lowest)
        sorted_teams = sorted(
            approved_teams, 
            key=lambda t: t.calculate_average_mmr(), 
            reverse=True
        )
        
        # Assign seeding numbers (1 = highest seed)
        for i, team in enumerate(sorted_teams):
            team.seeding = i + 1
    
    def create_matches(self) -> List[Match]:
        """Create first round matches for the tournament"""
        approved_teams = self.get_approved_teams()
        
        # Calculate seedings first
        self.calculate_seedings()
        
        # Sort teams by seeding (lowest number = highest seed)
        sorted_teams = sorted(approved_teams, key=lambda t: t.seeding)
        
        new_matches = []
        
        # Create first round matches
        num_teams = len(sorted_teams)
        num_byes = 0
        
        # Calculate number of byes needed for the first round
        # to make the tournament bracket work properly
        next_power_of_2 = 1
        while next_power_of_2 < num_teams:
            next_power_of_2 *= 2
            
        num_byes = next_power_of_2 - num_teams
        
        # Create matches for first round
        match_number = 1
        team_index = 0
        
        while team_index < num_teams:
            # If odd number of teams left or we need to give byes,
            # give bye to highest seed
            if team_index == num_teams - 1 or num_byes > 0:
                # Create a "bye" match
                team = sorted_teams[team_index]
                match_id = f"match_{self.id}_{1}_{match_number}"
                
                # Create match with None as opponent, will be handled specially
                match = Match(match_id, team.id, None, 1, match_number)
                match.winner_id = team.id  # Auto-win
                match.status = MatchStatus.COMPLETED
                
                self.matches[match_id] = match
                new_matches.append(match)
                
                team_index += 1
                num_byes -= 1
            else:
                team1 = sorted_teams[team_index]
                team2 = sorted_teams[team_index + 1]
                
                match_id = f"match_{self.id}_{1}_{match_number}"
                match = Match(match_id, team1.id, team2.id, 1, match_number)
                
                self.matches[match_id] = match
                new_matches.append(match)
                
                team_index += 2
            
            match_number += 1
        
        return new_matches
    
    def get_matches_by_round(self, round_number: int) -> List[Match]:
        """Get all matches for a specific round"""
        return [m for m in self.matches.values() if m.round_number == round_number]