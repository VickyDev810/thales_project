"""spaCy-based PII detector with custom patterns."""

import re
import spacy
from spacy.matcher import Matcher
from spacy.tokens import Span
from typing import List, Dict, Any, Optional
import logging

try:
    from .base import BasePIIDetector
    from ..models import PIIEntity, EntityType
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from detectors.base import BasePIIDetector
    from models import PIIEntity, EntityType


logger = logging.getLogger(__name__)


class SpacyPIIDetector(BasePIIDetector):
    """spaCy-based PII detector with enhanced pattern matching."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.nlp = None
        self.matcher = None
        self.custom_patterns = self._get_custom_patterns()
        
    def initialize(self) -> None:
        """Initialize spaCy model and custom patterns."""
        try:
            # Use en_core_web_sm reliably - en_core_web_lg has static vectors issues
            model_name = self.config.get("model", "en_core_web_sm")
            
            # Load the model with tok2vec disabled to avoid static vectors error
            try:
                self.nlp = spacy.load("en_core_web_sm", disable=["tok2vec"])
                logger.info(f"SpaCy PII detector initialized with model: en_core_web_sm (tok2vec disabled)")
            except Exception as e:
                # If disabling fails, load without disabling
                self.nlp = spacy.load("en_core_web_sm")
                logger.info(f"SpaCy PII detector initialized with model: en_core_web_sm")
            
            # Initialize matcher for pattern-based detection
            self.matcher = Matcher(self.nlp.vocab)
            self._add_custom_patterns()
            
            self.is_initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize spaCy detector: {e}")
            raise
    
    def detect(self, text: str) -> List[PIIEntity]:
        """Detect PII entities using spaCy NER and custom patterns."""
        if not self.is_initialized:
            self.initialize()
        
        if not text or not text.strip():
            return []
        
        doc = self.nlp(text)
        entities = []
        
        # Extract entities from spaCy NER
        for ent in doc.ents:
            entity_type = self._map_spacy_label(ent.label_)
            if entity_type:
                confidence = self._calculate_confidence(ent, doc)
                entities.append(PIIEntity(
                    entity_type=entity_type,
                    text=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=confidence,
                    source="spacy",
                    metadata={"label": ent.label_, "method": "ner"}
                ))
        
        # Extract entities from pattern matching
        matches = self.matcher(doc)
        for match_id, start, end in matches:
            span = doc[start:end]
            pattern_name = self.nlp.vocab.strings[match_id]
            entity_type = self._map_pattern_to_entity_type(pattern_name)
            
            if entity_type and not self._overlaps_with_existing(span, entities):
                confidence = self._calculate_pattern_confidence(span, pattern_name)
                entities.append(PIIEntity(
                    entity_type=entity_type,
                    text=span.text,
                    start=span.start_char,
                    end=span.end_char,
                    confidence=confidence,
                    source="spacy",
                    metadata={"pattern": pattern_name, "method": "pattern"}
                ))
        
        # Additional regex-based detection
        regex_entities = self._detect_with_regex(text)
        for entity in regex_entities:
            if not self._overlaps_with_existing_by_position(entity, entities):
                entities.append(entity)
        
        return sorted(entities, key=lambda x: x.start)
    
    def get_supported_entities(self) -> List[str]:
        """Get list of supported entity types."""
        return [
            "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD",
            "SSN", "IP_ADDRESS", "DATE_TIME", "LOCATION", "ORGANIZATION", "URL"
        ]
    
    def get_model_info(self) -> Dict[str, str]:
        """Get spaCy model information."""
        if not self.is_initialized:
            return {"status": "not_initialized"}
        
        return {
            "model": self.nlp.meta.get("name", "unknown"),
            "version": self.nlp.meta.get("version", "unknown"),
            "language": self.nlp.meta.get("lang", "unknown"),
            "pipeline": str(self.nlp.pipe_names)
        }
    
    def _get_custom_patterns(self) -> Dict[str, List[Dict]]:
        """Define custom patterns for PII detection."""
        return {
            "email": [
                {"LOWER": {"REGEX": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"}}
            ],
            "phone": [
                {"TEXT": {"REGEX": r"\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}"}}
            ],
            "ssn": [
                {"TEXT": {"REGEX": r"\b\d{3}-\d{2}-\d{4}\b"}}
            ],
            "credit_card": [
                {"TEXT": {"REGEX": r"\b(?:\d{4}[-\s]?){3}\d{4}\b"}}
            ],
            "ip_address": [
                {"TEXT": {"REGEX": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"}}
            ]
        }
    
    def _add_custom_patterns(self) -> None:
        """Add custom patterns to the matcher."""
        patterns = {
            "EMAIL": [
                [{"TEXT": {"REGEX": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"}}]
            ],
            "PHONE": [
                [{"TEXT": {"REGEX": r"\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}"}}]
            ],
            "SSN": [
                [{"TEXT": {"REGEX": r"\b\d{3}-\d{2}-\d{4}\b"}}],
                [{"TEXT": {"REGEX": r"\b\d{9}\b"}}]
            ],
            "CREDIT_CARD": [
                [{"TEXT": {"REGEX": r"\b(?:\d{4}[-\s]?){3}\d{4}\b"}}]
            ],
            "IP_ADDRESS": [
                [{"TEXT": {"REGEX": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"}}]
            ],
            "URL": [
                [{"TEXT": {"REGEX": r"https?://[^\s]+"}}]
            ]
        }
        
        for pattern_name, pattern_list in patterns.items():
            self.matcher.add(pattern_name, pattern_list)
    
    def _detect_with_regex(self, text: str) -> List[PIIEntity]:
        """Additional regex-based detection for complex patterns."""
        entities = []
        
        # Enhanced email detection
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            entities.append(PIIEntity(
                entity_type=EntityType.EMAIL_ADDRESS,
                text=match.group(),
                start=match.start(),
                end=match.end(),
                confidence=0.95,
                source="spacy",
                metadata={"method": "regex", "pattern": "email"}
            ))
        
        # Enhanced phone number detection
        phone_patterns = [
            r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        ]
        
        for pattern in phone_patterns:
            for match in re.finditer(pattern, text):
                entities.append(PIIEntity(
                    entity_type=EntityType.PHONE_NUMBER,
                    text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.9,
                    source="spacy",
                    metadata={"method": "regex", "pattern": "phone"}
                ))
        
        return entities
    
    def _map_spacy_label(self, label: str) -> Optional[EntityType]:
        """Map spaCy entity labels to our EntityType enum."""
        mapping = {
            "PERSON": EntityType.PERSON,
            "ORG": EntityType.ORGANIZATION,
            "GPE": EntityType.LOCATION,
            "LOC": EntityType.LOCATION,
            "DATE": EntityType.DATE_TIME,
            "TIME": EntityType.DATE_TIME,
            "MONEY": None,  # Not PII
            "PERCENT": None,  # Not PII
            "FACILITY": EntityType.LOCATION,
            "PRODUCT": None,  # Not PII
            "EVENT": None,  # Not PII
            "WORK_OF_ART": None,  # Not PII
            "LAW": None,  # Not PII
            "LANGUAGE": None,  # Not PII
            "NORP": None,  # Not PII
            "FAC": EntityType.LOCATION
        }
        return mapping.get(label)
    
    def _map_pattern_to_entity_type(self, pattern_name: str) -> Optional[EntityType]:
        """Map pattern names to entity types."""
        mapping = {
            "EMAIL": EntityType.EMAIL_ADDRESS,
            "PHONE": EntityType.PHONE_NUMBER,
            "SSN": EntityType.SSN,
            "CREDIT_CARD": EntityType.CREDIT_CARD,
            "IP_ADDRESS": EntityType.IP_ADDRESS,
            "URL": EntityType.URL
        }
        return mapping.get(pattern_name)
    
    def _calculate_confidence(self, ent: Span, doc) -> float:
        """Calculate confidence score for spaCy entities."""
        # Base confidence from spaCy
        base_confidence = 0.7
        
        # Adjust based on entity length
        if len(ent.text) > 2:
            base_confidence += 0.1
        
        # Adjust based on context
        if ent.label_ in ["PERSON", "ORG"]:
            # Check if it's capitalized properly
            if ent.text.istitle():
                base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _calculate_pattern_confidence(self, span: Span, pattern_name: str) -> float:
        """Calculate confidence for pattern-matched entities."""
        confidence_map = {
            "EMAIL": 0.95,
            "PHONE": 0.9,
            "SSN": 0.95,
            "CREDIT_CARD": 0.9,
            "IP_ADDRESS": 0.85,
            "URL": 0.9
        }
        return confidence_map.get(pattern_name, 0.8)
    
    def _overlaps_with_existing(self, span: Span, entities: List[PIIEntity]) -> bool:
        """Check if span overlaps with existing entities."""
        for entity in entities:
            if (span.start_char < entity.end and span.end_char > entity.start):
                return True
        return False
    
    def _overlaps_with_existing_by_position(self, new_entity: PIIEntity, entities: List[PIIEntity]) -> bool:
        """Check if new entity overlaps with existing entities by position."""
        for entity in entities:
            if (new_entity.start < entity.end and new_entity.end > entity.start):
                return True
        return False 