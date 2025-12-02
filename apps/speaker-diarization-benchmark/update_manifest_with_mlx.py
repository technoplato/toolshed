import json
import mlx_whisper
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MANIFEST_PATH = Path("data/clips/manifest.json")
CLIP_ID = "clip_youtube_jAlKYYr1bpY_0_60.wav"
CLIP_PATH = Path("data/clips") / CLIP_ID
MODEL_NAME = "mlx-community/whisper-large-v3-turbo"

def main():
    if not MANIFEST_PATH.exists():
        logger.error("Manifest not found")
        return

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    # Find clip
    clip_entry = next((c for c in manifest if c['id'] == CLIP_ID), None)
    if not clip_entry:
        logger.error(f"Clip {CLIP_ID} not found in manifest")
        return

    logger.info(f"Transcribing {CLIP_ID} with {MODEL_NAME}...")
    
    # Transcribe
    result = mlx_whisper.transcribe(str(CLIP_PATH), path_or_hf_repo=MODEL_NAME, word_timestamps=True)
    
    # Format segments
    new_segments = []
    for seg in result['segments']:
        new_segments.append({
            "start": seg['start'],
            "end": seg['end'],
            "text": seg['text'].strip(),
            "speaker": "Unknown" # No diarization yet
        })

    # Update manifest
    if 'transcriptions' not in clip_entry:
        clip_entry['transcriptions'] = {}
    
    clip_entry['transcriptions']['mlx_whisper_turbo'] = new_segments
    
    # Save
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Updated manifest with {len(new_segments)} segments from MLX Turbo.")

if __name__ == "__main__":
    main()
