"""Presidio-based PII detector with enhanced recognizers."""

from typing import List, Dict, Any, Optional
import logging
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine

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


class PresidioPIIDetector(BasePIIDetector):
    """Presidio-based PII detector with enhanced recognizers."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.analyzer = None
        self.anonymizer = None
        self.supported_languages = self.config.get("languages", ["en"])
        self.score_threshold = self.config.get("score_threshold", 0.35)
        
    def initialize(self) -> None:
        """Initialize Presidio analyzer and anonymizer."""
        try:
            # Use en_core_web_sm reliably - en_core_web_lg has static vectors issues
            nlp_configuration = {
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}]
            }
            
            # Create NLP engine
            nlp_engine_provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
            nlp_engine = nlp_engine_provider.create_engine()
            model_name = "en_core_web_sm"
            
            # Create analyzer with custom recognizers
            registry = RecognizerRegistry()
            registry.load_predefined_recognizers(nlp_engine=nlp_engine)
            
            # Add custom recognizers for enhanced detection
            self._add_custom_recognizers(registry, nlp_engine)
            
            # Initialize analyzer
            self.analyzer = AnalyzerEngine(
                registry=registry,
                nlp_engine=nlp_engine,
                supported_languages=self.supported_languages
            )
            
            # Initialize anonymizer
            self.anonymizer = AnonymizerEngine()
            
            self.is_initialized = True
            logger.info(f"Presidio PII detector initialized successfully with model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Presidio detector: {e}")
            raise
    
    def detect(self, text: str) -> List[PIIEntity]:
        """Detect PII entities using Presidio analyzer."""
        if not self.is_initialized:
            self.initialize()
        
        if not text or not text.strip():
            return []
        
        try:
            # Analyze text with Presidio
            results = self.analyzer.analyze(
                text=text,
                language="en",
                score_threshold=self.score_threshold
            )
            
            entities = []
            for result in results:
                entity_type = self._map_presidio_entity_type(result.entity_type)
                if entity_type:
                    entities.append(PIIEntity(
                        entity_type=entity_type,
                        text=text[result.start:result.end],
                        start=result.start,
                        end=result.end,
                        confidence=result.score,
                        source="presidio",
                        metadata={
                            "recognition_metadata": result.recognition_metadata,
                            "analysis_explanation": str(result.analysis_explanation) if result.analysis_explanation else None
                        }
                    ))
            
            return sorted(entities, key=lambda x: x.start)
            
        except Exception as e:
            logger.error(f"Error during Presidio analysis: {e}")
            return []
    
    def get_supported_entities(self) -> List[str]:
        """Get list of supported entity types."""
        return [
            "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD",
            "SSN", "IBAN_CODE", "IP_ADDRESS", "DATE_TIME", "LOCATION",
            "ORGANIZATION", "URL", "MEDICAL_LICENSE", "US_DRIVER_LICENSE",
            "US_PASSPORT", "CRYPTO"
        ]
    
    def get_model_info(self) -> Dict[str, str]:
        """Get Presidio model information."""
        if not self.is_initialized:
            return {"status": "not_initialized"}
        
        recognizers = []
        if self.analyzer and self.analyzer.registry:
            recognizers = [r.__class__.__name__ for r in self.analyzer.registry.recognizers]
        
        return {
            "engine": "presidio",
            "supported_languages": str(self.supported_languages),
            "score_threshold": str(self.score_threshold),
            "recognizers": str(recognizers)
        }
    
    def anonymize(self, text: str, entities: List[PIIEntity]) -> str:
        """Anonymize text using detected entities."""
        if not self.anonymizer:
            return text
        
        # Convert PIIEntity to Presidio RecognizerResult format
        presidio_results = []
        for entity in entities:
            from presidio_analyzer import RecognizerResult
            presidio_results.append(RecognizerResult(
                entity_type=entity.entity_type.value,
                start=entity.start,
                end=entity.end,
                score=entity.confidence
            ))
        
        try:
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=presidio_results
            )
            return anonymized_result.text
        except Exception as e:
            logger.error(f"Error during anonymization: {e}")
            return text
    
    def _add_custom_recognizers(self, registry: RecognizerRegistry, nlp_engine) -> None:
        """Add custom recognizers to enhance detection."""
        try:
            # Enhanced email recognizer
            from presidio_analyzer.predefined_recognizers import EmailRecognizer
            enhanced_email = EmailRecognizer()
            registry.add_recognizer(enhanced_email)
            
            # Enhanced phone recognizer
            from presidio_analyzer.predefined_recognizers import PhoneRecognizer
            enhanced_phone = PhoneRecognizer()
            registry.add_recognizer(enhanced_phone)
            
            # Enhanced credit card recognizer
            from presidio_analyzer.predefined_recognizers import CreditCardRecognizer
            enhanced_cc = CreditCardRecognizer()
            registry.add_recognizer(enhanced_cc)
            
            # Enhanced SSN recognizer - use custom implementation
            try:
                from presidio_analyzer.predefined_recognizers import UsSSNRecognizer
                enhanced_ssn = UsSSNRecognizer()
                registry.add_recognizer(enhanced_ssn)
            except ImportError:
                # Silently use custom SSN recognizer if UsSSNRecognizer is not available
                self._add_custom_ssn_recognizer(registry)
            
            # Enhanced IP address recognizer
            from presidio_analyzer.predefined_recognizers import IpRecognizer
            enhanced_ip = IpRecognizer()
            registry.add_recognizer(enhanced_ip)
            
            # Enhanced URL recognizer
            from presidio_analyzer.predefined_recognizers import UrlRecognizer
            enhanced_url = UrlRecognizer()
            registry.add_recognizer(enhanced_url)
            
            # Add custom crypto recognizer
            self._add_crypto_recognizer(registry)
            
            # Add custom medical license recognizer
            self._add_medical_license_recognizer(registry)
            
            logger.info("Custom recognizers added successfully")
            
        except Exception as e:
            logger.warning(f"Some custom recognizers could not be added: {e}")
            # Continue with basic functionality
    
    def _add_crypto_recognizer(self, registry: RecognizerRegistry) -> None:
        """Add cryptocurrency address recognizer."""
        try:
            from presidio_analyzer import Pattern, PatternRecognizer
            
            # Bitcoin address patterns
            bitcoin_patterns = [
                Pattern("Bitcoin Legacy", r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b", 0.8),
                Pattern("Bitcoin Bech32", r"\bbc1[a-z0-9]{39,59}\b", 0.8),
                Pattern("Bitcoin Segwit", r"\b3[a-km-zA-HJ-NP-Z1-9]{25,34}\b", 0.7),
            ]
            
            # Ethereum address pattern
            ethereum_patterns = [
                Pattern("Ethereum", r"\b0x[a-fA-F0-9]{40}\b", 0.8),
            ]
            
            crypto_recognizer = PatternRecognizer(
                supported_entity="CRYPTO",
                patterns=bitcoin_patterns + ethereum_patterns,
                name="CryptoRecognizer"
            )
            
            registry.add_recognizer(crypto_recognizer)
            
        except Exception as e:
            logger.warning(f"Could not add crypto recognizer: {e}")
    
    def _add_medical_license_recognizer(self, registry: RecognizerRegistry) -> None:
        """Add medical license recognizer."""
        try:
            from presidio_analyzer import Pattern, PatternRecognizer
            
            # Medical license patterns (simplified)
            medical_patterns = [
                Pattern("Medical License", r"\b[A-Z]{2}\d{4,8}\b", 0.6),
                Pattern("DEA Number", r"\b[A-Z]{2}\d{7}\b", 0.8),
                Pattern("NPI", r"\b\d{10}\b", 0.5),  # National Provider Identifier
            ]
            
            medical_recognizer = PatternRecognizer(
                supported_entity="MEDICAL_LICENSE",
                patterns=medical_patterns,
                name="MedicalLicenseRecognizer"
            )
            
            registry.add_recognizer(medical_recognizer)
            
        except Exception as e:
            logger.warning(f"Could not add medical license recognizer: {e}")
    
    def _add_custom_ssn_recognizer(self, registry: RecognizerRegistry) -> None:
        """Add custom SSN recognizer as fallback."""
        try:
            from presidio_analyzer import Pattern, PatternRecognizer
            
            # SSN patterns
            ssn_patterns = [
                Pattern("SSN with dashes", r"\b\d{3}-\d{2}-\d{4}\b", 0.8),
                Pattern("SSN with spaces", r"\b\d{3}\s\d{2}\s\d{4}\b", 0.8),
                Pattern("SSN without separators", r"\b\d{9}\b", 0.6),
            ]
            
            ssn_recognizer = PatternRecognizer(
                supported_entity="US_SSN",
                patterns=ssn_patterns,
                name="CustomSSNRecognizer"
            )
            
            registry.add_recognizer(ssn_recognizer)
            
        except Exception as e:
            logger.warning(f"Could not add custom SSN recognizer: {e}")
    
    def _map_presidio_entity_type(self, presidio_type: str) -> Optional[EntityType]:
        """Map Presidio entity types to our EntityType enum."""
        mapping = {
            "PERSON": EntityType.PERSON,
            "EMAIL_ADDRESS": EntityType.EMAIL_ADDRESS,
            "PHONE_NUMBER": EntityType.PHONE_NUMBER,
            "CREDIT_CARD": EntityType.CREDIT_CARD,
            "US_SSN": EntityType.SSN,
            "IBAN_CODE": EntityType.IBAN_CODE,
            "IP_ADDRESS": EntityType.IP_ADDRESS,
            "DATE_TIME": EntityType.DATE_TIME,
            "LOCATION": EntityType.LOCATION,
            "ORGANIZATION": EntityType.ORGANIZATION,
            "URL": EntityType.URL,
            "MEDICAL_LICENSE": EntityType.MEDICAL_LICENSE,
            "US_DRIVER_LICENSE": EntityType.US_DRIVER_LICENSE,
            "US_PASSPORT": EntityType.US_PASSPORT,
            "CRYPTO": EntityType.CRYPTO,
            # Additional Presidio types
            "US_BANK_NUMBER": EntityType.CREDIT_CARD,  # Map to credit card for now
            "AU_ABN": EntityType.ORGANIZATION,
            "AU_ACN": EntityType.ORGANIZATION,
            "AU_TFN": EntityType.SSN,  # Map to SSN equivalent
            "AU_MEDICARE": EntityType.MEDICAL_LICENSE,
            "UK_NHS": EntityType.MEDICAL_LICENSE,
            "ES_NIF": EntityType.SSN,
            "IT_FISCAL_CODE": EntityType.SSN,
            "IT_DRIVER_LICENSE": EntityType.US_DRIVER_LICENSE,
            "IT_VAT_CODE": EntityType.ORGANIZATION,
            "IT_PASSPORT": EntityType.US_PASSPORT,
            "IT_IDENTITY_CARD": EntityType.US_DRIVER_LICENSE,
        }
        return mapping.get(presidio_type) 