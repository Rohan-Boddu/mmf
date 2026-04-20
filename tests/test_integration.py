"""
test_integration.py — End-to-end integration tests for the MMF Platform.
Covers: Document Ingestion -> Learning -> Retrieval Pipeline.
"""
import pytest
import os
import io
import json
import time
from pathlib import Path

def test_full_ingest_to_query_pipeline(client):
    """
    Test the full pipeline:
    1. Ingest a CSV file via API
    2. Verify it's in the knowledge base
    3. Query the chat and verify retrieval
    """
    # 1. Ingest CSV
    csv_content = b"query,response\nWhat is a quantum bit?,A qubit or quantum bit is the basic unit of quantum information.\nHow does quantum entanglement work?,Entanglement is a physical phenomenon where particles remain connected."
    data = {'file': (io.BytesIO(csv_content), 'quantum.csv')}
    
    ingest_res = client.post('/api/knowledge/ingest', data=data, content_type='multipart/form-data')
    assert ingest_res.status_code == 200
    
    # 2. Verify knowledge base update
    # Note: In the test environment, we need to ensure the runtime reloads or we use the updated knowledge
    # The API /api/knowledge should show the new entries
    knowledge_res = client.get('/api/knowledge')
    assert knowledge_res.status_code == 200
    knowledge = knowledge_res.get_json()
    
    found_qubit = False
    for item in knowledge:
        if "quantum bit" in str(item.get("queries", [])).lower():
            found_qubit = True
            break
    assert found_qubit, "Ingested entry 'quantum bit' not found in knowledge base"

    # 3. Query Chat
    # Give the async learner a tiny bit of time if needed, 
    # though in the test client it might be synchronous depending on setup.
    # Our API actually re-initializes runtime if needed or uses the same DEV_TARGET.
    chat_res = client.post('/api/chat', json={"message": "explain quantum bit"})
    assert chat_res.status_code == 200
    chat_data = chat_res.get_json()
    
    assert "qubit" in chat_data["response"].lower()
    assert "basic unit" in chat_data["response"].lower()

def test_concurrent_writes_protection(client, app):
    """
    Test that concurrent writes are handled without corruption.
    We'll simulate multiple simultaneous ingestion requests.
    """
    import concurrent.futures
    import io

    def make_ingest_request(i):
        content = f"query,response\nQuery {i},Response {i}".encode('utf-8')
        data = {'file': (io.BytesIO(content), f'file_{i}.csv')}
        return client.post('/api/knowledge/ingest', data=data, content_type='multipart/form-data')

    # Run 5 concurrent ingestions
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_ingest_request, i) for i in range(5)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # All should succeed (eventually, after waiting for lock)
    for res in results:
        assert res.status_code == 200

    # Verify count
    knowledge_res = client.get('/api/knowledge')
    knowledge = knowledge_res.get_json()
    
    # Check that we have at least the 5 new entries
    responses = [item.get("response") for item in knowledge]
    for i in range(5):
        assert f"Response {i}" in responses
