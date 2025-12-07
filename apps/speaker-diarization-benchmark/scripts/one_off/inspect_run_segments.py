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

def inspect_segments():
    app_id = os.getenv("INSTANT_APP_ID")
    admin_secret = os.getenv("INSTANT_ADMIN_SECRET")
    
    if not app_id or not admin_secret:
        print("Error: INSTANT_APP_ID and INSTANT_ADMIN_SECRET must be set.")
        return

    repo = InstantDBVideoRepository(app_id, admin_secret)
    
    target_video_id = "4417c492-cb62-546d-94f0-1f9af5546212"
    
    print(f"Querying runs for video {target_video_id}...")
    
    query = {
        "videos": {
            "$": { "where": { "id": target_video_id } },
            "transcriptionRuns": {
                "segments": { "$": { "limit": 3 } }
            },
            "diarizationRuns": {
                "segments": { "$": { "limit": 3 }, "speaker": {} }
            }
        }
    }
    
    resp = repo._query(query)
    videos = resp.get("videos", [])
    if not videos:
        print("Video not found.")
        return
        
    video = videos[0]
    
    print(f"Video: {video.get('title')}")
    
    print("\n--- Transcription Runs ---")
    for run in video.get("transcriptionRuns", []):
        print(f"Run ID: {run['id']}")
        segments = run.get("segments", [])
        print(f"  Segment Count (Limit 3): {len(segments)}")
        for s in segments:
            print(f"    [{s.get('start_time')}-{s.get('end_time')}]: {s.get('text')}")
            
    print("\n--- Diarization Runs ---")
    for run in video.get("diarizationRuns", []):
        print(f"Run ID: {run['id']}")
        segments = run.get("segments", [])
        print(f"  Segment Count (Limit 3): {len(segments)}")
        for s in segments:
            spk = s.get("speaker", {}).get("name", "Unknown")
            print(f"    [{s.get('start_time')}-{s.get('end_time')}]: Speaker {spk}")

if __name__ == "__main__":
    inspect_segments()
