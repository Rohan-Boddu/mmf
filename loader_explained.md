# Loader module explained (`mmf/loader.py`)

## What does it do?
The Loader's single job is to ingest and validate the memory files. It operates fully unaware of *what* the matching logic is.

## Key components for beginners:
1. **`__init__`**: Captures the path to the MMF system layout.
2. **`load()`**: The execution logic. It explicitly asks to load the three mandatory files (`manifest.json`, `config.json`, and `knowledge.json`) and runs validation loops over them natively.
3. **Zip Archive Native Decoding (v0.2 Upgrade)**: 
   - We upgraded the `_load_json()` helper. It now detects if `self.directory_path.is_file()` and if it happens to be an officially packaged `.mmf` ZIP Archive.
   - If it is a ZIP array, it utilizes Python's built-in `zipfile` module to extract the JSON files streams *straight into memory* without unzipping them to your physical disk!
   - This successfully enables the portability of the system (using `.mmf` files).
4. **Validation Pipeline**: The `_validate_knowledge()` method strictly iterates over the dataset, ensuring every element enforces the required structure (like missing query/response objects), guaranteeing system robustness and failure prevention.

## Strict Encapsulation
If we ever decide to move our JSON files onto an AWS bucket or transition them to a SQLite database, this is the **ONLY** file in the architecture that needs updating. The underlying system relies heavily on this clean encapsulation!
