"""
HOW:
  `uv run verify_data_layer.py`

  [Inputs]
  - None (Uses mock/temporary data if needed, or non-destructive read)
  
  [Outputs]
  - Logs verification steps.

WHO:
  Antigravity
  (Context: Verification)

WHAT:
  Verifies the Python Data Layer implementation.
  1. Instantiates Repository via Factory.
  2. Creates a Video entity.
  3. Creates a TranscriptionRun & Segments.
  4. Saves them.
  5. Reloads and verifies data integrity.
  6. Checks Stable Segment generation (virtual).

WHEN:
  2025-12-05

WHERE:
  apps/speaker-diarization-benchmark/verify_data_layer.py
"""

import sys
from pathlib import Path
import shutil
import time

# Ensure src is in path
sys.path.append(str(Path(__file__).parent))

from src.data.factory import DatabaseFactory
from src.data.models import Video, TranscriptionRun, TranscriptionSegment

def main():
    print("--- Verifying Data Layer ---")
    
    # 1. Setup Test Environment (Avoid messing up real manifest)
    test_manifest = Path("data/clips/test_manifest.json")
    test_embeddings = Path("data/test_embeddings.json")
    
    if test_manifest.exists(): test_manifest.unlink()
    if test_embeddings.exists(): test_embeddings.unlink()
    
    config = {
        "type": "json",
        "json_options": {
            "manifest_path": str(test_manifest),
            "embeddings_path": str(test_embeddings)
        }
    }
    
    print("[1] Instantiating Repository...")
    repo = DatabaseFactory.get_repository(config)
    print("    Success.")
    
    # 2. Create Video
    print("\n[2] Creating Video...")
    vid = Video(
        title="Test Video",
        filepath="data/clips/test.wav",
        duration=35.0,
        url="http://example.com/video"
    )
    vid_id = repo.save_video(vid)
    print(f"    Saved Video ID: {vid_id} (Expected: {vid.id})")
    
    loaded_vid = repo.get_video(vid_id)
    assert loaded_vid.title == "Test Video"
    assert loaded_vid.duration == 35.0
    print("    Verified Video reload.")
    
    # 3. Create Transcription
    print("\n[3] Creating Transcription Run...")
    run = TranscriptionRun(
        video_id=vid_id,
        model="verify-model-v1",
        name="test_run_01",
        segmentation_threshold=0.6,
        context_window=2
    )
    
    segments = [
        TranscriptionSegment(start=0.5, end=2.5, text="Hello world."),
        TranscriptionSegment(start=3.0, end=5.0, text="This is a test."),
        TranscriptionSegment(start=12.0, end=14.0, text="Crossing a stable boundary.")
    ]
    
    repo.save_transcription_run(run, segments)
    print("    Saved Transcription Run.")
    
    # Verify by reloading (via our helper which mimics the legacy structure)
    # The JSON adapter doesn't fully support get_transcription_run by ID yet, 
    # but we can check the file manually or use get_transcriptions_for_video if implemented.
    # Actually, let's just inspect the JSON file content to be sure.
    import json
    with open(test_manifest) as f:
        data = json.load(f)
        entry = data[0]
        assert "test_run_01" in entry['transcriptions']
        saved_segs = entry['transcriptions']['test_run_01']
        assert len(saved_segs) == 3
        assert saved_segs[0]['text'] == "Hello world."
        
        meta = entry['transcription_metadata']['test_run_01']
        assert meta['segmentation_threshold'] == 0.6
    print("    Verified JSON structure.")
    
    # 4. Stable Segments
    print("\n[4] Checking Stable Segments (Virtual)...")
    stable_segs = repo.get_stable_segments(vid_id, 0, 35.0)
    # Duration 35s -> 0-10, 10-20, 20-30, 30-40 (4 segments)
    print(f"    Found {len(stable_segs)} stable segments.")
    for s in stable_segs:
        print(f"    - [{s.start}-{s.end}] Index: {s.index}")
    
    assert len(stable_segs) == 4
    assert stable_segs[0].start == 0.0
    assert stable_segs[3].end == 40.0
    
    print("\n[SUCCESS] Data Layer Verification Complete.")
    
    # Cleanup
    if test_manifest.exists(): test_manifest.unlink()
    if test_embeddings.exists(): test_embeddings.unlink()

if __name__ == "__main__":
    main()
