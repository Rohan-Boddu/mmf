"""
synthesizer.py — MMF Intelligent Response Synthesizer v0.7.1
Master Refactor: Controlled Semantic Response Generator.
SparkLight Schema Upgrade: execution_steps, variants, visual_hooks, reasoning_map.
"""

import re
import json
from typing import List, Dict, Optional, Tuple

# --- Intent Detection ---

def _detect_intent(query: str) -> str:
    """Detect query intent with SparkLight-extended heuristics."""
    q = query.lower()
    if "implement" in q or "code" in q:
        return "implementation"
    elif "vs" in q or "difference" in q or "compare" in q:
        return "comparison"
    elif "show" in q or "visualize" in q or "animate" in q:
        return "visualization"
    elif "why" in q or "error" in q or "fail" in q:
        return "debugging"
    elif "step by step" in q or "step-by-step" in q:
        return "steps"
    elif "how" in q or "explain" in q:
        return "explanation"
    else:
        return "definition"

# --- Structured Extraction ---

def _parse_content_json(item: Dict) -> Dict:
    """Parse content_json into a normalized dict with all SparkLight fields."""
    raw = item.get("content_json") or ""
    
    content = {}
    if raw and (raw.startswith("{") or raw.startswith("[")):
        try:
            content = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            content = {}

    return {
        "title": content.get("title") or content.get("topic") or content.get("question") or "",
        "summary": content.get("summary") or content.get("answer") or content.get("description") or "",
        "key_points": content.get("key_points") or [],
        "code": content.get("code") or {},
        "execution_steps": content.get("execution_steps") or [],
        "variants": content.get("variants") or [],
        "visual_hooks": content.get("visual_hooks") or [],
        "reasoning_map": content.get("reasoning_map") or {},
    }

def _extract_content(node: Dict) -> Tuple[str, str, List[str]]:
    """Extract title, summary, key_points from a chunk dict."""
    item = node.get("item", {})
    raw_json = item.get("content_json") or node.get("response", "")
    
    content = {}
    if raw_json and (raw_json.startswith("{") or raw_json.startswith("[")):
        try:
            content = json.loads(raw_json)
        except (json.JSONDecodeError, TypeError):
            content = {}

    title = content.get("title") or content.get("topic") or content.get("question")
    summary = content.get("summary") or content.get("answer") or content.get("description") or ""
    
    # Legacy Markdown Support
    if not title and raw_json:
        match = re.search(r'#### Insight:\s*(.*)', raw_json)
        if match:
            title = match.group(1).split('\n')[0].strip()
            summary = re.sub(r'#### Insight:.*?\n', '', raw_json).strip()
    
    title = title or "Concept"
    if not summary and raw_json and not (raw_json.startswith("{") or raw_json.startswith("[")):
        summary = raw_json
        
    key_points = content.get("key_points") or []
    return title, summary, key_points

def _extract_code(node: Dict, query: str) -> Optional[str]:
    """Language-aware code extraction."""
    item = node.get("item", {})
    content_json = item.get("content_json")
    if not content_json:
        return None
        
    try:
        data = json.loads(content_json)
        code_data = data.get("code")
    except (json.JSONDecodeError, TypeError):
        return None

    if not code_data:
        return None

    q = query.lower()
    if isinstance(code_data, dict):
        if " c " in q or q.endswith(" in c"):
            return code_data.get("c")
        elif "python" in q:
            return code_data.get("python")
        elif "cpp" in q or "c++" in q:
            return code_data.get("cpp")
        else:
            return code_data.get("python") or code_data.get("c")

    return code_data

def _detect_language(query: str) -> str:
    """Detect requested language for code block labelling."""
    q = query.lower()
    if "python" in q: return "python"
    if "cpp" in q or "c++" in q: return "cpp"
    if " c " in q or q.endswith(" in c"): return "c"
    return "python"

def _deduplicate(items: List[str]) -> List[str]:
    """
    Deduplicates items while preserving order.
    Uses normalized set for exact matches and token-set overlap for near-duplicates.
    """
    seen_normalized = set()
    result = []
    
    for item in items:
        if not item or not item.strip():
            continue
            
        # 1. Normalize for structural comparison
        tokens = set(re.sub(r'[^a-z0-9\s]', '', item.lower()).split())
        normalized = "".join(sorted(list(tokens)))
        
        if not normalized:
            continue
            
        # 2. Check for near-duplicates using token overlap (Jaccard-like)
        is_duplicate = False
        if normalized in seen_normalized:
            is_duplicate = True
        else:
            # Check overlap with already accepted items
            for seen_norm in seen_normalized:
                # If one string's tokens are a significant subset of another, or very high overlap
                # This is a simple heuristic for "semantic near-match" in short strings
                if len(normalized) > 4 and len(seen_norm) > 4:
                    # Simple length-based heuristic: if they are very similar in content
                    if normalized in seen_norm or seen_norm in normalized:
                        is_duplicate = True
                        break
        
        if not is_duplicate:
            seen_normalized.add(normalized)
            result.append(item.strip())
            
    return result

