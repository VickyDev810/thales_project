"""FastAPI-based REST API for PII detection system."""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import time
from contextlib import asynccontextmanager

from .ensemble_detector import EnsemblePIIDetector
from .models import PIIDetectionResult, BatchDetectionResult, PIIEntity, EntityType
from .config import config


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global detector instance
detector: Optional[EnsemblePIIDetector] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global detector
    
    # Startup
    logger.info("Initializing PII detection system...")
    detector = EnsemblePIIDetector()
    detector.initialize()
    logger.info("PII detection system initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PII detection system...")


# Create FastAPI app
app = FastAPI(
    title="Advanced PII Detection API",
    description="A high-performance PII detection system combining spaCy and Presidio",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class DetectionRequest(BaseModel):
    """Request model for PII detection."""
    text: str = Field(..., description="Text to analyze for PII")
    confidence_threshold: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0, 
        description="Minimum confidence threshold for entities"
    )
    entity_types: Optional[List[str]] = Field(
        None, 
        description="Specific entity types to detect"
    )


class BatchDetectionRequest(BaseModel):
    """Request model for batch PII detection."""
    texts: List[str] = Field(..., description="List of texts to analyze")
    confidence_threshold: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0, 
        description="Minimum confidence threshold for entities"
    )
    entity_types: Optional[List[str]] = Field(
        None, 
        description="Specific entity types to detect"
    )


class AnonymizationRequest(BaseModel):
    """Request model for text anonymization."""
    text: str = Field(..., description="Text to anonymize")
    anonymization_strategy: str = Field(
        "replace", 
        description="Anonymization strategy: 'replace', 'redact', 'mask'"
    )
    confidence_threshold: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0, 
        description="Minimum confidence threshold for entities"
    )


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: float
    model_info: Dict[str, Any]


class EntityStatsResponse(BaseModel):
    """Entity statistics response."""
    total_entities: int
    entity_type_counts: Dict[str, int]
    average_confidence: float
    high_confidence_count: int


# API endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    if not detector or not detector.is_initialized:
        raise HTTPException(status_code=503, detail="PII detection system not initialized")
    
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        model_info=detector.get_model_info()
    )


@app.get("/supported-entities")
async def get_supported_entities():
    """Get list of supported entity types."""
    if not detector:
        raise HTTPException(status_code=503, detail="PII detection system not initialized")
    
    return {
        "supported_entities": detector.get_supported_entities(),
        "total_count": len(detector.get_supported_entities())
    }


@app.post("/detect", response_model=PIIDetectionResult)
async def detect_pii(request: DetectionRequest):
    """Detect PII entities in text."""
    if not detector:
        raise HTTPException(status_code=503, detail="PII detection system not initialized")
    
    try:
        # Override confidence threshold if provided
        original_threshold = detector.confidence_threshold
        if request.confidence_threshold is not None:
            detector.confidence_threshold = request.confidence_threshold
        
        result = detector.detect(request.text)
        
        # Filter by entity types if specified
        if request.entity_types:
            filtered_entities = [
                entity for entity in result.entities
                if entity.entity_type.value in request.entity_types
            ]
            result.entities = filtered_entities
        
        # Restore original threshold
        detector.confidence_threshold = original_threshold
        
        return result
        
    except Exception as e:
        logger.error(f"Error during PII detection: {e}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@app.post("/detect/batch", response_model=BatchDetectionResult)
async def detect_pii_batch(request: BatchDetectionRequest):
    """Detect PII entities in multiple texts."""
    if not detector:
        raise HTTPException(status_code=503, detail="PII detection system not initialized")
    
    if len(request.texts) > config.BATCH_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"Batch size exceeds maximum allowed ({config.BATCH_SIZE})"
        )
    
    try:
        # Override confidence threshold if provided
        original_threshold = detector.confidence_threshold
        if request.confidence_threshold is not None:
            detector.confidence_threshold = request.confidence_threshold
        
        result = detector.batch_detect(request.texts)
        
        # Filter by entity types if specified
        if request.entity_types:
            for detection_result in result.results:
                filtered_entities = [
                    entity for entity in detection_result.entities
                    if entity.entity_type.value in request.entity_types
                ]
                detection_result.entities = filtered_entities
        
        # Restore original threshold
        detector.confidence_threshold = original_threshold
        
        return result
        
    except Exception as e:
        logger.error(f"Error during batch PII detection: {e}")
        raise HTTPException(status_code=500, detail=f"Batch detection failed: {str(e)}")


