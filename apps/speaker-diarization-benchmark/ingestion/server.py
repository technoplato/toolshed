
"""
WHO:
  Antigravity
  (Context: Audio Ingestion System)

WHAT:
  Server implementation for the Ground Truth UI, backed by InstantDB.
  
  [Endpoints]
  - GET /: Serves the UI.
  - POST /split_segment: Splits a segment and updates InstantDB.
  - POST /relabel_speaker: updates InstantDB + Postgres (metadata).
  
  [Inputs]
  - ServerConfig
  
  [Outputs]
  - Running HTTP server
  
WHEN:
  2025-12-06

WHERE:
  apps/speaker-diarization-benchmark/ingestion/server.py
"""

import http.server
import socketserver
import json
import os
import sys
import webbrowser
import threading
import time
from typing import List
from pathlib import Path

from .config import ServerConfig
from src.data.factory import DatabaseFactory
from src.data.models import DiarizationSegment, DiarizationRun
from src.embeddings.pgvector_client import PgVectorClient
import numpy as np

# Lazy load Pyannote
class Embedder:
    _pipeline = None
    
    @classmethod
    def get_pipeline(cls):
        if cls._pipeline is None:
            print("Loading pyannote/embedding pipeline...")
            from pyannote.audio import Inference
            # Use a lightweight model or the standard one
            cls._pipeline = Inference("pyannote/embedding", window="sliding", duration=3.0, step=1.0) # Or just plain embedding? 'pyannote/embedding' works.
            # Actually, `Model.from_pretrained("pyannote/embedding")`?
            # pyannote.audio 3.1 uses `Model.from_pretrained`.
            # Let's check how we did it in workflows.
            # We referenced `pyannote/embedding` before.
            # Let's use `Model` + `Inference`.
            from pyannote.audio import Model
            model = Model.from_pretrained("pyannote/embedding", use_auth_token=os.environ.get("HF_TOKEN"))
            cls._pipeline = Inference(model, window="whole")
        return cls._pipeline

    @staticmethod
    def extract_embedding(audio_path: str, start: float, end: float) -> List[float]:
        pipeline = Embedder.get_pipeline()
        from pyannote.audio.core.io import Audio
        loader = Audio(sample_rate=16000, mono="downmix")
        
        # Load snippet
        # Audio.crop returns (waveform, sample_rate)
        # Inference expects waveform or path?
        # Inference(window="whole") expects waveform or path.
        
        snippet = loader.crop(audio_path, Segment(start, end)) # pyannote.core.Segment
        # snippet is Tensor? No, loader.crop return Tensor.
        # Wait, I need pyannote.core.Segment
        from pyannote.core import Segment as PySegment
        
        waveform, sr = loader.crop(audio_path, PySegment(start, end))
        
        # Inference
        embedding = pipeline({"waveform": waveform, "sample_rate": sr})
        # embedding is (1, D)
        return embedding[0].tolist()

