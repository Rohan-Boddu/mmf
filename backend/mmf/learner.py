"""
Learner module for the MMF system.
Responsible ONLY for securely storing new knowledge back into the .mmf system.
"""
import json
import uuid
import datetime
from pathlib import Path

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

    def learn(self, query: str, response: str, tags: list = None) -> dict:
        """
        Legacy wrapper for backwards compatibility with single-query injection.
        """
        if not tags: tags = []
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
            return []

        knowledge = self._load_current_knowledge()
        
        # Build mapping of all existing queries to their parent item reference (to merge in place)
        query_map = {}
        for item in knowledge:
            # Handle legacy 'query' logic inline natively
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
                
                # 1. Merge Queries (Union array, lowercased tracking internally but preserving format)
                current_queries = duplicate_target.get('queries', [])
                if 'query' in duplicate_target and duplicate_target['query']:
                    current_queries.append(duplicate_target.pop('query'))
                
                merged_queries = list(set(current_queries + new_queries))
                
                # Query Pruning: Limit MAX_QUERIES = 5
                # Diversity rule natively executed by keeping longest structurally complex variables
                if len(merged_queries) > 5:
                    merged_queries.sort(key=len, reverse=True)
                    merged_queries = merged_queries[:5]
                    
                duplicate_target['queries'] = merged_queries
                
                # 2. Merge Tags (Union array) + Tag Cleanup
                current_tags = set(duplicate_target.get('tags', []))
                current_tags.update(tags)
                
                # Strip native basic stopwords
                stop_words = {"is", "a", "an", "the", "of", "and", "in", "to", "for", "with", "what"}
                clean_tags = [t.lower() for t in current_tags if t.lower() not in stop_words]
                
                # Limit to 5
                duplicate_target['tags'] = clean_tags[:5]
                
                # 3. Choose Best Response (better structure or longer string)
                old_response = duplicate_target.get('response', '')
                if len(response) > len(old_response):
                    duplicate_target['response'] = response
                
                # 4. Bump confidence
                old_conf = duplicate_target.get('confidence', 0.9)
                duplicate_target['confidence'] = min(1.0, old_conf + 0.05)
                
                # Re-map all the newly added queries to this object to catch intra-batch dupes
                for mq in merged_queries:
                    query_map[mq.lower()] = duplicate_target

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
                knowledge.append(new_entry)
                added_entries.append(new_entry)
                
                # Add to query_map to prevent intra-batch dupes
                for nq in new_queries:
                    query_map[nq.lower()] = new_entry

        # We always save because we might have either added or merged items.
        # Actually save only if there was a mutation. Since tracking mutations is complex with refs, we just save.
        self._save_knowledge(knowledge)
            
        return {"added": added_entries, "merged": merged_entries}

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
        """Safely saves the knowledge list back to the file."""
        import zipfile
        import os
        import shutil

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
                # We use an atomic-like approach (minimizing open window)
                with open(self.knowledge_path, 'w', encoding='utf-8') as f:
                    json.dump(knowledge, f, indent=2)
            except Exception as e:
                raise IOError(f"Failed to save knowledge safely: {e}")
