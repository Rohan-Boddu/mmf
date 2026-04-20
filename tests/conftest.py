import pytest
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from mmf.loader import MMFLoader
from mmf.matcher import TfidfMatcher
from mmf.runtime import MMFRuntime

@pytest.fixture
def sample_knowledge():
    return [
        {
            "id": "1",
            "queries": ["What is MMF?", "Explain MMF architecture"],
            "response": "MMF is a high-precision retrieval system.",
            "tags": ["architecture", "intro"],
            "confidence": 1.0,
            "source": "manual"
        },
        {
            "id": "2",
            "queries": ["How to install MMF?"],
            "response": "Use pip install -r requirements.txt",
            "tags": ["install", "setup"],
            "confidence": 0.9,
            "source": "manual"
        }
    ]

@pytest.fixture
def temp_mmf_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)
        k_path = path / "knowledge.json"
        
        sample_data = [
            {
                "id": "test-1",
                "queries": ["Test query"],
                "response": "Test response",
                "tags": ["test"],
                "confidence": 1.0,
                "source": "test"
            }
        ]
        
        with open(k_path, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f)
            
        # Create manifest.json and config.json if needed by loader
        with open(path / "manifest.json", 'w') as f:
            json.dump({"version": "0.7.2"}, f)
            
        with open(path / "config.json", 'w') as f:
            json.dump({"match_threshold": 0.5}, f)
            
        yield str(path)

@pytest.fixture
def runtime(temp_mmf_dir):
    loader = MMFLoader(temp_mmf_dir)
    matcher = TfidfMatcher()
    rt = MMFRuntime(loader, matcher)
    rt.initialize()
    return rt
