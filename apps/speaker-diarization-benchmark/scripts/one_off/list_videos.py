import sys
import os
import json
from dotenv import load_dotenv

# Adjust path to find src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.append(project_root)

from src.data.impl.instant_db_adapter import InstantDBVideoRepository

load_dotenv()

def list_videos():
    app_id = os.getenv("INSTANT_APP_ID")
    admin_secret = os.getenv("INSTANT_ADMIN_SECRET")
    
    if not app_id or not admin_secret:
        print("Error: INSTANT_APP_ID and INSTANT_ADMIN_SECRET must be set.")
        return

    repo = InstantDBVideoRepository(app_id, admin_secret)
    
    print("Querying specific video...")
    
    target_id = "4417c492-cb62-546d-94f0-1f9af5546212"
    
    query = {
        "videos": {
            "$": { "where": { "id": target_id } },
            "stableSegments": { "$": { "limit": 5, "order": { "index": "asc" } } },
            "transcriptionRuns": {
                "transcriptionSegments": { "$": { "limit": 3 } }
            },
            "diarizationRuns": {
                "diarizationSegments": { "$": { "limit": 3 }, "speaker": {} }
            }
        }
    }
    
    resp = repo._query(query)
    videos = resp.get("videos", [])
    
    if not videos:
        print("Target video not found.")
        return

    v = videos[0]
    print(f"ID: {v['id']}")
    print(f"Title: {v.get('title')}")
    
    # Stable Segments
    ss = v.get("stableSegments", [])
    print(f"\nStable Segments (Limit 5): {len(ss)} found (query limit 5)")
    for s in ss:
        print(f"  #{s.get('index')}: {s.get('start_time')}s - {s.get('end_time')}s")

    # Transcription Runs
    tr = v.get("transcriptionRuns", [])
    print(f"\nTranscription Runs: {len(tr)}")
    for run in tr:
        segs = run.get("transcriptionSegments", [])
        print(f"  Run {run['id']}: {len(segs)} segments (Limit 3 shown)")
        for s in segs:
            print(f"    [{s.get('start_time')}-{s.get('end_time')}]: {s.get('text')}")

    # Diarization Runs
    dr = v.get("diarizationRuns", [])
    print(f"\nDiarization Runs: {len(dr)}")
    for run in dr:
        segs = run.get("diarizationSegments", [])
        print(f"  Run {run['id']}: {len(segs)} segments (Limit 3 shown)")
        for s in segs:
            spk = s.get("speaker", {}).get("name")
            print(f"    [{s.get('start_time')}-{s.get('end_time')}]: {spk}")

if __name__ == "__main__":
    list_videos()
