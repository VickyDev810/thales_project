from .llm import get_response

def detect_with_llm(text: str):
    return get_response(text)