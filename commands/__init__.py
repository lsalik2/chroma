from .chroma import register_chroma
from .translate import register_translate
from .randomize import register_randomize

def setup_commands(tree):
    register_chroma(tree)
    register_translate(tree)
    register_randomize(tree)