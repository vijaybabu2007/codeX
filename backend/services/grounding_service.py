import re

def verify_grounding(supporting_quote: str, source_text: str) -> tuple[bool, str, str | None]:
    """
    Deterministically checks whether the supporting quote can be verified in the source text.
    Returns: (is_grounded, status_string, matched_snippet_or_reason)
    """
    if not supporting_quote or not supporting_quote.strip():
        return False, "UNVERIFIED", "No supporting quote provided by generator."

    quote = supporting_quote.strip()
    
    # 1. Exact Substring Match
    if quote in source_text:
        return True, "VERIFIED", quote

    # 2. Case-insensitive Substring Match
    if quote.lower() in source_text.lower():
        start_idx = source_text.lower().find(quote.lower())
        matched = source_text[start_idx : start_idx + len(quote)]
        return True, "VERIFIED", matched

    # 3. Normalized whitespace match
    def normalize_tokens(s: str) -> str:
        s = re.sub(r"[^\w\s]", "", s)
        return " ".join(s.lower().split())

    norm_quote = normalize_tokens(quote)
    norm_source = normalize_tokens(source_text)

    if norm_quote and norm_quote in norm_source:
        return True, "VERIFIED", quote

    # 4. Truncated prefix match (in case model trimmed trailing punctuation)
    if len(quote) > 30:
        prefix = quote[:30]
        if prefix.lower() in source_text.lower():
            return True, "VERIFIED", prefix

    return False, "UNVERIFIED", f"Quote not found in source text: '{quote[:80]}...'"
