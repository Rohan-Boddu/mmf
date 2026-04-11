# Processor module explained (`mmf/processor.py`)

## What does it do?
The Processor represents the first stage of the MMF Knowledge Extraction Pipeline. Its job is to take large, messy blocks of raw text (like a Wikipedia article or an entire chat log) and slice it down into clean, manageable, individual sentences.

## Key components for beginners:
1. **Cleaning Chaos**: Human text is rarely perfect. It can have double spaces, weird line-breaks (`\n` and `\r`), and mixed casing.
   - We instantly convert everything to lowercase to enforce standardization.
   - We strip out newline characters, effectively flattening paragraphs into a single continuous string.
2. **Sentence Boundary Detection**: Instead of importing heavy Linguistic frameworks to detect punctuation, we leverage Python's robust Native Regex engine (`re.split`). By splitting on periods (`.`), exclamation marks (`!`), and question marks (`?`), we naturally fracture the text block into discrete chunks.
3. **Invalidity Filtering**: It rejects meaningless string artifacts (like empty spaces or strings exactly 2 characters long) reducing noise passed downstream to the extractor.

## Scalability
By keeping the Processor strictly separated from the Extractor, we can eventually plug it into a PDF reader or Web Scraper. As long as it spits out a standard Python List of cleaned strings, the downstream Extractor will never care where the text originated!
