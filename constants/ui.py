from discord import SelectOption

FORMAT_UI_OPTIONS = [
    SelectOption(label="Normal", value="0", description="No special formatting"),
    SelectOption(label="Bold", value="1", description="Bold text"),
    SelectOption(label="Underline", value="4", description="Underlined text")
]

BACKGROUND_UI_OPTIONS = [
    SelectOption(label="Dark Blue", value="40"),
    SelectOption(label="Dark Grey", value="42"),
    SelectOption(label="Grey", value="43"),
    SelectOption(label="Indigo", value="45"),
    SelectOption(label="Light Grey", value="44"),
    SelectOption(label="Orange", value="41"),
    SelectOption(label="Silver", value="46"),
    SelectOption(label="White", value="47")
]

TEXT_UI_OPTIONS = [
    SelectOption(label="Blue", value="34"),
    SelectOption(label="Cyan", value="36"),
    SelectOption(label="Green", value="32"),
    SelectOption(label="Grey", value="30"),
    SelectOption(label="Pink", value="35"),
    SelectOption(label="Red", value="31"),
    SelectOption(label="White", value="37"),
    SelectOption(label="Yellow", value="33")
]

LANGUAGE_UI_OPTIONS = [
    SelectOption(label="English", value="en"),
    SelectOption(label="Spanish", value="es"),
    SelectOption(label="French", value="fr"),
    SelectOption(label="German", value="de"),
    SelectOption(label="Italian", value="it"),
    SelectOption(label="Portuguese", value="pt"),
    SelectOption(label="Russian", value="ru"),
    SelectOption(label="Japanese", value="ja"),
    SelectOption(label="Chinese (Simplified)", value="zh-cn"),
    SelectOption(label="Arabic", value="ar")
]