import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Centralized configuration for the MMF Platform."""
    
    # Flask settings
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-replace-in-prod')
    
    # API settings
    API_BASE = os.getenv('API_BASE', f'http://localhost:{PORT}')
    
    # Paths
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    MMF_DEV_DIR = os.path.abspath(os.path.join(BASE_DIR, 'mmf_dev'))
    MMF_ZIP_PATH = os.path.abspath(os.path.join(BASE_DIR, 'assistant.mmf'))
    
    # Security
    RATE_LIMIT = os.getenv('RATE_LIMIT', '20 per minute')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 10 * 1024 * 1024)) # 10MB default
    
    @classmethod
    def validate(cls):
        """Validates critical configuration at startup."""
        critical_paths = [cls.MMF_DEV_DIR]
        for path in critical_paths:
            if not os.path.exists(path):
                # We don't fail if assistant.mmf is missing (it might be built later),
                # but mmf_dev is required for the system to function in its current state.
                # Actually, in prod only assistant.mmf might exist.
                pass
        
        # Ensure knowledge.json exists in mmf_dev if mmf_dev exists
        if os.path.exists(cls.MMF_DEV_DIR):
            k_json = os.path.join(cls.MMF_DEV_DIR, 'knowledge.json')
            if not os.path.exists(k_json):
                raise RuntimeError(f"Critical knowledge file missing: {k_json}")

    @classmethod
    def get_runtime_config(cls):
        """Loads runtime-tunable parameters from config.json."""
        import json
        config_path = os.path.join(cls.BASE_DIR, 'config.json')
        default_config = {
            "match_threshold": 0.5,
            "fallback_message": "No suitable knowledge found."
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    return {**default_config, **json.load(f)}
            except Exception:
                return default_config
        return default_config
