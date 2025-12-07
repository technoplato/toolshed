import sys
import os
import json
from dotenv import load_dotenv

# Adjust path to find src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
sys.path.append(project_root)

from src.data.impl.instant_db_adapter import InstantDBVideoRepository

load_dotenv()

def find_video_with_segments():
    app_id = os.getenv("INSTANT_APP_ID")
    admin_secret = os.getenv("INSTANT_ADMIN_SECRET")
    
    if not app_id or not admin_secret:
        print("Error: INSTANT_APP_ID and INSTANT_ADMIN_SECRET must be set.")
        return

    repo = InstantDBVideoRepository(app_id, admin_secret)
    
    print("Querying for any transcription segments...")
    
    # Query for segments and their parent runs/videos
    query = {
        "transcriptionSegments": {
            "$": { "limit": 5 },
            "run": {
                "video": {}
            }
        }
    }
    
    resp = repo._query(query)
    
    if not resp.get("transcriptionSegments"):
        print("No transcription segments found in the entire database.")
        return

    print(f"Found {len(resp['transcriptionSegments'])} sample segments.")
    
    seen_videos = set()
    
    for seg in resp["transcriptionSegments"]:
        runs = seg.get("run", [])
        for run in runs:
            videos = run.get("video", [])
            for video in videos:
                if video["id"] not in seen_videos:
                    print(f"\n--- Found Populated Video ---")
                    print(f"ID: {video['id']}")
                    print(f"Title: {video.get('title', 'Unknown')}")
                    print(f"Filepath: {video.get('filepath', 'Unknown')}")
                    seen_videos.add(video["id"])
                    
    if not seen_videos:
        print("\nFound segments, but they don't seem linked to Videos properly.")

if __name__ == "__main__":
    find_video_with_segments()
