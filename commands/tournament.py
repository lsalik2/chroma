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