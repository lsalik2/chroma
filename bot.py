import os
import discord
import random
from discord import app_commands
from dotenv import load_dotenv
from googletrans import Translator

# --------------------- Section: Helper Functions ---------------------
def build_ansi_response(message: str, format_value: int, text_color_value: int, background_color_value: int, mobile_friendly: bool = False) -> str:
    """
    Build the ANSI formatted response.
    If mobile_friendly is True, only the raw ANSI code block is returned.
    Otherwise, a preview and a raw block for copy-pasting are provided.
    """
    ansi_code = f"\u001b[{format_value};{text_color_value};{background_color_value}m"
    reset_code = "\u001b[0m"
    if mobile_friendly:
        return f"```ansi\n{ansi_code}{message}{reset_code}\n```"
    else:
        return (
            "Here's your colorized message:\n"
            f"```ansi\n{ansi_code}{message}{reset_code}\n```\n"
            "Raw text for copy-pasting:\n"
            "\`\`\`ansi\n"
            f"{ansi_code}{message}{reset_code}\n"
            "\`\`\`"
        )

async def translate_text(text: str, dest_language: str) -> dict:
    """
    Translate text to the specified language and return result details.
    This is an async function that awaits the translation.
    """
    translator = Translator()
    try:
        # Properly await the translation as it's a coroutine
        result = await translator.translate(text, dest=dest_language)
        return {
            "success": True,
            "original_text": text,
            "translated_text": result.text,
            "src_language": result.src,
            "dest_language": result.dest
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "original_text": text
        }
    
def randomize_format(message: str, mobile_friendly: bool = False) -> str:
    '''
    Randomizes the ANSI formatted response.
    If mobile_friendly is True, only the raw ANSI code block is returned.
    Otherwise, a preview and a raw block for copy-pasting are provided.
    '''
    format_value = random.choice([0, 1, 4])
    text_color_value = random.choice([31, 32, 33, 34, 35, 36, 37])
    background_color_value = random.choice([40, 41, 42, 43, 44, 45, 46, 47])

    ansi_code = f"\u001b[{format_value};{text_color_value};{background_color_value}m"
    reset_code = "\u001b[0m"
    if mobile_friendly:
        return f"```ansi\n{ansi_code}{message}{reset_code}\n```"
    else:
        return (
            "Here's your colorized message:\n"
            f"```ansi\n{ansi_code}{message}{reset_code}\n```\n"
            "Raw text for copy-pasting:\n"
            "\`\`\`ansi\n"
            f"{ansi_code}{message}{reset_code}\n"
            "\`\`\`"
        )

# --------------------- Section: Options Choices ---------------------
FORMAT_OPTIONS = [
    app_commands.Choice(name="Normal", value=0),
    app_commands.Choice(name="Bold", value=1),
    app_commands.Choice(name="Underline", value=4)
]

BACKGROUND_COLORS = [
    app_commands.Choice(name="Dark Blue", value=40),
    app_commands.Choice(name="Dark Grey", value=42),
    app_commands.Choice(name="Grey", value=43),
    app_commands.Choice(name="Indigo", value=45),
    app_commands.Choice(name="Light Grey", value=44),
    app_commands.Choice(name="Orange", value=41),
    app_commands.Choice(name="Silver", value=46),
    app_commands.Choice(name="White", value=47)
]

TEXT_COLORS = [
    app_commands.Choice(name="Blue", value=34),
    app_commands.Choice(name="Cyan", value=36),
    app_commands.Choice(name="Green", value=32),
    app_commands.Choice(name="Grey", value=30),
    app_commands.Choice(name="Pink", value=35),
    app_commands.Choice(name="Red", value=31),
    app_commands.Choice(name="White", value=37),
    app_commands.Choice(name="Yellow", value=33)
]

LANGUAGE_OPTIONS = [
    app_commands.Choice(name="English", value="en"),
    app_commands.Choice(name="Spanish", value="es"),
    app_commands.Choice(name="French", value="fr"),
    app_commands.Choice(name="German", value="de"),
    app_commands.Choice(name="Italian", value="it"),
    app_commands.Choice(name="Portuguese", value="pt"),
    app_commands.Choice(name="Russian", value="ru"),
    app_commands.Choice(name="Japanese", value="ja"),
    app_commands.Choice(name="Chinese (Simplified)", value="zh-cn"),
    app_commands.Choice(name="Arabic", value="ar")
]

