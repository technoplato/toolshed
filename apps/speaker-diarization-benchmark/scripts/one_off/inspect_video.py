
import sys
from pathlib import Path
# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingestion.instant_client import InstantClient

VIDEO_ID = "a85ae635-963a-4c8f-9716-146b31e4446a"

def main():
    client = InstantClient()
    try:
        video = client.get_video(VIDEO_ID)
        print(f"ID: {video.get('id')}")
        print(f"Source ID: {video.get('source_id')}")
        print(f"Title: {video.get('title')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
