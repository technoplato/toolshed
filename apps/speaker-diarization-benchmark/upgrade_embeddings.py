"""
ONE-OFF SCRIPT: Upgrade Speaker Embeddings to 512-dim

This script upgrades the existing 256-dimensional speaker embeddings to 512-dimensional embeddings
(compatible with the current pyannote/embedding model) by re-processing segments that have already
been labeled in manifest.json.

It will OVERWRITE data/speaker_embeddings.json with the new high-dimensional vectors.
"""

import json
import logging
from pathlib import Path
import torch
import numpy as np
from pyannote.audio import Model, Inference
from pyannote.audio.core.io import Audio
from pyannote.core import Segment

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
CLIPS_DIR = DATA_DIR / "clips"
MANIFEST_FILE = CLIPS_DIR / "manifest.json"
DB_FILE = DATA_DIR / "speaker_embeddings.json"
HF_TOKEN = "REDACTED_SECRET"

def main():
    if not MANIFEST_FILE.exists():
        logger.error("Manifest not found.")
        return

    # Load Manifest
    with open(MANIFEST_FILE) as f:
        manifest = json.load(f)
    logger.info(f"Loaded manifest with {len(manifest)} clips.")

    # Initialize Model
    logger.info("Loading embedding model (pyannote/embedding)...")
    try:
        # Using pyannote/embedding (access granted)
        import omegaconf
        import pytorch_lightning
        import typing
        import collections
        from pyannote.audio.core.task import Specifications, Problem, Resolution
        import pyannote.audio.core.model
        
        with torch.serialization.safe_globals([
            torch.torch_version.TorchVersion,
            omegaconf.listconfig.ListConfig,
            omegaconf.dictconfig.DictConfig,
            Specifications,
            Problem,
            Resolution,
            pyannote.audio.core.model.Introspection,
            pytorch_lightning.callbacks.early_stopping.EarlyStopping,
            pytorch_lightning.callbacks.model_checkpoint.ModelCheckpoint,
            omegaconf.base.ContainerMetadata,
            omegaconf.base.Metadata,
            omegaconf.nodes.AnyNode,
            omegaconf.nodes.StringNode,
            omegaconf.nodes.IntegerNode,
            omegaconf.nodes.FloatNode,
            omegaconf.nodes.BooleanNode,
            typing.Any,
            list,
            dict,
            collections.defaultdict,
            int,
            float,
            str,
            tuple,
            set,
        ]):
            model = Model.from_pretrained("pyannote/embedding", use_auth_token=HF_TOKEN)
        
        inference = Inference(model, window="whole")
        model.to(torch.device("cpu")) # Force CPU
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return

    audio_io = Audio(sample_rate=16000, mono="downmix")
    
    # New Database
    new_db = {}
    
    total_segments = 0
    processed_segments = 0
    
    for clip in manifest:
        clip_id = clip['id']
        clip_path = Path(clip['clip_path'])
        
        if not clip_path.exists():
            # Try relative path
            clip_path = Path(__file__).parent / clip['clip_path']
            if not clip_path.exists():
                logger.warning(f"Clip not found: {clip_path}. Skipping.")
                continue

        if 'transcriptions' not in clip or 'mlx_whisper_turbo_seg_level' not in clip['transcriptions']:
            continue
            
        segments = clip['transcriptions']['mlx_whisper_turbo_seg_level']
        
        for seg in segments:
            speaker = seg.get('speaker')
            
            # Filter for REAL names
            if not speaker: continue
            if speaker.startswith("SEG_SPK_") or speaker.startswith("SPEAKER_") or speaker.startswith("UNKNOWN_"):
                continue
                
            total_segments += 1
            
            # Extract Embedding
            try:
                waveform, sr = audio_io.crop(clip_path, Segment(seg['start'], seg['end']))
                emb = inference({"waveform": waveform, "sample_rate": sr})
                
                if speaker not in new_db:
                    new_db[speaker] = []
                
                # Convert to list for JSON serialization
                new_db[speaker].append(emb.tolist())
                processed_segments += 1
                
                if processed_segments % 10 == 0:
                    logger.info(f"Processed {processed_segments} segments...")
                    
            except Exception as e:
                logger.error(f"Error processing segment for {speaker} in {clip_id}: {e}")

    logger.info(f"Finished processing. Total segments: {total_segments}. Successfully embedded: {processed_segments}.")
    
    if processed_segments > 0:
        logger.info(f"Saving new database to {DB_FILE}...")
        with open(DB_FILE, 'w') as f:
            json.dump(new_db, f, indent=2)
        logger.info("Database upgraded successfully!")
        
        # Verify dimension
        first_key = next(iter(new_db))
        dim = len(new_db[first_key][0])
        logger.info(f"New embedding dimension: {dim}")
    else:
        logger.warning("No segments found to process. Database NOT updated.")

if __name__ == "__main__":
    main()
