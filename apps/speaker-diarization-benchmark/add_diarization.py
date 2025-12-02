"""
WHO:   Antigravity, User
       (Context: Creating Ground Truth Data for Speaker Diarization Benchmark)

WHAT:  Applies speaker diarization to existing audio clips in the manifest.
       [Inputs] data/clips/manifest.json, audio files referenced in manifest
       [Outputs] Updates manifest.json with "speaker" field for each segment
       [Side Effects] Downloads pyannote models (requires HF token)
       [How to run] uv run add_diarization.py

WHEN:  2025-11-30
       [Change Log:
        - 2025-11-30: Initial creation
        - 2025-11-30: Added safe_globals fix for PyTorch 2.6+ / pyannote compatibility]

WHERE: apps/speaker-diarization-benchmark/add_diarization.py

WHY:   To establish ground truth for who is speaking when.
       [Design Decisions]
       - Uses `pyannote/speaker-diarization-3.1` pipeline.
       - **Speaker Counting**: By default, the pipeline automatically estimates the number of speakers
         using agglomerative clustering on speaker embeddings. It does not have a hard limit, but
         accuracy depends on the distinctness of voices and audio quality.
       - **Configuration**: Currently uses default hyperparameters. To enforce a specific number of
         speakers (if known), `num_speakers=N` can be passed to the pipeline.
       - **Matching**: Assigns speakers to transcription segments based on maximum temporal overlap.
"""
import json
import logging
import os
import argparse
from pathlib import Path
import torch
import omegaconf
from pyannote.audio import Pipeline
from pyannote.audio.core.task import Specifications, Problem, Resolution

# Configure logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("diarization_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
CLIPS_DIR = DATA_DIR / "clips"
MANIFEST_FILE = CLIPS_DIR / "manifest.json"
DB_FILE = DATA_DIR / "speaker_embeddings.json"
HF_TOKEN = "REDACTED_SECRET"

def get_dominant_speaker(segment_start, segment_end, diarization):
    """Find the speaker with the most overlap for a given time range."""
    overlaps = {}
    segment_duration = segment_end - segment_start
    
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        # Calculate overlap
        start = max(segment_start, turn.start)
        end = min(segment_end, turn.end)
        overlap = max(0, end - start)
        
        if overlap > 0:
            overlaps[speaker] = overlaps.get(speaker, 0) + overlap

    if not overlaps:
        return "UNKNOWN"
        
    # Return speaker with max overlap
    return max(overlaps, key=overlaps.get)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-speakers", type=int, help="Minimum number of speakers")
    parser.add_argument("--max-speakers", type=int, help="Maximum number of speakers")
    parser.add_argument("--clip-id", type=str, help="Process only this clip ID")
    args = parser.parse_args()

    if not MANIFEST_FILE.exists():
        logger.error("Manifest not found.")
        return

    with open(MANIFEST_FILE) as f:
        manifest = json.load(f)
        
    logger.info("Loading pyannote pipeline...")
    try:
        # Use safe_globals to allow loading legacy checkpoints with weights_only=True
        with torch.serialization.safe_globals([
            torch.torch_version.TorchVersion,
            omegaconf.listconfig.ListConfig,
            omegaconf.dictconfig.DictConfig,
            Specifications,
            Problem,
            Resolution,
        ]):
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=HF_TOKEN
            )
        
        # Move to GPU if available
        if torch.backends.mps.is_available():
            pipeline.to(torch.device("mps"))
        elif torch.cuda.is_available():
            pipeline.to(torch.device("cuda"))
            
    except Exception as e:
        logger.error(f"Failed to load pipeline: {e}")
        return

    for entry in manifest:
        if args.clip_id and entry["id"] != args.clip_id:
            continue

        clip_path = Path(entry["clip_path"])
        if not clip_path.exists():
            clip_path = Path(__file__).parent / entry["clip_path"]
            
        if not clip_path.exists():
            logger.warning(f"Clip not found: {entry['clip_path']}")
            continue
            
        logger.info(f"Diarizing {entry['id']}...")
        
        # Prepare options
        options = {}
        if args.min_speakers:
            options["min_speakers"] = args.min_speakers
        if args.max_speakers:
            options["max_speakers"] = args.max_speakers
            
        diarization = pipeline(str(clip_path), **options)
        
        logger.debug(f"Diarization result type: {type(diarization)}")
        logger.debug(f"Attributes: {dir(diarization)}")
        
        # Try to find the annotation
        embeddings = None
        if hasattr(diarization, 'speaker_embeddings'):
            embeddings = diarization.speaker_embeddings
            
        if hasattr(diarization, 'speaker_diarization'):
            diarization = diarization.speaker_diarization
        elif hasattr(diarization, 'annotation'):
            diarization = diarization.annotation

        # --- Speaker Identification & Caching ---
        
        # 1. Cache Embeddings for Enrollment
        if embeddings is not None:
            cache_dir = DATA_DIR / "cache" / "embeddings"
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Map index to SPEAKER_XX
            cache_data = {}
            for i in range(len(embeddings)):
                label = f"SPEAKER_{i:02d}"
                cache_data[label] = embeddings[i].tolist()
            
            with open(cache_dir / f"{entry['id']}.json", 'w') as f:
                json.dump(cache_data, f)
                
        # 2. Identify Speakers
        speaker_map = {}
        if embeddings is not None and DB_FILE.exists():
            try:
                with open(DB_FILE) as f:
                    db = json.load(f)
                
                from scipy.spatial.distance import cdist
                import numpy as np
                
                for i in range(len(embeddings)):
                    label = f"SPEAKER_{i:02d}"
                    vec = embeddings[i].reshape(1, -1)
                    
                    best_name = None
                    best_dist = 0.5 # Threshold
                    
                    for name, stored_vectors in db.items():
                        # Compare with mean of stored vectors (Centroid)
                        if not stored_vectors: continue
                        centroid = np.mean(stored_vectors, axis=0).reshape(1, -1)
                        dist = cdist(vec, centroid, metric='cosine')[0][0]
                        
                        if dist < best_dist:
                            best_dist = dist
                            best_name = name
                    
                    if best_name:
                        speaker_map[label] = best_name
                        logger.info(f"Identified {label} as {best_name} (dist: {best_dist:.4f})")
            except Exception as e:
                logger.error(f"Identification failed: {e}")

        # Apply mapping to diarization object
        if speaker_map:
            from pyannote.core import Annotation
            new_diarization = Annotation()
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                new_label = speaker_map.get(speaker, speaker)
                new_diarization[turn] = new_label
            diarization = new_diarization

        logger.debug(f"Diarization result for {entry['id']}:")
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            logger.debug(f"  Speaker {speaker}: {turn.start:.2f}s - {turn.end:.2f}s")
        
        logger.debug(f"Diarization result for {entry['id']}:")
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            logger.debug(f"  Speaker {speaker}: {turn.start:.2f}s - {turn.end:.2f}s")
        
        # Process each model's transcription
        if "transcriptions" in entry:
            for model_name, segments in entry["transcriptions"].items():
                logger.info(f"  Aligning speakers for {model_name}...")
                for seg in segments:
                    speaker = get_dominant_speaker(seg["start"], seg["end"], diarization)
                    logger.debug(f"    Segment {seg['start']:.2f}-{seg['end']:.2f}: {speaker}")
                    seg["speaker"] = speaker
                    
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)
        
    logger.info(f"Done! Updated manifest saved to {MANIFEST_FILE}")

if __name__ == "__main__":
    main()