# --- Node Wrapper ---

class NodeWrapper:
    """Wraps the chunk dict to provide easy access for the synthesis logic."""
    def __init__(self, chunk: Dict):
        self.chunk = chunk
        self.item = chunk.get("item", {})
        self.intent = chunk.get("intent", "definition")
        self.query = chunk.get("matching_query", "")
        title, _, _ = _extract_content(chunk)
        self.topic = title.lower()
        self.parsed = _parse_content_json(self.item)

# --- Core Synthesis Engine ---

def synthesize(chunks: List[Dict], query: str = "") -> str:
    """Core entrypoint for the semantic response generator."""
    if not chunks:
        return "I couldn't find a strong match. Try rephrasing your query."

    # Step 1: Primary Node Lock
    primary = NodeWrapper(chunks[0])
    secondary = [NodeWrapper(c) for c in chunks[1:3]]

    # Step 2: Strict Secondary Filtering
    filtered_secondary = []
    for node in secondary:
        if node.intent != primary.intent:
            continue
        if primary.intent != "comparison" and "vs" in node.query.lower():
            continue
        if primary.intent != "debugging" and any(w in node.query.lower() for w in ["error", "overflow", "fail", "limit"]):
            continue
        if node.topic == primary.topic:
            continue
        filtered_secondary.append(node)

    # Step 3: Extract structured content from primary
    title, summary, key_points = _extract_content(primary.chunk)
    all_key_points = list(key_points)

    # Enrich ONLY key points from filtered secondary nodes
    for node in filtered_secondary:
        # Only merge if it's a comparison or if topics are significantly similar
        # (For now, let's prioritize primary topic integrity for non-comparisons)
        if primary.intent == "comparison" or node.topic in primary.topic or primary.topic in node.topic:
            _, _, extra_points = _extract_content(node.chunk)
            all_key_points.extend(extra_points)

    # Step 5: Deduplication + Limit
    all_key_points = _deduplicate(all_key_points)[:6]
    
    intent = _detect_intent(query)

    # Safety Fallback
    if not summary or len(summary.strip()) < 10:
        return "I couldn't find a clear explanation. Try rephrasing your query."

    # --- Build Response Based on Intent ---
    response_parts = []
    response_parts.append(f"#### Insight: {title}")
    response_parts.append(summary.strip())

    # Key Points (always included if available)
    if all_key_points:
        response_parts.append("#### Key Points:")
        response_parts.append("\n".join([f"- {p}" for p in all_key_points]))

    # --- SparkLight: Execution Steps ---
    if intent in ("steps", "explanation"):
        steps = primary.parsed.get("execution_steps", [])
        if steps:
            response_parts.append("#### Execution Steps:")
            response_parts.append("\n".join(steps))

    # --- SparkLight: Comparison via reasoning_map + variants ---
    if intent == "comparison":
        rmap = primary.parsed.get("reasoning_map", {})
        variants = primary.parsed.get("variants", [])
        if rmap:
            response_parts.append("#### Reasoning:")
            response_parts.append(f"**Problem**: {rmap.get('problem', 'N/A')}")
            response_parts.append(f"**Solution**: {rmap.get('solution', 'N/A')}")
            response_parts.append(f"**Tradeoffs**: {rmap.get('tradeoffs', 'N/A')}")
        if variants:
            response_parts.append(f"**Related Variants**: {', '.join(variants)}")

    # --- SparkLight: Visualization Hooks ---
    if intent == "visualization":
        hooks = primary.parsed.get("visual_hooks", [])
        if hooks:
            response_parts.append("#### Visual Hooks:")
            response_parts.append("\n".join([f"- `{h}`" for h in hooks]))

    # --- Implementation Code (only when requested) ---
    if intent == "implementation":
        code_block = _extract_code(primary.chunk, query)
        if code_block:
            lang = _detect_language(query)
            response_parts.append("#### Implementation:")
            response_parts.append(f"```{lang}\n{code_block.strip()}\n```")

    return "\n\n".join(response_parts)
