"""
Matcher module for the MMF system.
v0.5: Added contextual ad-hoc RAG blending with separate TF-IDF and weighted score merging.
"""
from abc import ABC, abstractmethod
import hashlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class BaseMatcher(ABC):
    """
    Abstract base class for matchers.
    Allows for future-proofing (e.g. replacing with Vector DB or Embedding matching).
    """
    @abstractmethod
    def find_best_match(self, query: str, knowledge: list, threshold: float, ad_hoc_knowledge: list = None) -> dict:
        pass

class TfidfMatcher(BaseMatcher):
    """
    Semantic TF-IDF matcher with optional ad-hoc context blending.
    - MMF knowledge = persistent cached index (lazy cache-busted)
    - Ad-hoc knowledge = temporary per-request vectorizer (never contaminates global vocab)
    """
    def __init__(self):
        self.vectorizer = TfidfVectorizer(lowercase=True)
        self.cached_knowledge_hash = None
        self.tfidf_matrix = None
        self.flat_queries = []
        self.flat_query_to_item_index = []

    def _hash_knowledge(self, knowledge: list) -> str:
        hash_str = "".join([k.get('id', str(i)) + k.get('created_at', '') for i, k in enumerate(knowledge)])
        return hashlib.md5(hash_str.encode('utf-8')).hexdigest()

    def _build_index(self, knowledge: list):
        """Constructs and caches the flat TF-IDF index from persistent knowledge."""
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

    def _score_candidates(self, query_vec, flat_queries, tfidf_matrix, item_map, knowledge_list, weight: float) -> list:
        """
        Computes cosine similarities and returns weighted candidate list.
        weight: 1.0 for full weight, 0.0–1.0 for blended weight.
        """
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
        candidates = []
        for idx, best_data in item_best.items():
            sim = best_data['sim']
            item = knowledge_list[idx]
            confidence = item.get('confidence', 1.0)
            # Weighted final score
            raw_score = (0.7 * sim) + (0.3 * confidence)
            final_score = raw_score * weight
            candidates.append({
                "item": item,
                "response": item.get('response', ''),
                "similarity": float(sim),
                "final_score": float(final_score),
                "matching_query": best_data['query_str'],
                "source": item.get('source', 'mmf')
            })
        return candidates

    def find_best_match(self, query: str, knowledge: list, threshold: float, ad_hoc_knowledge: list = None) -> dict:
        """
        Calculates cosine similarities across the cached MMF TF-IDF matrix,
        optionally blending results from a separate ad-hoc context vectorizer.
        
        Blending weight: 0.55 MMF / 0.45 Context (balanced, context-boosted).
        """
        # --- MMF Persistent Branch ---
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
                        self.flat_query_to_item_index, knowledge, weight=mmf_weight
                    )
                except Exception:
                    mmf_candidates = []

        # --- Ad-Hoc Context Branch (ephemeral, never modifies global vocab) ---
        adhoc_candidates = []
        if ad_hoc_knowledge:
            try:
                adhoc_queries = []
                adhoc_item_map = []
                for idx, item in enumerate(ad_hoc_knowledge):
                    qs = item.get('queries', [])
                    if not qs and item.get('query'):
                        qs = [item['query']]
                    for q in qs:
                        adhoc_queries.append(q)
                        adhoc_item_map.append(idx)

                if adhoc_queries:
                    adhoc_vec = TfidfVectorizer(lowercase=True)
                    adhoc_matrix = adhoc_vec.fit_transform(adhoc_queries)
                    query_vec_adhoc = adhoc_vec.transform([query.lower()])
                    adhoc_candidates = self._score_candidates(
                        query_vec_adhoc, adhoc_queries, adhoc_matrix,
                        adhoc_item_map, ad_hoc_knowledge, weight=0.45
                    )
            except Exception:
                adhoc_candidates = []

        # --- Blend and Rank ---
        all_candidates = mmf_candidates + adhoc_candidates
        all_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        top_matches = all_candidates[:3]

        if top_matches:
            return {
                "type": "match",
                "top_matches": [{
                    "response":       m["response"],
                    "similarity":     m["similarity"],
                    "final_score":    m["final_score"],
                    "matching_query": m["matching_query"],
                    "source":         m.get("source", "mmf"),
                    "item":           m.get("item", {})
                } for m in top_matches]
            }

        return {"type": "no_match"}
