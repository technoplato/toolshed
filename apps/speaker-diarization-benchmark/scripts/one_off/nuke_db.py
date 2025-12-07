"""
HOW:
  Run from the speaker-diarization-benchmark directory:
  `uv run python scripts/one_off/nuke_db.py`

  [Inputs]
  - INSTANT_APP_ID (env): The InstantDB Application ID
  - INSTANT_ADMIN_SECRET (env): The Admin Secret for the app

  [Outputs]
  - Deletes ALL data from the InstantDB instance

  [Side Effects]
  - DESTRUCTIVE: Wipes entire database

WHO:
  Antigravity, User
  (Context: Schema migration - need clean slate for new schema)

WHAT:
  Nuclear option script to delete all data from InstantDB.
  Uses the Admin API to query and delete all entities.

WHEN:
  Created: 2025-12-07
  Last Modified: 2025-12-07

WHERE:
  apps/speaker-diarization-benchmark/scripts/one_off/nuke_db.py

WHY:
  When migrating to a new schema, existing data may conflict.
  This provides a clean slate for the new schema to be pushed.
"""

import sys
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

def nuke():
    """Delete all data from InstantDB."""
    
    # Load .env from repo root
    repo_root = Path(__file__).resolve().parents[4]
    env_path = repo_root / ".env"
    load_dotenv(env_path)
    
    app_id = os.getenv("INSTANT_APP_ID")
    admin_secret = os.getenv("INSTANT_ADMIN_SECRET")
    
    if not app_id or not admin_secret:
        print("Error: INSTANT_APP_ID and INSTANT_ADMIN_SECRET must be set in .env")
        print(f"Looked for .env at: {env_path}")
        return
    
    print(f"Using App ID: {app_id[:8]}...")
    print("Nuking Database...")
    
    base_url = "https://api.instantdb.com/admin"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_secret}",
        "App-Id": app_id
    }
    
    # New schema collections (after redesign)
    collections = [
        "publications",
        "videos",
        "speakers",
        "transcriptionConfigs",
        "diarizationConfigs",
        "transcriptionRuns",
        "diarizationRuns",
        "words",
        "diarizationSegments",
        "speakerAssignments",
        "segmentSplits",
        "wordTextCorrections",
        "shazamMatches",
        # Old schema collections (in case any remain)
        "stableSegments",
        "correctedSegments",
        "transcriptionSegments",
    ]
    
    total_deleted = 0
    
    for collection in collections:
        try:
            # Query all items in collection
            resp = requests.post(
                f"{base_url}/query",
                json={"query": {collection: {}}},
                headers=headers,
                timeout=30
            )
            
            if resp.status_code != 200:
                print(f"  {collection}: Query failed ({resp.status_code})")
                continue
                
            items = resp.json().get(collection, [])
            
            if not items:
                print(f"  {collection}: Empty")
                continue
            
            # Delete in batches
            steps = [["delete", collection, item["id"]] for item in items]
            batch_size = 100
            
            for i in range(0, len(steps), batch_size):
                batch = steps[i:i+batch_size]
                resp = requests.post(
                    f"{base_url}/transact",
                    json={"steps": batch},
                    headers=headers,
                    timeout=30
                )
                if resp.status_code != 200:
                    print(f"  {collection}: Delete batch failed ({resp.status_code})")
                    
            print(f"  {collection}: Deleted {len(items)} items")
            total_deleted += len(items)
            
        except Exception as e:
            print(f"  {collection}: Error - {e}")
    
    print(f"\nDatabase Wiped. Total deleted: {total_deleted} items.")

if __name__ == "__main__":
    nuke()
