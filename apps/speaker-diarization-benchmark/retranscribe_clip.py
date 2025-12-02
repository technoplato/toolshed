import json
import logging
from pathlib import Path
from pywhispercpp.model import Model
from prepare_ground_truth import transcribe_clip

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CLIPS_DIR = Path("data/clips")
MANIFEST_FILE = CLIPS_DIR / "manifest.json"

def main():
    if not MANIFEST_FILE.exists():
        logger.error("Manifest not found.")
        return

    with open(MANIFEST_FILE) as f:
        manifest = json.load(f)
        
    logger.info("Loading pywhispercpp model (small)...")
    model = Model('small', print_realtime=False, print_progress=False)
    
    for entry in manifest:
        clip_path = Path(entry["clip_path"])
        if not clip_path.exists():
            # Try relative to script dir if path is relative
            clip_path = Path(__file__).parent / entry["clip_path"]
            
        if not clip_path.exists():
            logger.warning(f"Clip not found: {entry['clip_path']}")
            continue
            
        logger.info(f"Retranscribing {entry['id']}...")
        transcription = transcribe_clip(model, clip_path)
        
        entry["transcription"] = transcription
        logger.info("Updated transcription.")
        
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)
        
    logger.info(f"Done! Updated manifest saved to {MANIFEST_FILE}")
    logger.info(f"New transcription sample: {manifest[0]['transcription']}")

if __name__ == "__main__":
    main()
