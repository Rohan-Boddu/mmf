"""
query_generator.py — MMF Hybrid Query Generator
Zero-dependency semantic query expansion using pure Python.

Converts raw text chunks into optimized query arrays for TF-IDF retrieval.
"""

import re
from typing import List

# --- Hardcoded Stopword Set ---
STOPWORDS = {
    "the", "is", "are", "was", "were", "and", "or", "to", "of", "in",
    "on", "for", "with", "a", "an", "it", "its", "this", "that", "these",
    "those", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "will", "would", "could", "should", "may", "might", "can",
    "as", "at", "by", "from", "into", "through", "during", "before",
    "after", "above", "below", "between", "each", "also", "so", "but",
    "not", "no", "if", "then", "than", "when", "where", "which", "who",
    "how", "what", "all", "any", "both", "more", "most", "other",
    "such", "own", "same", "just", "about", "up", "out", "they"
}


def clean_text(text: str) -> str:
    """
    Step 1: Lowercase, normalize, strip noise characters.
    Preserves alphabetic tokens and spaces only.
    """
    if not text or not isinstance(text, str):
        return ""
    text = text.lower()
    # Remove special characters but keep spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_keywords(cleaned: str, top_n: int = 8) -> List[str]:
    """
    Step 2 & 3: Extract meaningful keyword tokens.
    Filters stopwords, short tokens; prioritizes by frequency.
    """
    tokens = cleaned.split()

    # Filter: length > 3, not a stopword, not purely numeric
    candidates = [t for t in tokens if len(t) > 3 and t not in STOPWORDS and not t.isdigit()]

    # Count frequency to prioritize repeated meaningful terms
    freq = {}
    for t in candidates:
        freq[t] = freq.get(t, 0) + 1

    # Sort by frequency descending, then alphabetically for stability
    ranked = sorted(freq.keys(), key=lambda w: (-freq[w], w))
    return ranked[:top_n]


def detect_topic(text: str, keywords: List[str]) -> str:
    """
    Step 4: Heuristic topic detection using the first meaningful sentence.
    Falls back to the top keyword if no clear topic found.
    """
    # Split on sentence boundaries
    sentences = re.split(r'[.!?]', text)
    first = sentences[0].strip() if sentences else ""

    # Clean and tokenize first sentence
    cleaned_first = clean_text(first)
    first_tokens = [t for t in cleaned_first.split() if len(t) > 3 and t not in STOPWORDS]

    if first_tokens:
        return first_tokens[0]

    # Fallback to top keyword
    return keywords[0] if keywords else ""


def generate_queries(chunk: str) -> List[str]:
    """
    Steps 5-8: Core entry point. Converts a raw text chunk into
    3-5 optimized semantic queries for TF-IDF retrieval.

    Returns [] for empty or too-short chunks (< 80 chars).
    """
    if not chunk or not isinstance(chunk, str):
        return []

    # Edge case: too short to be meaningful
    if len(chunk.strip()) < 80:
        return []

    cleaned = clean_text(chunk)
    keywords = extract_keywords(cleaned)

    if not keywords:
        return []

    topic = detect_topic(chunk, keywords)

    queries = []

    # Pattern 1: Definition query
    if topic:
        queries.append(f"what is {topic}")

    # Pattern 2: Explanation query
    if topic:
        queries.append(f"explain {topic}")

    # Pattern 3: Meaning query
    if topic:
        queries.append(f"{topic} meaning")

    # Pattern 4: Keyword combination (top 2-3 keywords excluding topic if repeated)
    kw_pool = [k for k in keywords if k != topic]
    if len(kw_pool) >= 2:
        queries.append(f"{kw_pool[0]} {kw_pool[1]}")
    elif len(kw_pool) == 1:
        queries.append(f"{topic} {kw_pool[0]}")

    # Pattern 5: Functional query (optional, only if topic found)
    if topic and len(queries) < 5:
        queries.append(f"how does {topic} work")

    # Step 6: Deduplication (preserve order)
    seen = set()
    unique_queries = []
    for q in queries:
        q_lower = q.strip().lower()
        if q_lower not in seen and q_lower:
            seen.add(q_lower)
            unique_queries.append(q_lower)

    # Step 7: Max 5 output queries
    return unique_queries[:5]
