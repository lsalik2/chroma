from discord import ui, ButtonStyle, Interaction, SelectOption, app_commands, Message
from constants.ui import FORMAT_UI_OPTIONS, BACKGROUND_UI_OPTIONS, TEXT_UI_OPTIONS
from utils.ansi_format import build_ansi_response

class SelectionView(ui.View):
    """
    A View containing four dropdown selects for Format, Background color,
    Text color, and optional Mobile-friendly output, plus a Submit button.
    """
    def __init__(self, message_text: str):
        super().__init__(timeout=120)
        self.message_text = message_text
        
        # Default values (if user never picks anything)
        self.format_value = 0
        self.background_color_value = 40
        self.text_color_value = 32
        self.mobile_friendly_value = None

        self.add_item(FormatSelect(row=0))
        self.add_item(BackgroundColorSelect(row=1))
        self.add_item(TextColorSelect(row=2))
        self.add_item(MobileFriendlySelect(row=3))
    
    @ui.button(label="Submit", style=ButtonStyle.green, row=4)
    async def submit_button(self, interaction: Interaction, button: ui.Button):
        mobile_flag = (self.mobile_friendly_value == "yes")
        response = build_ansi_response(self.message_text, self.format_value, self.text_color_value, self.background_color_value, mobile_flag)
        await interaction.response.defer()
        await interaction.delete_original_response()
        await interaction.followup.send(content=response, ephemeral=True)
        self.stop()

class FormatSelect(ui.Select):
    def __init__(self, row: int = 0):
        super().__init__(
            placeholder="Pick a format...",
            min_values=1,
            max_values=1,
            options=FORMAT_UI_OPTIONS,
            row=row
        )
    
    async def callback(self, interaction: Interaction):
        parent_view = self.view
        if isinstance(parent_view, SelectionView):
            parent_view.format_value = int(self.values[0])
        await interaction.response.defer()

class BackgroundColorSelect(ui.Select):
    def __init__(self, row: int = 1):
        super().__init__(
            placeholder="Pick a background color...",
            min_values=1,
            max_values=1,
            options=BACKGROUND_UI_OPTIONS,
            row=row
        )
    
    async def callback(self, interaction: Interaction):
        parent_view = self.view
        if isinstance(parent_view, SelectionView):
            parent_view.background_color_value = int(self.values[0])
        await interaction.response.defer()

class TextColorSelect(ui.Select):
    def __init__(self, row: int = 2):
        super().__init__(
            placeholder="Pick a text color...",
            min_values=1,
            max_values=1,
            options=TEXT_UI_OPTIONS,
            row=row
        )
    
    async def callback(self, interaction: Interaction):
        parent_view = self.view
        if isinstance(parent_view, SelectionView):
            parent_view.text_color_value = int(self.values[0])
        await interaction.response.defer()

class MobileFriendlySelect(ui.Select):
    def __init__(self, row: int = 3):
        options = [
            SelectOption(label="Yes", value="yes")
        ]
        super().__init__(
            placeholder="Mobile-friendly output? (Optional)",
            min_values=0,
            max_values=1,
            options=options,
            row=row
        )
    
    async def callback(self, interaction: Interaction):
        parent_view = self.view
        if isinstance(parent_view, SelectionView) and self.values:
            parent_view.mobile_friendly_value = self.values[0]
        await interaction.response.defer()

def register_chroma_view(tree: app_commands.CommandTree):
    @tree.context_menu(name="Colorize")
    async def colorize_message(interaction: Interaction, message: Message):
        view = SelectionView(message.content or "Sample text")
        await interaction.response.send_message(
            content="Choose format, colors, and mobile output, then click **Submit**.",
            view=view,
            ephemeral=True
        )