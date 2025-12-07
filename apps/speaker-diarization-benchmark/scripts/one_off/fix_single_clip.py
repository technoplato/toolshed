import sys
import os
import json
import logging
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Adjust path to find src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.append(project_root)

from src.data.impl.instant_db_adapter import InstantDBVideoRepository
from src.data.models import (
    Video, TranscriptionRun, TranscriptionSegment, 
    DiarizationRun, DiarizationSegment, Speaker,
    TranscriptionConfig, DiarizationConfig
)

load_dotenv()

# HARDCODED DATA FROM USER
CLIP_DATA = {
    "id": "clip_youtube_jAlKYYr1bpY_0_60.wav", # This is our Internal ID for now
    "video_id": "4417c492-cb62-546d-94f0-1f9af5546212", # UUID from DB if exists, or generate new? 
    # Actually, we should use the existing Video UUID if possible to avoid creating duplicates if ID is different.
    # But user said "ID for this video" is clip_youtube_jAlKYYr1bpY_0_60.wav.
    # InstantDBVideoRepository.save_video uses video.id as UUID if provided? 
    # No, save_video generates UUID if not valid UUID?
    # Let's check repository logic. It typically uses _generate_uuid(id) if ID is not UUID.
    
    "clip_path": "data/clips/clip_youtube_jAlKYYr1bpY_0_60.wav",
    "title": "Ep 569 - A Derosa Garden (feat. Joe Derosa)",
    "original_url": "https://www.youtube.com/watch?v=jAlKYYr1bpY",
    "start_time": 0,
    "duration": 60,
    "transcription_metadata": {
      "benchmark_tuned_t0.45_w2": {
        "pipeline": "benchmark_word_level.py",
        "commit_hash": "73be24a80fef24bafff720c3c6fa5f2c315feca5",
        "is_dirty": True,
        "threshold": 0.45,
        "window": 2,
        "cluster_threshold": 0.7,
        "id_threshold": 0.5,
        "timestamp": "2025-12-02 10:59:48"
      }
    },
    "segments": [
        {"start": 0, "end": 1.46, "text": "The Wild Wild West.", "speaker": "MSSP Theme Music"},
        {"start": 1.82, "end": 2.38, "text": "Two hours.", "speaker": "Shane Gillis"},
        {"start": 2.58, "end": 2.92, "text": "We're doing two.", "speaker": "Shane Gillis"},
        {"start": 3.30, "end": 4.18, "text": "Whatever you want to do.", "speaker": "Joe DeRosa"},
        {"start": 4.3, "end": 5.5, "text": "Yeah, just know the pace.", "speaker": "Matt McCusker"},
        {"start": 5.78, "end": 5.92, "text": "We're going to talk to Paige.", "speaker": "Shane Gillis"},
        {"start": 6.06, "end": 6.92, "text": "Oh, I like that, man.", "speaker": "Matt McCusker"},
        {"start": 7.04, "end": 7.84, "text": "I like that approach.", "speaker": "Matt McCusker"},
        {"start": 8.42, "end": 10.14, "text": "Can you guys not release this till October?", "speaker": "Joe DeRosa"},
        {"start": 10.76, "end": 11.18, "text": "Oh, wow.", "speaker": "Shane Gillis"},
        {"start": 11.18, "end": 11.92, "text": "I'm joking.", "speaker": "Joe DeRosa"},
        {"start": 12.22, "end": 13.84, "text": "I was going to say, I thought they're special.", "speaker": "Shane Gillis"},
        {"start": 13.98, "end": 14.92, "text": "Yeah, totally.", "speaker": "Joe DeRosa"},
        {"start": 15.16, "end": 16.92, "text": "Also, I was waiting to share it for this episode.", "speaker": "Shane Gillis"},
        {"start": 17.08, "end": 17.36, "text": "Thank you.", "speaker": "Joe DeRosa"},
        {"start": 17.76, "end": 19.66, "text": "I was in a tomb on Monday.", "speaker": "Shane Gillis"},
        {"start": 20.18, "end": 21.94, "text": "Dude, trust me.", "speaker": "Joe DeRosa"},
        {"start": 22.14, "end": 24.98, "text": "When you hit me back, I was like, he just did it.", "speaker": "Joe DeRosa"},
        {"start": 25.7, "end": 26.9, "text": "He's in the tomb.", "speaker": "Joe DeRosa"},
        {"start": 26.9, "end": 27.94, "text": "He's in the tomb.", "speaker": "Matt McCusker"},
        {"start": 29.64, "end": 30.12, "text": "I...", "speaker": "Matt McCusker"},
        {"start": 30.78, "end": 33.82, "text": "Sorry, because discussing the tomb I was just in is...", "speaker": "Shane Gillis"},
        {"start": 33.82, "end": 35.4, "text": "The tomb was...", "speaker": "Shane Gillis"},
        {"start": 35.4, "end": 35.78, "text": "Sacrophagus?", "speaker": "Matt McCusker"},
        {"start": 36.22, "end": 36.94, "text": "I was in...", "speaker": "Joe DeRosa"},
        {"start": 36.94, "end": 37.4, "text": "I've risen.", "speaker": "Shane Gillis"},
        {"start": 37.56, "end": 38.42, "text": "I'm Lazarus right now.", "speaker": "Shane Gillis"},
        {"start": 38.5, "end": 39.5, "text": "This is the third day.", "speaker": "Shane Gillis"},
        {"start": 39.78, "end": 40.5, "text": "I'm actually...", "speaker": "Shane Gillis"},
        {"start": 40.5, "end": 41.2, "text": "What's the tomb?", "speaker": "Matt McCusker"},
        {"start": 41.36, "end": 43.66, "text": "Like, is the tomb the bed or the couch?", "speaker": "Matt McCusker"},
        {"start": 43.82, "end": 44.98, "text": "The tomb is...", "speaker": "Shane Gillis"},
        {"start": 44.98, "end": 46.44, "text": "I just played...", "speaker": "Shane Gillis"},
        {"start": 46.44, "end": 49.92, "text": "There's a new game called Ready or Not, and I played it for two days.", "speaker": "Shane Gillis"},
        {"start": 50.3, "end": 50.86, "text": "That's awesome.", "speaker": "Joe DeRosa"},
        {"start": 51.14, "end": 52.56, "text": "I played the entire...", "speaker": "Shane Gillis"},
        {"start": 52.56, "end": 53.42, "text": "I played every mission.", "speaker": "Shane Gillis"},
        {"start": 54.06, "end": 54.54, "text": "Meanwhile...", "speaker": "Matt McCusker"},
        {"start": 54.54, "end": 55.4, "text": "That's so long.", "speaker": "Shane Gillis"},
        {"start": 55.92, "end": 57.1, "text": "Psychologically, what's the thought...", "speaker": "Matt McCusker"},
        {"start": 57.1, "end": 58.44, "text": "Is it thought process all in addition?", "speaker": "Matt McCusker"},
        {"start": 58.74, "end": 59.16, "text": "It's...", "speaker": "Shane Gillis"},
        {"start": 59.16, "end": 59.98, "text": "Usually, it's a...", "speaker": "Shane Gillis"}
    ]
}

