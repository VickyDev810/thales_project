#!/usr/bin/env python3
"""
Main PII Detection Interface
Provides ensemble-based PII detection with specified output format.
"""

import sys
import os
from typing import List, Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def get_pattern_name(entity_type: str, source: str) -> str:
    """Convert entity type and source to pattern name."""
    pattern_mapping = {
        "PERSON": "person_name",
        "EMAIL_ADDRESS": "email_address",
        "PHONE_NUMBER": "phone_number",
        "CREDIT_CARD": "credit_card",
        "SSN": "social_security_number",
        "IBAN_CODE": "iban_code",
        "IP_ADDRESS": "ip_address",
        "DATE_TIME": "date_time",
        "LOCATION": "location",
        "ORGANIZATION": "organization",
        "URL": "url",
        "MEDICAL_LICENSE": "medical_license",
        "US_DRIVER_LICENSE": "driver_license",
        "US_PASSPORT": "passport",
        "CRYPTO": "cryptocurrency_address"
    }
    return pattern_mapping.get(entity_type, entity_type.lower())

def determine_validation_status(entity_type: str, confidence: float, source: str) -> bool:
    """Determine if the entity is validated based on type, confidence, and source."""
    # High confidence entities from ensemble or multiple sources are considered validated
    if source == "ensemble" and confidence >= 0.8:
        return True
    
    # Specific entity types with high confidence are validated
    if entity_type in ["EMAIL_ADDRESS", "PHONE_NUMBER", "IP_ADDRESS", "URL"] and confidence >= 0.9:
        return True
    
    # Credit cards, SSNs with pattern validation
    if entity_type in ["CREDIT_CARD", "SSN", "IBAN_CODE"] and confidence >= 0.85:
        return True
    
    return confidence >= 0.9

def determine_safety_level(entity_type: str, confidence: float, validated: bool) -> str:
    """Determine the safety level for masking."""
    if not validated or confidence < 0.5:
        return "low"
    
    # High-risk PII types
    high_risk_types = ["SSN", "CREDIT_CARD", "MEDICAL_LICENSE", "US_PASSPORT", "US_DRIVER_LICENSE"]
    if entity_type in high_risk_types:
        return "high"
    
    # Medium-risk PII types
    medium_risk_types = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "IBAN_CODE"]
    if entity_type in medium_risk_types:
        return "medium"
    
    # Lower-risk types
    return "low"

def is_safe_to_mask(entity_type: str, safety_level: str, confidence: float) -> bool:
    """Determine if it's safe to mask this entity."""
    # Always safe to mask high-confidence, high-risk entities
    if safety_level == "high" and confidence >= 0.8:
        return True
    
    # Safe to mask medium-risk entities with good confidence
    if safety_level == "medium" and confidence >= 0.7:
        return True
    
    # Low-risk entities need higher confidence to be safe to mask
    if safety_level == "low" and confidence >= 0.85:
        return True
    
    return False

def detect_pii_ensemble(text: str, confidence_threshold: float = 0.5) -> List[Dict[str, Any]]:
    """
    Detect PII using ensemble approach and return in specified format.
    
    Args:
        text: Input text to analyze
        confidence_threshold: Minimum confidence threshold for entities
        
    Returns:
        List of dictionaries with pattern detection results
    """
    try:
        from .src.ensemble_detector import EnsemblePIIDetector
        
        # Initialize ensemble detector with optimal settings
        config = {
            "voting_strategy": "weighted",  # Best accuracy
            "confidence_threshold": confidence_threshold,
            "spacy_weight": 0.4,
            "presidio_weight": 0.6,
            "enable_parallel": True  # Better performance
        }
        
        # Create and initialize detector
        detector = EnsemblePIIDetector(config)
        detector.initialize()
        
        # Detect PII entities
        result = detector.detect(text)
        
        # Convert to required format
        formatted_results = []
        
        for entity in result.entities:
            # Calculate derived fields
            pattern_name = get_pattern_name(entity.entity_type.value, entity.source)
            validated = determine_validation_status(entity.entity_type.value, entity.confidence, entity.source)
            safety_level = determine_safety_level(entity.entity_type.value, entity.confidence, validated)
            safe_to_mask = is_safe_to_mask(entity.entity_type.value, safety_level, entity.confidence)
            
            # Create formatted result
            formatted_result = {
                "pattern_name": pattern_name,
                "validated": validated,
                "confidence": round(entity.confidence, 3),
                "start": entity.start,
                "end": entity.end,
                "safe_to_mask": safe_to_mask,
                "safety_level": safety_level,
                "value": entity.text
            }
            
            formatted_results.append(formatted_result)
        
        return formatted_results
        
    except Exception as e:
        print(f"Error in PII detection: {e}")
        return []

