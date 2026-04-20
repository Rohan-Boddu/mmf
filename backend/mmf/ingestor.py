import re
import csv
import io
from .processor import process_text
from .extractor import extract_knowledge

def process_file_content(filename: str, file_bytes: bytes, query_col: str = None, answer_col: str = None) -> list:
    """
    Core entrypoint for the Document Pipeline.
    Detects the architecture cleanly based on filename explicitly mapping specialized parsers securely.
    query_col / answer_col: forwarded to _ingest_csv for named column mapping.
    """
    ext = filename.split('.')[-1].lower()
    
    try:
        if ext != 'pdf':
            content_str = file_bytes.decode('utf-8')
        else:
            content_str = "" # Passed mechanically via bytes explicitly later
    except UnicodeDecodeError:
        return []

    entries = []

    if ext == 'txt':
        entries = _ingest_txt(content_str)
    elif ext == 'csv':
        entries = _ingest_csv(content_str, query_col=query_col, answer_col=answer_col)
    elif ext == 'js':
        entries = _ingest_js(content_str)
    elif ext == 'sql':
        entries = _ingest_sql(content_str)
    elif ext == 'pdf':
        entries = _ingest_pdf(file_bytes, source_name=filename)

    # Filter out empty or broken entries mathematically
    clean_entries = []
    for e in entries:
        if e.get("queries") and e.get("response") and len(str(e["response"]).strip()) > 3:
            clean_entries.append(e)

    return clean_entries

def _ingest_txt(content: str) -> list:
    """Pipes text into native NLP processors and extracts X is Y heuristics safely."""
    sentences = process_text(content)
    return extract_knowledge(sentences)

def _ingest_csv(content: str, query_col: str = None, answer_col: str = None) -> list:
    """
    Named-column CSV parser. Accepts any CSV with headers.
    query_col / answer_col: column names to use. Falls back to positional (col 0 / col 1) if not provided.
    No row limit — processes full file.
    """
    entries = []
    reader = csv.DictReader(io.StringIO(content.strip()))
    headers = reader.fieldnames or []

    # Determine which columns to use
    use_named = query_col and answer_col and query_col in headers and answer_col in headers

    if not use_named:
        # Positional fallback: col 0 = query, col 1 = answer
        reader = csv.reader(io.StringIO(content.strip()))
        for row in reader:
            if not row or len(row) < 2:
                continue
            q = str(row[0]).strip()
            r = str(row[1]).strip()
            if q and r and q.lower() not in ('query', headers[0] if headers else ''):
                entries.append({
                    "queries": [q],
                    "response": r,
                    "tags": [w.lower() for w in q.split() if len(w) > 3][:4],
                    "source": "csv_ingest",
                    "confidence": 1.0
                })
        return entries

    for row in reader:
        q = str(row.get(query_col, '')).strip()
        r = str(row.get(answer_col, '')).strip()
        if not q or not r:
            continue
        entries.append({
            "queries": [q],
            "response": r,
            "tags": [w.lower() for w in q.split() if len(w) > 3][:4],
            "source": "csv_ingest",
            "confidence": 1.0
        })
    return entries

def _ingest_js(content: str) -> list:
    """Heuristic logic scanning for functions and object definitions explicitly mapping blocks natively."""
    entries = []
    
    # 1. Regex searching for `function XYZ(args) {`
    func_pattern = re.compile(r"function\s+([a-zA-Z0-9_]+)\s*\((.*?)\)\s*\{", re.MULTILINE)
    for match in func_pattern.finditer(content):
        func_name = match.group(1)
        args_str = match.group(2)
        
        # A rough block extractor capturing up to the next function natively
        start_idx = match.start()
        end_idx = content.find("function", start_idx + 10)
        if end_idx == -1: end_idx = len(content)
            
        raw_code = content[start_idx:end_idx].strip()
        if len(raw_code) > 400: raw_code = raw_code[:397] + "..." # Size bounding limits safely
        
        entries.append({
            "queries": [f"what does javascript function {func_name} do", f"explain function {func_name}"],
            "response": f"Javascript function `{func_name}({args_str})` is defined mathematically as:\n{raw_code}",
            "tags": ["javascript", "function", "code", func_name],
            "source": "js_ingest",
            "confidence": 0.85
        })
        
    return entries

def _ingest_sql(content: str) -> list:
    """Heuristic scanner searching for structural array definitions (CREATE TABLE) cleanly."""
    entries = []
    
    table_pattern = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)", re.IGNORECASE)
    for match in table_pattern.finditer(content):
        table_name = match.group(1)
        
        start_idx = match.start()
        end_idx = content.find(";", start_idx) 
        if end_idx == -1: end_idx = len(content)
        
        raw_code = content[start_idx:end_idx+1].strip()
        if len(raw_code) > 500: raw_code = raw_code[:497] + "..."
        
        entries.append({
            "queries": [f"what is sql table {table_name}", f"explain database {table_name}", f"table {table_name} schema"],
            "response": f"The SQL structure for `{table_name}` natively translates as:\n{raw_code}",
            "tags": ["sql", "database", "table", "schema", table_name],
            "source": "sql_ingest",
            "confidence": 0.95
        })
        
    return entries

def _ingest_pdf(file_bytes: bytes, source_name: str = "pdf_document") -> list:
    """
    Semantic Chunk-Based RAG Ingestion for PDF documents.
    Processes pages sequentially to reduce memory footprint.
    """
    import PyPDF2
    from .query_generator import generate_queries
    import logging

    logger = logging.getLogger('mmf.ingestor')

    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    except Exception as e:
        logger.error(f"Failed to read PDF {source_name}: {str(e)}")
        return []

    entries = []
    count = 0
    buffer = ""

    for page in reader.pages:
        if count >= 200:
            break
            
        try:
            raw = page.extract_text()
            if not raw:
                continue
            
            # Append to buffer and split into chunks
            buffer += raw + "\n"
            
            # Look for paragraph boundaries in the buffer
            if "\n\n" in buffer:
                raw_chunks = re.split(r'\n\s*\n', buffer)
                # Keep the last potentially incomplete chunk in the buffer
                buffer = raw_chunks.pop()
                
                for chunk in raw_chunks:
                    chunk = chunk.strip()
                    if len(chunk) < 100:
                        continue

                    queries = generate_queries(chunk)
                    if not queries:
                        continue

                    tags_raw = [w.lower() for w in chunk.split() if len(w) > 4]
                    tags = list(dict.fromkeys(tags_raw))[:5]

                    entries.append({
                        "queries": queries,
                        "response": chunk,
                        "tags": tags,
                        "source": source_name,
                        "confidence": 0.6
                    })
                    count += 1
                    if count >= 200:
                        break
        except Exception as e:
            logger.warning(f"Error extracting text from page in {source_name}: {str(e)}")
            continue

    # Process remaining buffer as a final chunk
    if count < 200 and len(buffer.strip()) >= 100:
        chunk = buffer.strip()
        queries = generate_queries(chunk)
        if queries:
            tags_raw = [w.lower() for w in chunk.split() if len(w) > 4]
            tags = list(dict.fromkeys(tags_raw))[:5]
            entries.append({
                "queries": queries,
                "response": chunk,
                "tags": tags,
                "source": source_name,
                "confidence": 0.6
            })

    return entries

