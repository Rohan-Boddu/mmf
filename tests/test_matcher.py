"""
test_matcher.py — Unit tests for MMF Matcher module.
Tests intent detection, scoring, threshold edge cases.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from mmf.matcher import detect_intent, TfidfMatcher


class TestDetectIntent:
    """Tests for the detect_intent helper function."""

    def test_implementation_intent(self):
        assert detect_intent("implement binary search") == "implementation"
        assert detect_intent("show me the code for quicksort") == "implementation"

    def test_comparison_intent(self):
        assert detect_intent("stack vs queue") == "comparison"
        assert detect_intent("difference between array and linked list") == "comparison"

    def test_debugging_intent(self):
        assert detect_intent("why does my program fail") == "debugging"
        assert detect_intent("segfault error in C") == "debugging"

    def test_explanation_intent(self):
        assert detect_intent("how does a hash table work") == "explanation"
        assert detect_intent("explain recursion") == "explanation"

    def test_definition_intent_fallback(self):
        assert detect_intent("binary search tree") == "definition"
        assert detect_intent("linked list") == "definition"

    def test_empty_query_returns_definition(self):
        assert detect_intent("") == "definition"

    def test_case_insensitivity(self):
        assert detect_intent("IMPLEMENT quicksort") == "implementation"
        assert detect_intent("WHY does it FAIL") == "debugging"


class TestTfidfMatcher:
    """Tests for the TfidfMatcher class."""

    @pytest.fixture
    def matcher(self):
        return TfidfMatcher()

    @pytest.fixture
    def knowledge_base(self):
        return [
            {
                "id": "1",
                "queries": ["What is a binary search tree?", "BST definition"],
                "response": "A binary search tree is a data structure...",
                "tags": ["tree", "binary", "data structure"],
                "confidence": 1.0,
                "source": "manual"
            },
            {
                "id": "2",
                "queries": ["What is a linked list?", "linked list definition"],
                "response": "A linked list is a linear data structure...",
                "tags": ["linked list", "data structure"],
                "confidence": 1.0,
                "source": "manual"
            },
            {
                "id": "3",
                "queries": ["What is a hash table?", "hash map"],
                "response": "A hash table is a data structure for key-value storage...",
                "tags": ["hash", "data structure"],
                "confidence": 1.0,
                "source": "manual"
            },
        ]

    def test_exact_match_returns_result(self, matcher, knowledge_base):
        result = matcher.find_best_match("What is a binary search tree?", knowledge_base, 0.5)
        assert result["type"] == "match"
        assert "top_matches" in result
        assert result["top_matches"][0]["similarity"] > 0.5

    def test_no_match_below_threshold(self, matcher, knowledge_base):
        result = matcher.find_best_match("quantum physics entanglement", knowledge_base, 0.5)
        assert result["type"] == "no_match"

    def test_threshold_edge_case_just_above(self, matcher, knowledge_base):
        """Test that a query scoring just at or above the HARD_THRESHOLD is returned."""
        result = matcher.find_best_match("binary search tree data structure", knowledge_base, 0.5)
        if result["type"] == "match":
            assert result["top_matches"][0]["final_score"] >= 0.6  # HARD_THRESHOLD

    def test_threshold_edge_case_just_below(self, matcher, knowledge_base):
        """Test that unrelated queries are rejected."""
        result = matcher.find_best_match("recipe for chocolate cake", knowledge_base, 0.5)
        assert result["type"] == "no_match"

    def test_empty_knowledge_base(self, matcher):
        result = matcher.find_best_match("test query", [], 0.5)
        assert result["type"] == "no_match"

    def test_empty_query(self, matcher, knowledge_base):
        result = matcher.find_best_match("", knowledge_base, 0.5)
        assert result["type"] == "no_match"

    def test_cache_invalidation_on_knowledge_change(self, matcher, knowledge_base):
        """Test that the matcher rebuilds its index when knowledge changes."""
        matcher.find_best_match("binary search tree", knowledge_base, 0.5)
        old_hash = matcher.cached_knowledge_hash

        knowledge_base.append({
            "id": "4",
            "queries": ["What is a stack?"],
            "response": "A stack is a LIFO data structure.",
            "tags": ["stack"],
            "confidence": 1.0,
            "source": "manual"
        })
        matcher.find_best_match("what is a stack", knowledge_base, 0.5)
        assert matcher.cached_knowledge_hash != old_hash

    def test_top_matches_limited_to_3(self, matcher, knowledge_base):
        result = matcher.find_best_match("data structure", knowledge_base, 0.1)
        if result["type"] == "match":
            assert len(result["top_matches"]) <= 3

    def test_language_detection(self, matcher):
        assert matcher._detect_language("implement in c++") == "cpp"
        assert matcher._detect_language("python solution") == "python"
        assert matcher._detect_language("write in c code") == "c"
        assert matcher._detect_language("what is a tree") is None
