import json
import os
import logging
from typing import List, Set

logger = logging.getLogger(__name__)

STATE_FILE = "state.json"

class StateStore:
    def __init__(self, file_path: str = STATE_FILE):
        self.file_path = file_path
        self.processed_ids: Set[str] = set()
        self.load()

    def load(self):
        """Load state from JSON file."""
        if not os.path.exists(self.file_path):
            logger.info("No state file found. Starting fresh.")
            return

        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                # Keep only last 1000 IDs to prevent infinite growth if needed, 
                # or just load all. For now simple load.
                self.processed_ids = set(data.get("processed_ids", []))
            logger.info(f"Loaded {len(self.processed_ids)} processed IDs from state.")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")

    def save(self):
        """Save state to JSON file."""
        try:
            data = {
                "processed_ids": list(self.processed_ids)
            }
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info("State saved.")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def is_processed(self, email_id: str) -> bool:
        return email_id in self.processed_ids

    def add_processed(self, email_ids: List[str]):
        if not email_ids:
            return
        self.processed_ids.update(email_ids)
        self.save()
