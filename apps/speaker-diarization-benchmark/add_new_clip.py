import json
import os

MANIFEST_PATH = 'data/clips/manifest.json'
CLIP_PATH = '/Users/laptop/Development/Personal/psuedonymous/toolshed/apps/speaker-diarization-benchmark/data/clips/clip_local_mssp-old-test-ep-1_240_180.mp3'

def main():
    with open(MANIFEST_PATH, 'r') as f:
        data = json.load(f)

    new_entry = {
        "id": os.path.basename(CLIP_PATH), 
        "clip_path": CLIP_PATH,
        "title": "MSSP Test Ep 1 (240s-420s)",
        "duration": 180.0,
        "start_time": 240.0,
        "original_url": "local",
        "transcriptions": {}
    }
    
    # Check if already exists
    if not any(c['clip_path'] == CLIP_PATH for c in data):
        data.append(new_entry)
        with open(MANIFEST_PATH, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Added {CLIP_PATH} to manifest.")
    else:
        print("Clip already in manifest.")

if __name__ == "__main__":
    main()
