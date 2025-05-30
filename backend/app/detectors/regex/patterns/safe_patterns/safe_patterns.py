from app.detectors.regex.patterns.base.patterns import Patterns

class SafePatterns(Patterns):
    @staticmethod
    def static_safe_patterns():
        return {
            "Email": {
                "pattern": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}\b",
                "safe_to_mask": True,
                "safety_level": "safe_static",
            },
            "Phone Number (India)": {
                "pattern": r"\b(?:\+91[\-\s]?|91[\-\s]?|0)?[6-9]\d{9}\b",
                "safe_to_mask": True,
                "safety_level": "safe_static",
            },
            "Phone Number (US)": {
                "pattern": r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
                "safe_to_mask": True,
                "safety_level": "safe_static",
            },
            "Vehicle Registration (India)": {
                "pattern": r"\b[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}\b",
                "safe_to_mask": True,
                "safety_level": "safe_static",
            },
            "ISO 8601 Date": {
                "pattern": r"\b\d{4}-\d{2}-\d{2}\b",
                "safe_to_mask": True,
                "safety_level": "safe_static",
            }
        }

    @staticmethod
    def safe_validated_patterns():
        return {
            "Credit Card Number": {
                # Matches any 13-19 digit number with optional spaces/hyphens (more permissive)
                "pattern": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{1,7}\b",
                "safe_to_mask": True,
                "safety_level": "safe_validated", 
                "validation": "is_luhn_valid",
                "expected_length": None,  # Variable length
                "specificity": 25,  # Lower than Aadhaar to let Aadhaar win for 12-digit
            },
            "IBAN": {
                "pattern": r"\b[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b",
                "safe_to_mask": True,
                "safety_level": "safe_validated",
                "validation": "is_iban_valid",
            },
            "India Aadhaar": {
                # Made more specific - exactly 12 digits in 4-4-4 format
                "pattern": r"\b\d{4}\s\d{4}\s\d{4}\b",
                "safe_to_mask": False,
                "safety_level": "safe_validated",
                "validation": "is_verhoeff_valid",
                "expected_length": 12,  # Exactly 12 digits
                "specificity": 35,  # Higher specificity than credit card for 12-digit numbers
            },
            "SSN (Canada)": {
                "pattern": r"\b[1-9]{1}[0-9]{8}\b",
                "safe_to_mask": False,
                "safety_level": "safe_validated",
                "validation": "is_canadian_sin_valid",
            },
            "Bank Routing Number (US)": {
                "pattern": r"\b\d{9}\b",
                "safe_to_mask": False,
                "safety_level": "safe_validated",
                "validation": "is_us_routing_number_valid",
            },
            "India GSTIN": {
                "pattern": r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1}\b",
                "safe_to_mask": False,
                "safety_level": "safe_validated",
                "validation": "is_india_gstin_valid",
            },
        }

    @classmethod
    def get_patterns(cls):
         return {
            **cls.static_safe_patterns(),
            **cls.safe_validated_patterns(),
        }