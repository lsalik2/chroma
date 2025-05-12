from .chroma import register_chroma
from .translate import register_translate
from .randomize import register_randomize
from .tournament import register_tournament
from .admin import register_admin

def setup_commands(tree):
    register_chroma(tree)
    register_translate(tree)
    register_randomize(tree)
    register_tournament(tree)
    register_admin(tree)