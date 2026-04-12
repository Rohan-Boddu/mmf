"""
synthesizer.py — MMF Rule-Based Response Synthesizer

Converts Top-K retrieved chunks into a single, coherent, generative-feeling response.
Zero LLM dependency. Pure deterministic text synthesis.

HOW IT WORKS:
1. Score chunks by relevance (passed in pre-ranked from matcher)
2. Deduplicate sentences across chunks
3. Build a structured response using grammatical connectors
4. Apply light formatting rules for readability
"""

import re
from typing import List, Dict


# Sentence connectors ordered by semantic role
_INTRO_CONNECTORS  = ["", "In summary, ", "To explain this: "]
_EXTEND_CONNECTORS = [" Additionally, ", " Furthermore, ", " It also follows that "]
_CLOSING_CONNECTOR = " Together, these concepts form a complete picture."

_MIN_SENTENCE_LEN = 30  # Characters — discard stub sentences
_MAX_OUTPUT_SENTENCES = 6


def _split_sentences(text: str) -> List[str]:
    """Split a paragraph into individual sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if len(s.strip()) >= _MIN_SENTENCE_LEN]


def _deduplicate(sentences: List[str], sim_threshold: float = 0.55) -> List[str]:
    """
    Remove near-duplicate sentences using word-overlap Jaccard similarity.
    Pure Python — no external libraries.
    """
    seen_sets = []
    unique = []
    for sentence in sentences:
        words = set(re.findall(r'\b\w+\b', sentence.lower()))
        is_dup = False
        for seen in seen_sets:
            if not words or not seen:
                continue
            jaccard = len(words & seen) / len(words | seen)
            if jaccard > sim_threshold:
                is_dup = True
                break
        if not is_dup:
            unique.append(sentence)
            seen_sets.append(words)
    return unique


def synthesize(chunks: List[Dict], query: str = "") -> str:
    """
    Core synthesizer entry point.

    Args:
        chunks: List of matched knowledge items ordered by relevance score.
                Each item must have a 'response' key (string).
        query:  Original user query for context-aware framing.

    Returns:
        A single synthesized string combining the most relevant information.
    """
    if not chunks:
        return ""

    # Step 1: Extract all response text from top-K chunks
    all_sentences = []
    for chunk in chunks:
        response_text = chunk.get("response", "")
        if not response_text:
            continue
        sentences = _split_sentences(response_text)
        all_sentences.extend(sentences)

    if not all_sentences:
        # Fallback: return the best chunk verbatim
        return chunks[0].get("response", "")

    # Step 2: Deduplicate across chunks
    unique_sentences = _deduplicate(all_sentences)

    # Step 3: Cap output length
    selected = unique_sentences[:_MAX_OUTPUT_SENTENCES]

    # Step 4: Single chunk or single sentence — return directly, no connectors
    if len(selected) == 1:
        return selected[0]

    # Step 5: Build synthesized output with connectors
    parts = []
    for i, sentence in enumerate(selected):
        if i == 0:
            # First sentence — prepend intro connector only if multiple chunks contributed
            connector = _INTRO_CONNECTORS[0] if len(chunks) == 1 else _INTRO_CONNECTORS[1]
            parts.append(f"{connector}{sentence}")
        else:
            connector = _EXTEND_CONNECTORS[min(i - 1, len(_EXTEND_CONNECTORS) - 1)]
            # Avoid double-punctuation artifacts
            sentence_body = sentence.lstrip()
            parts.append(f"{connector}{sentence_body[0].lower()}{sentence_body[1:]}")

    result = "".join(parts)

    # Step 6: Ensure terminal punctuation
    if result and result[-1] not in ".!?":
        result += "."

    return result
