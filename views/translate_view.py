from discord import ui, ButtonStyle, Interaction, Embed, Color, app_commands, Message
from constants.ui import LANGUAGE_UI_OPTIONS
from utils.translator import translate_text

class TranslationView(ui.View):
    """
    A View containing a language dropdown select and a Submit button.
    """
    def __init__(self, message_text: str):
        super().__init__(timeout=120)
        self.message_text = message_text
        
        # Default target language
        self.target_language = "en"
        
        self.add_item(LanguageSelect(row=0))
    
    @ui.button(label="Submit", style=ButtonStyle.green, row=1)
    async def submit_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        # Await the translation
        result = await translate_text(self.message_text, self.target_language)
        
        # Delete the original response (the selection UI)
        await interaction.delete_original_response()
        
        if result["success"]:
            detected_language = result["src_language"]
            target_language = result["dest_language"]
            
            embed = Embed(
                title="Translation",
                color=Color.blue()
            )
            embed.add_field(
                name=f"Original ({detected_language})",
                value=result["original_text"],
                inline=False
            )
            embed.add_field(
                name=f"Translation ({target_language})",
                value=result["translated_text"],
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(
                f"Error translating: {result['error']}",
                ephemeral=True
            )
        self.stop()

class LanguageSelect(ui.Select):
    def __init__(self, row: int = 0):
        super().__init__(
            placeholder="Select a language to translate to...",
            min_values=1,
            max_values=1,
            options=LANGUAGE_UI_OPTIONS,
            row=row
        )

    async def callback(self, interaction: Interaction):
        parent_view = self.view
        if isinstance(parent_view, TranslationView):
            parent_view.target_language = self.values[0]
        await interaction.response.defer()

def register_translate_view(tree: app_commands.CommandTree):
    @tree.context_menu(name="Translate")
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