"""
WHO:   Cursor Agent, User
       (Context: Created to benchmark and reproduce the "good" transcription/diarization pipeline)

WHAT:  Benchmarks the word-level embedding and segmentation pipeline.
       [Inputs] --clip-path (path to wav file)
       [Outputs] JSON with segments, speakers, and performance metrics.
       [Side Effects] Loads models into memory, prints logs.
       [How to run]
       python3 apps/speaker-diarization-benchmark/benchmark_word_level.py --clip-path data/clips/clip_youtube_jAlKYYr1bpY_0_60.wav

WHEN:  2025-12-02
       2025-12-02
       [Change Log:
        - 2025-12-02: Initial creation with word-level embedding and greedy grouping]

WHERE: apps/speaker-diarization-benchmark/benchmark_word_level.py
       Not deployed yet.

WHY:   To verify the hypothesis that word-level embedding + grouping yields better diarization than segment-level embedding.
"""

import argparse
import json
import time
import logging
import sys
import psutil
import os
import numpy as np
import torch
from pathlib import Path
from scipy.spatial.distance import cdist

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
HF_TOKEN = os.getenv("HF_TOKEN") # TODO: Move to env var
DATA_DIR = Path("data")
SPEAKER_DB = DATA_DIR / "speaker_embeddings.json"

# Import transcribe from local module
try:
    from transcribe import transcribe
except ImportError:
    # Handle case where script is run from root or elsewhere
    sys.path.append(str(Path(__file__).parent))
    from transcribe import transcribe

