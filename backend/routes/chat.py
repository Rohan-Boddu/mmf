from flask import Blueprint, request, jsonify, current_app

chat_bp = Blueprint('chat_bp', __name__)

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """
    Core REST endpoint receiving user interface texts.
    Secured by native Engine thread-locking ensuring mathematical operations don't
    intersect drastically while dynamic compilation/vectorization runs locally.
    """
    data = request.get_json()
    if not data or not data.get('message') or not str(data.get('message')).strip():
        return jsonify({"error": "Missing or natively empty 'message' payload strings."}), 400
        
    user_message = data['message'].strip()
    ad_hoc = data.get('ad_hoc_knowledge', [])
    
    # Isolate Engine thread safely
    engine_lock = current_app.config['engine_lock']
    runtime = current_app.config['runtime']
    
    with engine_lock:
        try:
            # Passes input downward handling processor filtering natively internally
            match_result = runtime.query(user_message, ad_hoc_knowledge=ad_hoc, debug=False)
            
            # Unpack dynamically enforcing strictly isolated AI payload structure requested
            if match_result.get("type") == "match":
                return jsonify({
                    "response": match_result.get('response'),
                    "reason": match_result.get('reason'),
                    "confidence": match_result.get('confidence', 0.0),
                    "final_score": match_result.get('final_score', 0.0),
                    "source": match_result.get('source', '')
                }), 200
            else:
                return jsonify({
                    "response": match_result.get("message", "No match found."),
                    "reason": "Threshold rejection / No semantic vector overlap",
                    "confidence": 0,
                    "final_score": 0
                }), 200
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500


@chat_bp.route('/chat/context', methods=['POST'])
def chat_context():
    """
    Extracts semantic nodes from an uploaded file temporarily.
    Does NOT persist to the `.mmf` model natively.
    Limits to 30-75 nodes depending on extraction density mathematically.
    """
    if 'file' not in request.files:
        return jsonify({"error": "Missing file."}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected."}), 400

    query_col  = request.form.get('query_col', None)
    answer_col = request.form.get('answer_col', None)

    try:
        file_bytes = file.read()
        from mmf.ingestor import process_file_content
        
        entries = process_file_content(file.filename, file_bytes,
                                       query_col=query_col, answer_col=answer_col)
        
        if not entries:
            return jsonify({"status": "skipped", "message": "No nodes extracted."}), 200

        # Dynamic limitation: larger node arrays cap at 75, normal defaults to 30
        limit = 75 if len(entries) > 200 else 30
        nodes = entries[:limit]

        # Inject context source telemetry securely
        for n in nodes:
            n["source"] = f"attached:{file.filename}"
            n["confidence"] = 0.85 # High confidence for active context

        return jsonify({
            "status": "success",
            "nodes": nodes,
            "filename": file.filename
        }), 200

    except Exception as e:
        return jsonify({"error": f"Upload failure: {str(e)}"}), 500
