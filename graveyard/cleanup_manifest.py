import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MANIFEST_PATH = Path("data/clips/manifest.json")
KEYS_TO_REMOVE = ["pywhispercpp.small", "faster_whisper_aligned", "pywhispercpp.base"]

def main():
    if not MANIFEST_PATH.exists():
        logger.error("Manifest not found")
        return

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    count = 0
    for clip in manifest:
        if 'transcriptions' in clip:
            for key in KEYS_TO_REMOVE:
                if key in clip['transcriptions']:
                    del clip['transcriptions'][key]
                    count += 1
    
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)
        
    logger.info(f"Removed {count} transcription entries from manifest.")

if __name__ == "__main__":
    main()
