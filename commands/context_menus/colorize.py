from discord import app_commands, Interaction, Message
from views.chroma_view import SelectionView

@app_commands.context_menu(name="Colorize")
async def colorize_context_menu(
    interaction: Interaction, 
    message: Message
):
    """
    Context menu command that works on messages.
    Right-click on a message -> Apps -> Colorize.
    """
    view = SelectionView(message.content if message.content else "Sample text")
    await interaction.response.send_message(
        content="Select below your format, background color, text color (and optionally, a mobile-friendly output), then click **Submit**.",
        view=view,
        ephemeral=True
    )
