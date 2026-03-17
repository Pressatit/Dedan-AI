
import re

GREETINGS = {
    "hi", "hello", "hey", "yo",
    "good morning", "good afternoon", "good evening",
    "sup", "what's up", "whats up"
}

def is_low_signal(text: str) -> bool:
    text = text.lower().strip()

    # very short
    if len(text) < 8:
        return True

    # exact greetings
    if text in GREETINGS:
        return True

    # greetings with punctuation
    if re.fullmatch(r"(hi|hello|hey)[!. ]*", text):
        return True

    return False


def generate_conversation_title(text: str) -> str | None:
    """
    Returns None if title should NOT be generated yet
    """
    text = text.strip()

    if is_low_signal(text):
        return None

    # If message is short but meaningful, keep it
    if len(text) <= 40:
        return text

    words = text.split()
    return " ".join(words[:6]) + "..."