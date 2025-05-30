from app.detectors.regex.patterns.base.patterns import Patterns

class UnsafePatterns(Patterns):
    @staticmethod
    def unsafe_patterns():
        return {
            "SSN (US)": {
                "pattern": r"\b\d{3}-\d{2}-\d{4}\b",
                "safe_to_mask": False,
                "safety_level": "unsafe",
                "confidence": 85,
            },
            "MAC Address": {
                "pattern": r"\b([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b",
                "safe_to_mask": False,
                "safety_level": "unsafe",
            },
            "Full Name": {
                "pattern": r"\b([A-Z][a-z]+)\s([A-Z][a-z]+)(\s[A-Z][a-z]+)?\b",
                "safe_to_mask": False,
                "safety_level": "unsafe",
            },
            "Passport Number (India)": {
                "pattern": r"\b[A-PR-WY][0-9]{7}\b",
                "safe_to_mask": False,
                "safety_level": "unsafe",
            },
            "India PAN": {
                "pattern": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
                "safe_to_mask": False,
                "safety_level": "unsafe",
            },
            "UUID": {
                "pattern": r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b",
                "safe_to_mask": True,
                "safety_level": "unsafe",
            },
            "IPv4 Address": {
                "pattern": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
                "safe_to_mask": True,
                "safety_level": "unsafe",
                "confidence": 80,
            },
            "URL": {
                "pattern": r"\bhttps?://[^\s]+\b",
                "safe_to_mask": True,
                "safety_level": "unsafe",
                "confidence": 75,
            },
        }

    @classmethod
    def get_patterns(cls):
        return cls.unsafe_patterns()