def get_memory_usage():
    """Returns current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def load_embedding_model():
    """Loads the pyannote embedding model"""
    logger.info("Loading embedding model...")
    from pyannote.audio import Model, Inference
    
    # Use CPU to avoid MPS issues if any, or stick to default
    # The reference script forced CPU for MPS errors
    device = torch.device("cpu")
    
    model = Model.from_pretrained("pyannote/embedding", use_auth_token=HF_TOKEN)
    model.to(device)
    inference = Inference(model, window="whole")
    
    return inference, device

def load_known_speakers():
    """Loads known speaker embeddings"""
    if not SPEAKER_DB.exists():
        logger.warning(f"Speaker DB not found at {SPEAKER_DB}")
        return {}
    
    try:
        with open(SPEAKER_DB) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load speaker DB: {e}")
        return {}

def identify_speaker(embedding, known_speakers, threshold=0.5):
    """Identifies speaker from embedding"""
    if not known_speakers:
        return "UNKNOWN", 1.0
        
    best_name = "UNKNOWN"
    best_dist = threshold
    
    # embedding shape: (dimension,)
    # stored_vectors shape: (n_samples, dimension)
    
    target = embedding.reshape(1, -1)
    
    for name, stored_vectors in known_speakers.items():
        if not stored_vectors: continue
        
        # Calculate centroid of stored vectors
        # stored_vectors is a list of lists
        stored_matrix = np.array(stored_vectors)
        centroid = np.mean(stored_matrix, axis=0).reshape(1, -1)
        
        try:
            dist = cdist(target, centroid, metric='cosine')[0][0]
            if dist < best_dist:
                best_dist = dist
                best_name = name
        except ValueError as e:
            continue
            
    return best_name, best_dist

def main():
    parser = argparse.ArgumentParser(description="Benchmark word-level diarization")
    parser.add_argument("--clip-path", type=str, required=True, help="Path to audio file")
    parser.add_argument("--threshold", type=float, default=0.5, help="Clustering threshold")
    args = parser.parse_args()
    
    clip_path = Path(args.clip_path)
    if not clip_path.exists():
        logger.error(f"File not found: {clip_path}")
        sys.exit(1)
        
    metrics = {
        "start_time": time.time(),
        "steps": {}
    }
    
    # 1. Transcription
    logger.info("Step 1: Transcription")
    t0 = time.time()
    try:
        transcription_result = transcribe(str(clip_path))
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        sys.exit(1)
    
    metrics["steps"]["transcription"] = time.time() - t0
    logger.info(f"Transcription took {metrics['steps']['transcription']:.2f}s")
    
    # Flatten words
    all_words = []
    for seg in transcription_result.segments:
        all_words.extend(seg.words)
        
    logger.info(f"Found {len(all_words)} words.")
    
    # 2. Embedding
    logger.info("Step 2: Embedding Generation")
    t0 = time.time()
    
    inference, device = load_embedding_model()
    known_speakers = load_known_speakers()
    
    from pyannote.audio.core.io import Audio
    from pyannote.core import Segment as PyannoteSegment
    
    audio_io = Audio(sample_rate=16000, mono="downmix")
    
    word_embeddings = []
    valid_words = []
    
    for i, word in enumerate(all_words):
        duration = word.end - word.start
        if duration < 0.05: # Skip very short words
            continue
            
        try:
            waveform, sr = audio_io.crop(clip_path, PyannoteSegment(word.start, word.end))
            # Force CPU
            # inference expects dict
            emb = inference({"waveform": waveform, "sample_rate": sr})
            
            if not np.isnan(emb).any():
                word_embeddings.append(emb)
                valid_words.append(word)
        except Exception as e:
            logger.debug(f"Failed to embed word {word.word}: {e}")
            
    metrics["steps"]["embedding"] = time.time() - t0
    logger.info(f"Generated {len(word_embeddings)} embeddings in {metrics['steps']['embedding']:.2f}s")
    
    # 3. Grouping (Segmentation)
    logger.info("Step 3: Grouping/Segmentation")
    t0 = time.time()
    
    segments = []
    if not valid_words:
        logger.warning("No valid words to group.")
    else:
        current_segment_words = [valid_words[0]]
        current_segment_embs = [word_embeddings[0]]
        
        for i in range(1, len(valid_words)):
            word = valid_words[i]
            emb = word_embeddings[i]
            
            # Calculate centroid of current segment
            centroid = np.mean(current_segment_embs, axis=0)
            
            # Distance to current centroid
            dist = cdist(emb.reshape(1, -1), centroid.reshape(1, -1), metric='cosine')[0][0]
            
            # Check time continuity (gap > 1.0s implies new segment)
            time_gap = word.start - current_segment_words[-1].end
            
            if dist > args.threshold or time_gap > 1.0:
                # Finalize current segment
                segments.append({
                    "words": current_segment_words,
                    "embeddings": current_segment_embs
                })
                # Start new
                current_segment_words = [word]
                current_segment_embs = [emb]
            else:
                current_segment_words.append(word)
                current_segment_embs.append(emb)
        
        # Add last segment
        if current_segment_words:
            segments.append({
                "words": current_segment_words,
                "embeddings": current_segment_embs
            })
            
    metrics["steps"]["grouping"] = time.time() - t0
    logger.info(f"Created {len(segments)} segments in {metrics['steps']['grouping']:.2f}s")
    
    # 4. Identification
    logger.info("Step 4: Identification")
    t0 = time.time()
    
    final_segments = []
    for seg in segments:
        centroid = np.mean(seg["embeddings"], axis=0)
        speaker, dist = identify_speaker(centroid, known_speakers)
        
        start_time = seg["words"][0].start
        end_time = seg["words"][-1].end
        text = " ".join([w.word for w in seg["words"]])
        
        final_segments.append({
            "start": start_time,
            "end": end_time,
            "text": text,
            "speaker": speaker,
            "confidence": 1 - dist
        })
        
    metrics["steps"]["identification"] = time.time() - t0
    metrics["total_time"] = time.time() - metrics["start_time"]
    metrics["final_memory_mb"] = get_memory_usage()
    
    # Output results
    output = {
        "metrics": metrics,
        "segments": final_segments
    }
    
    print(json.dumps(output, indent=2, default=str))
    
    # Audio processing speed
    audio_duration = final_segments[-1]["end"] if final_segments else 0
    if audio_duration > 0:
        speed_factor = metrics["total_time"] / audio_duration
        logger.info(f"Processing factor: {speed_factor:.2f}x real-time (Lower is better)")
        logger.info(f"Time for 1 hour of audio: {speed_factor * 60:.2f} minutes")

if __name__ == "__main__":
    main()


