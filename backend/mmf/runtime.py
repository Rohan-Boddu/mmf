"""
Runtime orchestration module for the MMF system.
Orchestrates: input -> match -> synthesize -> response.
v0.6.1: Added rule-based Response Synthesizer layer for generative-feeling outputs.
"""
from mmf.loader import MMFLoader
from mmf.matcher import BaseMatcher

class MMFRuntime:
    """Orchestrates the loading, matching, synthesis, and query execution."""

    def __init__(self, loader: MMFLoader, matcher: BaseMatcher):
        self.loader = loader
        self.matcher = matcher
        self.knowledge = None
        self.config = None
        self.manifest = None
        self.is_initialized = False

    def initialize(self) -> None:
        """Uses the loader to pull all data into memory, preparing the runtime."""
        data = self.loader.load()
        self.manifest = data['manifest']
        self.config   = data['config']
        self.knowledge = data['knowledge']
        self.is_initialized = True

    def query(self, user_input: str, ad_hoc_knowledge: list = None, debug: bool = False) -> dict:
        """
        Full pipeline:
          1. Normalize input
          2. TF-IDF match against persistent + ad-hoc knowledge
          3. Collect all above-threshold Top-K matches
          4. Synthesize a single coherent response from Top-K chunks
          5. Return explainable payload
        """
        if not self.is_initialized:
            raise RuntimeError("MMFRuntime must be initialized before querying.")

        from mmf.processor import normalize_query
        from mmf.synthesizer import synthesize

        # 1. Normalize
        clean_input = normalize_query(user_input)
        threshold = self.config.get('runtime', {}).get('match_threshold', 0.5)

        # 2. Retrieve Top-K
        match_result = self.matcher.find_best_match(
            clean_input, self.knowledge, threshold,
            ad_hoc_knowledge=ad_hoc_knowledge
        )

        if match_result.get("type") == "match" and "top_matches" in match_result:
            top_matches = match_result["top_matches"]

            if debug:
                print("\n[DEBUG] Top-K Outcomes:")
                for i, m in enumerate(top_matches):
                    print(f"  {i+1}: Score={m['final_score']:.4f} | Sim={m['similarity']:.4f} | Q='{m['matching_query']}'")

            # 3. Filter — keep only candidates above threshold
            best_match = top_matches[0]
            if best_match["final_score"] < threshold:
                return {"type": "no_match", "message": "No suitable knowledge found."}

            above_threshold = [m for m in top_matches if m["final_score"] >= threshold]

            # 4. Synthesize across all qualifying chunks
            synthesized = synthesize(above_threshold, query=clean_input)

            # Fallback: if synthesizer returns empty, use best match verbatim
            if not synthesized:
                synthesized = best_match["response"]

            explanation = (
                f"Synthesized from {len(above_threshold)} chunk(s). "
                f"Best match: '{best_match['matching_query']}' "
                f"(score {best_match['final_score']:.2f})"
            )

            return {
                "type":          "match",
                "response":      synthesized,
                "reason":        explanation,
                "matching_query": best_match["matching_query"],
                "similarity":    best_match["similarity"],
                "confidence":    best_match.get("item", {}).get("confidence", best_match["similarity"])
                                 if isinstance(best_match.get("item"), dict) else best_match["similarity"],
                "final_score":   best_match["final_score"],
                "source":        best_match.get("source", "mmf"),
                "chunks_used":   len(above_threshold)
            }

        return {
            "type":    "no_match",
            "message": "No suitable knowledge found."
        }

