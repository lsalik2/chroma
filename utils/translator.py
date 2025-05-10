from googletrans import Translator

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