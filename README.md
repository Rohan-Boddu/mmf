# MMF AI Platform

### Self-learning AI that builds knowledge dynamically — no retraining, no cloud, no API keys.

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-REST_API-000000?style=flat&logo=flask)](https://flask.palletsprojects.com)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-TF--IDF-F7931E?style=flat&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=flat)](LICENSE)

</div>

---

## Overview

Most AI systems require pre-trained models, cloud APIs, or expensive inference hardware. **MMF is different.**

MMF (Memory Model File) is a knowledge engine that learns from your documents at runtime — no model weights, no fine-tuning, no cloud dependency. You feed it text, PDFs, datasets, or Q&A pairs. It builds a searchable semantic vector space. You query it in plain English and get ranked, synthesized, explainable answers instantly.

**What problem does it solve?**
You have raw documents, datasets, and domain knowledge. You want a system that can answer questions about that knowledge — intelligently, privately, and without waiting for model training or paying API costs.

**What makes it different?**

| Approach | Training | Cloud | Explains Itself | Updates Live | Cost |
|---|---|---|---|---|---|
| Fine-tuned LLM | Never Required | Usually |  No |  No |  High cost |
| RAG (LLM-based) | Never |  Required | Partial | Partial | cost Per call |
| Vector DB (embeddings) | Never | Optional |  No | LIVE |  cost for Embedding API |
| **MMF** |  Never |  Never |  Always |  Live |  Free |

---

## How MMF Differs From RAG

Standard RAG systems work like this:

```
User Query → Embeddings Model → Vector DB → LLM (GPT-4 / Claude) → Response
```

Every step has a cost: embedding API calls, vector DB hosting, LLM token fees.

**MMF replaces all of that:**

```
User Query → TF-IDF Vectorizer → MMF Knowledge Index → Synthesizer → Response
```

| Component | Traditional RAG | MMF |
|---|---|---|
| Semantic Search | Neural embeddings (paid API or GPU) | TF-IDF (CPU, free) |
| Storage | Pinecone / Weaviate / Chroma | Local `mmf_dev/` directory |
| Generation | LLM (GPT, Claude, Gemini) | Rule-based synthesizer (built-in) |
| Knowledge Updates | Re-embed and re-index | Live hot-reload, no re-index |
| Explainability | Black box | Score + matched query + source |
| Infra | API keys, billing, latency | `pip install -r requirements.txt` |

MMF is not trying to replace GPT. It is a **lightweight, deterministic, self-contained alternative** for structured knowledge retrieval — where correctness, speed, explainability, and data privacy matter more than open-ended generation.

---

## The Generative Layer — Without an LLM (In Progress)

MMF is not just a retriever. It includes a built-in **Rule-Based Response Synthesizer** that makes responses feel coherent and complete, even when the answer spans multiple knowledge chunks.

### How it works

**Step 1 — Retrieve Top-K chunks**

User asks: *"Explain stack operations"*

TF-IDF retrieves:
```
Chunk 1: "A stack is a linear data structure that follows LIFO order..."
Chunk 2: "The push operation inserts an element at the top of the stack..."
Chunk 3: "The pop operation removes the topmost element from the stack..."
```

**Step 2 — Synthesize**

The `synthesizer.py` module:
- Splits each chunk into sentences
- Removes near-duplicate sentences using Jaccard similarity
- Connects them with grammatical connectors
- Returns a single fluent response

**Step 3 — Output**

```
A stack is a linear data structure that follows LIFO order. Additionally, 
the push operation inserts an element at the top of the stack. Furthermore, 
the pop operation removes the topmost element from the stack.
```

This feels generative because it *is* synthesized — but deterministically, from your actual knowledge, with zero hallucination.

### When to add an LLM (optional)

The synthesizer is designed as a **drop-in replacement point**. When you're ready to add an LLM:

```
User Query
    ↓
MMF retrieves Top-K structured chunks  ← this part stays exactly the same
    ↓
Send chunks + query to Ollama / GPT-4  ← swap synthesizer.py for this
    ↓
LLM generates fluent answer grounded in your data
```

MMF's retrieval pipeline becomes the **retriever** in a proper RAG system the moment you wire in a generation model. The architecture is already designed for this.

---

## Architecture

```
User Input (Chat UI)
        │
        ▼
  Flask REST API
  /chat · /chat/context · /knowledge/*
        │
        ▼
   MMF Runtime
   normalize_query()
        │
        ▼
  TfidfMatcher.find_best_match()
        │
   ┌────┴─────────────┐
   │                  │
Persistent         Ad-Hoc Context
Knowledge          (session-only, attached files)
(assistant.mmf)
weight: 0.55       weight: 0.45
   │                  │
   └────── Blend ─────┘
           Sort ↓
     Top-K Above Threshold
           │
           ▼
     synthesizer.synthesize()
     (multi-chunk deduplication + connectors)
           │
           ▼
  { response, source, similarity,
    final_score, matched_query, chunks_used }
```

### Scoring formula

```
final_score = (0.7 × cosine_similarity) + (0.3 × node_confidence)
```

Context blending weights:
- Persistent MMF knowledge → `× 0.55`
- Session-attached files   → `× 0.45`

---

## Features

- **Semantic Search** — TF-IDF cosine similarity with top-K ranking, soft thresholding, and per-response explainability
- **Response Synthesizer** — Merges multiple retrieved chunks into one coherent answer using deterministic rule-based NLP
- **Self-Learning** — Add, edit, or remove knowledge live in the UI; changes hot-reload without restarting Flask
- **Document Ingestion** — Parse `.pdf`, `.csv`, `.txt`, `.js`, `.sql` into structured semantic nodes
- **Hybrid Query Generator** — Converts raw text chunks into 3–5 retrieval-optimized query variants per node
- **Context-Aware Chat (RAG-style)** — Attach files temporarily; nodes blend into every query without being saved
- **HuggingFace Import** — Pull any public dataset via the HuggingFace Datasets API. No API key required
- **Explainable Outputs** — Every response returns `similarity`, `final_score`, `matched_query`, `source`, `chunks_used`
- **Modern Chat UI** — ChatGPT-style interface, dark/light mode, typing indicators, toast notifications, progress bars
- **Chat Export** — Download any conversation as a structured `.md` file

---

## Demo Flow

**1 — Ask something the system doesn't know**
```
You: What is gradient descent?
MMF: No suitable knowledge found.
```

**2 — Teach it directly in the UI**
```
⚙️ Matrix Core → + Inject Node
Query:    "what is gradient descent"
Response: "An optimization algorithm that minimizes a loss function by
           iteratively adjusting parameters in the direction of steepest descent."
```

**3 — Ask again**
```
You: what is gradient descent?
MMF: An optimization algorithm that minimizes a loss function by iteratively
     adjusting parameters in the direction of steepest descent.
     [similarity: 0.94 | score: 0.76 | chunks used: 1]
```

**4 — Upload a textbook, ask a multi-chunk question**
```
[+] Attach: ml_textbook.pdf  →  75 nodes extracted

You: Explain backpropagation and how it uses gradient descent
MMF: Backpropagation is an algorithm for computing gradients in neural networks.
     Additionally, it uses the chain rule to propagate error signals backward
     through each layer. Furthermore, these gradients are then applied by
     gradient descent to update the network's weights.
     [📎 From: ml_textbook.pdf | chunks used: 3]
```

---

## Installation

```bash
# Clone the repo
git clone https://github.com/Rohan-Boddu/mmf
cd mmf

# Install dependencies (no GPU, no CUDA, no downloads > 50MB)
pip install -r requirements.txt

# Start the engine
python main.py
```

Open `frontend/index.html` in your browser. Flask runs on `http://localhost:5000`.

---

## Project Structure

```
mmf/
│
├── backend/
│   ├── app.py                   # Flask factory — CORS, blueprint registration
│   ├── mmf/
│   │   ├── runtime.py           # Orchestrates: query → retrieve → synthesize → respond
│   │   ├── matcher.py           # TF-IDF engine + ephemeral ad-hoc context blending
│   │   ├── synthesizer.py       # Rule-based response synthesizer (multi-chunk fusion)
│   │   ├── learner.py           # Deduplication, merging, atomic persistence
│   │   ├── ingestor.py          # Multi-format document parser
│   │   ├── query_generator.py   # Zero-dependency semantic query expander
│   │   ├── builder.py           # Compiles mmf_dev/ → assistant.mmf ZIP binary
│   │   ├── loader.py            # Loads .mmf binary into memory
│   │   ├── extractor.py         # Heuristic NLP pattern extraction
│   │   └── processor.py         # Text normalization utilities
│   └── routes/
│       ├── chat.py              # /chat · /chat/context
│       └── knowledge.py         # CRUD · ingest · export · bulk ops · HuggingFace
│
├── frontend/
│   ├── index.html               # UI shell — modals, context strip, panels
│   ├── style.css                # Design system — glassmorphism, toasts, progress bars
│   └── script.js                # UI logic — context, chat export, CRUD, bulk ops
│
├── main.py                      # Entry point — builds .mmf and starts Flask
├── requirements.txt
├── AGENT_RULES.md               # Architecture governance rules
└── CHANGELOG.md                 # Full version history
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Query the engine (supports `ad_hoc_knowledge` array) |
| `POST` | `/api/chat/context` | Extract nodes from a file for session-wide context |
| `GET` | `/api/knowledge` | List all knowledge nodes |
| `POST` | `/api/knowledge` | Add a single node |
| `PUT` | `/api/knowledge/<id>` | Update a node |
| `DELETE` | `/api/knowledge/<id>` | Delete a node |
| `POST` | `/api/knowledge/bulk-delete` | Delete multiple nodes by ID |
| `POST` | `/api/knowledge/ingest` | Ingest a document file |
| `POST` | `/api/knowledge/csv-headers` | Peek at CSV column names |
| `GET` | `/api/knowledge/export` | Download `assistant.mmf` binary |
| `GET` | `/api/knowledge/export/nodes` | Download all nodes as CSV |
| `POST` | `/api/knowledge/import` | Upload and replace with a `.mmf` binary |
| `POST` | `/api/knowledge/import/huggingface` | Import rows from a HuggingFace dataset |

---

## Why This Project Matters

**No retraining.** Add, correct, or remove knowledge instantly through the UI. The engine hot-reloads in milliseconds. This is architecturally impossible with fine-tuned or pre-trained models.

**Lightweight AI alternative.** Runs on any laptop. No GPU, no 70GB model downloads, no Docker, no cloud account. The `.mmf` binary is a ZIP — portable, versionable, shareable.

**Generative without an LLM.** The rule-based synthesizer fuses multiple retrieved chunks into coherent, connected responses. When you're ready to upgrade to an LLM, you swap one function — the retrieval pipeline stays identical.

**Explainable by default.** Every response tells you which query matched, what the cosine similarity was, what the final score was, and how many chunks were used. There are no black boxes.

**Modular by design.** Every component has strict bounded responsibilities. Swapping TF-IDF for FAISS, adding auth, or wiring in Ollama requires changes to exactly one file each.

---

## Roadmap

- [ ] **LLM Generation Layer** — Send retrieved chunks to Ollama / OpenAI / Gemini for fluent, grounded answers(optional)
- [ ] **Rule-Based Response Synthesizer** — Implement a lightweight generation layer to combine top-k retrieved chunks into coherent, human-readable answers                                                    without relying on LLMs.
- [ ] **Neural Embeddings** — Replace TF-IDF with `sentence-transformers` for deep semantic similarity
- [ ] **FAISS Vector Index** — Scale to millions of nodes without memory pressure
- [ ] **Streaming Responses** — Server-sent events for real-time token output
- [ ] **Multi-User Sessions** — Isolated session contexts with lightweight auth

---

## License

MIT — see [LICENSE](LICENSE).

---

## Author

**Rohan Boddu**
Built as an exploration of production-grade AI knowledge systems without model dependencies — proving that intelligent retrieval, dynamic learning, and explainability don't require a pre-trained model.

---

<div align="center">
<sub>No cloud. No retraining. No black boxes.</sub>
</div>
