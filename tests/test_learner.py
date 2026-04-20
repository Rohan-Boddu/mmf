"""
test_learner.py — Unit tests for MMF Learner module.
Tests merge correctness, atomic writes, batch learning.
"""
import pytest
import os
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from mmf.learner import MMFLearner


@pytest.fixture
def temp_knowledge_dir():
    """Creates a temporary directory with a valid knowledge.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        k_path = Path(tmpdir) / "knowledge.json"
        seed = [
            {
                "id": "existing-1",
                "queries": ["what is python"],
                "response": "Python is a programming language.",
                "tags": ["python", "language"],
                "source": "manual",
                "confidence": 1.0
            },
            {
                "id": "existing-2",
                "queries": ["what is javascript"],
                "response": "JavaScript is a web programming language.",
                "tags": ["javascript", "web"],
                "source": "manual",
                "confidence": 0.9
            }
        ]
        with open(k_path, 'w', encoding='utf-8') as f:
            json.dump(seed, f, indent=2)
        yield tmpdir


class TestLearnSingle:
    """Tests for the single-entry learn() method."""

    def test_basic_learn(self, temp_knowledge_dir):
        learner = MMFLearner(temp_knowledge_dir)
        result = learner.learn("what is rust", "Rust is a systems programming language.")
        assert result.get("id")
        assert result["queries"] == ["what is rust"]

        # Verify it was saved to disk
        with open(Path(temp_knowledge_dir) / "knowledge.json", 'r') as f:
            data = json.load(f)
        assert len(data) == 3
        assert any("rust" in str(item.get("queries", [])).lower() for item in data)

    def test_learn_with_tags(self, temp_knowledge_dir):
        learner = MMFLearner(temp_knowledge_dir)
        result = learner.learn("what is go", "Go is a language by Google.", tags=["go", "google"])
        assert "go" in result.get("tags", [])

    def test_learn_empty_query_skipped(self, temp_knowledge_dir):
        learner = MMFLearner(temp_knowledge_dir)
        result = learner.learn("", "Some response")
        assert result == {}

    def test_learn_empty_response_skipped(self, temp_knowledge_dir):
        learner = MMFLearner(temp_knowledge_dir)
        result = learner.learn("some query", "")
        assert result == {}


class TestLearnBatch:
    """Tests for the batch learn_batch() method."""

    def test_batch_add_new_entries(self, temp_knowledge_dir):
        learner = MMFLearner(temp_knowledge_dir)
        entries = [
            {"queries": ["what is rust"], "response": "Rust is a systems language.", "tags": ["rust"]},
            {"queries": ["what is kotlin"], "response": "Kotlin is a JVM language.", "tags": ["kotlin"]}
        ]
        result = learner.learn_batch(entries)
        assert len(result["added"]) == 2
        assert len(result["merged"]) == 0

    def test_batch_merge_duplicate(self, temp_knowledge_dir):
        learner = MMFLearner(temp_knowledge_dir)
        entries = [
            {"queries": ["what is python"], "response": "Python is an interpreted language.", "tags": ["interpreted"]}
        ]
        result = learner.learn_batch(entries)
        assert len(result["added"]) == 0
        assert len(result["merged"]) == 1

    def test_batch_intra_batch_dedup(self, temp_knowledge_dir):
        learner = MMFLearner(temp_knowledge_dir)
        entries = [
            {"queries": ["what is rust"], "response": "Rust v1."},
            {"queries": ["what is rust"], "response": "Rust v2."}
        ]
        result = learner.learn_batch(entries)
        # Second entry should merge with the first one added
        assert len(result["added"]) == 1
        assert len(result["merged"]) == 1

    def test_batch_empty_entries(self, temp_knowledge_dir):
        learner = MMFLearner(temp_knowledge_dir)
        result = learner.learn_batch([])
        assert result == []

    def test_batch_entries_without_queries_skipped(self, temp_knowledge_dir):
        learner = MMFLearner(temp_knowledge_dir)
        entries = [
            {"queries": [], "response": "Orphan response."}
        ]
        result = learner.learn_batch(entries)
        assert len(result["added"]) == 0


class TestAtomicWrites:
    """Tests for atomic file write behavior."""

    def test_knowledge_file_not_corrupted_after_write(self, temp_knowledge_dir):
        learner = MMFLearner(temp_knowledge_dir)
        learner.learn("test query", "test response")

        k_path = Path(temp_knowledge_dir) / "knowledge.json"
        with open(k_path, 'r', encoding='utf-8') as f:
            data = json.load(f)  # Should not raise
        assert isinstance(data, list)
        assert len(data) == 3

    def test_no_temp_files_left_behind(self, temp_knowledge_dir):
        learner = MMFLearner(temp_knowledge_dir)
        learner.learn("test query", "test response")

        files = os.listdir(temp_knowledge_dir)
        tmp_files = [f for f in files if f.endswith('.tmp')]
        assert len(tmp_files) == 0

    def test_knowledge_preserves_existing_entries(self, temp_knowledge_dir):
        learner = MMFLearner(temp_knowledge_dir)
        learner.learn("new query", "new response")

        with open(Path(temp_knowledge_dir) / "knowledge.json", 'r') as f:
            data = json.load(f)

        ids = [item.get("id") for item in data]
        assert "existing-1" in ids
        assert "existing-2" in ids


class TestCorruptedKnowledge:
    """Tests for behavior with corrupted/malformed knowledge files."""

    def test_load_corrupted_json_raises_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            k_path = Path(tmpdir) / "knowledge.json"
            with open(k_path, 'w') as f:
                f.write("{corrupt json data[[[")

            learner = MMFLearner(tmpdir)
            with pytest.raises(IOError):
                learner.learn("test", "test")

    def test_load_missing_file_raises_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            learner = MMFLearner(tmpdir)
            with pytest.raises(IOError):
                learner.learn("test", "test")
