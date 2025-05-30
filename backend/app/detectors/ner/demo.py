#!/usr/bin/env python3
"""Comprehensive demo of the PII Detection System."""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_subheader(title):
    """Print a formatted subheader."""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

def demo_basic_detection():
    """Demonstrate basic PII detection."""
    print_header("🔍 BASIC PII DETECTION DEMO")
    
    from ensemble_detector import EnsemblePIIDetector
    
    # Sample texts with different types of PII
    test_cases = [
        {
            "name": "Personal Information",
            "text": "Hi, I'm Dr. Sarah Johnson and I work at Microsoft Corporation in Seattle."
        },
        {
            "name": "Contact Information", 
            "text": "You can reach me at sarah.johnson@microsoft.com or call (206) 555-0123."
        },
        {
            "name": "Financial Information",
            "text": "My credit card number is 4532 1234 5678 9012 and my SSN is 123-45-6789."
        },
        {
            "name": "Technical Information",
            "text": "The server IP is 192.168.1.100 and you can visit https://www.example.com."
        },
        {
            "name": "Cryptocurrency",
            "text": "Send Bitcoin to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa or Ethereum to 0x742d35Cc6634C0532925a3b8D4C0C8b3C2e1e3e3."
        }
    ]
    
    # Initialize detector
    print("Initializing PII Detection System...")
    detector = EnsemblePIIDetector({
        "voting_strategy": "weighted",
        "confidence_threshold": 0.3,
        "enable_parallel": True
    })
    detector.initialize()
    print("✅ System initialized successfully!\n")
    
    total_entities = 0
    total_time = 0
    
    for i, case in enumerate(test_cases, 1):
        print_subheader(f"Test Case {i}: {case['name']}")
        print(f"Text: {case['text']}")
        
        # Detect PII
        result = detector.detect(case['text'])
        total_entities += result.entity_count
        total_time += result.processing_time
        
        print(f"\n📊 Results:")
        print(f"   • Processing time: {result.processing_time:.3f} seconds")
        print(f"   • Entities found: {result.entity_count}")
        
        if result.entities:
            print(f"   • Detected entities:")
            for j, entity in enumerate(result.entities, 1):
                print(f"     {j}. {entity.entity_type.value}: '{entity.text}'")
                print(f"        Confidence: {entity.confidence:.3f} | Source: {entity.source}")
        else:
            print(f"   • No PII entities detected")
        print()
    
    print_subheader("📈 Overall Statistics")
    print(f"Total entities detected: {total_entities}")
    print(f"Total processing time: {total_time:.3f} seconds")
    print(f"Average time per text: {total_time/len(test_cases):.3f} seconds")
    
    return detector

def demo_anonymization(detector):
    """Demonstrate text anonymization."""
    print_header("🔒 TEXT ANONYMIZATION DEMO")
    
    sample_text = """
    Dear John Smith,
    
    Thank you for your inquiry. Please contact us at support@company.com 
    or call our customer service at (555) 123-4567. 
    
    For verification, we may need your SSN (123-45-6789) and the last 4 digits 
    of your credit card (4532 1234 5678 9012).
    
    Best regards,
    Customer Service Team
    """
    
    print(f"Original text:\n{sample_text}")
    
    # Detect PII first
    result = detector.detect(sample_text)
    print(f"\n🔍 Found {result.entity_count} PII entities to anonymize")
    
    # Demonstrate different anonymization strategies
    strategies = [
        ("replace", "Replace with entity type"),
        ("redact", "Replace with [REDACTED]"),
        ("mask", "Replace with asterisks")
    ]
    
    for strategy, description in strategies:
        print_subheader(f"Strategy: {strategy.upper()} - {description}")
        
        # Simple anonymization implementation
        anonymized = sample_text
        for entity in sorted(result.entities, key=lambda x: x.start, reverse=True):
            if strategy == "replace":
                replacement = f"[{entity.entity_type.value}]"
            elif strategy == "redact":
                replacement = "[REDACTED]"
            else:  # mask
                replacement = "*" * len(entity.text)
            
            anonymized = anonymized[:entity.start] + replacement + anonymized[entity.end:]
        
        print(f"Anonymized text:\n{anonymized}")

