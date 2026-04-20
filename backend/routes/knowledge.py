from flask import Blueprint, request, jsonify, current_app, send_file
import os
import json
import uuid
import datetime
import zipfile

# We need to import our specialized backend architecture logic safely explicitly
from mmf.builder import build_mmf

knowledge_bp = Blueprint('knowledge_bp', __name__)

DEV_TARGET = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../mmf_dev'))
ZIP_TARGET = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../assistant.mmf'))

def _trigger_hard_reload():
    """
    Triggers explicit `.mmf` recompilation and memory cache restarts seamlessly
    via thread safety without halting the physical web server completely!
    """
    # 1. Compress DEV into ZIP correctly mapping builder API natively
    # build_mmf requires (source_folder, output_folder, output_name)
    build_mmf(DEV_TARGET, os.path.dirname(ZIP_TARGET), os.path.basename(ZIP_TARGET))
    
    # 2. Re-initialize singleton safely
    runtime = current_app.config['runtime']
    runtime.initialize()

def _atomic_write(filepath, data):
    """Executes safe atomic writes preventing partial JSON corruption during server crash nodes."""
    temp_path = filepath + ".tmp"
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(temp_path, filepath)

@knowledge_bp.route('/knowledge', methods=['GET'])
def get_knowledge():
    """
    Get All Knowledge Nodes
    ---
    responses:
      200:
        description: List of knowledge nodes
        schema:
          type: array
          items:
            type: object
    """
    k_path = os.path.join(DEV_TARGET, 'knowledge.json')
    try:
        with open(k_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": f"Failed to load knowledge natively: {str(e)}"}), 500

@knowledge_bp.route('/knowledge', methods=['POST'])
def add_knowledge():
    """
    Inject New Knowledge Node
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            query:
              type: string
            response:
              type: string
            tags:
              type: array
              items:
                type: string
    responses:
      201:
        description: Node created successfully
    """
    data = request.get_json()
    if not data or not data.get('query') or not data.get('response'):
        return jsonify({"error": "Malformed payload natively. 'query' and 'response' strings explicitly required."}), 400
        
    engine_lock = current_app.config['engine_lock']
    with engine_lock:
        try:
            # Explicit decoupled Learner ingestion 
            from mmf.learner import MMFLearner
            learner = MMFLearner(DEV_TARGET)
            
            # Learner safely translates string to array and executes semantic deduplications natively!
            learner.learn(data['query'], data['response'], data.get('tags', []))
            
            _trigger_hard_reload()
            return jsonify({"status": "success", "message": "Knowledge generated mapped securely!"}), 201
            
        except Exception as e:
            return jsonify({"error": f"Intake validation failure: {str(e)}"}), 500

@knowledge_bp.route('/knowledge/<entry_id>', methods=['PUT'])
def update_knowledge(entry_id):
    """Overrides explicit structural blocks safely using Atomic file integrations natively."""
    data = request.get_json()
    if not data or not entry_id:
        return jsonify({"error": "Missing payload or explicit entry definition target"}), 400

    engine_lock = current_app.config['engine_lock']
    k_path = os.path.join(DEV_TARGET, 'knowledge.json')
    
    with engine_lock:
        try:
            with open(k_path, 'r', encoding='utf-8') as f:
                knowledge = json.load(f)
                
            found = False
            for doc in knowledge:
                if doc.get('id') == entry_id:
                    if data.get('query'):
                        doc['queries'] = [data['query']]
                    if data.get('response'):
                        doc['response'] = data['response']
                    found = True
                    break
                    
            if not found:
                return jsonify({"error": "Knowledge UUID unmapped. Integrity failure."}), 404
                
            _atomic_write(k_path, knowledge)
            _trigger_hard_reload()
            return jsonify({"status": "success", "message": "Overrides integrated stably"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@knowledge_bp.route('/knowledge/<entry_id>', methods=['DELETE'])
def delete_knowledge(entry_id):
    """Executes destructive arrays locally before syncing backups natively."""
    if not entry_id:
        return jsonify({"error": "Missing entry destruction UUID"}), 400

    engine_lock = current_app.config['engine_lock']
    k_path = os.path.join(DEV_TARGET, 'knowledge.json')
    
    with engine_lock:
        try:
            with open(k_path, 'r', encoding='utf-8') as f:
                knowledge = json.load(f)
                
            filtered = [doc for doc in knowledge if doc.get('id') != entry_id]
            if len(filtered) == len(knowledge):
                 return jsonify({"error": "Knowledge UUID unmapped."}), 404
                 
            _atomic_write(k_path, filtered)
            _trigger_hard_reload()
            return jsonify({"status": "success", "message": "Destructive array purged permanently"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@knowledge_bp.route('/knowledge/bulk-delete', methods=['POST'])
def bulk_delete_knowledge():
    """
    Bulk Delete Knowledge Nodes
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            ids:
              type: array
              items:
                type: string
    responses:
      200:
        description: Nodes deleted successfully
    """
    data = request.get_json()
    ids_to_delete = data.get("ids", []) if data else []
    if not ids_to_delete:
        return jsonify({"error": "No IDs provided."}), 400

    engine_lock = current_app.config['engine_lock']
    k_path = os.path.join(DEV_TARGET, 'knowledge.json')
    with engine_lock:
        try:
            with open(k_path, 'r', encoding='utf-8') as f:
                knowledge = json.load(f)
            id_set = set(ids_to_delete)
            filtered = [doc for doc in knowledge if doc.get('id') not in id_set]
            removed = len(knowledge) - len(filtered)
            _atomic_write(k_path, filtered)
            _trigger_hard_reload()
            return jsonify({"status": "success", "removed": removed}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@knowledge_bp.route('/knowledge/export', methods=['GET'])
def export_knowledge():
    """Builds and serves the formal dynamic .mmf zip payload mapping."""
    if not os.path.exists(ZIP_TARGET):
        return jsonify({"error": "Compiled Matrix mapping doesn't locally verify."}), 404
    return send_file(ZIP_TARGET, as_attachment=True, download_name='assistant.mmf')

@knowledge_bp.route('/knowledge/export/nodes', methods=['GET'])
def export_nodes_csv():
    """Exports the knowledge nodes as a flat CSV file (query, response)."""
    import csv
    import io as _io
    k_path = os.path.join(DEV_TARGET, 'knowledge.json')
    try:
        with open(k_path, 'r', encoding='utf-8') as f:
            knowledge = json.load(f)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    output = _io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["query", "response", "confidence", "source"])
    for item in knowledge:
        # Use the first query as the primary query column
        queries = item.get('queries', [item.get('query', '')])
        primary_query = queries[0] if queries else ''
        writer.writerow([
            primary_query,
            item.get('response', ''),
            item.get('confidence', ''),
            item.get('source', '')
        ])

    output.seek(0)
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment; filename=knowledge_nodes.csv"}
    )

@knowledge_bp.route('/knowledge/import', methods=['POST'])
def import_knowledge():
    """Uploads external .mmf payloads mapping them explicitly over memory."""
    if 'file' not in request.files:
        return jsonify({"error": "Missing payload block. Attach file binary."}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file mapping selected."}), 400
        
    engine_lock = current_app.config['engine_lock']
    with engine_lock:
        try:
            temp_path = os.path.join(DEV_TARGET, 'temp_upload.zip')
            file.save(temp_path)
            
            # Extract natively overriding dynamic states precisely
            with zipfile.ZipFile(temp_path, 'r') as zf:
                zf.extractall(DEV_TARGET)
                
            os.remove(temp_path)
            _trigger_hard_reload()
            
            return jsonify({"status": "success", "message": "Architecture imported & hot-reloaded safely."}), 200
        except Exception as e:
            return jsonify({"error": f"Failed native integration: {str(e)}"}), 500

@knowledge_bp.route('/knowledge/csv-headers', methods=['POST'])
def csv_headers():
    """Peeks at a CSV file and returns its column headers for the UI mapping step."""
    if 'file' not in request.files:
        return jsonify({"error": "No file attached."}), 400
    file = request.files['file']
    try:
        import csv as _csv, io as _io
        content = file.read().decode('utf-8', errors='replace')
        reader = _csv.DictReader(_io.StringIO(content))
        headers = list(reader.fieldnames or [])
        return jsonify({"headers": headers}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@knowledge_bp.route('/knowledge/ingest', methods=['POST'])
def ingest_knowledge():
    """Ingests raw documents (.txt, .csv, .js, .sql, .pdf) parsing heuristic mathematics."""
    if 'file' not in request.files:
        return jsonify({"error": "Missing payload block. Attach file binary."}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file mapping selected."}), 400

    # Named column mapping for CSV files
    query_col  = request.form.get('query_col', None)
    answer_col = request.form.get('answer_col', None)
        
    engine_lock = current_app.config['engine_lock']
    with engine_lock:
        try:
            file_bytes = file.read()
            from mmf.ingestor import process_file_content
            from mmf.learner import MMFLearner
            
            entries = process_file_content(file.filename, file_bytes,
                                           query_col=query_col, answer_col=answer_col)
            if not entries:
                return jsonify({"status": "skipped", "message": "No vectors extracted. Check file format or column names."}), 200
                
            learner = MMFLearner(DEV_TARGET)
            result = learner.learn_batch(entries)
            
            added_count  = len(result.get("added", []))
            merged_count = len(result.get("merged", []))
            
            _trigger_hard_reload()
            
            return jsonify({
                "status":    "success", 
                "extracted": len(entries),
                "added":     added_count,
                "merged":    merged_count,
                "skipped":   len(entries) - (added_count + merged_count),
                "message":   f"Ingestion processed {len(entries)} nodes."
            }), 200
            
        except Exception as e:
            return jsonify({"error": f"Ingestion processor crashed: {str(e)}"}), 500


@knowledge_bp.route('/knowledge/import/huggingface', methods=['POST'])
def import_huggingface():
    """
    Fetches rows from a public HuggingFace dataset via their Datasets Server API
    and ingests them. Zero extra dependencies (uses urllib only).

    Expected JSON body:
    {
        "dataset_id": "rajpurkar/squad",
        "config":     "plain_text",   (optional, default: "default")
        "split":      "train",        (optional, default: "train")
        "query_col":  "question",     (required)
        "answer_col": "context",      (required)
        "limit":      100             (optional, max 500)
    }
    """
    import urllib.request
    import urllib.error

    body = request.get_json()
    if not body:
        return jsonify({"error": "JSON body required."}), 400

    dataset_id = body.get("dataset_id", "").strip()
    query_col  = body.get("query_col", "").strip()
    answer_col = body.get("answer_col", "").strip()
    config     = body.get("config", "default").strip()
    split      = body.get("split", "train").strip()
    limit      = min(int(body.get("limit", 100)), 500)

    if not dataset_id or not query_col or not answer_col:
        return jsonify({"error": "'dataset_id', 'query_col', and 'answer_col' are required."}), 400

    hf_url = (
        f"https://datasets-server.huggingface.co/rows"
        f"?dataset={dataset_id}&config={config}&split={split}&offset=0&length={limit}"
    )

    try:
        req = urllib.request.Request(hf_url, headers={"User-Agent": "MMF-Platform/0.6"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return jsonify({"error": f"HuggingFace API returned HTTP {e.code}. Check dataset_id / config / split."}), 502
    except Exception as e:
        return jsonify({"error": f"Failed to reach HuggingFace: {str(e)}"}), 502

    rows = payload.get("rows", [])
    if not rows:
        return jsonify({"status": "skipped", "message": "No rows returned from HuggingFace."}), 200

    entries = []
    for row_wrap in rows:
        row = row_wrap.get("row", {})
        q = str(row.get(query_col, "")).strip()
        a = row.get(answer_col)

        # Handle nested answer structures (e.g. SQuAD answers is a dict with "text" list)
        if isinstance(a, dict):
            a = a.get("text", a.get("answers", str(a)))
        if isinstance(a, list):
            a = a[0] if a else ""
        a = str(a).strip()

        if not q or not a or len(a) < 5:
            continue

        tags = [w.lower() for w in q.split() if len(w) > 3][:4]
        entries.append({
            "queries": [q],
            "response": a,
            "tags": tags,
            "source": f"huggingface:{dataset_id}",
            "confidence": 0.75
        })

    if not entries:
        return jsonify({"status": "skipped", "message": "No valid pairs found with those column names."}), 200

    engine_lock = current_app.config['engine_lock']
    with engine_lock:
        try:
            from mmf.learner import MMFLearner
            learner = MMFLearner(DEV_TARGET)
            result  = learner.learn_batch(entries)
            added   = len(result.get("added", []))
            merged  = len(result.get("merged", []))
            _trigger_hard_reload()
            return jsonify({
                "status":    "success",
                "fetched":   len(rows),
                "extracted": len(entries),
                "added":     added,
                "merged":    merged,
                "skipped":   len(entries) - (added + merged),
                "message":   f"Imported {len(entries)} entries from {dataset_id}."
            }), 200
        except Exception as e:
            return jsonify({"error": f"Ingestion failed: {str(e)}"}), 500
