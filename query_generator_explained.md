# MMF Hybrid Query Generator — Explained

## Purpose

`query_generator.py` is a **zero-dependency semantic intelligence layer** that converts raw text chunks (paragraphs extracted from PDFs, `.txt` files, or code) into an array of 3–5 optimized, natural language queries suitable for TF-IDF cosine similarity retrieval.

Instead of storing **"python is a programming language"** as a giant flat query, the generator creates multiple precise retrieval hooks like:

```
["what is python", "explain python", "python meaning", "programming language", "how does python work"]
```

This dramatically improves recall — especially when a user phrases a question differently from how the chunk is written.

---

## Architecture

### `clean_text(text)`
Lowercases the input, removes all special characters, and collapses whitespace. This produces a normalized string suitable for tokenization.

### `extract_keywords(cleaned, top_n=8)`
Tokenizes the cleaned text and filters by:
- Length > 3 characters
- Not in the hardcoded 60-word stopword list
- Not purely numeric

Then ranks by **word frequency** — repeated words signal topic importance. Returns top N keywords.

### `detect_topic(text, keywords)`
Uses the **first sentence** of the chunk as the primary topic signal (textbooks always introduce the topic first). Falls back to the top keyword if no meaningful first-sentence token is found.

### `generate_queries(chunk)`
The core function. For each chunk it generates up to 5 query patterns:

| Pattern | Example |
|---|---|
| `what is <topic>` | `what is algorithm` |
| `explain <topic>` | `explain algorithm` |
| `<topic> meaning` | `algorithm meaning` |
| `<kw1> <kw2>` | `computational steps` |
| `how does <topic> work` | `how does algorithm work` |

Deduplicates and caps at exactly 5 output queries.

---

## Integration with `ingestor.py`

In `_ingest_pdf()`, each paragraph chunk now calls:

```python
from .query_generator import generate_queries
queries = generate_queries(chunk)
```

This replaces the old `"queries": ["<raw_chunk>"]` pattern which forced the entire paragraph into a single massive term-frequency vector (noisy, unfocused, hard to match precisely).

---

## Edge Cases Handled

| Condition | Behaviour |
|---|---|
| Empty / None input | Returns `[]` |
| Chunk < 80 characters | Returns `[]` (skipped as noise) |
| No extractable keywords | Returns `[]` |
| No clear topic sentence | Falls back to top keyword |
| Duplicate queries generated | Deduplicated, order preserved |

---

## Future Extension Points

The module is designed for easy upgrades:

- **Embedding Expansion**: Replace `generate_queries()` with an embedding-based synonym expander (e.g. HuggingFace `SentenceTransformers`)
- **Synonym Mapping**: Inject a static dictionary `{"algorithm": ["procedure", "method", "routine"]}` into `generate_queries()` to expand coverage without any ML dependencies
