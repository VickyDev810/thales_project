
from .safe_patterns.safe_patterns import SafePatterns
from .unsafe_patterns.unsafe_patterns import UnsafePatterns

class CombinedPatterns:
    def get_all_patterns():
        return {
            **SafePatterns.get_patterns(),
            **UnsafePatterns.get_patterns(),
        }
