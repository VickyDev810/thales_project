"""Ensemble PII detector combining spaCy and Presidio for optimal accuracy."""

import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

try:
    from .detectors.spacy_detector import SpacyPIIDetector
    from .detectors.presidio_detector import PresidioPIIDetector
    from .models import PIIEntity, PIIDetectionResult, BatchDetectionResult, EntityType
    from .config import config
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from detectors.spacy_detector import SpacyPIIDetector
    from detectors.presidio_detector import PresidioPIIDetector
    from models import PIIEntity, PIIDetectionResult, BatchDetectionResult, EntityType
    from config import config


logger = logging.getLogger(__name__)


class EnsemblePIIDetector:
    """Ensemble PII detector combining spaCy and Presidio."""
    
    def __init__(self, custom_config: Dict[str, Any] = None):
        """Initialize ensemble detector with configuration."""
        self.config = custom_config or {}
        self.spacy_detector = None
        self.presidio_detector = None
        self.is_initialized = False
        
        # Ensemble configuration
        self.voting_strategy = self.config.get("voting_strategy", config.ENSEMBLE_VOTING)
        self.confidence_threshold = self.config.get("confidence_threshold", config.CONFIDENCE_THRESHOLD)
        self.spacy_weight = self.config.get("spacy_weight", config.SPACY_WEIGHT)
        self.presidio_weight = self.config.get("presidio_weight", config.PRESIDIO_WEIGHT)
        
        # Performance settings
        self.enable_parallel = self.config.get("enable_parallel", True)
        self.max_workers = self.config.get("max_workers", 2)
        
    def initialize(self) -> None:
        """Initialize both detectors."""
        try:
            start_time = time.time()
            
            # Initialize spaCy detector
            spacy_config = self.config.get("spacy", {})
            spacy_config["model"] = spacy_config.get("model", config.SPACY_MODEL)
            self.spacy_detector = SpacyPIIDetector(spacy_config)
            
            # Initialize Presidio detector
            presidio_config = self.config.get("presidio", {})
            presidio_config["languages"] = presidio_config.get("languages", config.PRESIDIO_SUPPORTED_LANGUAGES)
            presidio_config["score_threshold"] = presidio_config.get("score_threshold", config.PRESIDIO_SCORE_THRESHOLD)
            self.presidio_detector = PresidioPIIDetector(presidio_config)
            
            # Initialize detectors
            if self.enable_parallel:
                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = [
                        executor.submit(self.spacy_detector.initialize),
                        executor.submit(self.presidio_detector.initialize)
                    ]
                    for future in as_completed(futures):
                        future.result()  # This will raise any exceptions
            else:
                self.spacy_detector.initialize()
                self.presidio_detector.initialize()
            
            self.is_initialized = True
            init_time = time.time() - start_time
            logger.info(f"Ensemble PII detector initialized in {init_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Failed to initialize ensemble detector: {e}")
            raise
    
    def detect(self, text: str) -> PIIDetectionResult:
        """Detect PII entities using ensemble approach."""
        if not self.is_initialized:
            self.initialize()
        
        start_time = time.time()
        
        if not text or not text.strip():
            return PIIDetectionResult(
                original_text=text,
                entities=[],
                processing_time=time.time() - start_time,
                model_versions=self._get_model_versions()
            )
        
        try:
            # Run both detectors
            if self.enable_parallel:
                spacy_entities, presidio_entities = self._detect_parallel(text)
            else:
                spacy_entities = self.spacy_detector.detect(text)
                presidio_entities = self.presidio_detector.detect(text)
            
            # Combine results using ensemble strategy
            combined_entities = self._combine_entities(spacy_entities, presidio_entities)
            
            # Filter by confidence threshold
            filtered_entities = [
                entity for entity in combined_entities 
                if entity.confidence >= self.confidence_threshold
            ]
            
            processing_time = time.time() - start_time
            
            return PIIDetectionResult(
                original_text=text,
                entities=filtered_entities,
                processing_time=processing_time,
                model_versions=self._get_model_versions()
            )
            
        except Exception as e:
            logger.error(f"Error during ensemble detection: {e}")
            return PIIDetectionResult(
                original_text=text,
                entities=[],
                processing_time=time.time() - start_time,
                model_versions=self._get_model_versions()
            )
    
    def batch_detect(self, texts: List[str]) -> BatchDetectionResult:
        """Detect PII entities in multiple texts."""
        if not self.is_initialized:
            self.initialize()
        
        start_time = time.time()
        results = []
        
        for text in texts:
            result = self.detect(text)
            results.append(result)
        
        total_time = time.time() - start_time
        
        return BatchDetectionResult(
            results=results,
            total_processing_time=total_time,
            batch_size=len(texts)
        )
    
    def get_supported_entities(self) -> List[str]:
        """Get list of all supported entity types."""
        if not self.is_initialized:
            self.initialize()
        
        spacy_entities = set(self.spacy_detector.get_supported_entities())
        presidio_entities = set(self.presidio_detector.get_supported_entities())
        
        return sorted(list(spacy_entities.union(presidio_entities)))
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about both models."""
        if not self.is_initialized:
            return {"status": "not_initialized"}
        
        return {
            "ensemble_config": {
                "voting_strategy": self.voting_strategy,
                "confidence_threshold": self.confidence_threshold,
                "spacy_weight": self.spacy_weight,
                "presidio_weight": self.presidio_weight,
                "parallel_processing": self.enable_parallel
            },
            "spacy": self.spacy_detector.get_model_info(),
            "presidio": self.presidio_detector.get_model_info()
        }
    
    def _detect_parallel(self, text: str) -> Tuple[List[PIIEntity], List[PIIEntity]]:
        """Run both detectors in parallel."""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            spacy_future = executor.submit(self.spacy_detector.detect, text)
            presidio_future = executor.submit(self.presidio_detector.detect, text)
            
            spacy_entities = spacy_future.result()
            presidio_entities = presidio_future.result()
            
        return spacy_entities, presidio_entities
    
    def _combine_entities(self, spacy_entities: List[PIIEntity], presidio_entities: List[PIIEntity]) -> List[PIIEntity]:
        """Combine entities from both detectors using ensemble strategy."""
        if self.voting_strategy == "majority":
            return self._majority_voting(spacy_entities, presidio_entities)
        elif self.voting_strategy == "weighted":
            return self._weighted_voting(spacy_entities, presidio_entities)
        elif self.voting_strategy == "unanimous":
            return self._unanimous_voting(spacy_entities, presidio_entities)
        else:
            # Default to union of all entities
            return self._union_entities(spacy_entities, presidio_entities)
    
    def _majority_voting(self, spacy_entities: List[PIIEntity], presidio_entities: List[PIIEntity]) -> List[PIIEntity]:
        """Combine entities using majority voting (at least one detector agrees)."""
        return self._union_entities(spacy_entities, presidio_entities)
    
    def _weighted_voting(self, spacy_entities: List[PIIEntity], presidio_entities: List[PIIEntity]) -> List[PIIEntity]:
        """Combine entities using weighted voting."""
        combined = []
        all_entities = spacy_entities + presidio_entities
        
        # Group overlapping entities
        entity_groups = self._group_overlapping_entities(all_entities)
        
        for group in entity_groups:
            if len(group) == 1:
                # Single entity, keep as is
                combined.append(group[0])
            else:
                # Multiple overlapping entities, combine with weighted average
                combined_entity = self._merge_entities_weighted(group)
                combined.append(combined_entity)
        
        return combined
    
    def _unanimous_voting(self, spacy_entities: List[PIIEntity], presidio_entities: List[PIIEntity]) -> List[PIIEntity]:
        """Combine entities using unanimous voting (both detectors must agree)."""
        combined = []
        
        for spacy_entity in spacy_entities:
            for presidio_entity in presidio_entities:
                if self._entities_overlap(spacy_entity, presidio_entity):
                    # Entities overlap, combine them
                    merged = self._merge_two_entities(spacy_entity, presidio_entity)
                    combined.append(merged)
        
        return combined
    
    def _union_entities(self, spacy_entities: List[PIIEntity], presidio_entities: List[PIIEntity]) -> List[PIIEntity]:
        """Union of all entities, removing duplicates."""
        all_entities = spacy_entities + presidio_entities
        
        # Group overlapping entities and merge them
        entity_groups = self._group_overlapping_entities(all_entities)
        combined = []
        
        for group in entity_groups:
            if len(group) == 1:
                combined.append(group[0])
            else:
                # Merge overlapping entities
                merged = self._merge_entities_union(group)
                combined.append(merged)
        
        return combined
    
    def _group_overlapping_entities(self, entities: List[PIIEntity]) -> List[List[PIIEntity]]:
        """Group entities that overlap with each other."""
        if not entities:
            return []
        
        # Sort entities by start position
        sorted_entities = sorted(entities, key=lambda x: x.start)
        groups = []
        current_group = [sorted_entities[0]]
        
        for entity in sorted_entities[1:]:
            # Check if entity overlaps with any entity in current group
            overlaps = any(self._entities_overlap(entity, group_entity) for group_entity in current_group)
            
            if overlaps:
                current_group.append(entity)
            else:
                groups.append(current_group)
                current_group = [entity]
        
        groups.append(current_group)
        return groups
    
    def _entities_overlap(self, entity1: PIIEntity, entity2: PIIEntity) -> bool:
        """Check if two entities overlap."""
        return not (entity1.end <= entity2.start or entity2.end <= entity1.start)
    
    def _merge_two_entities(self, entity1: PIIEntity, entity2: PIIEntity) -> PIIEntity:
        """Merge two overlapping entities."""
        # Use the entity with higher confidence as base
        base_entity = entity1 if entity1.confidence >= entity2.confidence else entity2
        other_entity = entity2 if entity1.confidence >= entity2.confidence else entity1
        
        # Calculate weighted confidence
        weighted_confidence = (
            entity1.confidence * self.spacy_weight if entity1.source == "spacy" else entity1.confidence * self.presidio_weight
        ) + (
            entity2.confidence * self.spacy_weight if entity2.source == "spacy" else entity2.confidence * self.presidio_weight
        )
        weighted_confidence = min(weighted_confidence, 1.0)
        
        return PIIEntity(
            entity_type=base_entity.entity_type,
            text=base_entity.text,
            start=min(entity1.start, entity2.start),
            end=max(entity1.end, entity2.end),
            confidence=weighted_confidence,
            source="ensemble",
            metadata={
                "sources": [entity1.source, entity2.source],
                "original_confidences": [entity1.confidence, entity2.confidence],
                "merge_strategy": "weighted"
            }
        )
    
    def _merge_entities_weighted(self, entities: List[PIIEntity]) -> PIIEntity:
        """Merge multiple entities using weighted average."""
        if len(entities) == 1:
            return entities[0]
        
        # Find the entity with highest confidence as base
        base_entity = max(entities, key=lambda x: x.confidence)
        
        # Calculate weighted confidence
        total_weight = 0
        weighted_sum = 0
        
        for entity in entities:
            weight = self.spacy_weight if entity.source == "spacy" else self.presidio_weight
            weighted_sum += entity.confidence * weight
            total_weight += weight
        
        weighted_confidence = min(weighted_sum / total_weight if total_weight > 0 else base_entity.confidence, 1.0)
        
        return PIIEntity(
            entity_type=base_entity.entity_type,
            text=base_entity.text,
            start=min(entity.start for entity in entities),
            end=max(entity.end for entity in entities),
            confidence=weighted_confidence,
            source="ensemble",
            metadata={
                "sources": [entity.source for entity in entities],
                "original_confidences": [entity.confidence for entity in entities],
                "merge_strategy": "weighted_average"
            }
        )
    
    def _merge_entities_union(self, entities: List[PIIEntity]) -> PIIEntity:
        """Merge entities using union strategy (highest confidence wins)."""
        if len(entities) == 1:
            return entities[0]
        
        # Use entity with highest confidence
        best_entity = max(entities, key=lambda x: x.confidence)
        
        return PIIEntity(
            entity_type=best_entity.entity_type,
            text=best_entity.text,
            start=min(entity.start for entity in entities),
            end=max(entity.end for entity in entities),
            confidence=best_entity.confidence,
            source="ensemble",
            metadata={
                "sources": [entity.source for entity in entities],
                "original_confidences": [entity.confidence for entity in entities],
                "merge_strategy": "union"
            }
        )
    
    def _get_model_versions(self) -> Dict[str, str]:
        """Get version information for both models."""
        versions = {}
        
        if self.spacy_detector and self.spacy_detector.is_initialized:
            spacy_info = self.spacy_detector.get_model_info()
            versions["spacy"] = spacy_info.get("version", "unknown")
        
        if self.presidio_detector and self.presidio_detector.is_initialized:
            presidio_info = self.presidio_detector.get_model_info()
            versions["presidio"] = "2.2.33"  # Presidio version
        
        return versions
    
    def __enter__(self):
        """Context manager entry."""
        if not self.is_initialized:
            self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass 