import time
from typing import List, Dict, Callable
from collections import defaultdict
from pprint import pprint

# Assumes PIIDetector is already defined/imported
# You can also plug in other detectors by wrapping them with the same interface.

class PIIBenchmark:
    def __init__(self, detector, detect_method: Callable, name="Unnamed Detector"):
        self.detector = detector
        self.detect_method = detect_method
        self.name = name
    
    def benchmark_detector(self, texts, iterations=50):
        total_time = 0.0
        for _ in range(iterations):
            for text in texts:
                start = time.perf_counter()
                self.detector.detect_all(text)
                end = time.perf_counter()
                total_time += (end - start)
        avg_time = total_time / (len(texts) * iterations)
        print(f"Avg Time per Text (over {iterations}x): {avg_time:.6f}s")

    def benchmark(self, texts: List[str], ground_truth: List[int] = None, display_samples: int = 3):
        total_time = 0.0
        all_results = []
        correct_detections = 0

        print(f"\n🚀 Benchmarking: {self.name}")
        for i, text in enumerate(texts):
            start = time.time()
            results = self.detect_method(text)
            end = time.time()

            detection_time = end - start
            total_time += detection_time
            all_results.append((text, results, detection_time))

            detected_count = self._extract_entity_count(results)
            expected_count = ground_truth[i] if ground_truth else None

            if expected_count is not None:
                if detected_count == expected_count:
                    correct_detections += 1

            if i < display_samples:
                print(f"\n🔹 Sample {i+1}")
                print(f"Text: {text.strip()}")
                print(f"Detected entities: {detected_count}")
                for r in results:
                    if isinstance(r, dict):
                        print(f"  - {r.get('value', r)} (Confidence: {r.get('confidence', 'N/A')})")
                    else:
                        print(f"  - {r}")
                print(f"Time taken: {detection_time:.4f}s")

        avg_time = total_time / len(texts)
        accuracy = (correct_detections / len(texts)) * 100 if ground_truth else None

        print(f"\n📊 Summary for {self.name}")
        print(f"Total texts: {len(texts)}")
        print(f"Total time: {total_time:.4f}s")
        print(f"Average time per text: {avg_time:.4f}s")
        if ground_truth:
            print(f"Accuracy: {accuracy:.2f}% (Exact match)")

    def _extract_entity_count(self, results) -> int:
        """Utility to normalize different result formats."""
        if isinstance(results, list):
            return sum(
                1 for r in results if isinstance(r, dict) and 'value' in r
            )
        return len(results)



# === Example Usage ===

