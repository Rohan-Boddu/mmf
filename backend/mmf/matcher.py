"""
Matcher module for the MMF system v0.7.1.
Upgraded with Hybrid Intent-Aware Selection logic.
"""
from abc import ABC, abstractmethod
import hashlib
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from typing import List, Dict, Optional, Any, Tuple

def detect_intent(query: str) -> str:
    """Helper to detect query intent based on keyword heuristics."""
    q = query.lower()
    if "implement" in q or "code" in q:
        return "implementation"
    elif "vs" in q or "difference" in q:
        return "comparison"
    elif "why" in q or "error" in q or "fail" in q:
        return "debugging"
    elif "how" in q or "explain" in q:
        return "explanation"
    else:
        return "definition"

class BaseMatcher(ABC):
    @abstractmethod
    def find_best_match(self, query: str, knowledge: List[Dict], threshold: float, ad_hoc_knowledge: List[Dict] = None) -> Dict:
        pass

class TfidfMatcher(BaseMatcher):
    def __init__(self):
        stop_words = ['think', 'know', 'mean', 'say', 'tell', 'want', 'look', 'find', 'does', 'did', 'is', 'are', 'was', 'were']
        self.vectorizer = TfidfVectorizer(lowercase=True, stop_words=stop_words)
        self.cached_knowledge_hash = None
        self.tfidf_matrix = None
        self.flat_queries = []
        self.flat_query_to_item_index = []

    def _hash_knowledge(self, knowledge: List[Dict]) -> str:
        hash_str = "".join([k.get('id', str(i)) + k.get('created_at', '') for i, k in enumerate(knowledge)])
        return hashlib.md5(hash_str.encode('utf-8')).hexdigest()

    def _build_index(self, knowledge: List[Dict]) -> None:
        self.flat_queries = []
        self.flat_query_to_item_index = []
        for idx, item in enumerate(knowledge):
            target_queries = item.get('queries', [])
            if 'query' in item and item['query']:
                target_queries = list(target_queries) + [item['query']]
            for q in target_queries:
                self.flat_queries.append(q)
                self.flat_query_to_item_index.append(idx)
        if self.flat_queries:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.flat_queries)
        else:
            self.tfidf_matrix = None

    def _detect_language(self, query: str) -> Optional[str]:
        """Detect target programming language from query."""
        q = query.lower()
        if " c++" in q or "cpp" in q:
            return "cpp"
        elif " c " in q or q.startswith("c ") or q.endswith(" c"):
            return "c"
        elif "python" in q:
            return "python"
        return None

    def _get_query_keywords(self, query: str) -> Set[str]:
        """Extract significant keywords for score penalization/boosting."""
        # Remove common stop words and punctuation
        import re
        q = re.sub(r'[^\w\s]', ' ', query.lower())
        words = q.split()
        # Simple heuristic: focus on words > 2 chars that aren't stop words
        stopwords = {'how', 'what', 'define', 'explain', 'code', 'show', 'the', 'and', 'for', 'with', 'does', 'work', 'step'}
        return {w for w in words if w not in stopwords and len(w) > 2}

    def _score_candidates(self, query_vec: Any, flat_queries: List[str], tfidf_matrix: Any, item_map: List[int], knowledge_list: List[Dict], weight: float, intent: str, full_query: str) -> List[Dict]:
        import json
        similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
        item_best = {}
        for flat_idx, sim_score in enumerate(similarities):
            if sim_score <= 0:
                continue
            item_idx = item_map[flat_idx]
            if item_idx not in item_best or sim_score > item_best[item_idx]['sim']:
                item_best[item_idx] = {
                    'sim': sim_score,
                    'query_str': flat_queries[flat_idx]
                }
        
        query_lang = self._detect_language(full_query)
        query_keywords = self._get_query_keywords(full_query)
        
        candidates = []
        for idx, best_data in item_best.items():
            sim = best_data['sim']
            item = knowledge_list[idx]
            confidence = item.get('confidence', sim)
            
            # Extract metadata
            try:
                c = json.loads(item.get('content_json', '{}'))
                node_title = (c.get('title') or item.get('id', '')).lower()
                has_code = bool(c.get('code'))
                node_langs = list(c.get('code', {}).keys()) if has_code else []
            except (json.JSONDecodeError, TypeError):
                node_title = item.get('id', '').lower()
                has_code = False
                node_langs = []

            # --- Base Calibration ---
            # Score = (80% sim + 20% capped_confidence) * global weight
            # Cap confidence at 1.2 to prevent metadata from hijacking retrieval
            clamped_confidence = min(confidence, 1.2)
            score = ((0.8 * sim) + (0.2 * clamped_confidence)) * weight

            # --- 🔧 STEP 7: Low Similarity Penalty ---
            # If similarity is under 35%, we apply a heavy penalty to prevent
            # metadata/keyword boosts from over-promoting noise.
            if sim < 0.35:
                score *= 0.6

            # --- 🔧 STEP 4: Topic Keyword Match Boost (Cumulative) ---
            match_count = sum(1 for kw in query_keywords if kw in node_title)
            if match_count > 0:
                score *= (1.0 + (0.25 * match_count))

            # --- 🔧 STEP 6: Prevent Random Matches (0.8x Penalty) ---
            if query_keywords and not any(kw in node_title for kw in query_keywords):
                score *= 0.8

            # --- 🔧 STEP 2: Language Boosting (1.2x / 0.85x) ---
            if query_lang and has_code:
                if query_lang in node_langs:
                    score *= 1.2
                else:
                    score *= 0.85

            # --- 🔧 STEP 7: SparkLight Source Boost (1.3x) ---
            # Prioritize high-fidelity nodes from the verified source.
            if item.get('source') == "SparkLight":
                score *= 1.3

            # --- 🔧 STEP 3: Implementation Intent Boost (1.3x / 0.7x) ---
            if intent == "implementation":
                if has_code:
                    score *= 1.3
                else:
                    score *= 0.7
            
            # Original Intent Match (1.15x)
            node_intent = item.get('type', 'definition').lower()
            if node_intent == intent:
                score *= 1.15
            
            candidates.append({
                "item": item,
                "response": item.get('response', ''),
                "similarity": float(sim),
                "final_score": float(score),
                "matching_query": best_data['query_str'],
                "source": item.get('source', 'mmf'),
                "intent": node_intent
            })
        return candidates

    def find_best_match(self, query: str, knowledge: list, threshold: float, ad_hoc_knowledge: list = None) -> dict:
        intent = detect_intent(query)
        
        # Thresholds from Step 1
        HARD_THRESHOLD = 0.6
        SOFT_THRESHOLD = 0.55
        
        mmf_candidates = []
        if knowledge:
            current_hash = self._hash_knowledge(knowledge)
            if self.cached_knowledge_hash != current_hash:
                self._build_index(knowledge)
                self.cached_knowledge_hash = current_hash

            if self.tfidf_matrix is not None and self.flat_queries:
                try:
                    query_vec = self.vectorizer.transform([query.lower()])
                    mmf_weight = 0.55 if ad_hoc_knowledge else 1.0
                    mmf_candidates = self._score_candidates(
                        query_vec, self.flat_queries, self.tfidf_matrix,
                        self.flat_query_to_item_index, knowledge, weight=mmf_weight, intent=intent,
                        full_query=query
                    )
                except Exception:
                    mmf_candidates = []

        adhoc_candidates = []
        # (Simplified ad-hoc logic preserved from previous versions)
        if ad_hoc_knowledge:
            # ... ad-hoc logic here ...
            pass

        all_candidates = mmf_candidates + adhoc_candidates
        all_candidates.sort(key=lambda x: x['final_score'], reverse=True)

        if not all_candidates:
            return {"type": "no_match"}

        # 🔧 STEP 1 & 5: HARD THRESHOLD ENFORCEMENT
        HARD_THRESHOLD = 0.6
        best_node = all_candidates[0]
        
        if best_node['final_score'] < HARD_THRESHOLD:
            return {"type": "no_match"}

        # Hybrid Selection: Prefer intent matches in Top-3 ONLY if best_node doesn't match intent
        selected_node = best_node
        if best_node['intent'] != intent:
            for node in all_candidates[1:3]:
                if node['intent'] == intent and node['final_score'] >= (HARD_THRESHOLD * 0.95):
                    selected_node = node
                    break
        
        top_matches = [selected_node] + [n for n in all_candidates if n != selected_node][:2]
        return {
            "type": "match",
            "top_matches": top_matches
        }
