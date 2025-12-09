
import sys
import os
import json
import uuid
import requests
import time
from pathlib import Path
# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from ingestion.instant_client import InstantClient, DiarizationSegment
from ingestion.identify import identify_speakers, print_plan
from src.embeddings.pgvector_client import PgVectorClient

# Constants
VIDEO_UUID = "a85ae635-963a-4c8f-9716-146b31e4446a" # Joe DeRosa
VIDEO_SOURCE_ID = "jAlKYYr1bpY" # Source ID for linking
CACHE_FILE = Path("data/cache/transcription/jAlKYYr1bpY__mlx-whisper__whisper-large-v3-turbo.json")
AUDIO_PATH = "data/clips/jAlKYYr1bpY.wav"
SERVER_URL = "http://localhost:3001"

def main():
    print(f"🔧 Initializing for video {VIDEO_UUID}...")
    
    # 1. Setup Clients
    try:
        instant_client = InstantClient()
        pg_dsn = os.getenv("SPEAKER_DB_DSN") or "postgresql://diarization:diarization_dev@localhost:5433/speaker_embeddings"
        pg_client = PgVectorClient(pg_dsn)
        print("   ✅ Clients connected")
    except Exception as e:
        print(f"   ❌ Failed to connect: {e}")
        sys.exit(1)

    # 2. Load Transcription Segments
    if not CACHE_FILE.exists():
        print(f"❌ Transcription cache not found: {CACHE_FILE}")
        sys.exit(1)
        
    with open(CACHE_FILE) as f:
        data = json.load(f)
        
    whisper_segments = data.get("result", {}).get("segments", [])
    print(f"   ✅ Loaded {len(whisper_segments)} Whisper segments")

    # 3. Convert to DiarizationSegments
    diarization_segments = []
    for seg in whisper_segments:
        # Create a temporary UUID
        seg_id = str(uuid.uuid4())
        
        ds = DiarizationSegment(
            id=seg_id,
            start_time=seg["start"],
            end_time=seg["end"],
            speaker_label="WHISPER_SEG", # Dummy label
            embedding_id=None,
            confidence=1.0,
            is_invalidated=False,
            speaker_assignments=[]
        )
        diarization_segments.append(ds)

    # 4. Run Identification
    print("\n🚀 Running identification on Whisper segments...")
    print("   (Cache disabled to ensure new computation)")
    
    plan = identify_speakers(
        instant_client=instant_client,
        pg_client=pg_client,
        video_id=VIDEO_UUID,
        audio_path=AUDIO_PATH,
        segments=diarization_segments,
        use_cache=False, # FORCE COMPUTE
        threshold=0.5,
        top_k=5
    )
    
    # 5. Filter for Identified Segments
    identified_segments = []
    
    print("\n🔍 Processing results...")
    for res in plan.results:
        # We want to keep ALL segments now
        
        if res.status == "identified" and res.speaker_id:
            # Label = Speaker Name (stored in identified_speaker) or ID
            label = res.identified_speaker or res.speaker_id
            confidence = res.distance
        else:
            # Status is "unknown", "skipped", or failed
            label = "UNKNOWN"
            # If skipped or no distance, set confidence to 0 (or distance 1.0)
            confidence = res.distance if res.distance is not None else 1.0
            
        seg_payload = {
            "start_time": res.segment_start,
            "end_time": res.segment_end,
            "speaker_label": label, 
            "confidence": confidence,
            "embedding_id": None
        }
        identified_segments.append(seg_payload)

    count_total = len(identified_segments)
    print(f"   ✅ Prepared {count_total} segments (Identified + Unknown) for saving")

    # 6. Save to InstantDB
    print("\n💾 Saving to InstantDB...")
    
    # 6a. Create Run
    run_payload = {
        "video": {
            "source_id": VIDEO_SOURCE_ID,
            # We just provide source_id so it links to existing video
        },
        "diarizationRun": {
            "workflow": "whisper_identified",
            "tool_version": "1.0",
            "pipeline_script": "identify_transcription_segments.py",
            "is_preferred": True, # Make it preferred so user sees it? Or False? User said "view them in the UI with this diarization run ID"
            "num_speakers_detected": len(set(s["speaker_label"] for s in identified_segments)),
            "processing_time_seconds": 0,
        }
    }
    
    try:
        resp = requests.post(f"{SERVER_URL}/ingestion-runs", json=run_payload)
        resp.raise_for_status()
        run_data = resp.json()
        diar_run_id = run_data["diarization_run_id"]
        print(f"   ✅ Created Run ID: {diar_run_id}")
        
    except Exception as e:
        print(f"   ❌ Failed to create run: {e}")
        if hasattr(e, 'response') and e.response:
             print(e.response.text)
        sys.exit(1)

    # 6b. Save Segments
    # Add confidence (1 - distance) normalization if needed. 
    # Distance is 0.0 (perfect) to >1.0. Confidence usually 0.0-1.0.
    # Simple conversion: max(0, 1 - distance)
    for s in identified_segments:
        dist = s["confidence"]
        s["confidence"] = max(0.0, 1.0 - dist)
    
    segments_payload = {
        "run_id": diar_run_id,
        "segments": identified_segments
    }
    
    try:
        resp = requests.post(f"{SERVER_URL}/diarization-segments", json=segments_payload)
        resp.raise_for_status()
        print(f"   ✅ Saved {len(identified_segments)} segments")
        
    except Exception as e:
        print(f"   ❌ Failed to save segments: {e}")
        exit(1)

    print("\n🎉 Done! Refresh the UI.")

if __name__ == "__main__":
    main()
