
import os
import json
import sys
import uuid
import math
from dotenv import load_dotenv

# Adjust path to find src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.append(project_root)

from src.data.impl.instant_db_adapter import InstantDBVideoRepository
from src.data.models import Video, DiarizationSegment, Speaker

load_dotenv()

TARGET_CLIP_ID = "clip_youtube_jAlKYYr1bpY_0_60.wav"
TARGET_VIDEO_ID = "4417c492-cb62-546d-94f0-1f9af5546212" # From previous finding

def main():
    app_id = os.getenv("INSTANT_APP_ID")
    admin_secret = os.getenv("INSTANT_ADMIN_SECRET")
    
    if not app_id or not admin_secret:
        print("Error: INSTANT_APP_ID or INSTANT_ADMIN_SECRET not set.")
        return

    repo = InstantDBVideoRepository(app_id, admin_secret)

    # 1. Load Manifest
    manifest_path = os.path.join(project_root, "data/clips/manifest.json")
    if not os.path.exists(manifest_path):
        print(f"Manifest not found at {manifest_path}")
        return

    with open(manifest_path, "r") as f:
        data = json.load(f)

    # Find the clip
    clip_data = next((c for c in data if c["id"] == TARGET_CLIP_ID), None)
    if not clip_data:
        print(f"Clip {TARGET_CLIP_ID} not found in manifest.")
        return

    # 2. Extract Data (Speakers and Words)
    # We use "mlx_whisper_turbo_seg_level" as ground truth for now
    segments = clip_data.get("transcriptions", {}).get("mlx_whisper_turbo_seg_level", [])
    if not segments:
        print("No mlx_whisper_turbo_seg_level segments found in manifest.")
        return

    print(f"Found {len(segments)} segments in manifest.")

    # 3. Query existing Runs/Segments from DB for this video
    # We need to find the specific RUN ID we are fixing.
    # We'll just fetch ALL runs for the video and look for the one with segments essentially matching?
    # Or matches "benchmark_tuned" config? 
    # Or just update ALL runs? 
    # User said: "diarizationRuns.id = c22a7475-e6a1-500b-b427-9a9e553bba8d"
    # Wait, user *gave* us the Run ID! 
    # "Where diarizationRuns.id = ..."
    DIARIZATION_RUN_ID = "c22a7475-e6a1-500b-b427-9a9e553bba8d"
    
    # We also need the Transcription Run ID linked to it?
    # Or just update speakers for D-Run, and Words for T-Run?
    # We need to find the T-Run ID.
    
    q_run = {
        "diarizationRuns": {
            "$": {"where": {"id": DIARIZATION_RUN_ID}},
            "transcriptionRun": {}, 
            "diarizationSegments": {}
        }
    }
    
    res = repo._query(q_run)
    d_runs = res.get("diarizationRuns", [])
    if not d_runs:
        print(f"Diarization Run {DIARIZATION_RUN_ID} not found in DB.")
        return
        
    d_run = d_runs[0]
    t_run = d_run.get("transcriptionRun")
    d_segs_db = d_run.get("diarizationSegments", [])
    
    if not t_run:
        print("No linked Transcription Run found via graph. Querying separately?")
        # InstantDB might return obj or list? "has one" -> obj usually? 
        # Check adapter or console log. Adapter usually returns lists for everything from rest API?
        # instant-core js returns obj for One relation.
        # Python adapter?
        # If it's a list:
        if isinstance(t_run, list) and t_run: t_run = t_run[0]
    
    if not t_run:
        # Fallback: Query all T-runs for video?
        print("Could not find T-Run linked to D-Run. Checking Video...")
        # Query T-Runs for video
        q_tr = {"transcriptionRuns": {"$": {"where": {"video_id": TARGET_VIDEO_ID}}}}
        res_tr = repo._query(q_tr)
        t_runs = res_tr.get("transcriptionRuns", [])
        if t_runs:
             # Pick the one created most recently or just the first?
             # Let's picking the first one for now.
             t_run = t_runs[0]
             print(f"Fallback: Found {len(t_runs)} T-Runs. Using {t_run['id']}.")
        
    if not t_run:
        print("Could not find T-Run even by Video ID.")
    else:
        TRANSCRIPTION_RUN_ID = t_run["id"]
        print(f"Found T-Run ID: {TRANSCRIPTION_RUN_ID}")
        
        # Load Existing T-Segments
        q_t = {
            "transcriptionSegments": {
                 "$": {"where": {"run_id": TRANSCRIPTION_RUN_ID}}
            }
        }
        res_t = repo._query(q_t)
        t_segs_db = res_t.get("transcriptionSegments", [])
        
        # HYDRATE WORDS (T-Segments)
        # We need to match DB segments to Manifest segments.
        # Match by start_time (approx)?
        updates_t = []
        
        # Build lookup by start time
        manifest_by_start = {round(s["start"], 2): s for s in segments}
        
        for t_seg in t_segs_db:
            start = t_seg.get("start_time")
            key = round(start, 2)
            match = manifest_by_start.get(key)
            if match:
                text = match.get("text", "")
                # Create Words payload
                # Simple split by space + linear interpolation
                words_arr = text.split()
                duration = match["end"] - match["start"]
                if not words_arr: continue
                
                word_dur = duration / len(words_arr)
                w_list = []
                curr = match["start"]
                for w in words_arr:
                    w_list.append({
                        "word": w,
                        "start": round(curr, 2),
                        "end": round(curr + word_dur, 2),
                        "conf": 1.0
                    })
                    curr += word_dur
                    
                updates_t.append(
                    ["update", "transcriptionSegments", t_seg["id"], {"words": w_list}]
                )
        
        if updates_t:
            print(f"Updating {len(updates_t)} Transcription Segments with Words...")
            repo._transact(updates_t)

    # HYDRATE SPEAKERS (D-Segments)
    updates_d = []
    
    # 1. Fetch Existing Speakers from DB
    print("Fetching existing speakers from DB...")
    res_spk = repo._query({"speakers": {}})
    db_speakers = res_spk.get("speakers", [])
    
    # Build Map: Name -> UUID
    # Normalize name to lower case for safer matching? Or exact? 
    # User's list has "Matt McCusker", "Shane Gillis". 
    # Manifest has "Matt McCusker". Exact match should work.
    name_to_id = {s["name"]: s["id"] for s in db_speakers if "name" in s}
    print(f"Found {len(name_to_id)} existing speakers.")
    
    # Build lookup for D-Segments in DB (by start time)
    d_manifest_by_start = {round(s["start"], 2): s for s in segments}
    
    for d_seg in d_segs_db:
        start = d_seg.get("start_time")
        key = round(start, 2)
        match = d_manifest_by_start.get(key)
        
        if match:
             spk_name = match.get("speaker")
             if spk_name:
                 # Lookup existing ID
                 spk_id = name_to_id.get(spk_name)
                 
                 if not spk_id:
                     print(f"Warning: Speaker '{spk_name}' not found in DB. Creating...")
                     # Create new if missing (fallback)
                     spk_id = str(uuid.uuid4())
                     updates_d.append(
                        ["update", "speakers", spk_id, {"name": spk_name, "is_human": True}]
                     )
                     name_to_id[spk_name] = spk_id
                 
                 # Link D-Segment to Speaker
                 # format: ["link", entity1, id1, {label: id2}] 
                 updates_d.append(
                     ["link", "diarizationSegments", d_seg["id"], {"speaker": spk_id}]
                 )
    
    if updates_d:
        print(f"Updating {len(updates_d)} steps for Diarization Segments...")
        repo._transact(updates_d)
        
    print("Hydration Complete.")

if __name__ == "__main__":
    main()
