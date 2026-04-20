# MMF v0.7.2 — Production Hardening Walkthrough

## Overview

v0.7.2 is a **non-functional upgrade** — no changes to the retrieval engine, scoring logic, or matching behavior. This release focuses entirely on production readiness: testing, deployment, observability, security, and data safety.

## What Changed

### 🧪 Testing (Phase 2)
- **88 automated tests** across 5 test suites
- Covers: matcher, synthesizer, learner, ingestor, and full API integration
- Includes concurrency testing (4 parallel threads)
- Coverage: **68% overall**, core modules 74–96%

### 🐳 Deployment (Phase 3)
- **Dockerfile**: Multi-stage build, non-root user, healthcheck
- **docker-compose.yml**: Persistent volumes for data and backups
- **gunicorn.conf.py**: Dynamic workers, preloading, request limits
- **Frontend**: Auto-detects API URL based on current hostname

### 📊 Observability (Phase 4)
- **Structured JSON logging** replacing all `print()` statements
- **Request ID tracking** via `X-Request-ID` header
- **`/health` endpoint**: System status, initialization, version
- **`/metrics` endpoint**: Request counts, latency (avg/p95/p99), errors

### 🔒 Security (Phase 5)
- **Input sanitization**: 2000 char limit, stripped, validated
- **10MB upload limit** configurable via environment
- **Structured error logging** for background learner

### 💾 Data Safety (Phase 6)
- **Atomic write flow**: Write → Validate → Backup → Replace
- **Versioning**: Auto-timestamped backups (max 10 kept)
- **Rollback**: Restore any previous knowledge.json version
- **Corruption detection**: Validate knowledge structure on demand

### 🖥️ CLI (Phase 7)
Commands: `serve`, `validate`, `stats`, `rollback`, `test-query`, `build`, `interactive`

### ⚙️ Configuration (Phase 1)
- `config.py`: Centralized, environment-aware configuration
- `.env.example`: Template for all configurable values
- `config.json`: Runtime-tunable parameters

### 🔄 CI/CD
- GitHub Actions workflow: lint + test + coverage on Python 3.10–3.12

## How to Run

### Development
```bash
pip install -r requirements.txt
python main.py serve --debug
```

### Tests
```bash
python -m pytest tests/ -v --cov=backend/mmf
```

### Docker
```bash
docker-compose up --build
```

### CLI
```bash
python main.py validate
python main.py stats
python main.py test-query "what is binary search"
python main.py rollback --version=knowledge_20260420_120000.json
```
