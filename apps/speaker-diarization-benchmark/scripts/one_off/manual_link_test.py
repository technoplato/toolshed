
import os
import sys
import json
import uuid
import time
from dotenv import load_dotenv

# Adjust path to find src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.append(project_root)

from src.data.impl.instant_db_adapter import InstantDBVideoRepository

load_dotenv()

TARGET_RUN_ID = "c22a7475-e6a1-500b-b427-9a9e553bba8d"

def main():
    app_id = os.getenv("INSTANT_APP_ID")
    admin_secret = os.getenv("INSTANT_ADMIN_SECRET")
    repo = InstantDBVideoRepository(app_id, admin_secret)

    print("Fetching segments...")
    # ... (skipping segment query for a moment or doing both)
    
    print("Fetching All Speakers Direct...")
    res_spk = repo._query({"speakers": {"$": {}}})
    print(json.dumps(res_spk, indent=2))

if __name__ == "__main__":
    main()
