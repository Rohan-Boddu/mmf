# Extractor module explained (`mmf/extractor.py`)

## What does it do?
The Extractor serves as a native heuristic NLP generation layer. It mathematically filters clean python strings and structurally formats them into full MMF multi-query payloads.

## Key components for beginners:
1. **The Core Rule Engine**: NLP models are massive. To keep the framework perfectly local, the Extractor relies purely on native rules. It scans sentences searching for `X is Y` structural anchors.
2. **Multi-Query Generation (v0.3.1)**:
   - Previously, 1 sentence generated 1 generic query. 
   - Now, a single valid sentence mathematically fragments out into conversational arrays! `YouTube is a video platform` structurally translates directly into `["what is youtube", "define youtube", "tell me about youtube"]` concurrently! 
   - Finding *any* matching node from this massive generated vocabulary instantly snaps the context, greatly augmenting hit-rates natively against simple text overlapping!
3. **Smart Source Tagging**:
   - Generates confidence nodes intrinsically `confidence: 0.9` and anchors the origin point string `source: "dataset"`.
   - Eliminates standard English conjunctions/prepositions dynamically from the resulting array, capturing only the purest categorical `tags` left behind.

## Legacy Compatibility
Even though the output radically changed structurally from `query: ""` to `queries: []`, this decoupled architecture ensures your core matching algorithm seamlessly routes both formats synchronously maintaining 100% interoperability with your v0.2 generated components!
