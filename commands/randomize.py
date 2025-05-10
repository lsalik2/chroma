from discord import app_commands, Interaction, Embed, Color
from utils.ansi_format import randomize_format

@app_commands.command(name="random", description="🪅  Generate random colorful ANSI code block")
@app_commands.describe(
    message="The message to colorize",
    mobile_friendly="Mobile-friendly copy-paste output")
@app_commands.choices(
    mobile_friendly=[app_commands.Choice(name="Yes", value="yes")])
async def randomize_command(
    interaction: Interaction, 
    message: str, 
    mobile_friendly: app_commands.Choice[str] = None
    ):
    mobile_flag = (mobile_friendly is not None and mobile_friendly.value == "yes")
    response = randomize_format(message, mobile_flag)
    await interaction.response.send_message(response, ephemeral=True)

def register_randomize(tree):
    tree.add_command(randomize_command)