def fix_clip():
    app_id = os.getenv("INSTANT_APP_ID")
    admin_secret = os.getenv("INSTANT_ADMIN_SECRET")
    repo = InstantDBVideoRepository(app_id, admin_secret)
    
    print("Saving Video...")
    # NOTE: We use the ID from the file (clip_youtube...). 
    # The repository will likely salt it to generate UUID, or use it if we forced it.
    # We want to be consistent with what 'find_populated_video' saw (4417c492...).
    # 4417c492... is typically UUID v5 of "clip_youtube_jAlKYYr1bpY_0_60.wav" or so.
    video = Video(
        id=CLIP_DATA["id"],
        title=CLIP_DATA["title"],
        filepath=CLIP_DATA["clip_path"],
        duration=CLIP_DATA["duration"],
        url=CLIP_DATA["original_url"]
    )
    video_uuid = repo.save_video(video)
    print(f"Video Saved: {video_uuid}")
    
    # Ensure Stable Segments
    # We can rely on repo._ensure_stable_segments which is called by save_video.
    # But we need their UUIDs to link!
    # repo doesn't return them.
    # We must query them back or re-calculate UUIDs.
    # InstantDB repo strategy for stable segments:
    # uuid = _generate_uuid(f"{video_uuid}_stable_{index}")
    # We can rely on that.
    
    # Prepare Segments
    t_segments = []
    d_segments = []
    
    for s in CLIP_DATA["segments"]:
        t_segments.append(TranscriptionSegment(
            start=s["start"], end=s["end"], text=s["text"]
        ))
        d_segments.append(DiarizationSegment(
            start=s["start"], end=s["end"], speaker_id=s["speaker"]
        ))
        
    print(f"Prepared {len(t_segments)} transcription and {len(d_segments)} diarization segments.")
    
    # Save Transcription Run
    t_config = TranscriptionConfig(model="mlx_whisper_manual", language="en")
    tr = TranscriptionRun(
        id=None, # Adapter will generate
        video_id=video_uuid,
        config=t_config,
        runner="manual_fix",
        created_at=datetime.now(),
        git_commit_sha="manual",
        pipeline_file="manual"
    )
    tr_uuid = repo.save_transcription_run(tr, t_segments)
    print(f"Transcription Run Saved: {tr_uuid}")
    
    # Save Diarization Run
    d_config = DiarizationConfig(embedding_model="pyannote/embedding", clustering_method="manual", cluster_threshold=0.0)
    dr = DiarizationRun(
        id=None,
        video_id=video_uuid,
        config=d_config,
        runner="manual_fix",
        created_at=datetime.now(),
        git_commit_sha="manual",
        pipeline_file="manual",
        transcription_run_id=tr_uuid
    )
    dr_uuid = repo.save_diarization_run(dr, d_segments)
    print(f"Diarization Run Saved: {dr_uuid}")
    
    print("Done! Validated Schema Links should be active.")

if __name__ == "__main__":
    fix_clip()
