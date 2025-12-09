
import json
from pathlib import Path

# Path determined from analyzing audio_ingestion.py and cache.py
CACHE_FILE = Path("data/cache/transcription/jAlKYYr1bpY__mlx-whisper__whisper-large-v3-turbo.json")

def main():
    if not CACHE_FILE.exists():
        print(f"❌ Cache file not found: {CACHE_FILE}")
        return

    print(f"✅ Reading cache file: {CACHE_FILE}\n")
    
    with open(CACHE_FILE, "r") as f:
        data = json.load(f)
    
    result = data.get("result", {})
    segments = result.get("segments", [])
    
    print(f"Found {len(segments)} segments.\n")
    print("idx | start - end | text")
    print("-" * 60)
    
    for i, seg in enumerate(segments):
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        text = seg.get("text", "").strip()
        print(f"{i:3d} | {start:6.2f} - {end:6.2f} | {text}")

if __name__ == "__main__":
    main()
