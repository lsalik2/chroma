from discord import app_commands

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