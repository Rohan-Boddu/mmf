"""
gunicorn.conf.py — Production WSGI configuration for MMF Platform.
"""
import multiprocessing
import os

# Server Socket
bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"

# Worker Processes
# Formula: (2 × CPU cores) + 1
workers = (2 * multiprocessing.cpu_count()) + 1

# Worker class
worker_class = "sync"

# Timeout (seconds) — kills workers that are silent for too long
timeout = 30

# Preload app — loads the application before forking workers
# Saves memory via copy-on-write, but means app code changes require full restart
preload_app = True

# Max requests per worker before recycling (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = os.getenv("LOG_LEVEL", "info")

# Graceful shutdown
graceful_timeout = 10

# Security
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190