FORMAT_UI_OPTIONS = [
    discord.SelectOption(label="Normal", value="0", description="No special formatting"),
    discord.SelectOption(label="Bold", value="1", description="Bold text"),
    discord.SelectOption(label="Underline", value="4", description="Underlined text")
]

BACKGROUND_UI_OPTIONS = [
    discord.SelectOption(label="Dark Blue", value="40"),
    discord.SelectOption(label="Dark Grey", value="42"),
    discord.SelectOption(label="Grey", value="43"),
    discord.SelectOption(label="Indigo", value="45"),
    discord.SelectOption(label="Light Grey", value="44"),
    discord.SelectOption(label="Orange", value="41"),
    discord.SelectOption(label="Silver", value="46"),
    discord.SelectOption(label="White", value="47")
]

TEXT_UI_OPTIONS = [
    discord.SelectOption(label="Blue", value="34"),
    discord.SelectOption(label="Cyan", value="36"),
    discord.SelectOption(label="Green", value="32"),
    discord.SelectOption(label="Grey", value="30"),
    discord.SelectOption(label="Pink", value="35"),
    discord.SelectOption(label="Red", value="31"),
    discord.SelectOption(label="White", value="37"),
    discord.SelectOption(label="Yellow", value="33")
]

LANGUAGE_UI_OPTIONS = [
    discord.SelectOption(label="English", value="en"),
    discord.SelectOption(label="Spanish", value="es"),
    discord.SelectOption(label="French", value="fr"),
    discord.SelectOption(label="German", value="de"),
    discord.SelectOption(label="Italian", value="it"),
    discord.SelectOption(label="Portuguese", value="pt"),
    discord.SelectOption(label="Russian", value="ru"),
    discord.SelectOption(label="Japanese", value="ja"),
    discord.SelectOption(label="Chinese (Simplified)", value="zh-cn"),
    discord.SelectOption(label="Arabic", value="ar")
]

# --------------------- Section: Setup and Intents ---------------------
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# --------------------- Section: Start-up Functions and Debugs ---------------------
@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    try:
        print("Syncing commands globally...")
        await tree.sync()
        print("Command sync completed successfully")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    activity = discord.Activity(
        type=discord.ActivityType.listening, 
        name="/rv_chroma_test"
    )
    await client.change_presence(activity=activity)
    print('Bot is ready!')

# --------------------- Section: /chroma Command ---------------------
@tree.command(name="chroma", description="Create a colorful ANSI code block")
@app_commands.describe(
    message="The message to colorize",
    format="Text formatting",
    background_color="The background color",
    text_color="The color of the text",
    mobile_friendly="Mobile-friendly copy-paste output"
)
@app_commands.choices(
    format=FORMAT_OPTIONS,
    background_color=BACKGROUND_COLORS,
    text_color=TEXT_COLORS,
    mobile_friendly=[app_commands.Choice(name="Yes", value="yes")]
)
async def chroma_command(
    interaction: discord.Interaction, 
    message: str, 
    format: app_commands.Choice[int],
    background_color: app_commands.Choice[int],
    text_color: app_commands.Choice[int],
    mobile_friendly: app_commands.Choice[str] = None
):
    mobile_flag = (mobile_friendly is not None and mobile_friendly.value == "yes")
    response = build_ansi_response(message, format.value, text_color.value, background_color.value, mobile_flag)
    await interaction.response.send_message(response, ephemeral=True)

