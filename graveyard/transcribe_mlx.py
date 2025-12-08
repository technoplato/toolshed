import json
import sys
from transcribe import transcribe

MANIFEST_PATH = 'data/clips/manifest.json'

def main():
    if len(sys.argv) < 2:
        print("Usage: python transcribe_mlx.py <clip_path>")
        sys.exit(1)
        
    clip_path = sys.argv[1]
    
    # Use the standardized transcription function
    try:
        result = transcribe(clip_path)
    except Exception as e:
        print(f"Transcription failed: {e}")
        sys.exit(1)
    
    # Convert Pydantic models to dicts for JSON serialization
    segments = [seg.model_dump() for seg in result.segments]
        
    # Update manifest
    with open(MANIFEST_PATH, 'r') as f:
        data = json.load(f)
        
    found = False
    from pathlib import Path
    clip_path_abs = str(Path(clip_path).resolve())
    clip_id_target = Path(clip_path).name

    for clip in data:
        # Check absolute path, relative path, or ID
        current_abs = str(Path(clip['clip_path']).resolve()) if 'clip_path' in clip else ""
        
        # Debug matching
        # print(f"Checking {clip['id']} | Abs: {current_abs} vs Target: {clip_path_abs}")
        
        if current_abs == clip_path_abs or clip['id'] == clip_id_target:
            print(f"Match found! Updating {clip['id']}")
            if 'transcriptions' not in clip:
                clip['transcriptions'] = {}
            clip['transcriptions']['mlx_whisper_turbo'] = segments
            found = True
            break
            
    if found:
        with open(MANIFEST_PATH, 'w') as f:
            json.dump(data, f, indent=4)
        print("Transcription saved to manifest.")
    else:
        print(f"Clip not found in manifest! Target ID: {clip_id_target}, Target Path: {clip_path_abs}")
        print("Available IDs:", [c['id'] for c in data])

if __name__ == "__main__":
    main()
