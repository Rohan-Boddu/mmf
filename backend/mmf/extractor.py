"""
Extractor module for the MMF system.
Converts cleaned sentences into structured knowledge entries using native strict rules.
"""
from typing import List

def extract_knowledge(sentences: List[str]) -> List[dict]:
    """
    Extracts structured MMF knowledge entries from cleaned sentences using 'X is Y' rules.
    
    Args:
        sentences (List[str]): Cleaned sentences from processor.
        
    Returns:
        List[dict]: List of structured query/response/tag dictionaries.
    """
    entries = []
    
    for sentence in sentences:
        # Rule 5: Skip invalid sentences (too short or no meaningful structure)
        if len(sentence) < 10 or " is " not in sentence:
            continue
            
        # Rule 1: Detect "X is Y"
        parts = sentence.split(" is ", 1)
        if len(parts) != 2:
            continue
            
        subject = parts[0].strip()
        definition = parts[1].strip()
        
        # Guard clause: avoid capturing massive structural blocks improperly
        if len(subject) > 30 or not subject or not definition:
            continue
            
        # Rule 2: Multi-Query Generation
        queries = [
            f"what is {subject}",
            f"define {subject}",
            f"tell me about {subject}"
        ]
        
        # Rule 3: Response
        response = f"{subject} is {definition}."
        
        # Rule 4: Smart Tagging
        stop_words = {"is", "a", "an", "the", "of", "and", "in", "to", "for", "with"}
        # Basic cleanup: remove simple punctuation from words before tagging to ensure purity
        clean_sentence = "".join(c for c in sentence if c.isalnum() or c.isspace())
        words = [w for w in clean_sentence.split() if w not in stop_words]
        tags = words[:4] # Store up to 4 meaningful keywords
        
        entries.append({
            "queries": queries,
            "response": response,
            "tags": tags,
            "source": "dataset",
            "confidence": 0.9
        })
        
    return entries
