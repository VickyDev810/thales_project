"""Configuration settings for the PII detection system."""

from typing import List, Dict, Any
try:
    from pydantic import BaseSettings
except ImportError:
    from pydantic_settings import BaseSettings


class PIIDetectionConfig(BaseSettings):
    """Configuration for PII detection system."""
    
    # spaCy model configuration
    # Note: en_core_web_lg has static vectors compatibility issues with current setup
    # Using en_core_web_sm as it works reliably with all components
    SPACY_MODEL: str = "en_core_web_sm"  # Changed from en_core_web_lg due to static vectors error
    SPACY_CUSTOM_PATTERNS: bool = True
    
    # Presidio configuration
    PRESIDIO_SUPPORTED_LANGUAGES: List[str] = ["en"]
    PRESIDIO_SCORE_THRESHOLD: float = 0.35
    
    # Combined system configuration
    CONFIDENCE_THRESHOLD: float = 0.5
    ENSEMBLE_VOTING: str = "weighted"  # "majority", "weighted", "unanimous"
    
    # Entity types to detect
    ENTITY_TYPES: List[str] = [
        "PERSON",
        "EMAIL_ADDRESS", 
        "PHONE_NUMBER",
        "CREDIT_CARD",
        "SSN",
        "IBAN_CODE",
        "IP_ADDRESS",
        "DATE_TIME",
        "LOCATION",
        "ORGANIZATION",
        "URL",
        "MEDICAL_LICENSE",
        "US_DRIVER_LICENSE",
        "US_PASSPORT",
        "CRYPTO"
    ]
    
    # Performance settings
    BATCH_SIZE: int = 100
    MAX_TEXT_LENGTH: int = 1000000
    ENABLE_CACHING: bool = True
    
    # Model weights for ensemble
    SPACY_WEIGHT: float = 0.4
    PRESIDIO_WEIGHT: float = 0.6
    
    class Config:
        env_prefix = "PII_"


# Global configuration instance
config = PIIDetectionConfig() 