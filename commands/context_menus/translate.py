from discord import app_commands, Interaction, Message
from views.translate_view import TranslationView

@app_commands.context_menu(name="Translate")
async def translate_context_menu(
    interaction: Interaction,
    message: Message
):
    """
    Context menu command for translation.
    Right-click on a message -> Apps -> Translate.
    """
    view = TranslationView(message.content if message.content else "")
    await interaction.response.send_message(
        content="Select a language to translate to, then click **Submit**.",
        view=view,
        ephemeral=True
    )
