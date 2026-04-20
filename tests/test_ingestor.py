"""
test_ingestor.py — Unit tests for MMF Ingestor module.
Tests file parsing for txt, csv, js, sql, and malformed inputs.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from mmf.ingestor import process_file_content


class TestTxtIngestion:
    """Tests for plain text file ingestion."""

    def test_basic_txt_ingestion(self):
        content = b"Python is a programming language. Java is an object-oriented language."
        entries = process_file_content("test.txt", content)
        assert isinstance(entries, list)

    def test_empty_txt_returns_empty(self):
        entries = process_file_content("empty.txt", b"")
        assert entries == []

    def test_whitespace_only_txt(self):
        entries = process_file_content("ws.txt", b"   \n\n   ")
        assert entries == []


class TestCsvIngestion:
    """Tests for CSV file ingestion."""

    def test_basic_csv_positional(self):
        content = b"query,response\nWhat is Python?,Python is a language.\nWhat is Java?,Java is a language."
        entries = process_file_content("test.csv", content)
        assert len(entries) >= 2
        assert entries[0]["queries"][0] == "What is Python?"

    def test_csv_with_named_columns(self):
        content = b"question,answer,extra\nWhat is Rust?,Systems language,ignored\nWhat is Go?,Google language,ignored"
        entries = process_file_content("test.csv", content, query_col="question", answer_col="answer")
        assert len(entries) == 2
        assert entries[0]["queries"][0] == "What is Rust?"
        assert entries[0]["response"] == "Systems language"

    def test_csv_with_wrong_column_names_falls_back(self):
        content = b"question,answer\nWhat is X?,X is Y."
        entries = process_file_content("test.csv", content, query_col="nonexistent", answer_col="also_nonexistent")
        # Falls back to positional parsing
        assert len(entries) >= 1

    def test_empty_csv(self):
        entries = process_file_content("empty.csv", b"")
        assert entries == []

    def test_csv_with_only_header(self):
        content = b"query,response"
        entries = process_file_content("header_only.csv", content)
        assert entries == []

    def test_csv_single_column(self):
        content = b"only_one_column\nvalue1\nvalue2"
        entries = process_file_content("single.csv", content)
        assert entries == []  # Needs at least 2 columns


class TestJsIngestion:
    """Tests for JavaScript file ingestion."""

    def test_basic_js_function_extraction(self):
        content = b"""
function greet(name) {
    return "Hello " + name;
}

function add(a, b) {
    return a + b;
}
"""
        entries = process_file_content("test.js", content)
        assert len(entries) == 2
        assert any("greet" in str(e.get("queries", [])) for e in entries)

    def test_empty_js_file(self):
        entries = process_file_content("empty.js", b"")
        assert entries == []

    def test_js_no_functions(self):
        content = b"const x = 5;\nconst y = 10;\nconsole.log(x + y);"
        entries = process_file_content("no_func.js", content)
        assert entries == []


class TestSqlIngestion:
    """Tests for SQL file ingestion."""

    def test_basic_sql_table_extraction(self):
        content = b"""
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(200)
);

CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id INT,
    total DECIMAL(10,2)
);
"""
        entries = process_file_content("test.sql", content)
        assert len(entries) == 2
        assert any("users" in str(e.get("queries", [])) for e in entries)

    def test_empty_sql_file(self):
        entries = process_file_content("empty.sql", b"")
        assert entries == []

    def test_sql_no_tables(self):
        content = b"SELECT * FROM users WHERE id = 1;"
        entries = process_file_content("select.sql", content)
        assert entries == []


class TestMalformedInputs:
    """Tests for edge cases and malformed file inputs."""

    def test_binary_garbage(self):
        content = bytes(range(256)) * 10
        entries = process_file_content("garbage.txt", content)
        assert entries == []

    def test_unsupported_extension(self):
        entries = process_file_content("test.xyz", b"some content")
        assert entries == []

    def test_unicode_content(self):
        content = "Ünïcödé is a character encoding standard.".encode('utf-8')
        entries = process_file_content("unicode.txt", content)
        assert isinstance(entries, list)

    def test_very_large_response_filtered(self):
        """Entries with responses <= 3 chars should be filtered."""
        content = b"query,response\nWhat?,Hi"
        entries = process_file_content("short.csv", content)
        # "Hi" is only 2 chars, should be filtered
        assert all(len(e["response"]) > 3 for e in entries)

    def test_null_bytes_in_content(self):
        content = b"Hello\x00World is a test string."
        entries = process_file_content("null.txt", content)
        assert isinstance(entries, list)
