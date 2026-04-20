"""
mmf_logger.py — Structured logging for the MMF Platform.
Provides JSON-formatted logs with request ID tracking.
"""
import logging
import json
import time
import uuid
import os
from functools import wraps


class JSONFormatter(logging.Formatter):
    """Formats log records as structured JSON for production observability."""

    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        for field in ['request_id', 'route', 'method', 'latency_ms', 'query',
                      'match_score', 'status_code', 'ip', 'user_agent']:
            if hasattr(record, field):
                log_entry[field] = getattr(record, field)

        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(level=None):
    """Configures the root MMF logger with structured JSON output."""
    log_level = level or os.getenv('LOG_LEVEL', 'INFO').upper()

    logger = logging.getLogger('mmf')
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Avoid duplicate handlers on re-initialization
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    # Suppress noisy libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    return logger


def get_logger(name='mmf'):
    """Returns a named child logger under the mmf namespace."""
    return logging.getLogger(f'mmf.{name}')


# --- Metrics Collector ---

class MetricsCollector:
    """Simple in-memory metrics collector for request counts, latency, errors."""

    def __init__(self):
        self._data = {
            "total_requests": 0,
            "total_errors": 0,
            "total_chat_requests": 0,
            "total_knowledge_requests": 0,
            "avg_latency_ms": 0.0,
            "latency_samples": [],
        }

    def record_request(self, route: str, latency_ms: float, is_error: bool = False):
        self._data["total_requests"] += 1
        if is_error:
            self._data["total_errors"] += 1
        if '/chat' in route:
            self._data["total_chat_requests"] += 1
        elif '/knowledge' in route:
            self._data["total_knowledge_requests"] += 1

        self._data["latency_samples"].append(latency_ms)
        # Keep only last 1000 samples to bound memory
        if len(self._data["latency_samples"]) > 1000:
            self._data["latency_samples"] = self._data["latency_samples"][-1000:]

        samples = self._data["latency_samples"]
        self._data["avg_latency_ms"] = round(sum(samples) / len(samples), 2)

    def get_metrics(self) -> dict:
        samples = self._data["latency_samples"]
        return {
            "total_requests": self._data["total_requests"],
            "total_errors": self._data["total_errors"],
            "total_chat_requests": self._data["total_chat_requests"],
            "total_knowledge_requests": self._data["total_knowledge_requests"],
            "avg_latency_ms": self._data["avg_latency_ms"],
            "p95_latency_ms": round(sorted(samples)[int(len(samples) * 0.95)] if samples else 0, 2),
            "p99_latency_ms": round(sorted(samples)[int(len(samples) * 0.99)] if samples else 0, 2),
        }


# Global metrics instance
metrics = MetricsCollector()