def demo_batch_processing(detector):
    """Demonstrate batch processing capabilities."""
    print_header("⚡ BATCH PROCESSING DEMO")
    
    # Create a batch of texts
    batch_texts = [
        "Contact Alice Johnson at alice@company.com",
        "Bob Smith's phone number is (555) 987-6543",
        "Credit card: 4111 1111 1111 1111, SSN: 987-65-4321",
        "Server located at 10.0.0.1, website: https://secure.example.com",
        "Send payment to Bitcoin address: 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
        "Dr. Emily Chen works at Stanford University Hospital",
        "Emergency contact: (911) 555-0911, email: emergency@hospital.org",
        "Patient ID: 12345, DOB: 1985-03-15, Insurance: Blue Cross",
        "IP whitelist: 192.168.1.0/24, 10.0.0.0/8",
        "API key: sk-1234567890abcdef, webhook: https://api.example.com/hook"
    ]
    
    print(f"Processing batch of {len(batch_texts)} texts...")
    
    # Process batch
    start_time = time.time()
    batch_result = detector.batch_detect(batch_texts)
    end_time = time.time()
    
    print(f"\n📊 Batch Processing Results:")
    print(f"   • Total texts processed: {batch_result.batch_size}")
    print(f"   • Total processing time: {batch_result.total_processing_time:.3f} seconds")
    print(f"   • Average time per text: {batch_result.average_processing_time:.3f} seconds")
    print(f"   • Total entities found: {batch_result.total_entities}")
    print(f"   • Throughput: {batch_result.batch_size/batch_result.total_processing_time:.1f} texts/second")
    
    # Show detailed results for first few texts
    print(f"\n📋 Detailed Results (first 3 texts):")
    for i, result in enumerate(batch_result.results[:3], 1):
        print(f"\n   Text {i}: \"{batch_texts[i-1][:50]}{'...' if len(batch_texts[i-1]) > 50 else ''}\"")
        print(f"   Entities: {result.entity_count}")
        for entity in result.entities:
            print(f"     • {entity.entity_type.value}: '{entity.text}' ({entity.confidence:.2f})")

def demo_voting_strategies(detector):
    """Demonstrate different voting strategies."""
    print_header("🗳️  VOTING STRATEGIES DEMO")
    
    from ensemble_detector import EnsemblePIIDetector
    
    test_text = "Dr. John Smith works at john.smith@hospital.com, phone: (555) 123-4567"
    
    strategies = ["majority", "weighted", "unanimous"]
    
    for strategy in strategies:
        print_subheader(f"Strategy: {strategy.upper()}")
        
        # Create detector with specific strategy
        strategy_detector = EnsemblePIIDetector({
            "voting_strategy": strategy,
            "confidence_threshold": 0.3,
            "enable_parallel": False
        })
        strategy_detector.initialize()
        
        result = strategy_detector.detect(test_text)
        
        print(f"Text: {test_text}")
        print(f"Entities found: {result.entity_count}")
        print(f"Processing time: {result.processing_time:.3f}s")
        
        for entity in result.entities:
            print(f"  • {entity.entity_type.value}: '{entity.text}' (confidence: {entity.confidence:.3f})")
            if hasattr(entity, 'metadata') and entity.metadata:
                if 'sources' in entity.metadata:
                    print(f"    Sources: {entity.metadata['sources']}")

