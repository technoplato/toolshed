import json
import logging
import subprocess
import numpy as np
from pathlib import Path
from scipy.spatial.distance import cdist
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
import torch
import omegaconf
from pyannote.audio.core.task import Specifications, Problem, Resolution

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
CLIPS_DIR = DATA_DIR / "clips"
DOWNLOADS_DIR = DATA_DIR / "downloads"
SOURCE_VIDEOS_DIR = DOWNLOADS_DIR / "source-videos"
MANIFEST_FILE = CLIPS_DIR / "manifest.json"
DB_FILE = DATA_DIR / "speaker_embeddings.json"
HF_TOKEN = "REDACTED_SECRET"

def identify_speaker(embedding, db, threshold=0.5):
    vec = np.array(embedding).reshape(1, -1)
    best_name = None
    best_dist = threshold

    for name, stored_vectors in db.items():
        if not stored_vectors: continue
        centroid = np.mean(stored_vectors, axis=0).reshape(1, -1)
        dist = cdist(vec, centroid, metric='cosine')[0][0]
        
        if dist < best_dist:
            best_dist = dist
            best_name = name
            
    return best_name, best_dist

def align_words_with_diarization(words, diarization, speaker_map):
    aligned_segments = []
    current_segment = None
    
    for word in words:
        midpoint = word.start + (word.end - word.start) / 2
        speaker_label = "UNKNOWN"
        
        for turn, _, label in diarization.itertracks(yield_label=True):
            if turn.start <= midpoint <= turn.end:
                speaker_label = label
                break
        
        # Map to real name if available
        real_name = speaker_map.get(speaker_label, speaker_label)
        
        if current_segment is None or current_segment["speaker"] != real_name:
            if current_segment:
                aligned_segments.append(current_segment)
            
            current_segment = {
                "start": word.start,
                "end": word.end,
                "text": word.word.strip(),
                "speaker": real_name
            }
        else:
            current_segment["end"] = word.end
            current_segment["text"] += " " + word.word.strip()
            
    if current_segment:
        aligned_segments.append(current_segment)
        
    return aligned_segments

