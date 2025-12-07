"""
HOW:
  `python3 playground/migrate_clip.py`
  
  [Inputs]
  - data/clips/manifest.json
  - ENV vars: INSTANT_APP_ID, INSTANT_ADMIN_SECRET

  [Outputs]
  - Populates InstantDB with Video, TranscriptionRun, and Segments.

WHO:
  Antigravity
"""

import sys
print("DEBUG: Script started", flush=True)
import os
import json
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Adjust path to find src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
sys.path.append(project_root)

from src.data.impl.instant_db_adapter import InstantDBVideoRepository
from src.data.models import (
    Video, TranscriptionRun, TranscriptionSegment, 
    DiarizationRun, DiarizationSegment, Speaker,
    TranscriptionConfig, DiarizationConfig
)

load_dotenv()

def migrate():
    print("DEBUG: Inside migrate()", flush=True)
    app_id = os.getenv("INSTANT_APP_ID")
    admin_secret = os.getenv("INSTANT_ADMIN_SECRET")
    print(f"DEBUG: App ID found: {bool(app_id)}", flush=True)
    
    if not app_id or not admin_secret:
        print("Error: INSTANT_APP_ID and INSTANT_ADMIN_SECRET must be set.", flush=True)
        return

    repo = InstantDBVideoRepository(app_id, admin_secret)
    
    manifest_path = "apps/speaker-diarization-benchmark/data/clips/manifest.json"
    print(f"DEBUG: Checking manifest at {os.path.abspath(manifest_path)}", flush=True)
    if not os.path.exists(manifest_path):
        print(f"Manifest not found at {manifest_path}", flush=True)
        return
        
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        
    print(f"Found {len(manifest)} clips to migrate.")
    
    import re
    
    # Defaults
    DEFAULT_RUNNER = "mlx" 
    DEFAULT_MODEL = "whisper-turbo"

    for clip in manifest:
        clip_id = clip.get("id")
        # TARGET FILTER
        target_id = "clip_youtube_jAlKYYr1bpY_0_60.wav"
        if clip_id != target_id:
            continue
            
        print(f"Migrating {clip_id}...")
        
        # 1. Create Video Entity
        video = Video(
            id=clip_id,
            title=clip.get("title", clip_id),
            url=clip.get("original_url", ""),
            filepath=clip.get("clip_path", ""),
            duration=clip.get("duration", 0),
            channel_id=clip.get("channel_id"),
            upload_date=clip.get("upload_date"),
            view_count=clip.get("view_count")
        )
        
        video_uuid = repo.save_video(video)
        print(f"  -> Saved Video {video_uuid}")
        
        # 2. Migrate Transcriptions
        transcriptions = clip.get("transcriptions", {})
        transcription_metadata = clip.get("transcription_metadata", {})
        
        for run_key, segments_raw in transcriptions.items():
            print(f"    -> Migrating run: {run_key}")
            
            # --- Config Extraction ---
            # Try to parse T=, W=, C=, ID= from key or metadata
            # Example key: "benchmark_tuned_t0.45_w2" or "mlx_whisper_turbo"
            
            # Metadata might look like: "mlx_whisper_turbo": {"segmentation_threshold": 0.45, ...}
            meta = transcription_metadata.get(run_key, {})
            
            # Regex for key parsing fallback
            # Matches _t0.45_ or _w2_ etc
            t_match = re.search(r"_t([\d\.]+)", run_key)
            w_match = re.search(r"_w(\d+)", run_key)
            
            seg_threshold = meta.get("segmentation_threshold") or (float(t_match.group(1)) if t_match else None)
            context_window = meta.get("context_window") or (int(w_match.group(1)) if w_match else None)
            
            # Identify Model & Runner
            runner = DEFAULT_RUNNER
            model = DEFAULT_MODEL
            if "deepgram" in run_key:
                runner = "deepgram"
                model = "nova-2" # guess
            elif "assemblyai" in run_key:
                runner = "assemblyai"
                model = "best"
            
            # Create TranscriptionConfig
            t_config = TranscriptionConfig(
                model=model,
                language="en",
                threshold=seg_threshold,
                window=context_window,
                parameters=meta
            )

            # Convert segments
            trans_segments = []
            diar_segments = []
            is_diarized = False
            
            for s in segments_raw:
                speaker = s.get("speaker")
                text = s.get("text", "")
                start = s.get("start", 0)
                end = s.get("end", 0)
                
                trans_segments.append(TranscriptionSegment(
                    start=start, end=end, text=text
                ))
                
                if speaker:
                    is_diarized = True
                    # Check for embedding ID in segment (unlikely in old manifest, but checking)
                    diar_segments.append(DiarizationSegment(
                        start=start, end=end, speaker_id=speaker
                    ))
            
            print(f"      DEBUG: Found {len(trans_segments)} segments in manifest.", flush=True)

            # Transcription Run
            tr_run = TranscriptionRun(
                video_id=video_uuid,
                config=t_config,
                runner=runner,
                git_commit_sha=meta.get("git_commit_sha"),
                pipeline_file=meta.get("pipeline_file")
            )
            tr_uuid = repo.save_transcription_run(tr_run, trans_segments)
            print(f"      -> Saved TranscriptionRun {tr_uuid}")
            
            # Diarization Run (if exists)
            if is_diarized:
                 # Clean up diarization config
                 # C=clustering, ID=identification ??? User said T, W, C, ID.
                 # Assuming C=clustering_threshold, ID=identification_threshold if applicable to pyannote?
                 # Or just generic params.
                 
                 c_match = re.search(r"_c([\d\.]+)", run_key)
                 id_match = re.search(r"_id([\d\.]+)", run_key)
                 
                 clust_thresh = meta.get("clustering_threshold") or (float(c_match.group(1)) if c_match else None)
                 ident_thresh = meta.get("identification_threshold") or (float(id_match.group(1)) if id_match else None)
                 
                 d_config = DiarizationConfig(
                     embedding_model="pyannote/embedding", # Default for now
                     clustering_method="unknown",
                     cluster_threshold=clust_thresh,
                     identification_threshold=ident_thresh,
                     parameters=meta
                 )
                 
                 dr_run = DiarizationRun(
                     video_id=video_uuid,
                     transcription_run_id=tr_uuid,
                     config=d_config,
                     runner=runner,
                     git_commit_sha=meta.get("git_commit_sha"),
                     pipeline_file=meta.get("pipeline_file")
                 )
                 repo.save_diarization_run(dr_run, diar_segments)
                 print(f"      -> Saved DiarizationRun")
    
if __name__ == "__main__":
    print("Starting Migration...", flush=True)
    migrate()
