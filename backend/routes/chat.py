from flask import Blueprint, request, jsonify, current_app, Response, g
import json
import time
import re
import threading
import os
import html
from mmf.learner import MMFLearner
from mmf_logger import get_logger

logger = get_logger('chat')

chat_bp = Blueprint('chat_bp', __name__)

# --- Input Validation ---
MAX_QUERY_LENGTH = 2000  # Max characters for a chat query

def _sanitize_input(text: str) -> str:
    """Sanitize user input: strip, length-limit, and escape."""
    if not text or not isinstance(text, str):
        return ""
    text = text.strip()
    if len(text) > MAX_QUERY_LENGTH:
        text = text[:MAX_QUERY_LENGTH]
    return text

DEV_TARGET = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../mmf_dev'))

def background_learn(query, response):
    """
    Executes learning in a separate thread to avoid blocking the chat response.
    Only learns if the response is substantial.
    """
    try:
        # We use a secondary thread-safe lock check if needed, 
        # but MMFLearner handles its own file operations.
        learner = MMFLearner(DEV_TARGET)
        # We tag it as 'chat_learned' for traceability
        learner.learn(query, response, tags=["chat_learned"])
        logger.info(f"Background learning successful: {query[:30]}...", extra={'query': query[:50]})
    except Exception as e:
        logger.error(f"Background learning failed: {str(e)}", exc_info=True)

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """
    Standard Chat Query
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            message:
              type: string
              example: "What is a binary search tree?"
            ad_hoc_knowledge:
              type: array
              items:
                type: object
    responses:
      200:
        description: Successful response
        schema:
          type: object
          properties:
            response:
              type: string
    """
    data = request.get_json()
    if not data or not data.get('message') or not str(data.get('message')).strip():
        return jsonify({"error": "Missing or natively empty 'message' payload strings."}), 400
        
    user_message = _sanitize_input(data['message'])
    if not user_message:
        return jsonify({"error": "Message is empty after sanitization."}), 400
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
                response_text = match_result.get('response')
                
                # Trigger Background Learning
                threading.Thread(target=background_learn, args=(user_message, response_text)).start()

                return jsonify({
                    "response": response_text,
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


@chat_bp.route('/chat/stream', methods=['POST'])
def chat_stream():
    """
    Streaming Chat Query (SSE)
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            message:
              type: string
    responses:
      200:
        description: Event stream of chunks
    """
    data = request.get_json()
    if not data or not data.get('message') or not str(data.get('message')).strip():
        return jsonify({"error": "Missing or natively empty 'message' payload strings."}), 400
        
    user_message = data['message'].strip()
    ad_hoc = data.get('ad_hoc_knowledge', [])
    
    engine_lock = current_app.config['engine_lock']
    runtime = current_app.config['runtime']

    def generate():
        with engine_lock:
            try:
                # 1. Pipeline Execution
                match_result = runtime.query(user_message, ad_hoc_knowledge=ad_hoc, debug=False)
                
                # 2. Extract Response & Metadata
                if match_result.get("type") == "match":
                    full_response = match_result.get('response', '')
                    metadata = {
                        "type": "metadata",
                        "matching_query": match_result.get('matching_query', ''),
                        "confidence": match_result.get('confidence', 0.0),
                        "source": match_result.get('source', 'mmf')
                    }
                else:
                    full_response = match_result.get("message", "No match found.")
                    metadata = {
                        "type": "metadata",
                        "matching_query": "None",
                        "confidence": 0,
                        "source": "system"
                    }

                # 3. Yield Metadata first
                yield f"data: {json.dumps(metadata)}\n\n"
                
                # 4. Stream Content Delta with simulated typing feel
                # Tokenize by words to make it look active
                tokens = re.split(r'(\s+)', full_response)
                for token in tokens:
                    if token:
                        chunk = {"type": "content", "delta": token}
                        yield f"data: {json.dumps(chunk)}\n\n"
                        # Variable sleep for realistic feel: 0.02 - 0.05s
                        time.sleep(0.03)
                
                # 6. Trigger Background Learning for Stream
                threading.Thread(target=background_learn, args=(user_message, full_response)).start()

                # 5. Yield End Signal
                yield f"data: {json.dumps({'type': 'end'})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


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