def detect_pii_with_metadata(text: str, 
                           confidence_threshold: float = 0.5,
                           include_metadata: bool = False) -> Dict[str, Any]:
    """
    Enhanced PII detection with additional metadata.
    
    Args:
        text: Input text to analyze
        confidence_threshold: Minimum confidence threshold
        include_metadata: Whether to include processing metadata
        
    Returns:
        Dictionary with results and optional metadata
    """
    results = detect_pii_ensemble(text, confidence_threshold)
    
    response = {
        "entities": results,
        "total_entities": len(results),
        "text_length": len(text)
    }
    
    if include_metadata:
        # Add processing metadata
        entity_types = list(set(r["pattern_name"] for r in results))
        high_confidence_count = len([r for r in results if r["confidence"] >= 0.8])
        validated_count = len([r for r in results if r["validated"]])
        safe_to_mask_count = len([r for r in results if r["safe_to_mask"]])
        
        response["metadata"] = {
            "unique_entity_types": entity_types,
            "high_confidence_entities": high_confidence_count,
            "validated_entities": validated_count,
            "safe_to_mask_entities": safe_to_mask_count,
            "confidence_threshold_used": confidence_threshold
        }
    
    return response

def batch_detect_pii(texts: List[str], 
                    confidence_threshold: float = 0.5) -> List[Dict[str, Any]]:
    """
    Batch process multiple texts for PII detection.
    
    Args:
        texts: List of texts to analyze
        confidence_threshold: Minimum confidence threshold
        
    Returns:
        List of results for each text
    """
    try:
        from .src.ensemble_detector import EnsemblePIIDetector
        
        # Initialize detector once for efficiency
        config = {
            "voting_strategy": "weighted",
            "confidence_threshold": confidence_threshold,
            "enable_parallel": True
        }
        
        detector = EnsemblePIIDetector(config)
        detector.initialize()
        
        # Process all texts
        batch_results = []
        for i, text in enumerate(texts):
            try:
                result = detector.detect(text)
                
                # Convert entities to required format
                formatted_entities = []
                for entity in result.entities:
                    pattern_name = get_pattern_name(entity.entity_type.value, entity.source)
                    validated = determine_validation_status(entity.entity_type.value, entity.confidence, entity.source)
                    safety_level = determine_safety_level(entity.entity_type.value, entity.confidence, validated)
                    safe_to_mask = is_safe_to_mask(entity.entity_type.value, safety_level, entity.confidence)
                    
                    formatted_entities.append({
                        "pattern_name": pattern_name,
                        "validated": validated,
                        "confidence": round(entity.confidence, 3),
                        "start": entity.start,
                        "end": entity.end,
                        "safe_to_mask": safe_to_mask,
                        "safety_level": safety_level,
                        "value": entity.text
                    })
                
                batch_results.append({
                    "text_index": i,
                    "entities": formatted_entities,
                    "entity_count": len(formatted_entities),
                    "processing_time": result.processing_time
                })
                
            except Exception as e:
                batch_results.append({
                    "text_index": i,
                    "error": str(e),
                    "entities": [],
                    "entity_count": 0
                })
        
        return batch_results
        
    except Exception as e:
        print(f"Error in batch PII detection: {e}")
        return []

def main():
    """
    Demo function showing the PII detection functionality.
    """
    print("🔍 Advanced PII Detection System - Main Interface")
    print("=" * 60)
    
    # Test cases
    test_texts = [
        "Hi, my name is John Smith and I work at Acme Corporation.",
        "Contact me at john.smith@email.com or call (555) 123-4567.",
        "My SSN is 123-45-6789 and my credit card is 4532-1234-5678-9012.",
        "Visit our website at https://example.com or connect to server 192.168.1.100.",
        "Send Bitcoin to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa for payment."
    ]
    
    print("\n📝 Testing individual text detection:")
    print("-" * 40)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}: {text}")
        results = detect_pii_ensemble(text, confidence_threshold=0.4)
        
        if results:
            print(f"Found {len(results)} PII entities:")
            for j, result in enumerate(results, 1):
                print(f"  {j}. {result}")
        else:
            print("  No PII entities found.")
    
    print(f"\n📊 Testing batch detection:")
    print("-" * 40)
    
    batch_results = batch_detect_pii(test_texts[:3], confidence_threshold=0.4)
    for result in batch_results:
        if "error" not in result:
            print(f"Text {result['text_index'] + 1}: {result['entity_count']} entities found")
        else:
            print(f"Text {result['text_index'] + 1}: Error - {result['error']}")
    
    print(f"\n🔍 Testing enhanced detection with metadata:")
    print("-" * 40)
    
    sample_text = "Dr. Sarah Johnson works at sarah@hospital.com, phone: (555) 987-6543"
    enhanced_result = detect_pii_with_metadata(sample_text, include_metadata=True)
    
    print(f"Sample text: {sample_text}")
    print(f"Results: {enhanced_result}")

# Convenience functions for direct usage
def analyze_text(text: str, threshold: float = 0.5) -> List[Dict[str, Any]]:
    """Simple interface for text analysis."""
    return detect_pii_ensemble(text, threshold)

def analyze_texts(texts: List[str], threshold: float = 0.5) -> List[Dict[str, Any]]:
    """Simple interface for batch analysis."""
    return batch_detect_pii(texts, threshold)