def extract_clip(source_path, clip_id, start_time, duration):
    clip_path = CLIPS_DIR / f"{clip_id}.wav"
    if clip_path.exists():
        return clip_path
        
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-t", str(duration),
        "-i", str(source_path),
        "-ac", "1", "-ar", "16000",
        str(clip_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return clip_path

def main():
    # Define Clips
    # Ep 569: 3 clips (60-120, 120-180, 180-240)
    # MSSP Ep 1: 3 clips (60-120, 120-180, 180-240)
    
    clips_to_process = []
    
    # Ep 569
    source_569 = DOWNLOADS_DIR / "jAlKYYr1bpY.wav"
    for start in [60, 120, 180]:
        clips_to_process.append({
            "source": source_569,
            "title": "Ep 569 - A Derosa Garden (feat. Joe Derosa)",
            "original_url": "https://www.youtube.com/watch?v=jAlKYYr1bpY",
            "start": start,
            "duration": 60,
            "id_prefix": "clip_youtube_jAlKYYr1bpY",
            "num_speakers": 3
        })
        
    # MSSP Ep 1
    source_mssp = SOURCE_VIDEOS_DIR / "mssp-old-test-ep-1.mp3"
    # Need to convert to wav first? extract_clip handles it via ffmpeg input
    # But wait, source path in process_new_benchmark_videos used a converted wav.
    # Let's check if converted wav exists.
    converted_mssp = DOWNLOADS_DIR / "mssp-old-test-ep-1.wav"
    if converted_mssp.exists():
        source_mssp = converted_mssp
        
    for start in [60, 120, 180]:
        clips_to_process.append({
            "source": source_mssp,
            "title": "Matt and Shane's Secret Podcast Ep. 1",
            "original_url": "",
            "start": start,
            "duration": 60,
            "id_prefix": "clip_local_mssp-old-test-ep-1",
            "num_speakers": 2
        })

    # Load Models
    logger.info("Loading faster-whisper...")
    try:
        whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
    except:
        whisper_model = WhisperModel("small", device="cpu", compute_type="float32")
        
    logger.info("Loading pyannote pipeline...")
    with torch.serialization.safe_globals([
        torch.torch_version.TorchVersion,
        omegaconf.listconfig.ListConfig,
        omegaconf.dictconfig.DictConfig,
        Specifications,
        Problem,
        Resolution,
    ]):
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", token=HF_TOKEN)

    # Load Speaker DB
    db = {}
    if DB_FILE.exists():
        with open(DB_FILE) as f:
            db = json.load(f)
            
    # Load Manifest
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE) as f:
            manifest = json.load(f)
    else:
        manifest = []

    for item in clips_to_process:
        clip_id = f"{item['id_prefix']}_{item['start']}_{item['duration']}" # e.g. ..._60_60 ?? No, duration is length.
        # Format: id_start_end usually? Or id_start_duration?
        # Previous format: clip_youtube_ID_START_DURATION.wav
        # Wait, previous was clip_youtube_jAlKYYr1bpY_0_60.wav (0 to 60)
        # So next is clip_youtube_jAlKYYr1bpY_60_60.wav? Or 60_120?
        # Let's stick to start_duration for consistency with previous script.
        # Actually, let's check manifest for previous entry.
        # "id": "clip_youtube_jAlKYYr1bpY_0_60.wav"
        # "start_time": 0, "duration": 60.
        # So suffix is _START_DURATION.
        
        clip_filename = f"{clip_id}.wav"
        logger.info(f"Processing {clip_filename}...")
        
        # 1. Extract
        clip_path = extract_clip(item["source"], clip_id, item["start"], item["duration"])
        
        # 2. Transcribe
        segments, _ = whisper_model.transcribe(str(clip_path), word_timestamps=True)
        all_words = []
        for s in segments:
            if s.words: all_words.extend(s.words)
            
        # 3. Diarize
        diarization = pipeline(str(clip_path), num_speakers=item["num_speakers"])
        
        # Get embeddings
        embeddings = None
        if hasattr(diarization, 'speaker_embeddings'):
            embeddings = diarization.speaker_embeddings
            
        # Unwrap annotation
        if hasattr(diarization, 'speaker_diarization'):
            annotation = diarization.speaker_diarization
        elif hasattr(diarization, 'annotation'):
            annotation = diarization.annotation
        else:
            annotation = diarization # Fallback
            
        # 4. Identify
        speaker_map = {}
        if embeddings is not None:
            for i in range(len(embeddings)):
                label = f"SPEAKER_{i:02d}"
                name, dist = identify_speaker(embeddings[i], db)
                if name:
                    speaker_map[label] = name
                    logger.info(f"  Identified {label} as {name} (dist: {dist:.4f})")
                else:
                    logger.info(f"  {label} is UNKNOWN")
                    
        # 5. Align
        aligned_segments = align_words_with_diarization(all_words, annotation, speaker_map)
        
        # 6. Update Manifest
        entry = next((e for e in manifest if e["id"] == clip_filename), None)
        if not entry:
            entry = {
                "id": clip_filename,
                "clip_path": f"data/clips/{clip_filename}",
                "transcriptions": {}
            }
            manifest.append(entry)
            
        entry["title"] = item["title"]
        entry["original_url"] = item["original_url"]
        entry["start_time"] = item["start"]
        entry["duration"] = item["duration"]
        
        # Save as standard transcription (UI uses this)
        entry["transcriptions"]["pywhispercpp.small"] = aligned_segments
        entry["transcriptions"]["faster_whisper_aligned"] = aligned_segments
        
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)
        
    logger.info("Done! All clips processed.")

if __name__ == "__main__":
    main()
