from discord import app_commands, Interaction
from constants.options import FORMAT_OPTIONS, BACKGROUND_COLORS, TEXT_COLORS
from utils.ansi_format import build_ansi_response

@app_commands.command(name="chroma", description="🌈  Create a colorful ANSI code block")
@app_commands.describe(
    message="The message to colorize",
    format="Text formatting",
    background_color="Background color",
    text_color="Text color",
    mobile_friendly="Mobile-friendly output"
)
@app_commands.choices(
    format=FORMAT_OPTIONS,
    background_color=BACKGROUND_COLORS,
    text_color=TEXT_COLORS,
    mobile_friendly=[app_commands.Choice(name="Yes", value="yes")]
)
async def chroma_command(interaction: Interaction, message: str,
                            format: app_commands.Choice[int],
                            background_color: app_commands.Choice[int],
                            text_color: app_commands.Choice[int],
                            mobile_friendly: app_commands.Choice[str] = None):
    mobile = mobile_friendly and mobile_friendly.value == "yes"
    response = build_ansi_response(message, format.value, text_color.value, background_color.value, mobile)
    await interaction.response.send_message(response, ephemeral=True)

def register_chroma(tree):
    tree.add_command(chroma_command)
