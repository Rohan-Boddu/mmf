# MMF AI Platform — Semantic RAG Knowledge Engine

> A production-ready, locally-executed AI knowledge engine with chunk-based semantic retrieval, document ingestion, and a modern chat UI. No cloud APIs required.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-REST_API-black)](https://flask.palletsprojects.com)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-TF--IDF-orange)](https://scikit-learn.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## What Is MMF?

The **Memory Model File (MMF)** platform is a locally-executed, document-aware semantic knowledge engine. It ingests documents, converts them into searchable knowledge nodes using TF-IDF cosine similarity, and answers natural language queries — all without any cloud LLM API.

Think of it as a **private, offline RAG (Retrieval-Augmented Generation) engine** you control completely.

---

## Features

| Feature | Description |
|---|---|
| 🧠 **Semantic TF-IDF Search** | Cosine similarity ranking across your entire knowledge base |
| 📄 **Multi-Format Ingestion** | `.txt`, `.csv`, `.js`, `.sql`, `.pdf` — all natively parsed |
| 🤗 **HuggingFace Dataset Import** | Pull any public dataset row-by-row via HTTP |
| 📎 **Chat Context Files** | Attach files to a conversation without permanently storing them |
| ✂️ **Hybrid Query Generator** | Converts raw chunks into 3–5 searchable query patterns per chunk |
| 💬 **Modern Chat UI** | Glassmorphism design, typing indicators, dark/light mode |
| ⚙️ **Knowledge Manager** | Full CRUD, bulk select/delete/export, inline editor |
| 💾 **Chat Export** | Download chat history as a structured Markdown file |
| 🔍 **Telemetry Panel** | Per-query cosine similarity, score, and matched query debug view |
| 🔄 **Hot Reload** | Edit knowledge live — engine reloads without restarting Flask |
| 📦 **`.mmf` Binary Format** | Atomic ZIP-based knowledge compilation and import/export |

---

## Architecture

```
User Input
    │
    ▼
Flask REST API  (/chat, /knowledge/*, /chat/context)
    │
    ▼
MMF Runtime  ──►  TfidfMatcher
                       │
           ┌───────────┴────────────┐
           │                        │
    Persistent Index         Ad-Hoc Context
    (assistant.mmf)          (session-only)
           │                        │
           └────── Score Blend ─────┘
                   (55% / 45%)
                       │
                       ▼
              Top-K Ranked Result
```

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Backend

```bash
python main.py
```

Flask will start on `http://localhost:5000`.

### 3. Open the Frontend

Open `frontend/index.html` in any modern browser (Chrome, Firefox, Edge).

---

## Project Structure

```
mmf-ai-platform/
├── backend/
│   ├── app.py                  # Flask app factory and route registration
│   ├── mmf/
│   │   ├── builder.py          # Compiles mmf_dev/ → assistant.mmf ZIP
│   │   ├── loader.py           # Loads assistant.mmf into memory
│   │   ├── runtime.py          # Orchestrates query → match → response
│   │   ├── matcher.py          # TF-IDF cosine similarity + ad-hoc blending
│   │   ├── learner.py          # Deduplication and knowledge persistence
│   │   ├── ingestor.py         # Document parsing pipeline
│   │   ├── query_generator.py  # Hybrid semantic query expansion
│   │   ├── extractor.py        # Heuristic "X is Y" text extraction
│   │   └── processor.py        # Text cleaning and normalization
│   └── routes/
│       ├── chat.py             # /chat and /chat/context endpoints
│       └── knowledge.py        # Full CRUD, ingest, export, HuggingFace import
├── frontend/
│   ├── index.html              # App shell and modals
│   ├── style.css               # Full design system (dark/light, glassmorphism)
│   └── script.js               # All UI logic, context management, chat export
├── main.py                     # Entry point — initializes runtime and starts Flask
├── requirements.txt
├── AGENT_RULES.md              # Development governance rules
├── CHANGELOG.md                # Version history
└── query_generator_explained.md
```

---

## Document Ingestion

Go to **⚙️ Matrix Core → Ingest Raw Document** and upload any supported file.

For CSVs a column-mapping dialog will appear automatically. For PDFs, text is split into paragraph-level semantic chunks.

### Supported Formats

| Format | Strategy |
|---|---|
| `.txt` | Sentence-level heuristic extraction |
| `.csv` | Named-column mapping (any header layout) |
| `.js` | Function block scanning |
| `.sql` | CREATE TABLE schema extraction |
| `.pdf` | Paragraph chunk splitting + Hybrid Query Generator |

---

## Chat Context Files

Click the **`+`** button in the chat bar to attach any file temporarily.  
Attached nodes are blended into every query for the session **without permanently modifying your knowledge base**.

When a response is sourced from an attached file, the chat bubble shows:
> `📎 From: filename.pdf`

---

## HuggingFace Dataset Import

Go to **⚙️ Matrix Core → 🤗 HuggingFace** and enter:
- Dataset ID (e.g. `rajpurkar/squad`)
- Query and Answer column names
- Row limit (max 500)

Uses the public HuggingFace Datasets Server API — no API key required for public datasets.

---

## Roadmap

- [ ] Ollama / OpenAI / Gemini LLM generation layer
- [ ] FAISS vector database backend
- [ ] Multi-user session isolation
- [ ] Streaming chat responses
- [ ] Scheduled dataset sync

---

## License

MIT — see [LICENSE](LICENSE).
