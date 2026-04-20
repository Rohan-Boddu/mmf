"""
test_synthesizer.py — Unit tests for MMF Synthesizer module.
Tests deduplication, chunk merging, intent-based synthesis.
"""
import pytest
import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from mmf.synthesizer import synthesize, _deduplicate, _detect_intent, _extract_content, _extract_code


class TestDeduplicate:
    """Tests for the _deduplicate helper."""

    def test_removes_exact_duplicates(self):
        items = ["Binary Tree", "Linked List", "Binary Tree"]
        result = _deduplicate(items)
        assert len(result) == 2
        assert result[0] == "Binary Tree"
        assert result[1] == "Linked List"

    def test_removes_case_insensitive_duplicates(self):
        items = ["Hash Table", "hash table", "HASH TABLE"]
        result = _deduplicate(items)
        assert len(result) == 1

    def test_removes_punctuation_variants(self):
        items = ["Binary-Tree", "Binary Tree", "binary_tree"]
        result = _deduplicate(items)
        assert len(result) == 1

    def test_preserves_order(self):
        items = ["C", "B", "A"]
        result = _deduplicate(items)
        assert result == ["C", "B", "A"]

    def test_skips_empty_strings(self):
        items = ["", "  ", "Valid", ""]
        result = _deduplicate(items)
        assert result == ["Valid"]

    def test_empty_input(self):
        assert _deduplicate([]) == []


class TestDetectIntentSynthesizer:
    """Tests for the synthesizer's _detect_intent (may differ from matcher's)."""

    def test_visualization_intent(self):
        assert _detect_intent("show me the tree") == "visualization"
        assert _detect_intent("visualize the graph") == "visualization"
        assert _detect_intent("animate the sort") == "visualization"

    def test_steps_intent(self):
        assert _detect_intent("step by step binary search") == "steps"
        assert _detect_intent("step-by-step quicksort") == "steps"

    def test_comparison_intent(self):
        assert _detect_intent("compare arrays vs linked lists") == "comparison"

    def test_implementation_intent(self):
        assert _detect_intent("implement bubble sort") == "implementation"


class TestSynthesize:
    """Tests for the core synthesize function."""

    def _make_chunk(self, response, queries=None, intent="definition", source="manual", content_json=None):
        item = {
            "id": "test-id",
            "queries": queries or ["test query"],
            "response": response,
            "source": source,
            "confidence": 1.0,
        }
        if content_json:
            item["content_json"] = json.dumps(content_json)
        return {
            "item": item,
            "response": response,
            "similarity": 0.9,
            "final_score": 0.85,
            "matching_query": queries[0] if queries else "test query",
            "source": source,
            "intent": intent
        }

    def test_empty_chunks_returns_fallback(self):
        result = synthesize([])
        assert "couldn't find" in result.lower()

    def test_single_chunk_returns_response(self):
        chunk = self._make_chunk(
            response="A binary search tree is a hierarchical data structure.",
            queries=["what is BST"],
            content_json={"title": "BST", "summary": "A binary search tree is a hierarchical data structure."}
        )
        result = synthesize([chunk], query="what is BST")
        assert "BST" in result
        assert "binary search tree" in result.lower()

    def test_structured_content_with_key_points(self):
        chunk = self._make_chunk(
            response="",
            queries=["what is array"],
            content_json={
                "title": "Array",
                "summary": "An array is a contiguous block of memory.",
                "key_points": ["O(1) random access", "Fixed size in static arrays"]
            }
        )
        result = synthesize([chunk], query="what is array")
        assert "Key Points" in result
        assert "O(1) random access" in result

    def test_implementation_intent_extracts_code(self):
        chunk = self._make_chunk(
            response="",
            queries=["implement binary search"],
            intent="implementation",
            content_json={
                "title": "Binary Search",
                "summary": "Binary search divides the search interval in half.",
                "code": {"python": "def binary_search(arr, target):\n    pass"}
            }
        )
        result = synthesize([chunk], query="implement binary search in python")
        assert "Implementation" in result
        assert "binary_search" in result

    def test_deduplication_across_chunks(self):
        chunk1 = self._make_chunk(
            response="",
            queries=["what is stack"],
            content_json={
                "title": "Stack",
                "summary": "A stack is a LIFO data structure.",
                "key_points": ["LIFO ordering", "Push and Pop operations"]
            }
        )
        chunk2 = self._make_chunk(
            response="",
            queries=["stack data structure"],
            intent="definition",
            content_json={
                "title": "Stack Operations",
                "summary": "Stack supports push, pop, peek.",
                "key_points": ["LIFO ordering", "Peek returns top element"]
            }
        )
        result = synthesize([chunk1, chunk2], query="what is stack")
        # "LIFO ordering" should only appear once
        count = result.lower().count("lifo ordering")
        assert count == 1

    def test_short_summary_returns_fallback(self):
        chunk = self._make_chunk(
            response="hi",
            queries=["test"],
            content_json={"title": "Test", "summary": "hi"}
        )
        result = synthesize([chunk], query="test")
        assert "couldn't find" in result.lower()

    def test_max_6_key_points(self):
        chunk = self._make_chunk(
            response="",
            queries=["test"],
            content_json={
                "title": "Test",
                "summary": "This is a test with many key points to verify the limit.",
                "key_points": [f"Point {i}" for i in range(10)]
            }
        )
        result = synthesize([chunk], query="test")
        point_count = result.count("- Point")
        assert point_count <= 6
