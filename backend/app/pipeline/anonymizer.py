from typing import List, Dict
from .crypto.utils import encrypt_with_public_key
from typing import List, Dict, Optional
import json
import os

# In-memory store: placeholder token -> encrypted PII (bytes)
encrypted_store: Dict[str, bytes] = {}



# Helper: generate short placeholder token
import hmac, hashlib
SECRET_KEY = b"342342343"  # keep secret & safe

def generate_placeholder_token(pattern_name: str, value: str) -> str:
    msg = f"{pattern_name}:{value}".encode()
    h = hmac.new(SECRET_KEY, msg, hashlib.sha256).hexdigest()[:8]  # shorter for UX
    token = f"{pattern_name.upper().replace(' ', '_')}_{h}__"
    return token

def find_all_occurrences(text: str, value: str) -> List[tuple]:
    positions = []
    start = 0
    while True:
        pos = text.find(value, start)
        if pos == -1:
            break
        positions.append((pos, pos + len(value)))
        start = pos + 1
    return positions

def anonymize_text(text: str, pii_results: List[Dict], public_key_pem: str) -> str:
    value_to_placeholder = {}
    replacements = []

    for pii in pii_results:
        pattern_name, value = pii['pattern_name'], pii['value']
        if value not in value_to_placeholder:
            # Encrypt sensitive value with public key
            encrypted_val = encrypt_with_public_key(public_key_pem, value)
            # Generate short placeholder token
            placeholder = generate_placeholder_token(pattern_name, value)
            # Store encrypted value for later decryption by placeholder
            encrypted_store[placeholder] = encrypted_val
            value_to_placeholder[value] = placeholder

            # Find all occurrences to replace
            for start, end in find_all_occurrences(text, value):
                replacements.append((start, end, placeholder))

    # Sort in reverse so replacement doesn't mess up indexes
    replacements.sort(key=lambda x: x[0], reverse=True)

    # Remove overlaps (keep first encountered)
    filtered = []
    for curr in replacements:
        start, end, ph = curr
        if all(not (start < f_end and end > f_start) for f_start, f_end, _ in filtered):
            filtered.append(curr)

    # Apply replacements
    for start, end, ph in filtered:
        text = text[:start] + ph + text[end:]

    return text


def anonymize_text_combined(
    text: str,
    builtin_pii_results: List[Dict],
    public_key_pem: str,
    custom_pii_json_path: Optional[str] = None
) -> str:
    """Anonymize text using both built-in PII results and optional custom PII JSON."""
    with open(custom_pii_json_path, 'r') as f:
        raw_data = json.load(f)
        print("[DEBUG] Loaded custom PII JSON:", raw_data)

    # Load custom PII from JSON if provided
    custom_pii = []
    if custom_pii_json_path and os.path.exists(custom_pii_json_path):
        try:
            with open(custom_pii_json_path, 'r') as f:
                raw_data = json.load(f)

            custom_pii = [
                {"pattern_name": item["type"], "value": item["value"]}
                for item in raw_data
                if item.get("safe_to_mask", False)
            ]
        except (json.JSONDecodeError, OSError) as e:
            print(f"[WARN] Failed to load custom PII JSON: {e}. Skipping.")

    # Combine both sources
    combined_pii = builtin_pii_results + custom_pii

    if not combined_pii:
        print("[INFO] No PII to anonymize. Returning original text.")
        return text

    return anonymize_text(text, combined_pii, public_key_pem)
