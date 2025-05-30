from app.detectors.regex.utils.pii_detector import PIIDetector
from .utils.pii_detector import PIIDetector

def detect_with_regex(text: str):
    detector = PIIDetector()
    patterns = detector.detect_all(text)
    return patterns


