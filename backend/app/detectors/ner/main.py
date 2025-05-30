from .pii_detector import detect_pii_ensemble


def detect_with_ner(text: str):
    return detect_pii_ensemble(text)