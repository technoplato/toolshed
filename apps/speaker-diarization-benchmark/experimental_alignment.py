import json
import logging
import torch
from pathlib import Path
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import os

HF_TOKEN = os.getenv("HF_TOKEN")
DATA_DIR = Path("data")
CLIPS_DIR = DATA_DIR / "clips"
MANIFEST_FILE = CLIPS_DIR / "manifest.json"

def align_words_with_diarization(words, diarization):
    """
    Aligns words with diarization segments.
    Returns a list of segments: {start, end, text, speaker}
    """
    aligned_segments = []
    current_segment = None
    
    for word in words:
        # Find speaker at word midpoint
        midpoint = word.start + (word.end - word.start) / 2
        speaker = "UNKNOWN"
        
        # Check diarization
        # pyannote Annotation.itertracks(yield_label=True)
        # We can optimize this search, but for a 60s clip, linear scan is fine.
        for turn, _, label in diarization.itertracks(yield_label=True):
            if turn.start <= midpoint <= turn.end:
                speaker = label
                break
        
        # If speaker changed or no current segment, start new one
        if current_segment is None or current_segment["speaker"] != speaker:
            if current_segment:
                aligned_segments.append(current_segment)
            
            current_segment = {
                "start": word.start,
                "end": word.end,
                "text": word.word.strip(),
                "speaker": speaker
            }
        else:
            # Append to current
            current_segment["end"] = word.end
            current_segment["text"] += " " + word.word.strip()
            
    if current_segment:
        aligned_segments.append(current_segment)
        
    return aligned_segments

def main():
    clip_id = "clip_local_mssp-old-test-ep-1_0_60.wav"
    clip_path = CLIPS_DIR / clip_id
    
    if not clip_path.exists():
        logger.error(f"Clip not found: {clip_path}")
        return

    # 1. Transcribe with faster-whisper (Word Timestamps)
    logger.info("Transcribing with faster-whisper (small)...")
    # Run on GPU if available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # Mac MPS support in faster-whisper is ... tricky. It uses CTranslate2. 
    # CTranslate2 supports CoreML or CPU on Mac. Let's stick to CPU for safety/simplicity unless we know better.
    # actually, device="auto" is best.
    
    try:
        model = WhisperModel("small", device="cpu", compute_type="int8")
    except Exception as e:
        logger.warning(f"Failed to load int8 model: {e}. Trying float32.")
        model = WhisperModel("small", device="cpu", compute_type="float32")

    segments, info = model.transcribe(str(clip_path), word_timestamps=True)
    
    all_words = []
    for segment in segments:
        if segment.words:
            all_words.extend(segment.words)
            
    logger.info(f"Transcribed {len(all_words)} words.")
    
    # 2. Diarize
    logger.info("Diarizing...")
    import omegaconf
    from pyannote.audio.core.task import Specifications, Problem, Resolution
    
    with torch.serialization.safe_globals([
        torch.torch_version.TorchVersion,
        omegaconf.listconfig.ListConfig,
        omegaconf.dictconfig.DictConfig,
        Specifications,
        Problem,
        Resolution,
    ]):
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", token=HF_TOKEN)
    
    # Force 2 speakers for this clip (Shane + Woman)
    diarization = pipeline(str(clip_path), num_speakers=2)
    
    if hasattr(diarization, 'speaker_diarization'):
        diarization = diarization.speaker_diarization
    elif hasattr(diarization, 'annotation'):
        diarization = diarization.annotation
    
    # 3. Align
    logger.info("Aligning...")
    new_segments = align_words_with_diarization(all_words, diarization)
    
    # 4. Print Results
    logger.info("Results:")
    for seg in new_segments:
        logger.info(f"[{seg['start']:.2f} - {seg['end']:.2f}] {seg['speaker']}: {seg['text']}")
        
    # 5. Update Manifest (Optional, let's just verify first)
    # But user said "Let's try it", implying we should apply it.
    # Let's save to a new key in manifest "faster_whisper_aligned"
    
    with open(MANIFEST_FILE) as f:
        manifest = json.load(f)
        
    entry = next((e for e in manifest if e["id"] == clip_id), None)
    if entry:
        entry["transcriptions"]["faster_whisper_aligned"] = new_segments
        # Also update the main one for the UI to see
        entry["transcriptions"]["pywhispercpp.small"] = new_segments 
        
        with open(MANIFEST_FILE, "w") as f:
            json.dump(manifest, f, indent=2)
            
        logger.info("Manifest updated!")

if __name__ == "__main__":
    main()
