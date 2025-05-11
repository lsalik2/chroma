from enum import Enum

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