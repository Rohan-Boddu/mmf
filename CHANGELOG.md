# CHANGELOG

All notable changes to the MMF AI Platform are documented here.

---

## [v0.6] — Current

### Added
- **Hybrid Query Generator** (`mmf/query_generator.py`): Zero-dependency semantic query expansion using pattern-based NLP, converting raw text chunks into 3–5 retrieval-optimized queries per node.
- **Chunk-Based PDF Ingestion**: PDFs are now split at paragraph boundaries and each chunk is vectorized independently using the Hybrid Query Generator.
- **Multi-Format Document Ingestor** (`mmf/ingestor.py`): Supports `.txt`, `.csv`, `.js`, `.sql`, `.pdf`. CSVs now accept named-column mapping (any header layout supported).
- **HuggingFace Dataset Import**: `POST /api/knowledge/import/huggingface` fetches rows from any public HuggingFace dataset via their Datasets Server API (no API key required). Configurable split, config, query/answer column, and row limit.
- **Chat Context Files**: `[+]` button in the chat bar attaches files temporarily for the session. Context nodes are scored with a separate ephemeral TF-IDF vectorizer and blended into query results (55% MMF / 45% context weighting). Not persisted to knowledge base.
- **Chat Export**: `💾 Export Chat` nav button downloads conversation as a structured `.md` file with timestamp and context file inventory.
- **Bulk Node Selection**: Knowledge Manager table now has a Select All checkbox, per-row checkboxes, and a bulk action toolbar (bulk delete, bulk CSV export).
- **Export Dropdown**: Export button now offers two options — `Matrix (.mmf)` for the compiled binary and `Nodes (.csv)` for a flat CSV of all knowledge nodes.
- **Custom UI System**: Replaced all native `alert()`/`confirm()` calls with:
  - Toast notifications (top-right, auto-dismiss, typed: success/error/warning/info)
  - Custom confirm dialog (Promise-based)
  - Progress overlay with animated bar (indeterminate → determinate)
- **Source Attribution**: Query responses now carry a `source` field. Chat bubbles display `📎 From: filename` when a match comes from an attached context file.
- **Bulk Delete API**: `POST /api/knowledge/bulk-delete` accepts an array of node IDs and removes them atomically.
- **CSV Column Peek API**: `POST /api/knowledge/csv-headers` returns column headers before upload so the UI can present a mapping dialog.

### Changed
- `TfidfMatcher.find_best_match()` now accepts `ad_hoc_knowledge` parameter for ephemeral context blending.
- `MMFRuntime.query()` now accepts and forwards `ad_hoc_knowledge`.
- `_ingest_pdf()` completely rewritten — removed heuristic extraction, now uses paragraph splitting + `generate_queries()`.
- `_ingest_csv()` upgraded from positional-only to full `DictReader` named-column support.
- `runtime.py` match return dict now includes `matching_query`, `similarity`, `confidence`, `final_score`, `source`.

---

## [v0.5]

### Added
- **Flask REST API** with hot-reload capability (atomic file writes, runtime memory flush).
- **Knowledge Manager Modal**: Full-screen glassmorphism panel for CRUD operations.
- **Document Ingestion Route** (`POST /api/knowledge/ingest`): Initial support for `.txt`, `.csv`, `.js`, `.sql`.
- **PDF Ingestion**: Initial `_ingest_pdf()` using PyPDF2 with heuristic extraction (superseded in v0.6).
- **Theme Toggle**: Native light/dark mode switching.
- **Debug Telemetry Panel**: Slide-in drawer showing cosine similarity, rank score, and matched query per response.

---

## [v0.4]

### Added
- **TF-IDF Semantic Matching**: Replaced exact-match with `TfidfVectorizer` + cosine similarity.
- **Top-K Ranking**: Returns top 3 candidates and applies soft thresholding.
- **Confidence Weighting**: `final_score = (0.7 × similarity) + (0.3 × confidence)`.
- **Cache Invalidation**: Knowledge index rebuilds only when the dataset changes (MD5 hash check).

---

## [v0.3]

### Added
- Initial `.mmf` binary format (ZIP-based, atomic write using `os.replace`).
- `MMFBuilder` and `MMFLoader` for compile/load cycle.
- `MMFLearner` with deduplication, tag pruning, and batch ingestion.

---

## [v0.1 – v0.2]

- Initial prototype with static `knowledge.json` and exact string matching.
