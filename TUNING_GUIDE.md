# MMF Platform — Parameter Tuning Guide

This document explains the core constants and thresholds that govern the retrieval and synthesis behavior of the MMF system.

## 1. Retrieval Thresholds (`matcher.py`)

### `match_threshold = 0.5`
- **Purpose**: Global minimum cosine similarity score required for a match to be considered.
- **Tuning**: 
    - Higher (0.6 - 0.7): Increases precision, reduces false positives, but may miss relevant content.
    - Lower (0.3 - 0.4): Increases recall, but risks retrieving irrelevant "hallucinated" context.

### `low_similarity_penalty` (35% threshold)
- **Purpose**: If base similarity is below 0.35, the score is penalized heavily to prevent weak matches from being promoted by metadata boosts.

## 2. Intent Boosting (`matcher.py`)

### `intent_boost = 1.3x`
- **Purpose**: Multiplier applied if the detected intent of the user query matches the intent of the knowledge node.
- **Why**: Ensures that if a user asks for "How to implement...", code-focused nodes are prioritized over generic definitions.

### `language_boost = 1.2x`
- **Purpose**: Multiplier applied if the query explicitly mentions a programming language (Python, C, C++) that is present in the node's code samples.

## 3. Synthesis Rules (`synthesizer.py`)

### `Deduplication Heuristics`
- **Mechanism**: Normalizes strings by removing punctuation and comparing sorted token sets.
- **Threshold**: If tokens overlap significantly or one set is a subset of another (for strings > 4 chars), it is flagged as a duplicate.

### `Key Point Limit = 6`
- **Purpose**: Caps the number of key points in the final response to ensure readability and prevent information overload.

## 4. Ingestion Constraints (`ingestor.py`)

### `MAX_QUERY_LENGTH = 2000`
- **Purpose**: Sanitizes user input and prevents extremely large queries from straining the vectorizer.

### `PDF Chunk Hard Ceiling = 200`
- **Purpose**: Limits the number of paragraphs extracted from a single PDF to prevent massive database bloat from a single file.

---

## 🛠️ How to Tune

Currently, these values are located as constants in the respective Python modules. For production environments, consider moving these to `config.json` for dynamic adjustment without code changes.
