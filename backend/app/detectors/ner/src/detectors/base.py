"""Base detector interface for PII detection."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
try:
    from ..models import PIIEntity, PIIDetectionResult
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from models import PIIEntity, PIIDetectionResult


class BasePIIDetector(ABC):
    """Abstract base class for PII detectors."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the detector with configuration."""
        self.config = config or {}
        self.is_initialized = False
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the detector (load models, etc.)."""
        pass
    
    @abstractmethod
    def detect(self, text: str) -> List[PIIEntity]:
        """Detect PII entities in the given text."""
        pass
    
    @abstractmethod
    def get_supported_entities(self) -> List[str]:
        """Get list of supported entity types."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        """Get information about the underlying model."""
        pass
    
    def batch_detect(self, texts: List[str]) -> List[List[PIIEntity]]:
        """Detect PII entities in multiple texts."""
        if not self.is_initialized:
            self.initialize()
        
        results = []
        for text in texts:
            entities = self.detect(text)
            results.append(entities)
        return results
    
    def __enter__(self):
        """Context manager entry."""
        if not self.is_initialized:
            self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass 