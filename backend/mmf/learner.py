"""
Learner module for the MMF system.
Responsible ONLY for securely storing new knowledge back into the .mmf system.
v0.7.2: Added versioning, atomic writes, backup, and corruption detection.
"""
import json
import uuid
import datetime
import logging
import shutil
import os
import time
from pathlib import Path
from filelock import FileLock, Timeout

logger = logging.getLogger('mmf.learner')

# Max backups to keep
MAX_BACKUPS = 10


class MMFLearner:
    """Class responsible for adding new knowledge securely without corrupting existing data."""

    def __init__(self, directory_path: str):
        """
        Initializes the learner with the given directory path.
        
        Args:
            directory_path (str): The path to the .mmf directory.
        """
        self.directory_path = Path(directory_path)
        self.knowledge_path = self.directory_path / "knowledge.json"
        self.lock_path = self.directory_path / "knowledge.json.lock"
        self.backup_dir = self.directory_path / "backups"

    def learn(self, query: str, response: str, tags: list = None) -> dict:
        """
        Legacy wrapper for backwards compatibility with single-query injection.
        """
        if not tags: tags = []
        if not query or not query.strip():
            return {}
        if not response or not response.strip():
            return {}
        entries = [{
            "queries": [query.strip()], 
            "response": response.strip(),
            "tags": tags,
            "source": "manual",
            "confidence": 0.9
        }]
        added = self.learn_batch(entries)
        return added["added"][0] if added["added"] else {}

    def learn_batch(self, entries: list) -> list:
        """
        Learns multiple concepts in a single transaction securely.
        Uses intelligent merging logic if duplicate queries are found.
        """
        if not entries:
            return {"added": [], "merged": []}

        lock = FileLock(self.lock_path, timeout=10)
        try:
            with lock:
                knowledge = self._load_current_knowledge()
                
                # Build mapping of all existing queries
                query_map = {}
                for item in knowledge:
                    item_queries = item.get('queries', [])
                    if 'query' in item and item['query']:
                        item_queries.append(item['query'])
                    
                    for q in item_queries:
                        query_map[q.lower()] = item

                added_entries = []
                merged_entries = []
                
                for raw_entry in entries:
                    new_queries = raw_entry.get('queries', [])
                    if not new_queries:
                        continue
                        
                    response = raw_entry.get('response', '').strip()
                    if not response:
                        continue
                        
                    tags = raw_entry.get('tags', [])
                    source = raw_entry.get('source', 'dataset')
                    confidence = raw_entry.get('confidence', 0.9)
                    
                    # Check for duplicates
                    duplicate_target = None
                    for q in new_queries:
                        q_lower = q.lower()
                        if q_lower in query_map:
                            duplicate_target = query_map[q_lower]
                            break
                            
                    if duplicate_target:
                        # Intelligent Merging
                        for key, value in raw_entry.items():
                            if key not in ['queries', 'response', 'tags', 'source', 'confidence'] and key not in duplicate_target:
                                duplicate_target[key] = value
                        merged_entries.append(duplicate_target)
                    else:
                        # Insert New Entry
                        new_entry = {
                            "id": str(uuid.uuid4()),
                            "queries": list(set(new_queries)),
                            "response": response,
                            "tags": list(set(tags)),
                            "source": source,
                            "confidence": confidence,
                            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                        }
                        
                        for key, value in raw_entry.items():
                            if key not in new_entry:
                                new_entry[key] = value

                        knowledge.append(new_entry)
                        added_entries.append(new_entry)
                        
                        for nq in new_queries:
                            query_map[nq.lower()] = new_entry

                # Save with atomic write + backup
                self._save_knowledge(knowledge)
                
                logger.info(f"Learn batch complete: {len(added_entries)} added, {len(merged_entries)} merged.")
                return {"added": added_entries, "merged": merged_entries}

        except Timeout:
            logger.error("Timeout waiting for knowledge lock")
            raise IOError("Could not acquire lock for knowledge base. Concurrent write in progress?")
        except Exception as e:
            logger.error(f"Error during learn_batch: {str(e)}", exc_info=True)
            raise

    def validate_knowledge(self) -> dict:
        """
        Validates the current knowledge.json for corruption.
        Returns a dict with 'valid' bool and 'errors' list.
        """
        result = {"valid": True, "errors": [], "entry_count": 0}
        
        try:
            knowledge = self._load_current_knowledge()
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Failed to load knowledge: {str(e)}")
            return result
        
        if not isinstance(knowledge, list):
            result["valid"] = False
            result["errors"].append("knowledge.json is not a list")
            return result
        
        result["entry_count"] = len(knowledge)
        
        for i, item in enumerate(knowledge):
            if not isinstance(item, dict):
                result["errors"].append(f"Entry {i} is not a dict")
                result["valid"] = False
                continue
            if 'response' not in item:
                result["errors"].append(f"Entry {i} missing 'response'")
                result["valid"] = False
            if 'queries' not in item and 'query' not in item:
                result["errors"].append(f"Entry {i} missing 'queries' or 'query'")
                result["valid"] = False
        
        return result

    def get_versions(self) -> list:
        """Returns a list of available backup versions."""
        if not self.backup_dir.exists():
            return []
        
        backups = sorted(self.backup_dir.glob("knowledge_*.json"), reverse=True)
        versions = []
        for b in backups:
            stat = b.stat()
            versions.append({
                "filename": b.name,
                "size_bytes": stat.st_size,
                "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        return versions

    def rollback(self, version_filename: str) -> bool:
        """
        Restores knowledge.json from a backup version.
        Creates a backup of current state before rolling back.
        """
        backup_path = self.backup_dir / version_filename
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup version not found: {version_filename}")
        
        # Validate the backup file first
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Backup is not a valid knowledge list")
        except Exception as e:
            raise ValueError(f"Backup file is corrupted: {str(e)}")
        
        # Backup current state before rollback
        self._create_backup()
        
        # Replace current knowledge with backup
        shutil.copy2(backup_path, self.knowledge_path)
        logger.info(f"Rolled back to version: {version_filename}")
        return True

    def _create_backup(self):
        """Creates a timestamped backup of the current knowledge.json."""
        if not self.knowledge_path.exists():
            return
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"knowledge_{timestamp}.json"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(self.knowledge_path, backup_path)
        logger.info(f"Created backup: {backup_name}")
        
        # Prune old backups
        backups = sorted(self.backup_dir.glob("knowledge_*.json"), reverse=True)
        for old_backup in backups[MAX_BACKUPS:]:
            old_backup.unlink()
            logger.info(f"Pruned old backup: {old_backup.name}")

    def _load_current_knowledge(self) -> list:
        """Safely loads current knowledge."""
        import zipfile
        if self.directory_path.is_file() and zipfile.is_zipfile(self.directory_path):
            try:
                with zipfile.ZipFile(self.directory_path, 'r') as zf:
                    with zf.open("knowledge.json", 'r') as f:
                        return json.loads(f.read().decode('utf-8'))
            except Exception as e:
                raise IOError(f"Failed to load knowledge from ZIP for learning: {e}")
        else:
            try:
                with open(self.knowledge_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                raise IOError(f"Failed to load knowledge for learning: {e}")

    def _save_knowledge(self, knowledge: list) -> None:
        """
        Safely saves the knowledge list with atomic write pattern:
        1. Write to temporary file
        2. Validate the written JSON
        3. Create backup of current file
        4. Atomically replace original file
        """
        import zipfile

        if self.directory_path.is_file() and zipfile.is_zipfile(self.directory_path):
            new_k_str = json.dumps(knowledge, indent=2)
            temp_zip_path = str(self.directory_path) + ".tmp"
            try:
                with zipfile.ZipFile(self.directory_path, 'r') as zin, \
                     zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                    for item in zin.infolist():
                        if item.filename != "knowledge.json":
                            zout.writestr(item, zin.read(item.filename))
                    zout.writestr("knowledge.json", new_k_str)
                shutil.move(temp_zip_path, self.directory_path)
            except Exception as e:
                if os.path.exists(temp_zip_path):
                    os.remove(temp_zip_path)
                raise IOError(f"Failed to safely repack zip MMF: {e}")
        else:
            try:
                # Step 1: Write to temp file
                temp_path = str(self.knowledge_path) + ".tmp"
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(knowledge, f, indent=2)
                
                # Step 2: Validate the temp file
                with open(temp_path, 'r', encoding='utf-8') as f:
                    validated = json.load(f)
                if not isinstance(validated, list):
                    raise ValueError("Written JSON is not a list")
                
                # Step 3: Backup current file
                self._create_backup()
                
                # Step 4: Atomic replace
                os.replace(temp_path, self.knowledge_path)
                
            except Exception as e:
                # Clean up temp file on failure
                temp_path = str(self.knowledge_path) + ".tmp"
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise IOError(f"Failed to save knowledge safely: {e}")
