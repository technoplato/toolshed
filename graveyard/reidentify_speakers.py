import json
import logging
import numpy as np
from pathlib import Path
from scipy.spatial.distance import cdist

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
CLIPS_DIR = DATA_DIR / "clips"
MANIFEST_FILE = CLIPS_DIR / "manifest.json"
DB_FILE = DATA_DIR / "speaker_embeddings.json"
CACHE_DIR = DATA_DIR / "cache" / "embeddings"

def identify_speaker(embedding, db, threshold=0.5):
    vec = np.array(embedding).reshape(1, -1)
    best_name = None
    best_dist = threshold

    for name, stored_vectors in db.items():
        if not stored_vectors: continue
        # Compare with centroid of stored vectors
        centroid = np.mean(stored_vectors, axis=0).reshape(1, -1)
        dist = cdist(vec, centroid, metric='cosine')[0][0]
        
        if dist < best_dist:
            best_dist = dist
            best_name = name
            
    return best_name, best_dist

def main():
    if not MANIFEST_FILE.exists() or not DB_FILE.exists():
        logger.error("Manifest or DB not found.")
        return

    with open(MANIFEST_FILE) as f:
        manifest = json.load(f)
        
    with open(DB_FILE) as f:
        db = json.load(f)
        
    logger.info(f"Loaded {len(db)} speakers from database.")
    
    updates_count = 0
    
    for entry in manifest:
        clip_id = entry['id']
        cache_file = CACHE_DIR / f"{clip_id}.json"
        
        if not cache_file.exists():
            logger.debug(f"No embeddings cache for {clip_id}")
            continue
            
        with open(cache_file) as f:
            embeddings_map = json.load(f)
            
        # Create a local map for this clip: SPEAKER_XX -> Real Name
        local_map = {}
        for label, embedding in embeddings_map.items():
            name, dist = identify_speaker(embedding, db)
            if name:
                local_map[label] = name
                logger.info(f"[{clip_id}] Identified {label} as {name} (dist: {dist:.4f})")
        
        if not local_map:
            continue
            
        # Apply to transcriptions
        if "transcriptions" in entry:
            for model_name, segments in entry["transcriptions"].items():
                for seg in segments:
                    current_speaker = seg.get("speaker")
                    # Only update if it's currently a generic label or we have a better match?
                    # For now, let's assume if we found a match in DB, it trumps the generic label.
                    # But we must be careful not to overwrite a manually corrected label if we can't distinguish.
                    # However, the user asked for syncing.
                    # If the current label is "SPEAKER_XX", update it.
                    # If it's already a name, maybe leave it? Or update if it matches the *ID*?
                    # The segment doesn't store the ID, just the display name.
                    # But we know the segment was originally "SPEAKER_XX" based on the cache key?
                    # Actually, the cache key "SPEAKER_00" corresponds to the *diarization* label.
                    # If the manifest has "SPEAKER_00", we replace it.
                    
                    if current_speaker in local_map:
                        seg["speaker"] = local_map[current_speaker]
                        updates_count += 1
                    elif current_speaker in embeddings_map and current_speaker not in local_map:
                        # It's a generic speaker that we FAILED to identify this time.
                        # Should we revert it? No, keep existing.
                        pass

    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)
        
    logger.info(f"Done! Updated {updates_count} segments.")

if __name__ == "__main__":
    main()
