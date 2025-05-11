from discord.ui import Modal, TextInput

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