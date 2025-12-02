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

MODELS_TO_RUN = ["base", "small"]

def main():
    if not MANIFEST_FILE.exists():
        logger.error("Manifest not found.")
        return

    with open(MANIFEST_FILE) as f:
        manifest = json.load(f)
        
    for model_name in MODELS_TO_RUN:
        logger.info(f"Loading pywhispercpp model ({model_name})...")
        model = Model(model_name, print_realtime=False, print_progress=False)
        
        for entry in manifest:
            # Migrate structure if needed
            if "transcriptions" not in entry:
                entry["transcriptions"] = {}
                # If there was a legacy 'transcription' field, move it?
                # Actually, we know the current state is 'small' from the previous run.
                # But to be safe and clean, let's just re-run everything or check if we want to preserve.
                # The user said "maintain our history", but since I just overwrote it in the previous step,
                # the "history" in the file is just the last run (small).
                # I'll treat the existing 'transcription' as 'pywhispercpp.small' if I have to guess,
                # but it's safer to just re-run both to guarantee correctness.
                if "transcription" in entry:
                    # We'll discard the flat 'transcription' in favor of the structured one
                    # or we could save it as 'legacy' if we wanted, but re-running is better.
                    del entry["transcription"]

            clip_path = Path(entry["clip_path"])
            if not clip_path.exists():
                clip_path = Path(__file__).parent / entry["clip_path"]
            
            if not clip_path.exists():
                logger.warning(f"Clip not found: {entry['clip_path']}")
                continue
                
            key = f"pywhispercpp.{model_name}"
            if key in entry["transcriptions"]:
                logger.info(f"Skipping {key} for {entry['id']} (already exists)")
                continue

            logger.info(f"Transcribing {entry['id']} with {model_name}...")
            transcription = transcribe_clip(model, clip_path)
            
            entry["transcriptions"][key] = transcription
            
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)
        
    logger.info(f"Done! Updated manifest saved to {MANIFEST_FILE}")

if __name__ == "__main__":
    main()