# --------------------- Section: /translate Command ---------------------
@tree.command(name="translate", description="Translate text to another language")
@app_commands.describe(
    text="The text to translate",
    language="The language to translate to"
)
@app_commands.choices(language=LANGUAGE_OPTIONS)
async def translate_command(
    interaction: discord.Interaction, 
    text: str,
    language: app_commands.Choice[str]
):
    await interaction.response.defer(ephemeral=True)
    result = await translate_text(text, language.value)
    
    if result["success"]:
        detected_language = result["src_language"]
        target_language = result["dest_language"]
        
        embed = discord.Embed(
            title="Translation",
            color=discord.Color.blue()
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

# --------------------- Section: Randomize Format ---------------------
@tree.command(name="randomize", description="Generate random colorful ANSI code block")
@app_commands.describe(
    message="The message to colorize",
    mobile_friendly="Mobile-friendly copy-paste output")

@app_commands.choices(
    mobile_friendly=[app_commands.Choice(name="Yes", value="yes")])

async def randomize_command(
    interaction: discord.Interaction, 
    message: str, 
    mobile_friendly: app_commands.Choice[str] = None
    ):
    mobile_flag = (mobile_friendly is not None and mobile_friendly.value == "yes")
    response = randomize_format(message, mobile_flag)
    await interaction.response.send_message(response, ephemeral=True)

# --------------------- Section: Colorize Context Menu ---------------------
@tree.context_menu(name="Colorize")
async def colorize_context_menu(
    interaction: discord.Interaction, 
    message: discord.Message
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

# --------------------- Section: Translate Context Menu ---------------------
@tree.context_menu(name="Translate")
async def translate_context_menu(
    interaction: discord.Interaction,
    message: discord.Message
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

# --------------------- Section: Colorize Custom View ---------------------
class SelectionView(discord.ui.View):
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
    
    @discord.ui.button(label="Submit", style=discord.ButtonStyle.green, row=4)
    async def submit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        mobile_flag = (self.mobile_friendly_value == "yes")
        response = build_ansi_response(self.message_text, self.format_value, self.text_color_value, self.background_color_value, mobile_flag)
        await interaction.response.defer()
        await interaction.delete_original_response()
        await interaction.followup.send(content=response, ephemeral=True)
        self.stop()

class FormatSelect(discord.ui.Select):
    def __init__(self, row: int = 0):
        super().__init__(
            placeholder="Pick a format...",
            min_values=1,
            max_values=1,
            options=FORMAT_UI_OPTIONS,
            row=row
        )
    
    async def callback(self, interaction: discord.Interaction):
        parent_view = self.view
        if isinstance(parent_view, SelectionView):
            parent_view.format_value = int(self.values[0])
        await interaction.response.defer()

class BackgroundColorSelect(discord.ui.Select):
    def __init__(self, row: int = 1):
        super().__init__(
            placeholder="Pick a background color...",
            min_values=1,
            max_values=1,
            options=BACKGROUND_UI_OPTIONS,
            row=row
        )
    
    async def callback(self, interaction: discord.Interaction):
        parent_view = self.view
        if isinstance(parent_view, SelectionView):
            parent_view.background_color_value = int(self.values[0])
        await interaction.response.defer()

class TextColorSelect(discord.ui.Select):
    def __init__(self, row: int = 2):
        super().__init__(
            placeholder="Pick a text color...",
            min_values=1,
            max_values=1,
            options=TEXT_UI_OPTIONS,
            row=row
        )
    
    async def callback(self, interaction: discord.Interaction):
        parent_view = self.view
        if isinstance(parent_view, SelectionView):
            parent_view.text_color_value = int(self.values[0])
        await interaction.response.defer()

class MobileFriendlySelect(discord.ui.Select):
    def __init__(self, row: int = 3):
        options = [
            discord.SelectOption(label="Yes", value="yes")
        ]
        super().__init__(
            placeholder="Mobile-friendly output? (Optional)",
            min_values=0,
            max_values=1,
            options=options,
            row=row
        )
    
    async def callback(self, interaction: discord.Interaction):
        parent_view = self.view
        if isinstance(parent_view, SelectionView) and self.values:
            parent_view.mobile_friendly_value = self.values[0]
        await interaction.response.defer()

# --------------------- Section: Translate Custom View ---------------------
class TranslationView(discord.ui.View):
    """
    A View containing a language dropdown select and a Submit button.
    """
    def __init__(self, message_text: str):
        super().__init__(timeout=120)
        self.message_text = message_text
        
        # Default target language
        self.target_language = "en"
        
        self.add_item(LanguageSelect(row=0))
    
    @discord.ui.button(label="Submit", style=discord.ButtonStyle.green, row=1)
    async def submit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        # Await the translation
        result = await translate_text(self.message_text, self.target_language)
        
        # Delete the original response (the selection UI)
        await interaction.delete_original_response()
        
        if result["success"]:
            detected_language = result["src_language"]
            target_language = result["dest_language"]
            
            embed = discord.Embed(
                title="Translation",
                color=discord.Color.blue()
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

class LanguageSelect(discord.ui.Select):
    def __init__(self, row: int = 0):
        super().__init__(
            placeholder="Select a language to translate to...",
            min_values=1,
            max_values=1,
            options=LANGUAGE_UI_OPTIONS,
            row=row
        )

    async def callback(self, interaction: discord.Interaction):
        parent_view = self.view
        if isinstance(parent_view, TranslationView):
            parent_view.target_language = self.values[0]
        await interaction.response.defer()

# --------------------- Section: Token Loading ---------------------
def main():
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables")
        return
    
    client.run(token)

if __name__ == "__main__":
    main()