"""
Loader module for the MMF system.
Responsible ONLY for reading files, validating structure, and raising clear errors.
"""
import json
import os
from pathlib import Path

class MMFLoader:
    """Class responsible for loading the .mmf directory contents."""

    def __init__(self, directory_path: str):
        """
        Initializes the loader with the given directory path.
        
        Args:
            directory_path (str): The path to the .mmf directory.
        """
        self.directory_path = Path(directory_path)

    def load(self) -> dict:
        """
        Loads and validates the manifest, config, and knowledge files.
        
        Returns:
            dict: A dictionary containing 'manifest', 'config', and 'knowledge' data.
            
        Raises:
            FileNotFoundError: If any of the required files are missing.
            ValueError: If the file contents are invalid (e.g. missing required keys).
        """
        # Load specific known files according to the constraints
        manifest = self._load_json("manifest.json")
        config = self._load_json("config.json")
        knowledge = self._load_json("knowledge.json")

        self._validate_knowledge(knowledge)

        return {
            "manifest": manifest,
            "config": config,
            "knowledge": knowledge
        }

    def _load_json(self, filename: str) -> dict | list:
        """
        Helper method to load a JSON file from the MMF directory or ZIP archive.
        
        Args:
            filename (str): The name of the file to load.
            
        Returns:
            dict | list: The parsed JSON data.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not valid JSON.
        """
        import zipfile

        if self.directory_path.is_file() and zipfile.is_zipfile(self.directory_path):
            try:
                with zipfile.ZipFile(self.directory_path, 'r') as zf:
                    with zf.open(filename, 'r') as f:
                        return json.loads(f.read().decode('utf-8'))
            except KeyError:
                raise FileNotFoundError(f"Required file '{filename}' not found in ZIP {self.directory_path}.")
            except Exception as e:
                raise ValueError(f"File '{filename}' inside ZIP contains invalid JSON or cannot be read: {e}")
        else:
            file_path = self.directory_path / filename
            if not file_path.exists():
                raise FileNotFoundError(f"Required file '{filename}' not found in {self.directory_path}.")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"File '{filename}' contains invalid JSON: {e}")

    def _validate_knowledge(self, knowledge: list):
        """
        Validates the structure of the knowledge base.
        
        Args:
            knowledge (list): The loaded knowledge data.
            
        Raises:
            ValueError: If the knowledge is not a list, or if entries are missing 'query'/'response'.
        """
        if not isinstance(knowledge, list):
            raise ValueError("knowledge.json must contain a list of objects.")
        
        for index, item in enumerate(knowledge):
            if not isinstance(item, dict):
                raise ValueError(f"Knowledge item at index {index} is not an object.")
            
            has_query = 'query' in item
            has_queries = 'queries' in item
            
            if not has_query and not has_queries:
                raise ValueError(f"Knowledge item at index {index} is missing a 'query' or 'queries' field.")
                
            if 'response' not in item:
                raise ValueError(f"Knowledge item at index {index} is missing a 'response' field.")