def demo_performance_comparison():
    """Demonstrate performance comparison between individual detectors and ensemble."""
    print_header("🏃 PERFORMANCE COMPARISON")
    
    from detectors.spacy_detector import SpacyPIIDetector
    from detectors.presidio_detector import PresidioPIIDetector
    from ensemble_detector import EnsemblePIIDetector
    
    test_text = """
    John Smith is a software engineer at Google Inc. You can reach him at 
    john.smith@gmail.com or call (650) 555-0123. His employee ID is EMP-12345 
    and his SSN is 123-45-6789. The office is located at 1600 Amphitheatre Parkway, 
    Mountain View, CA. For urgent matters, contact the main office at (650) 253-0000.
    """
    
    print(f"Test text length: {len(test_text)} characters")
    print(f"Test text: {test_text[:100]}...")
    
    # Test individual detectors
    detectors = [
        ("spaCy Only", SpacyPIIDetector()),
        ("Presidio Only", PresidioPIIDetector()),
        ("Ensemble", EnsemblePIIDetector({"enable_parallel": False})),
        ("Ensemble (Parallel)", EnsemblePIIDetector({"enable_parallel": True}))
    ]
    
    results = []
    
    for name, detector in detectors:
        print_subheader(f"Testing: {name}")
        
        # Initialize and test
        start_time = time.time()
        detector.initialize()
        init_time = time.time() - start_time
        
        # Run detection multiple times for average
        times = []
        entity_counts = []
        
        for _ in range(3):
            start = time.time()
            if hasattr(detector, 'detect'):
                result = detector.detect(test_text)
                if hasattr(result, 'entities'):
                    entities = result.entities
                else:
                    entities = result
            else:
                entities = detector.detect(test_text)
            end = time.time()
            
            times.append(end - start)
            entity_counts.append(len(entities))
        
        avg_time = sum(times) / len(times)
        avg_entities = sum(entity_counts) / len(entity_counts)
        
        print(f"   Initialization time: {init_time:.3f}s")
        print(f"   Average detection time: {avg_time:.3f}s")
        print(f"   Average entities found: {avg_entities:.1f}")
        print(f"   Characters per second: {len(test_text)/avg_time:.0f}")
        
        results.append((name, init_time, avg_time, avg_entities))
    
    # Summary comparison
    print_subheader("📊 Performance Summary")
    print(f"{'Detector':<20} {'Init (s)':<10} {'Detect (s)':<12} {'Entities':<10} {'Speed (c/s)':<12}")
    print("-" * 70)
    
    for name, init_time, detect_time, entities in results:
        speed = len(test_text) / detect_time
        print(f"{name:<20} {init_time:<10.3f} {detect_time:<12.3f} {entities:<10.1f} {speed:<12.0f}")

def demo_system_info():
    """Display system information and capabilities."""
    print_header("ℹ️  SYSTEM INFORMATION")
    
    from ensemble_detector import EnsemblePIIDetector
    
    detector = EnsemblePIIDetector()
    detector.initialize()
    
    # Get system info
    info = detector.get_model_info()
    supported_entities = detector.get_supported_entities()
    
    print_subheader("🔧 Configuration")
    ensemble_config = info.get('ensemble_config', {})
    for key, value in ensemble_config.items():
        print(f"   {key}: {value}")
    
    print_subheader("🧠 spaCy Model")
    spacy_info = info.get('spacy', {})
    for key, value in spacy_info.items():
        print(f"   {key}: {value}")
    
    print_subheader("🛡️  Presidio Engine")
    presidio_info = info.get('presidio', {})
    for key, value in presidio_info.items():
        if key == 'recognizers':
            recognizers = eval(value) if isinstance(value, str) else value
            print(f"   {key}: {len(recognizers)} recognizers")
            print(f"      {', '.join(recognizers[:5])}...")
        else:
            print(f"   {key}: {value}")
    
    print_subheader("🏷️  Supported Entity Types")
    print(f"   Total: {len(supported_entities)} entity types")
    
    # Group entities by category
    categories = {
        "Personal": ["PERSON", "DATE_TIME", "LOCATION"],
        "Contact": ["EMAIL_ADDRESS", "PHONE_NUMBER", "URL"],
        "Financial": ["CREDIT_CARD", "IBAN_CODE", "SSN"],
        "Government": ["US_DRIVER_LICENSE", "US_PASSPORT"],
        "Technical": ["IP_ADDRESS", "CRYPTO"],
        "Medical": ["MEDICAL_LICENSE"],
        "Organization": ["ORGANIZATION"]
    }
    
    for category, entity_types in categories.items():
        found = [et for et in entity_types if et in supported_entities]
        if found:
            print(f"   {category}: {', '.join(found)}")

def main():
    """Run the comprehensive demo."""
    print_header("🚀 ADVANCED PII DETECTION SYSTEM - COMPREHENSIVE DEMO")
    print("This demo showcases the capabilities of our ensemble-based PII detection system.")
    print("The system combines spaCy and Presidio for optimal accuracy and performance.")
    
    try:
        # Run all demos
        detector = demo_basic_detection()
        demo_anonymization(detector)
        demo_batch_processing(detector)
        demo_voting_strategies(detector)
        demo_performance_comparison()
        demo_system_info()
        
        print_header("✅ DEMO COMPLETED SUCCESSFULLY")
        print("The PII detection system is working correctly!")
        print("\nNext steps:")
        print("1. Start the API server: python -m src.api")
        print("2. Run the API client demo: python examples/api_client.py")
        print("3. Run the test suite: python -m pytest tests/")
        print("4. Check the README.md for detailed documentation")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 