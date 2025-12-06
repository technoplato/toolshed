import json
from pathlib import Path

manifest_path = Path("data/clips/manifest.json")
video_path = "data/downloads/jAlKYYr1bpY.wav"
video_id = "jAlKYYr1bpY.wav"

if not manifest_path.exists():
    print(f"Manifest not found at {manifest_path}")
    exit(1)

with open(manifest_path, 'r') as f:
    data = json.load(f)

# Check if exists
if any(item['id'] == video_id for item in data):
    print(f"Entry {video_id} already exists.")
else:
    new_entry = {
        "id": video_id,
        "clip_path": video_path,
        "transcriptions": {}
    }
    data.append(new_entry)
    with open(manifest_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Added {video_id} to manifest.")
