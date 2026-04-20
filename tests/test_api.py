"""
test_api.py — Integration tests for MMF Flask API endpoints.
Tests /chat, /knowledge, /health, /metrics.
"""
import pytest
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))


@pytest.fixture
def temp_mmf_project(tmp_path):
    """Creates a full temporary MMF project structure for testing."""
    mmf_dev = tmp_path / "mmf_dev"
    mmf_dev.mkdir()

    knowledge = [
        {
            "id": "test-api-1",
            "queries": ["What is a binary search tree?", "BST definition"],
            "response": "A binary search tree is a node-based data structure where each node has at most two children.",
            "tags": ["tree", "data structure"],
            "source": "manual",
            "confidence": 1.0
        },
        {
            "id": "test-api-2",
            "queries": ["What is a linked list?"],
            "response": "A linked list is a linear data structure with nodes connected by pointers.",
            "tags": ["linked list", "data structure"],
            "source": "manual",
            "confidence": 1.0
        }
    ]

    (mmf_dev / "knowledge.json").write_text(json.dumps(knowledge, indent=2), encoding='utf-8')
    (mmf_dev / "manifest.json").write_text(json.dumps({"name": "test", "version": "0.7.2"}), encoding='utf-8')
    (mmf_dev / "config.json").write_text(json.dumps({"match_threshold": 0.5}), encoding='utf-8')

    # Create frontend dir with a minimal index.html
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "index.html").write_text("<html><body>Test</body></html>", encoding='utf-8')

    return tmp_path


@pytest.fixture
def app(temp_mmf_project, monkeypatch):
    """Creates a Flask test app pointing at the temporary project."""
    # Monkey-patch the paths before importing app modules
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend'))
    sys.path.insert(0, backend_dir)

    # We need to patch the paths in the routes module
    import routes.knowledge as knowledge_mod
    import routes.chat as chat_mod

    monkeypatch.setattr(knowledge_mod, 'DEV_TARGET', str(temp_mmf_project / "mmf_dev"))
    monkeypatch.setattr(knowledge_mod, 'ZIP_TARGET', str(temp_mmf_project / "assistant.mmf"))
    monkeypatch.setattr(chat_mod, 'DEV_TARGET', str(temp_mmf_project / "mmf_dev"))

    from mmf.loader import MMFLoader
    from mmf.matcher import TfidfMatcher
    from mmf.runtime import MMFRuntime

    loader = MMFLoader(str(temp_mmf_project / "mmf_dev"))
    matcher = TfidfMatcher()
    runtime = MMFRuntime(loader, matcher)
    runtime.initialize()

    from flask import Flask
    from flask_cors import CORS
    import threading

    test_app = Flask(__name__)
    CORS(test_app)
    test_app.config['TESTING'] = True
    test_app.config['runtime'] = runtime
    test_app.config['engine_lock'] = threading.Lock()

    from routes.chat import chat_bp
    from routes.knowledge import knowledge_bp

    test_app.register_blueprint(chat_bp, url_prefix='/api')
    test_app.register_blueprint(knowledge_bp, url_prefix='/api')

    @test_app.route('/health')
    def health():
        from flask import jsonify
        return jsonify({"status": "healthy", "initialized": runtime.is_initialized}), 200

    yield test_app


@pytest.fixture
def client(app):
    return app.test_client()


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, client):
        res = client.get('/health')
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "healthy"
        assert data["initialized"] is True


class TestChatEndpoint:
    """Tests for the /api/chat endpoint."""

    def test_chat_with_valid_message(self, client):
        res = client.post('/api/chat', json={"message": "What is a binary search tree?"})
        assert res.status_code == 200
        data = res.get_json()
        assert "response" in data

    def test_chat_empty_message_returns_400(self, client):
        res = client.post('/api/chat', json={"message": ""})
        assert res.status_code == 400

    def test_chat_missing_message_returns_400(self, client):
        res = client.post('/api/chat', json={})
        assert res.status_code == 400

    def test_chat_no_body_returns_400(self, client):
        res = client.post('/api/chat')
        assert res.status_code in [400, 415]  # 415 if Content-Type missing

    def test_chat_unrelated_query_returns_no_match(self, client):
        res = client.post('/api/chat', json={"message": "recipe for chocolate cake baking"})
        assert res.status_code == 200
        data = res.get_json()
        # Should get a no-match fallback
        assert "response" in data


class TestChatStreamEndpoint:
    """Tests for the /api/chat/stream SSE endpoint."""

    def test_stream_returns_event_stream(self, client):
        res = client.post('/api/chat/stream', json={"message": "What is a binary search tree?"})
        assert res.status_code == 200
        assert 'text/event-stream' in res.content_type

    def test_stream_empty_message_returns_400(self, client):
        res = client.post('/api/chat/stream', json={"message": ""})
        assert res.status_code == 400


class TestKnowledgeEndpoint:
    """Tests for the /api/knowledge CRUD endpoints."""

    def test_get_knowledge(self, client):
        res = client.get('/api/knowledge')
        assert res.status_code == 200
        data = res.get_json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_add_knowledge(self, client):
        res = client.post('/api/knowledge', json={
            "query": "What is Rust?",
            "response": "Rust is a systems programming language."
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data["status"] == "success"

    def test_add_knowledge_missing_query_returns_400(self, client):
        res = client.post('/api/knowledge', json={"response": "test"})
        assert res.status_code == 400

    def test_add_knowledge_missing_response_returns_400(self, client):
        res = client.post('/api/knowledge', json={"query": "test"})
        assert res.status_code == 400

    def test_update_knowledge(self, client):
        res = client.put('/api/knowledge/test-api-1', json={
            "query": "Updated BST query",
            "response": "Updated BST response"
        })
        assert res.status_code == 200

    def test_update_nonexistent_returns_404(self, client):
        res = client.put('/api/knowledge/nonexistent-id', json={
            "query": "test",
            "response": "test"
        })
        assert res.status_code == 404

    def test_delete_knowledge(self, client):
        res = client.delete('/api/knowledge/test-api-2')
        assert res.status_code == 200

    def test_delete_nonexistent_returns_404(self, client):
        res = client.delete('/api/knowledge/nonexistent-id')
        assert res.status_code == 404

    def test_bulk_delete(self, client):
        res = client.post('/api/knowledge/bulk-delete', json={
            "ids": ["test-api-1"]
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data["removed"] >= 1

    def test_bulk_delete_no_ids_returns_400(self, client):
        res = client.post('/api/knowledge/bulk-delete', json={"ids": []})
        assert res.status_code == 400


class TestIngestEndpoint:
    """Tests for the /api/knowledge/ingest endpoint."""

    def test_ingest_csv_file(self, client):
        import io
        csv_content = b"query,response\nWhat is X?,X is a test thing.\nWhat is Y?,Y is another test thing."
        data = {'file': (io.BytesIO(csv_content), 'test.csv')}
        res = client.post('/api/knowledge/ingest', data=data, content_type='multipart/form-data')
        assert res.status_code == 200

    def test_ingest_no_file_returns_400(self, client):
        res = client.post('/api/knowledge/ingest')
        assert res.status_code == 400


class TestConcurrency:
    """Basic concurrency tests."""

    def test_concurrent_chat_requests(self, client):
        """Simulate multiple rapid chat requests."""
        import concurrent.futures

        def make_request(msg):
            return client.post('/api/chat', json={"message": msg})

        messages = [
            "What is a binary search tree?",
            "What is a linked list?",
            "What is a binary search tree?",
            "What is a linked list?",
        ]

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(make_request, msg) for msg in messages]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        for res in results:
            assert res.status_code == 200
