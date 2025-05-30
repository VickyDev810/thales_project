"""Data models for PII detection system."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class EntityType(str, Enum):
    """Enumeration of supported PII entity types."""
    PERSON = "PERSON"
    EMAIL_ADDRESS = "EMAIL_ADDRESS"
    PHONE_NUMBER = "PHONE_NUMBER"
    CREDIT_CARD = "CREDIT_CARD"
    SSN = "SSN"
    IBAN_CODE = "IBAN_CODE"
    IP_ADDRESS = "IP_ADDRESS"
    DATE_TIME = "DATE_TIME"
    LOCATION = "LOCATION"
    ORGANIZATION = "ORGANIZATION"
    URL = "URL"
    MEDICAL_LICENSE = "MEDICAL_LICENSE"
    US_DRIVER_LICENSE = "US_DRIVER_LICENSE"
    US_PASSPORT = "US_PASSPORT"
    CRYPTO = "CRYPTO"


class PIIEntity(BaseModel):
    """Represents a detected PII entity."""
    
    entity_type: EntityType
    text: str
    start: int
    end: int
    confidence: float = Field(ge=0.0, le=1.0)
    source: str  # "spacy", "presidio", or "ensemble"
    metadata: Optional[Dict[str, Any]] = None
    
    def __str__(self) -> str:
        return f"{self.entity_type.value}: '{self.text}' ({self.confidence:.2f})"


class PIIDetectionResult(BaseModel):
    """Result of PII detection on a text."""
    
    original_text: str
    entities: List[PIIEntity]
    processing_time: float
    model_versions: Dict[str, str]
    
    @property
    def entity_count(self) -> int:
        """Total number of detected entities."""
        return len(self.entities)
    
    @property
    def entity_types_found(self) -> List[EntityType]:
        """List of unique entity types found."""
        return list(set(entity.entity_type for entity in self.entities))
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[PIIEntity]:
        """Get all entities of a specific type."""
        return [entity for entity in self.entities if entity.entity_type == entity_type]
    
    def get_high_confidence_entities(self, threshold: float = 0.8) -> List[PIIEntity]:
        """Get entities with confidence above threshold."""
        return [entity for entity in self.entities if entity.confidence >= threshold]


class BatchDetectionResult(BaseModel):
    """Result of batch PII detection."""
    
    results: List[PIIDetectionResult]
    total_processing_time: float
    batch_size: int
    
    @property
    def total_entities(self) -> int:
        """Total entities across all texts."""
        return sum(result.entity_count for result in self.results)
    
    @property
    def average_processing_time(self) -> float:
        """Average processing time per text."""
        return self.total_processing_time / len(self.results) if self.results else 0.0


class AnonymizationResult(BaseModel):
    """Result of text anonymization."""
    
    original_text: str
    anonymized_text: str
    entities_anonymized: List[PIIEntity]
    anonymization_mapping: Dict[str, str]  # original -> anonymized
    processing_time: float 