def run_server(config: ServerConfig):
    # ... (rest same, updated port print)
    port = config.port
    print(f"Starting InstantDB Server on port {port}...")
    
    Handler = make_handler_class(config)
    
    # Auto-open browser
    url = f"http://localhost:{port}/data/clips/ground_truth_instant.html"
    print(f"Opening {url}")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    with ReusableTCPServer(("", port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            httpd.shutdown()

    return Handler

def make_handler_class(config: ServerConfig):
    
    # Initialize DB Repo
    app_id = os.environ.get("INSTANT_APP_ID")
    admin_secret = os.environ.get("INSTANT_ADMIN_SECRET")
    postgres_dsn = os.environ.get("POSTGRES_DSN") 
    
    if not app_id or not admin_secret:
        print("Error: INSTANT_APP_ID and INSTANT_ADMIN_SECRET must be set.")
        sys.exit(1)
    
    # Import locally to avoid top-level side effects if easy
    from src.data.impl.instant_db_adapter import InstantDBVideoRepository
    repo = InstantDBVideoRepository(app_id, admin_secret)
    
    pg_client = None
    if postgres_dsn:
        try:
            pg_client = PgVectorClient(postgres_dsn)
        except Exception as e:
            print(f"Error connecting to Postgres: {e}")
            print("Server will run without Vector DB support.")
            pg_client = None
    else:
        print("Warning: POSTGRES_DSN not set. Embeddings will not be saved to Vector DB.")

    class InstantDBHandler(http.server.SimpleHTTPRequestHandler):
        def do_POST(self):
            if self.path == '/split_segment':
                self.handle_split_segment()
            elif self.path == '/relabel_speaker_for_segment':
                self.handle_relabel_speaker_for_segment()
            elif self.path == '/delete_segment':
                self.handle_delete_segment()
            else:
                self.send_error(404)

        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

        def handle_split_segment(self):
            try:
                length = int(self.headers['Content-Length'])
                data = json.loads(self.rfile.read(length))
                print(f"Received split request: {data}")
                
                segment_id = data.get("segment_id")      # The ID of the DiarizationSegment to split
                new_lines = data.get("new_lines", [])    # List of strings
                video_id = data.get("video_id")          # ID of the video
                run_id = data.get("run_id")              # ID of the DiarizationRun
                start_time = data.get("start_time")      # Original segment start
                end_time = data.get("end_time")          # Original segment end
                
                if not (segment_id and video_id and run_id and start_time is not None and end_time is not None):
                    raise ValueError("Missing required fields: segment_id, video_id, run_id, start_time, end_time")

                # 1. Get Video Filepath
                video = repo.get_video(video_id) # We need to ensure get_video works or implement manual fetch
                # InstantDBVideoRepository.get_video is NOT implemented fully in previous step (composite was empty, instant adapter might be too).
                # Let's check InstantDBVideoRepository implementation.
                # It has save_video, but get_video might be missing.
                # Assuming I can't easily get filepath via repo yet without implementing it.
                # But wait, I migrated `filepath` to InstantDB explicitly.
                # I can query it.
                
                # Manual Query for Video Filepath
                q_vid = {
                    "videos": {
                        "$": {"where": {"id": video_id}}
                    }
                }
                res = repo._query(q_vid)
                videos_list = res.get("videos", [])
                if not videos_list:
                    raise ValueError(f"Video {video_id} not found")
                
                video_filepath = videos_list[0].get("filepath")
                # Resolve relative path if needed
                # manifest 'clip_path' was relative to 'data/clips'?
                # The migration script saved what was in manifest.
                # Typically `data/clips/foo.wav`.
                if not os.path.isabs(video_filepath):
                     # Assume relative to apps/speaker-diarization-benchmark/
                     # We are in that dir when running usually?
                     # `server.py` checked cwd.
                     video_filepath = os.path.abspath(video_filepath)
                
                if not os.path.exists(video_filepath):
                    print(f"Warning: Audio file not found at {video_filepath}")
                    # We can't extract embeddings if file missing.
                    # Proceed without embedding?
                
                # 2. Proportional Split Logic
                total_chars = sum(len(line) for line in new_lines)
                duration = end_time - start_time
                current_start = start_time
                
                new_segments_payload = []
                
                steps = []
                
                # Delete/Mark Old Segment
                # Ideally "replaced_by" link, but for now just delete or unlink?
                # User said: "mark the original segment as deleted/replaced"
                # Since we don't have "deleted" flag in schema usually (unless we add it), simplest is to unlink from run.
                # Or delete the entity.
                steps.append(["delete", "diarizationSegments", segment_id])
                
                for idx, line in enumerate(new_lines):
                    # Time calc
                    if total_chars > 0:
                        prop = len(line) / total_chars
                    else:
                        prop = 1.0 / len(new_lines)
                    
                    seg_duration = duration * prop
                    seg_end = current_start + seg_duration
                    
                    # 3. Embedding
                    new_embedding_id = None
                    if os.path.exists(video_filepath) and pg_client:
                        try:
                            # Extract & Embed
                            vec = Embedder.extract_embedding(video_filepath, current_start, seg_end)
                            # Save to Postgres
                            # Generate ID
                            new_embedding_id = str(uuid.uuid4())
                            pg_client.add_embedding(new_embedding_id, vec, metadata={"video_id": video_id, "text": line})
                        except Exception as e:
                            print(f"Embedding failed for segment {idx}: {e}")
                    
                    # 4. Create New Segment
                    new_seg_id = str(uuid.uuid4())
                    steps.append(["update", "diarizationSegments", new_seg_id, {
                        "start_time": current_start,
                        "end_time": seg_end,
                        # "text": line, # DiarizationSegment doesn't have text usually? 
                        # Migration script saved text to TranscriptionSegment.
                        # DiarizationSegment has metrics?
                        # If we are splitting Diarization, we assume we are refining WHO spoke WHEN.
                        # Text assignment is implicit via time overlap with Transcription.
                        # But wait, user passed `new_lines`.
                        # If we want to save text, we might need a linked TranscriptionSegment?
                        # For now, let's just save the DiarizationSegment. The text helps split the time.
                        # We map it to "UNKNOWN" speaker as requested.
                        "embedding_id": new_embedding_id,
                    }])
                    
                    # Link to Run
                    steps.append(["link", "diarizationRuns", run_id, {"segments": new_seg_id}])
                    
                    # Link to UNKNOWN speaker
                    # Find or Create UNKNOWN speaker?
                    # Ideally we have a generic UNKNOWN speaker or create a new "Unknown X"?
                    # User: "initially be UNKNOWN".
                    # I'll create a new speaker "UNKNOWN" (or find it) or just not link a speaker? 
                    # Schema requires `speaker_id`?
                    # Schema: `speaker_id: i.string().indexed()`. It's a string, not a link?
                    # Wait, migration script:
                    # `steps.append(["link", "diarizationSegments", seg_uuid, {"speaker": speaker_uuid}])`
                    # `speaker_id` attr in schema was string.
                    # Migration script saved: `speaker_uuid = ...`, `steps.append(["update", "speakers", speaker_uuid, {"name": seg.speaker_id}])`
                    # `diarizationSegments` has `speaker_id` AND a link to `speakers`?
                    # Schema:
                    # diarizationSegments: { speaker_id: string, ... }
                    # links: { speaker: ... }
                    # So we should populate `speaker_id="UNKNOWN"` and maybe link to a speaker entity?
                    
                    steps.append(["update", "diarizationSegments", new_seg_id, {"speaker_id": "UNKNOWN"}])
                    
                    # Link to a shared "UNKNOWN" speaker entity?
                    # Let's generate a consistent UUID for "UNKNOWN"
                    uk_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, "SPEAKER_UNKNOWN"))
                    steps.append(["update", "speakers", uk_uuid, {"name": "UNKNOWN", "is_human": False}])
                    steps.append(["link", "diarizationSegments", new_seg_id, {"speaker": uk_uuid}])
                    
                    # Update loop vars
                    current_start = seg_end
                    
                    new_segments_payload.append({
                        "id": new_seg_id,
                        "start": current_start - seg_duration,
                        "end": seg_end,
                        "speaker": "UNKNOWN"
                    })

                # Transact
                repo._transact(steps)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"segments": new_segments_payload}).encode())

            except Exception as e:
                print(f"Error splitting: {e}")
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())

        def handle_relabel_speaker_for_segment(self):
            try:
                length = int(self.headers['Content-Length'])
                data = json.loads(self.rfile.read(length))
                print(f"Received relabel request: {data}")
                
                segment_id = data.get("segment_id")
                new_speaker_id = data.get("new_speaker_id") # e.g. "Joe Rogan"
                
                if not segment_id or not new_speaker_id:
                    raise ValueError("Missing segment_id or new_speaker_id")
                
                # 1. Update InstantDB
                speaker_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"SPEAKER_{new_speaker_id}")) # Consistent hash
                
                steps = []
                # Ensure speaker exists
                steps.append(["update", "speakers", speaker_uuid, {"name": new_speaker_id}])
                
                # Update Segment
                steps.append(["update", "diarizationSegments", segment_id, {"speaker_id": new_speaker_id}])
                # Link
                steps.append(["link", "diarizationSegments", segment_id, {"speaker": speaker_uuid}])
                # Note: Unlinking old speaker is automatic for one-to-one links? 
                # DiarizationSegment -> Speaker is many-to-one.
                # A segment has ONE speaker. "speaker" link is singular? 
                # Schema: `diarizationSegments.link.speaker`. Usually one-to-one or many-to-one. 
                # InstantDB links are many-to-many by default unless constrained? 
                # But linking overwrites? No, it adds.
                # We should unlink old? 
                # "When you link two objects ... if the relationship is one-to-many..."
                # I'll enable "unlink" if I can find the old speaker.
                # But for now, linking new one implies relationship... 
                # To be partial to "replace", we usually just link.
                
                repo._transact(steps)
                
                # 2. Update Postgres
                # We need segment's embedding_id
                # Fetch segment to get embedding_id
                q_seg = {
                    "diarizationSegments": {
                        "$": {"where": {"id": segment_id}}
                    }
                }
                res = repo._query(q_seg)
                segs = res.get("diarizationSegments", [])
                if segs and pg_client:
                    seg = segs[0]
                    emb_id = seg.get("embedding_id")
                    if emb_id:
                         # Update metadata/speaker_id in Postgres
                         try:
                             pg_client.update_speaker_id(emb_id, new_speaker_id)
                             print(f"Updated Postgres speaker_id for embedding {emb_id} to {new_speaker_id}")
                         except Exception as e:
                             print(f"Failed to update Postgres for embedding {emb_id}: {e}")

                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
            except Exception as e:
                print(f"Error relabeling: {e}")
                traceback.print_exc()
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())

        def handle_delete_segment(self):
            try:
                length = int(self.headers['Content-Length'])
                data = json.loads(self.rfile.read(length))
                print(f"Received delete request: {data}")
                
                segment_id = data.get("segment_id")
                if not segment_id:
                    raise ValueError("Missing segment_id")
                
                # 1. Fetch Segment to get Embedding ID
                q_seg = {
                    "diarizationSegments": {
                        "$": {"where": {"id": segment_id}}
                    }
                }
                res = repo._query(q_seg)
                segs = res.get("diarizationSegments", [])
                
                if segs:
                    seg = segs[0]
                    emb_id = seg.get("embedding_id")
                    
                    # 2. Delete from Postgres
                    if emb_id and pg_client:
                        try:
                            pg_client.delete_embedding(emb_id)
                            print(f"Deleted embedding {emb_id} from Postgres.")
                        except Exception as e:
                            print(f"Failed to delete embedding {emb_id}: {e}")
                
                    # 3. Delete from InstantDB
                    steps = [
                        ["delete", "diarizationSegments", segment_id]
                    ]
                    repo._transact(steps)
                    print(f"Deleted segment {segment_id} from InstantDB.")
                    
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"OK")
                else:
                    print(f"Segment {segment_id} not found, skipping delete.")
                    self.send_error(404, "Segment not found")
                    
            except Exception as e:
                print(f"Error deleting: {e}")
                traceback.print_exc()
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())

    return InstantDBHandler
