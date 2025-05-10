from .chroma_view import SelectionView, register_chroma_view
from .translate_view import register_translate_view

__all__ = ["SelectionView", "register_chroma_view", "register_translate_view"]

def setup_views(tree, client):
    register_chroma_view(tree)
    register_translate_view(tree)