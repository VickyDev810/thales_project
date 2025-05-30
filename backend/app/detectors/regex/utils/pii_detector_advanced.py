import re
from app.detectors.regex.patterns.safe_patterns.safe_patterns import SafePatterns
from app.detectors.regex.patterns.unsafe_patterns.unsafe_patterns import UnsafePatterns
from app.detectors.regex.patterns.combined_patterns import CombinedPatterns
from app.detectors.regex.utils.validators import Validators
from typing import List, Dict, Any
from collections import defaultdict

class PIIDetector:
    def __init__(self):
        self.safe_patterns = SafePatterns.get_patterns()
        self.unsafe_patterns = UnsafePatterns.get_patterns()
        self.all_patterns = CombinedPatterns.get_all_patterns()

    def _calculate_confidence(self, match_text, validated, expected_length, specificity):
        score = 0

        # Base score for a regex match
        score += 20

        # Validation is king
        if validated:
            score += 50

        # Length logic — only matters when expected_length is set
        if expected_length:
            cleaned_digits = len(re.sub(r'\D', '', match_text))
            diff = abs(cleaned_digits - expected_length)
            if diff == 0:
                score += 20
            elif diff == 1:
                score += 10
            elif diff == 2:
                score += 5

        # Specificity = tiebreaker weight (higher number wins)
        score += min(specificity or 0, 20)

        # Format consistency — minor bonus
        if self._has_consistent_formatting(match_text):
            score += 5

        # Cap and return
        return min(score, 100)

    
    def _has_consistent_formatting(self, text):
        """Check if the text has consistent formatting (not mixed delimiters)"""
        # Count different types of separators
        spaces = text.count(' ')
        hyphens = text.count('-')
        dots = text.count('.')
        
        # If multiple separator types are used, it's inconsistent
        separator_types = sum([1 for count in [spaces, hyphens, dots] if count > 0])
        return separator_types <= 1

    def _detect_all_candidates(self, text: str, patterns: dict) -> List[Dict[str, Any]]:
        candidates = []

        for name, meta in patterns.items():
            pattern = meta.get("pattern")
            if not pattern:
                continue

            try:
                for match in re.finditer(pattern, text):
                    start, end = match.span()
                    match_text = match.group()

                    validator_name = meta.get("validation")
                    validated = False
                    if validator_name and hasattr(Validators, validator_name):
                        try:
                            validator_func = getattr(Validators, validator_name)
                            cleaned = re.sub(r'\D', '', match_text)
                            validated = validator_func(cleaned)
                        except Exception:
                            validated = False

                    specificity = meta.get("specificity", 0)
                    expected_length = meta.get("expected_length", None)
                    confidence = self._calculate_confidence(match_text, validated, expected_length, specificity)

                    result = {
                        "pattern_name": name,
                        "validated": validated,
                        "confidence": confidence,
                        "start": start,
                        "end": end,
                        "safe_to_mask": meta.get("safe_to_mask", False),
                        "safety_level": meta.get("safety_level", "unknown"),
                        "value": match_text
                    }

                    candidates.append(result)
            except re.error:
                continue

        return candidates

    def _resolve_overlaps(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        visited = set()

        def overlaps(a, b):
            return not (a["end"] <= b["start"] or a["start"] >= b["end"])

        # Build transitive overlapping groups
        groups = []
        for i, candidate in enumerate(candidates):
            if i in visited:
                continue

            group = [candidate]
            visited.add(i)

            changed = True
            while changed:
                changed = False
                for j, other in enumerate(candidates):
                    if j in visited:
                        continue
                    if any(overlaps(other, g) for g in group):
                        group.append(other)
                        visited.add(j)
                        changed = True

            groups.append(group)

        # Resolve each group by selecting the best match
        for group in groups:
            if len(group) == 1:
                results.append(group[0])
            else:
                # Choose the candidate with highest (validated, confidence)
                group.sort(key=lambda x: (x["validated"], x["confidence"]), reverse=True)
                best = group[0]
                results.append(best)

        return results


    def detect_all(self, text: str) -> List[Any]:
        candidates = self._detect_all_candidates(text, self.all_patterns)
        return self._resolve_overlaps(candidates)

    def detect_safe(self, text: str) -> List[Any]:
        candidates = self._detect_all_candidates(text, self.safe_patterns)
        return self._resolve_overlaps(candidates)

    def detect_unsafe(self, text: str) -> List[Any]:
        candidates = self._detect_all_candidates(text, self.unsafe_patterns)
        return self._resolve_overlaps(candidates)