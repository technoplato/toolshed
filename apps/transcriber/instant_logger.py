import logging
import time
import uuid
import os
import requests
import json
from datetime import datetime

class InstantDBHandler(logging.Handler):
    def __init__(self, app_id, admin_token, source="python-app"):
        super().__init__()
        self.app_id = app_id
        self.admin_token = admin_token
        self.source = source
        self.base_url = "https://api.instantdb.com"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {admin_token}",
            "App-Id": app_id
        }

    def emit(self, record):
        try:
            msg = self.format(record)
            
            # Construct the log entry
            log_id = str(uuid.uuid4())
            log_entry = {
                "timestamp": int(time.time() * 1000),
                "created_at": datetime.now().isoformat(), # Required by schema (string)
                "level": record.levelname,
                "message": msg,
                "source": self.source,
                "file": record.filename,
                "line": record.lineno,
                "module": record.module
            }

            # Construct the transaction step
            # We use the 'logs' namespace
            step = [
                "update",
                "logs",
                log_id,
                log_entry
            ]

            # Send the request synchronously
            response = requests.post(
                f"{self.base_url}/admin/transact",
                headers=self.headers,
                json={"steps": [step]},
                timeout=5
            )
            
            if response.status_code != 200:
                # Fallback to stderr if logging fails
                print(f"Failed to log to InstantDB: {response.text}")

        except Exception as e:
            self.handleError(record)
            print(f"Error in InstantDBHandler: {e}")

def setup_instant_logging(app_id, admin_token, source="python-app"):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Check if handler already exists to avoid duplicates
    for h in logger.handlers:
        if isinstance(h, InstantDBHandler):
            return logger

    handler = InstantDBHandler(app_id, admin_token, source)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Also add console handler if not present
    has_console = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
    if not has_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger
