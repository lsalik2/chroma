from discord import app_commands, Interaction, Embed, Color
from constants.options import LANGUAGE_OPTIONS
from utils.translator import translate_text

@app_commands.command(name="translate", description="🔡  Translate text to another language")
@app_commands.describe(
    text="The text to translate",
    language="The language to translate to"
)
@app_commands.choices(language=LANGUAGE_OPTIONS)
async def translate_command(
    interaction: Interaction, 
    text: str,
    language: app_commands.Choice[str]
):
    await interaction.response.defer(ephemeral=True)
    result = await translate_text(text, language.value)
    
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

def register_translate(tree):
    tree.add_command(translate_command)
