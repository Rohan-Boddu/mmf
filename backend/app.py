from flask import Flask, jsonify, request as flask_request, g
from flask_cors import CORS
import threading
import os
import sys
import time
import uuid
from flasgger import Swagger

# Ensure project root and backend directory are in sys.path for robust imports
current_dir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from backend.config import Config
from mmf_logger import setup_logging, get_logger, metrics
from mmf.loader import MMFLoader
from mmf.matcher import TfidfMatcher
from mmf.runtime import MMFRuntime

# Initialize structured logging
setup_logging()
logger = get_logger('app')

# Validate configuration at startup (fail fast)
Config.validate()
logger.info("Configuration validated successfully.")

# Configure MMF Architecture Hooks
ZIP_TARGET = Config.MMF_ZIP_PATH if os.path.exists(Config.MMF_ZIP_PATH) else Config.MMF_DEV_DIR

# Singletons mapping to structural nodes natively
loader = MMFLoader(ZIP_TARGET)
matcher = TfidfMatcher()
runtime = MMFRuntime(loader, matcher)
runtime.initialize()
logger.info("MMF Runtime initialized.", extra={"source": ZIP_TARGET})

# Cross-Thread Architecture Locks
engine_lock = threading.Lock()

def create_app() -> Flask:
    """Initializes and returns the Flask application mapping components globally."""
    app = Flask(__name__)
    CORS(app)

    # Swagger Configuration
    app.config['SWAGGER'] = {
        'title': 'MMF Platform API',
        'uiversion': 3,
        'description': 'Deterministic High-Precision Retrieval Engine API'
    }
    Swagger(app)

    app.config.from_object(Config)

    # Store global logical objects natively
    app.config['runtime'] = runtime
    app.config['engine_lock'] = engine_lock

    # --- Request ID Tracking Middleware ---
    @app.before_request
    def before_request_hook():
        g.request_id = flask_request.headers.get('X-Request-ID', str(uuid.uuid4()))
        g.start_time = time.time()

    @app.after_request
    def after_request_hook(response):
        latency_ms = (time.time() - g.get('start_time', time.time())) * 1000
        response.headers['X-Request-ID'] = g.get('request_id', 'unknown')

        # Record metrics
        is_error = response.status_code >= 400
        metrics.record_request(flask_request.path, latency_ms, is_error)

        # Structured log for every request
        logger.info(
            f"{flask_request.method} {flask_request.path} -> {response.status_code}",
            extra={
                'request_id': g.get('request_id'),
                'route': flask_request.path,
                'method': flask_request.method,
                'latency_ms': round(latency_ms, 2),
                'status_code': response.status_code,
                'ip': flask_request.remote_addr,
            }
        )
        return response

    # Register architecture blueprints
    from routes.chat import chat_bp
    from routes.knowledge import knowledge_bp

    app.register_blueprint(chat_bp, url_prefix='/api')
    app.register_blueprint(knowledge_bp, url_prefix='/api')

    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy",
            "initialized": runtime.is_initialized,
            "version": "0.7.2"
        }), 200

    # Metrics endpoint
    @app.route('/metrics')
    def metrics_endpoint():
        return jsonify(metrics.get_metrics()), 200

    # Native UI Routing overrides
    from flask import send_from_directory
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend'))

    @app.route('/')
    def serve_index():
        return send_from_directory(frontend_dir, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory(frontend_dir, path)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)
