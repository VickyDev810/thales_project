from app.detectors.regex.main import detect_with_regex
from app.detectors.ner.main import detect_with_ner
from app.detectors.llm.main import detect_with_llm

def detect_pii(text: str, mode: str = "all") -> dict:
    mode = mode.lower()
    results = {}

    if mode == "regex" or mode == "all":
        results["regex"] = detect_with_regex(text)
    if mode == "ner" or mode == "all":
        results["ner"] = detect_with_ner(text)
    if mode == "llm" or mode == "all":
        results["llm"] = detect_with_llm(text)

    if mode not in {"regex", "ner", "llm", "all"}:
        raise ValueError(f"Invalid mode: {mode}")

    return results
