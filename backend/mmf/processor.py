"""
Processor module for the MMF system.
Cleans and normalizes raw text before extraction.
"""
from typing import List
import re

def process_text(raw_text: str) -> List[str]:
    """
    Cleans raw text and splits it into sentences.
    
    Args:
        raw_text (str): The raw input text.
        
    Returns:
        List[str]: A list of cleaned sentences.
    """
    if not isinstance(raw_text, str) or not raw_text.strip():
        return []
        
    # Convert to lowercase
    text = raw_text.lower()
    
    # Replace newlines with spaces for a continuous line
    text = text.replace('\n', ' ').replace('\r', ' ')
    
    # Remove excessive continuous whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Split paragraphs into sentences natively using punctuation (.!?)
    raw_sentences = re.split(r'[.!?]+', text)
    
    cleaned_sentences = []
    for s in raw_sentences:
        s = s.strip()
        # Clean special chars (keeping alphanumeric, space, hyphens)
        s = re.sub(r'[^a-z0-9\s\-]', '', s).strip()
        
        if len(s) > 3: # Skip very short meaningless fragments
            cleaned_sentences.append(s)
            
    return cleaned_sentences

def normalize_query(query: str) -> str:
    """
    Normalizes a user query natively stripping out human-filler padding for denser semantic hits.
    
    Args:
        query (str): The raw user query.
        
    Returns:
        str: A densely normalized keyword query string.
    """
    if not query or not isinstance(query, str):
        return ""
        
    text = query.lower()
    
    # Strip explicit filler arrays natively
    filler_phrases = ["can you", "please", "tell me", "explain", "i want to know", "about", "what is"]
    for phrase in filler_phrases:
        # We replace with space to avoid merging words together: "can youexplain"
        text = text.replace(phrase, " ")
        
    # Strip basic punctuation safely mapping semantic keys
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    # Trim continuous native whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
