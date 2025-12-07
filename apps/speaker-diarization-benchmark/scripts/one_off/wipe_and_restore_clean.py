
import os
import sys
import json
import uuid
from dotenv import load_dotenv

# Adjust path to find src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.append(project_root)

from src.data.impl.instant_db_adapter import InstantDBVideoRepository

load_dotenv()

TARGET_RUN_ID = "c22a7475-e6a1-500b-b427-9a9e553bba8d"
TARGET_CLIP_ID = "clip_youtube_jAlKYYr1bpY_0_60.wav"

def main():
    app_id = os.getenv("INSTANT_APP_ID")
    admin_secret = os.getenv("INSTANT_ADMIN_SECRET")
    repo = InstantDBVideoRepository(app_id, admin_secret)

    print("=== Step 1: Wipe Existing Segments ===")
    q_all = {
        "diarizationSegments": {
            "$": {"where": {"run_id": TARGET_RUN_ID}}
        }
    }
    res = repo._query(q_all)
    existing_segs = res.get("diarizationSegments", [])
    print(f"Found {len(existing_segs)} segments to delete.")
    
    if existing_segs:
        del_steps = [["delete", "diarizationSegments", s["id"]] for s in existing_segs]
        batch_size = 100
        for i in range(0, len(del_steps), batch_size):
            repo._transact(del_steps[i:i+batch_size])
        print("Wipe Complete.")
    
    print("\n=== Step 2: Prepare Data from Manifest ===")
    manifest_path = os.path.join(project_root, "data/clips/manifest.json")
    with open(manifest_path, "r") as f:
        data = json.load(f)
    clip_data = next((c for c in data if c["id"] == TARGET_CLIP_ID), None)
    manifest_segs = clip_data.get("transcriptions", {}).get("mlx_whisper_turbo_seg_level", [])
    print(f"Loaded {len(manifest_segs)} segments from manifest.")
    
    # Speakers Map
    print("Fetching Speakers from DB...")
    res_spk = repo._query({"speakers": {"$": {}}})
    db_speakers = res_spk.get("speakers", [])
    name_to_id = {s["name"]: s["id"] for s in db_speakers if "name" in s}
    print(f"Mapped {len(name_to_id)} speakers.")

    # Stable Segments (for Overlap)
    print("Fetching Stable Segments...")
    q_stable = {
        "stableSegments": {
             "$": {"limit": 100} 
        }
    }
    res_s = repo._query(q_stable)
    stable_segs = res_s.get("stableSegments", [])
    print(f"Loaded {len(stable_segs)} stable segments for linking.")

    print("\n=== Step 3: Create and Link Segments ===")
    steps = []
    
    for seg in manifest_segs:
        # Create
        seg_uuid = str(uuid.uuid4())
        start = seg["start"]
        end = seg["end"]
        spk_name = seg.get("speaker")
        
        payload = {
            "run_id": TARGET_RUN_ID,
            "start_time": start,
            "end_time": end,
        }
        steps.append(["update", "diarizationSegments", seg_uuid, payload])
        
        # Link Run (Forward)
        steps.append(["link", "diarizationRuns", TARGET_RUN_ID, {"diarizationSegments": seg_uuid}])
        
        # Link Speaker (Forward from Segment -> Speaker)
        if spk_name:
            spk_id = name_to_id.get(spk_name)
            if spk_id:
                steps.append(["link", "diarizationSegments", seg_uuid, {"speaker": spk_id}])
            else:
                 print(f"Warning: Speaker '{spk_name}' not found.")
        
        # Link Stable Segments (Overlap)
        for s in stable_segs:
            s_start = s["start_time"]
            s_end = s["end_time"]
            # Overlap: Max(startA, startB) < Min(endA, endB)
            # Or simpler: A.start < B.end AND A.end > B.start
            if (start < s_end) and (end > s_start):
                 # Link D-Seg -> S-Seg
                 # diarizationSegments.stableSegments
                 steps.append(["link", "diarizationSegments", seg_uuid, {"stableSegments": s["id"]}])

    print(f"Prepared {len(steps)} total transaction steps.")
    
    # Execute batch
    batch_size = 100
    for i in range(0, len(steps), batch_size):
        repo._transact(steps[i:i+batch_size])
        
    print("Restore & Link Complete.")

if __name__ == "__main__":
    main()