@app.post("/anonymize")
async def anonymize_text(request: AnonymizationRequest):
    """Anonymize PII entities in text."""
    if not detector:
        raise HTTPException(status_code=503, detail="PII detection system not initialized")
    
    try:
        # First detect PII entities
        original_threshold = detector.confidence_threshold
        if request.confidence_threshold is not None:
            detector.confidence_threshold = request.confidence_threshold
        
        detection_result = detector.detect(request.text)
        
        # Restore original threshold
        detector.confidence_threshold = original_threshold
        
        # Anonymize based on strategy
        anonymized_text = _anonymize_text(
            request.text, 
            detection_result.entities, 
            request.anonymization_strategy
        )
        
        return {
            "original_text": request.text,
            "anonymized_text": anonymized_text,
            "entities_found": len(detection_result.entities),
            "entities": [
                {
                    "type": entity.entity_type.value,
                    "text": entity.text,
                    "start": entity.start,
                    "end": entity.end,
                    "confidence": entity.confidence
                }
                for entity in detection_result.entities
            ],
            "processing_time": detection_result.processing_time
        }
        
    except Exception as e:
        logger.error(f"Error during anonymization: {e}")
        raise HTTPException(status_code=500, detail=f"Anonymization failed: {str(e)}")


@app.get("/stats/entities", response_model=EntityStatsResponse)
async def get_entity_stats(text: str):
    """Get statistics about detected entities in text."""
    if not detector:
        raise HTTPException(status_code=503, detail="PII detection system not initialized")
    
    try:
        result = detector.detect(text)
        entities = result.entities
        
        if not entities:
            return EntityStatsResponse(
                total_entities=0,
                entity_type_counts={},
                average_confidence=0.0,
                high_confidence_count=0
            )
        
        # Calculate statistics
        entity_type_counts = {}
        total_confidence = 0
        high_confidence_count = 0
        
        for entity in entities:
            entity_type = entity.entity_type.value
            entity_type_counts[entity_type] = entity_type_counts.get(entity_type, 0) + 1
            total_confidence += entity.confidence
            
            if entity.confidence >= 0.8:
                high_confidence_count += 1
        
        average_confidence = total_confidence / len(entities)
        
        return EntityStatsResponse(
            total_entities=len(entities),
            entity_type_counts=entity_type_counts,
            average_confidence=average_confidence,
            high_confidence_count=high_confidence_count
        )
        
    except Exception as e:
        logger.error(f"Error calculating entity stats: {e}")
        raise HTTPException(status_code=500, detail=f"Stats calculation failed: {str(e)}")


@app.get("/config")
async def get_configuration():
    """Get current system configuration."""
    if not detector:
        raise HTTPException(status_code=503, detail="PII detection system not initialized")
    
    return {
        "ensemble_config": {
            "voting_strategy": detector.voting_strategy,
            "confidence_threshold": detector.confidence_threshold,
            "spacy_weight": detector.spacy_weight,
            "presidio_weight": detector.presidio_weight,
            "parallel_processing": detector.enable_parallel
        },
        "system_config": {
            "batch_size": config.BATCH_SIZE,
            "max_text_length": config.MAX_TEXT_LENGTH,
            "enable_caching": config.ENABLE_CACHING,
            "supported_entity_types": config.ENTITY_TYPES
        }
    }


def _anonymize_text(text: str, entities: List[PIIEntity], strategy: str) -> str:
    """Anonymize text based on detected entities and strategy."""
    if not entities:
        return text
    
    # Sort entities by start position in reverse order to avoid index shifting
    sorted_entities = sorted(entities, key=lambda x: x.start, reverse=True)
    
    anonymized_text = text
    
    for entity in sorted_entities:
        if strategy == "redact":
            replacement = "[REDACTED]"
        elif strategy == "mask":
            replacement = "*" * len(entity.text)
        elif strategy == "replace":
            replacement = f"[{entity.entity_type.value}]"
        else:
            replacement = "[ANONYMIZED]"
        
        anonymized_text = (
            anonymized_text[:entity.start] + 
            replacement + 
            anonymized_text[entity.end:]
        )
    
    return anonymized_text


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 