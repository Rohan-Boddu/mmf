from flask import Flask
from flask_cors import CORS
import threading
import os
import sys

# Ensure backend can import mmf dynamically properly mapped via user specs
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from mmf.loader import MMFLoader
from mmf.matcher import TfidfMatcher
from mmf.runtime import MMFRuntime

# Configure MMF Architecture Hooks (Mapped uniquely to 'assistant.mmf' ZIP as built production data)
ZIP_TARGET = os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../assistant.mmf'))

# Singletons mapping to structural nodes natively
loader = MMFLoader(ZIP_TARGET)
matcher = TfidfMatcher()
runtime = MMFRuntime(loader, matcher)
runtime.initialize()

# Cross-Thread Architecture Locks (Prevents concurrent users crashing model during reload phase)
engine_lock = threading.Lock()

def create_app():
    """Initializes and returns the rigid Flask application mapping components globally."""
    app = Flask(__name__)
    CORS(app) # Enable Cross-Origin safely mapping the separated frontend UI
    
    # Store global logical objects natively directly in app logic bypassing cyclic loads
    app.config['runtime'] = runtime
    app.config['engine_lock'] = engine_lock
    
    # Register architecture blueprints
    from routes.chat import chat_bp
    from routes.knowledge import knowledge_bp
    
    app.register_blueprint(chat_bp, url_prefix='/api')
    app.register_blueprint(knowledge_bp, url_prefix='/api')

    # Native UI Routing overrides (Preventing 404s when users hit the server root!)
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
    app.run(host='0.0.0.0', port=5000, debug=False)
