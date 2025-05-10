from random import choice

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

def randomize_format(message: str, mobile_friendly: bool = False) -> str:
    '''
    Randomizes the ANSI formatted response.
    If mobile_friendly is True, only the raw ANSI code block is returned.
    Otherwise, a preview and a raw block for copy-pasting are provided.
    '''
    format_value = choice([0, 1, 4])
    text_color_value = choice([31, 32, 33, 34, 35, 36, 37])
    background_color_value = choice([40, 41, 42, 43, 44, 45, 46, 47])

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