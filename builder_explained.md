# Builder module explained (`mmf/builder.py`)

## What does it do?
The Builder module acts as the system's "Compiler" or package manager. It takes a raw, exposed MMF directory (filled with individual JSON files) and compresses it beautifully into a single, cohesive `.mmf` ZIP binary file.

## Key components for beginners:
1. **`os.walk` Processing**: The script actively runs through every single file inside the targeted folder (e.g., `assistant.mmf\`).
2. **Relative Pathing (`arcname`)**: Instead of zipping your files via your computer's absolute paths (like `/Users/name/desktop/...`), which breaks when shared with others, it evaluates the `arcname` via `os.path.relpath()`. This drops the files flush against the root of the ZIP.
3. **The `zipfile` Protocol**: It executes a `ZIP_DEFLATED` compression protocol, compressing text footprints heavily without data loss.

## Why use the Builder?
In modern Software Architectural Standards, large multi-node systems are packaged (like Java's `.jar`, or iPhone's `.ipa`). This guarantees that your `manifest.json`, `config`, and `knowledge` states cannot be accidentally separated, providing clean version control backups and an incredibly tidy local file structure!
