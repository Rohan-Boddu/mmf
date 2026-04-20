# CHANGELOG

All notable changes to the MMF AI Platform are documented here.

---

## [v0.7.2] — 2026-04-20
- **MMF v0.7.2 "Production Hardening"**: Transformed MMF from a pre-production system into a **production-grade, fault-tolerant, observable retrieval engine**.
- 88 automated tests passing across 5 test suites.
- 68% code coverage (core modules 74–96%).
- Zero changes to retrieval precision or scoring logic.

### Added
- **Testing Infrastructure**: 88 unit + integration tests across `test_matcher.py`, `test_synthesizer.py`, `test_learner.py`, `test_ingestor.py`, `test_api.py` covering intent detection, deduplication, atomic writes, malformed inputs, API CRUD, streaming, and concurrency.
- **Structured Logging** (`backend/mmf_logger.py`): JSON-formatted logs with timestamp, level, route, latency, query, match score. Replaced all `print()` statements across the codebase.
- **Request ID Tracking**: Every request gets a UUID (`X-Request-ID` header) for end-to-end tracing.
- **Metrics Endpoint** (`GET /metrics`): Request count, error count, avg/p95/p99 latency.
- **Health Endpoint** (`GET /health`): Returns system status, initialization state, and version.
- **Centralized Configuration** (`backend/config.py`): Environment-aware config via `python-dotenv` with startup validation (fail fast).
- **Runtime Config** (`config.json`): User-tunable `match_threshold`, `fallback_message`.
- **Environment Template** (`.env.example`): Documents all configurable environment variables.
- **Docker Deployment**: Multi-stage `Dockerfile` with non-root user and healthcheck. `docker-compose.yml` with persistent volumes for data and backups.
- **Gunicorn Config** (`gunicorn.conf.py`): Dynamic workers `(2×CPU+1)`, preloading, request limits, worker recycling.
- **Atomic Write Flow** (`learner.py`): Write → Validate → Backup → Atomic Replace. Prevents data corruption on crashes.
- **Knowledge Versioning**: Automatic timestamped backups (max 10 kept) on every write. `get_versions()` and `rollback()` API.
- **Corruption Detection**: `validate_knowledge()` checks structural integrity of `knowledge.json` at startup or on demand.
- **Click CLI** (`main.py`): 7 commands — `serve`, `validate`, `stats`, `rollback`, `test-query`, `build`, `interactive`.
- **Input Sanitization**: Chat queries trimmed to 2000 chars, stripped, validated.
- **GitHub Actions CI**: Auto lint (`flake8`) + test + coverage on push/PR for Python 3.10–3.12.

### Changed
- **Frontend API URL**: Replaced hardcoded `localhost:5000` with environment-aware auto-detection.
- **app.py**: Now uses `Config` class, request ID middleware, structured logging, `/health` and `/metrics` routes.
- **chat.py**: Added `_sanitize_input()`, structured logging, proper error logging for background learner.
- **builder.py**: `print()` → `logger.info()`.
- **runtime.py**: `print()` → `logger.debug()`.

---

## [v0.7.1] — 2026-04-15
- **MMF v0.7.1 "Intelligent Release"**: Transformed MMF from a retrieval system into a high-fidelity **Intelligent Semantic Response Engine**.
- Overhauled the response pipeline with Intent-Aware selection and Structured Synthesis.
- **SparkLight Schema Integration**: Ingested 23 advanced algorithmic concepts from SparkLight with upgraded `content_json` schema.

### SparkLight Additions
- **Hashing**: Linear Probing, Quadratic Probing, Double Hashing, Separate Chaining, Rehashing.
- **Trees**: AVL Tree, Red-Black Tree, Splay Tree, B-Tree, Expression Tree.
- **Advanced Structures**: Doubly Linked List, Circular Queue, Deque.
- **Sorting**: Shell Sort, Heap Sort.
- **Graph**: BFS, DFS.
- **String/Algo**: Infix to Postfix, Postfix Evaluation, Palindrome Check, Time Complexity Analysis, Adjacency Matrix.

### New Schema Fields (SparkLight-style Executable Knowledge)
- `execution_steps`: Step-by-step logic for each concept.
- `variants`: Related approaches for cross-comparison synthesis.
- `visual_hooks`: Frontend visualization signals (e.g., `animate_probe_sequence`).
- `reasoning_map`: Structured Problem → Solution → Tradeoffs.

### Added
- **Intelligent Synthesizer v2** (`mmf/synthesizer.py`): Replaced naive concatenation with a **Master Synthesizer** that merges the Top-3 qualifying knowledge nodes into a single, cohesive, non-repetitive response using a primary-secondary lock architecture.
- **Hybrid Intent-Aware Selector** (`mmf/matcher.py`): Implemented a 4-case fallback selection strategy that prioritizes **Intent > Score** (Definition, Comparison, Debugging, Explanation, Implementation). Matches with correct intent are boosted by 1.15x.
- **Asynchronous Background Learning**: Integrated real-time persistence into the chat pipeline. Every conversation is now ingested in a non-blocking background thread for immediate knowledge expansion.
- **Structured JSON Ingestion**: Standardized the core knowledge base on a JSON-aware schema (`content_json`) supporting multi-language technical implementations.
- **Metadata-Aware Persistence** (`mmf/learner.py`): Upgraded the learner to preserve custom metadata fields during ingestion, ensuring structured data integrity.
- **Multi-Language Knowledge Base**: Hardened the index with deep theoretical insights and runnable implementations in **C, Python, and C++** for core DSA concepts.

### Changed
- **Precision Hardening**: Raised global `match_threshold` to **0.60** and implemented a **SOFT_THRESHOLD of 0.55** for intent-based second-best node bridging.
- **Refined Scoring**: Calibrated the ranking formula to `0.7 * similarity + 0.3 * confidence` with intent-based semantic penalties.
- **Response Format**: Responses now follow a premium structured pattern: `#### Insight` -> `#### Key Points` -> `#### Implementation`.

---

## [v0.6.1]
- Finalized v0.6 architecture benchmarks.
- Renamed development directory to `v0.6.1` for version consistency.
- Prepped groundwork for v0.7 Flexible Ingestion engine.

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
