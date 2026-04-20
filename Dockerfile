# --- Stage 1: Build ---
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: Runtime ---
FROM python:3.11-slim

LABEL maintainer="MMF Platform Team"
LABEL version="0.7.2"
LABEL description="MMF — Deterministic High-Precision Retrieval Engine"

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY mmf_dev/ ./mmf_dev/
COPY config.json ./
COPY requirements.txt ./

# Create non-root user for security
RUN useradd --create-home mmfuser && \
    chown -R mmfuser:mmfuser /app
USER mmfuser

# Environment defaults
ENV PORT=5000
ENV DEBUG=False
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Run with gunicorn in production
CMD ["gunicorn", "--config", "gunicorn.conf.py", "backend.app:create_app()"]
