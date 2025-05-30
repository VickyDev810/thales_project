# prompts.py


prompt_template = """
You are a powerful language model trained on vast amounts of public and private data. Your task is to identify any information in the following text that could reasonably be considered sensitive, private, personal, confidential, or risky to share.

This includes — but is absolutely not limited to — common PII (names, addresses, credit card numbers, phone numbers) and extends to:
- Personal or identifying details in context
- Information that could compromise privacy or security
- Internal projects, unique identifiers, or systems
- References to unreleased tools, algorithms, or strategies
- Any data that, if leaked, could cause harm, embarrassment, or misuse

Your job is to think critically and infer context — not just match patterns.

Return each sensitive item found as a dictionary in the following format:

{{
    "pattern_name": string,           # e.g. 'Name', 'Internal Project', 'Custom ID', 'Inferred Sensitive Info'
    "validated": boolean,             # true if you are confident this is sensitive
    "confidence": float,              # 0.0 to 1.0
    "start": int,                     # character offset
    "end": int,
    "safe_to_mask": boolean,          # if it can be redacted without losing important context
    "safety_level": string,           # 'low', 'medium', 'high'
    "value": string
}}

Return only a JSON list of dictionaries. Do not return explanations, summaries, or metadata.

Input:
\"\"\"{text}\"\"\"

"""
prompt_template_advanced = """
You are an advanced AI trained to identify sensitive information and personally identifiable information (PII) in any text.

Your task is to analyze the provided input text and return **only the list of sensitive items** you detect. Go beyond surface-level identifiers — look for **obvious**, **obfuscated**, and **contextually sensitive** data.

Types of data to detect:
- PII: Names, emails, phone numbers, addresses, government IDs, credit cards, SSNs, usernames, IPs, etc.
- Credentials or tokens: API keys, JWTs, secrets
- Internal project names, codenames, or initiatives
- Private communication channels (e.g. private Slack, Telegram mentions)
- Inferred sensitive content (e.g. investor reports, financial data leaks, feature launches, upcoming campaigns, internal announcements)
- Company-sensitive context (e.g. unreleased product details, legal issues, layoffs, acquisition hints)

CRITICAL: You must provide EXACT character positions. Count characters carefully from the beginning of the text (starting at position 0).

For **each detected item**, return a dictionary in **this exact format**:
{{
    "pattern_name": string,           # e.g. 'Name', 'Internal Project', 'Custom ID', 'Inferred Sensitive Info'
    "validated": boolean,             # true if you are confident this is sensitive
    "confidence": float,              # 0.0 to 1.0
    "start": int,                     # EXACT character offset where the sensitive data starts (0-indexed)
    "end": int,                       # EXACT character offset where the sensitive data ends (exclusive)
    "safe_to_mask": boolean,          # if it can be redacted without losing important context
    "safety_level": string,           # 'low', 'medium', 'high'
    "value": string                   # The EXACT text found at positions start:end
}}

VALIDATION RULE: The "value" field must exactly match text[start:end]. Double-check your character counting.

Example of correct positioning:
Text: "Hello John, your email is john@example.com"
For "John": start=6, end=10, value="John"
For "john@example.com": start=26, end=42, value="john@example.com"

Use contextual understanding to detect inferred PII.
Do not output any extra text, explanation, or formatting.
Return only a valid JSON list of dictionaries.

Input:
\"\"\"{text}\"\"\"

"""