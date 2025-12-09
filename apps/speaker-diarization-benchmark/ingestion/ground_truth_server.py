"""
HOW:
  Start the server:
    cd apps/speaker-diarization-benchmark
    uv run python -m ingestion.ground_truth_server --port 8000
  
  Or via audio_ingestion.py:
    uv run audio_ingestion.py server --port 8000
  
  Or via Docker:
    docker compose up -d ground-truth-server

  [Inputs]
  - INSTANT_APP_ID (env): Required for InstantDB connection
  - INSTANT_ADMIN_SECRET (env): Required for InstantDB admin access
  - POSTGRES_DSN (env): PostgreSQL connection string for embeddings
  - HF_TOKEN (env): HuggingFace token for PyAnnote models
  - PORT (env or --port): Server port (default: 8000)

  [Outputs]
  - HTTP server on localhost:{PORT}
  - Serves Ground Truth UI at /data/clips/ground_truth_instant.html

  [Side Effects]
  - Reads/writes to InstantDB via Admin SDK
  - Reads/writes to PostgreSQL for embeddings
  - Serves audio files for playback

WHO:
  Antigravity, Claude AI
  (Context: Audio Ingestion System - Ground Truth Labeling)

WHAT:
  Server implementation for the Ground Truth UI, backed by InstantDB.
  
  [Endpoints]
  - GET /: Serves static files (UI, audio)
  - POST /split_segment: Splits a segment into multiple segments
  - POST /assign_speaker: Creates speaker assignment for a segment
  - POST /delete_segment: Deletes a segment and its embedding
  
  [Key Behaviors]
  - When splitting: Original segment is invalidated, embedding is DELETED from PostgreSQL
  - When assigning speaker: If no embedding exists, one is extracted and saved
  - When deleting: Both InstantDB segment and PostgreSQL embedding are removed
  
WHEN:
  2025-12-06
  Last Modified: 2025-12-09
  [Change Log:
    - 2025-12-09: Fixed embedding deletion on split, added embedding extraction on relabel
    - 2025-12-09: Renamed from server.py to ground_truth_server.py for clarity
  ]

WHERE:
  apps/speaker-diarization-benchmark/ingestion/ground_truth_server.py

WHY:
  Provides a web interface for:
  1. Viewing diarization segments with audio playback
  2. Assigning speakers to segments (with autocomplete)
  3. Splitting segments that contain multiple speakers
  4. Deleting incorrectly linked segments
  
  The server ensures data consistency between InstantDB (metadata) and
  PostgreSQL (embeddings) by handling both in each operation.
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

# Add project root to path for absolute imports
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ingestion.config import ServerConfig
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
    print(f"Starting Ground Truth Server on port {port}...")
    
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
        def do_GET(self):
            """Handle GET requests with support for HTTP Range requests (needed for audio scrubbing)."""
            # Check if this is a range request for an audio file
            if self.headers.get('Range') and self.path.endswith(('.wav', '.mp3', '.m4a', '.ogg', '.flac')):
                self.handle_range_request()
            else:
                super().do_GET()
        
        def handle_range_request(self):
            """Handle HTTP Range requests for audio seeking/scrubbing."""
            try:
                # Translate path to file path
                path = self.translate_path(self.path)
                
                if not os.path.isfile(path):
                    self.send_error(404, "File not found")
                    return
                
                file_size = os.path.getsize(path)
                range_header = self.headers.get('Range')
                
                # Parse Range header: "bytes=start-end"
                if range_header.startswith('bytes='):
                    range_spec = range_header[6:]
                    
                    if '-' in range_spec:
                        start_str, end_str = range_spec.split('-', 1)
                        start = int(start_str) if start_str else 0
                        end = int(end_str) if end_str else file_size - 1
                    else:
                        start = int(range_spec)
                        end = file_size - 1
                    
                    # Clamp to valid range
                    start = max(0, min(start, file_size - 1))
                    end = max(start, min(end, file_size - 1))
                    content_length = end - start + 1
                    
                    # Send 206 Partial Content
                    self.send_response(206)
                    self.send_header('Content-Type', self.guess_type(path))
                    self.send_header('Content-Length', content_length)
                    self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                    self.send_header('Accept-Ranges', 'bytes')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    # Send the requested byte range
                    with open(path, 'rb') as f:
                        f.seek(start)
                        self.wfile.write(f.read(content_length))
                else:
                    # Invalid range format, fall back to normal GET
                    super().do_GET()
                    
            except BrokenPipeError:
                # Normal when client closes connection during seek - ignore
                pass
            except ConnectionResetError:
                # Normal when client resets connection - ignore
                pass
            except Exception as e:
                print(f"Range request error: {e}")
                try:
                    self.send_error(500, str(e))
                except:
                    pass
        
        def end_headers(self):
            """Add headers that enable range requests."""
            self.send_header('Accept-Ranges', 'bytes')
            super().end_headers()
        
        def do_POST(self):
            if self.path == '/split_segment':
                self.handle_split_segment()
            elif self.path == '/relabel_speaker_for_segment':
                self.handle_relabel_speaker_for_segment()
            elif self.path == '/assign_speaker':
                self.handle_assign_speaker()
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
            """
            Split a diarization segment into multiple segments.
            
            SIMPLIFIED API:
            Required fields:
              - segment_id: The diarization segment to split
              - lines: Array of text strings (one per resulting segment)
            
            Optional:
              - split_by: Who performed the split (default: "ground_truth_ui")
            
            Everything else (run_id, start_time, end_time, video_id) is looked up
            from the segment itself.
            
            SCHEMA FLOW:
            1. Fetch segment to get start_time, end_time, embedding_id, and parent run
            2. DELETE the original embedding from PostgreSQL (prevents garbage data)
            3. Create SegmentSplit record (audit trail)
            4. Mark original segment is_invalidated=true (NOT deleted - history preserved)
            5. Create N new DiarizationSegments with speaker_label="SPLIT_X"
            6. Link everything together
            
            NOTE: New segments are created WITHOUT embeddings. Embeddings will be
            extracted when the user assigns a speaker to each new segment.
            """
            try:
                import uuid
                from datetime import datetime
                
                length = int(self.headers['Content-Length'])
                data = json.loads(self.rfile.read(length))
                print(f"Received split request: {data}")
                
                segment_id = data.get("segment_id")
                lines = data.get("lines", [])
                split_by = data.get("split_by", "ground_truth_ui")
                
                if not segment_id:
                    raise ValueError("Missing required field: segment_id")
                
                if len(lines) < 2:
                    raise ValueError("Need at least 2 lines to split a segment")
                
                # Fetch the segment to get its properties and parent run
                q = {
                    "diarizationSegments": {
                        "$": {"where": {"id": segment_id}},
                        "diarizationRun": {}
                    }
                }
                result = repo._query(q)
                segments = result.get("diarizationSegments", [])
                
                if not segments:
                    raise ValueError(f"Segment not found: {segment_id}")
                
                segment = segments[0]
                start_time = segment.get("start_time")
                end_time = segment.get("end_time")
                embedding_id = segment.get("embedding_id")
                
                # Get run_id from the linked diarizationRun
                runs = segment.get("diarizationRun", [])
                if not runs:
                    raise ValueError(f"Segment has no parent diarization run")
                run_id = runs[0].get("id")
                
                print(f"  Segment: {start_time:.2f}s - {end_time:.2f}s, Run: {run_id}")
                
                # DELETE the original embedding from PostgreSQL
                # This is critical - the original embedding spans multiple speakers
                # and would pollute KNN search results if left in the database
                if embedding_id and pg_client:
                    try:
                        pg_client.delete_embedding(embedding_id)
                        print(f"  Deleted embedding {embedding_id} from PostgreSQL")
                    except Exception as e:
                        print(f"  Warning: Failed to delete embedding {embedding_id}: {e}")
                
                # Calculate proportional split times
                total_chars = sum(len(line) for line in lines)
                duration = end_time - start_time
                
                # Calculate split points (we use the boundary between lines)
                split_times = []
                current_time = start_time
                for i, line in enumerate(lines[:-1]):  # Don't need split after last line
                    prop = len(line) / total_chars if total_chars > 0 else 1.0 / len(lines)
                    current_time += duration * prop
                    split_times.append(current_time)
                
                # For this implementation, we use the FIRST split time as the primary split_time
                # In theory, multi-way splits could be multiple SegmentSplit records
                # For simplicity, we create ONE split record and multiple resulting segments
                primary_split_time = split_times[0] if split_times else (start_time + end_time) / 2
                
                steps = []
                
                # 1. Create SegmentSplit record
                split_id = str(uuid.uuid4())
                steps.append(["update", "segmentSplits", split_id, {
                    "split_time": primary_split_time,
                    "split_by": split_by,
                    "split_at": datetime.now().isoformat(),
                }])
                
                # 2. Link SegmentSplit to original segment
                steps.append(["link", "segmentSplits", split_id, {"originalSegment": segment_id}])
                
                # 3. Mark original segment as invalidated (NOT delete - preserve history)
                steps.append(["update", "diarizationSegments", segment_id, {
                    "is_invalidated": True
                }])
                
                # 4. Create new segments
                new_segments = []
                current_start = start_time
                
                for idx, line in enumerate(lines):
                    # Calculate end time
                    if idx < len(split_times):
                        seg_end = split_times[idx]
                    else:
                        seg_end = end_time
                    
                    # Create new segment
                    new_seg_id = str(uuid.uuid4())
                    new_speaker_label = f"SPLIT_{idx}"
                    
                    steps.append(["update", "diarizationSegments", new_seg_id, {
                        "start_time": current_start,
                        "end_time": seg_end,
                        "speaker_label": new_speaker_label,
                        "embedding_id": None,  # To be computed later
                        "confidence": None,
                        "is_invalidated": False,
                        "created_at": datetime.now().isoformat(),
                    }])
                    
                    # 5. Link new segment to SegmentSplit
                    steps.append(["link", "segmentSplits", split_id, {"resultingSegments": new_seg_id}])
                    
                    # 6. Link new segment to diarization run
                    steps.append(["link", "diarizationRuns", run_id, {"diarizationSegments": new_seg_id}])
                    
                    new_segments.append({
                        "id": new_seg_id,
                        "start_time": current_start,
                        "end_time": seg_end,
                        "speaker_label": new_speaker_label,
                        "text": line,
                    })
                    
                    current_start = seg_end
                
                # Execute transaction
                repo._transact(steps)
                print(f"Split segment {segment_id} into {len(new_segments)} new segments")
                
                # NOTE: Embeddings for new segments will be extracted when the user
                # assigns a speaker to each segment via handle_assign_speaker().
                # This is intentional - we don't want to extract embeddings for
                # segments that might be immediately deleted or re-split.
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "split_id": split_id,
                    "original_segment_id": segment_id,
                    "new_segments": new_segments
                }).encode())

            except Exception as e:
                print(f"Error splitting: {e}")
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(str(e).encode())

        def handle_relabel_speaker_for_segment(self):
            """Legacy endpoint - redirects to assign_speaker."""
            return self.handle_assign_speaker()
        
        def handle_assign_speaker(self):
            """
            Create a speaker assignment for a diarization segment.
            
            NEW SCHEMA FLOW:
            1. Find or create the Speaker entity by name
            2. Create a SpeakerAssignment record with:
               - source: "user" (manual correction)
               - confidence: 1.0 (user is certain)
               - assigned_by: user identifier
               - assigned_at: timestamp
            3. Link SpeakerAssignment to the segment and speaker
            4. If segment has no embedding, extract one and save to PostgreSQL
            5. Update PostgreSQL speaker_id for the embedding
            
            History is preserved - previous assignments remain but UI shows most recent.
            """
            try:
                import uuid
                from datetime import datetime
                
                length = int(self.headers['Content-Length'])
                data = json.loads(self.rfile.read(length))
                print(f"Received speaker assignment request: {data}")
                
                segment_id = data.get("segment_id")
                speaker_name = data.get("speaker_name") or data.get("new_speaker_id")
                source = data.get("source", "user")
                assigned_by = data.get("assigned_by", "ground_truth_ui")
                confidence = data.get("confidence", 1.0 if source == "user" else None)
                note = data.get("note")
                
                if not segment_id or not speaker_name:
                    raise ValueError("Missing segment_id or speaker_name")
                
                steps = []
                
                # 1. Find or create Speaker entity
                speaker_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"speaker_{speaker_name}"))
                steps.append(["update", "speakers", speaker_uuid, {
                    "name": speaker_name,
                    "is_human": True,
                    "ingested_at": datetime.now().isoformat(),
                }])
                
                # 2. Create SpeakerAssignment
                assignment_id = str(uuid.uuid4())
                assignment_data = {
                    "source": source,
                    "assigned_by": assigned_by,
                    "assigned_at": datetime.now().isoformat(),
                }
                if confidence is not None:
                    assignment_data["confidence"] = confidence
                if note:
                    assignment_data["note"] = note
                    
                steps.append(["update", "speakerAssignments", assignment_id, assignment_data])
                
                # 3. Link assignment to segment
                steps.append(["link", "diarizationSegments", segment_id, {"speakerAssignments": assignment_id}])
                
                # 4. Link assignment to speaker
                steps.append(["link", "speakerAssignments", assignment_id, {"speaker": speaker_uuid}])
                
                repo._transact(steps)
                print(f"Created speaker assignment: {speaker_name} -> segment {segment_id}")
                
                # Fetch segment with video info for embedding operations
                q_seg = {
                    "diarizationSegments": {
                        "$": {"where": {"id": segment_id}},
                        "diarizationRun": {
                            "video": {}
                        }
                    }
                }
                res = repo._query(q_seg)
                segs = res.get("diarizationSegments", [])
                
                if segs and pg_client:
                    seg = segs[0]
                    emb_id = seg.get("embedding_id")
                    
                    if emb_id:
                        # Embedding exists - just update the speaker_id
                        try:
                            pg_client.update_speaker_id(emb_id, speaker_name)
                            print(f"Updated Postgres speaker for embedding {emb_id}")
                        except Exception as e:
                            print(f"Failed to update Postgres: {e}")
                    else:
                        # No embedding - extract one and save it
                        # This happens for segments created from splits
                        try:
                            # Get audio path from video
                            runs = seg.get("diarizationRun", [])
                            video = runs[0].get("video", []) if runs else []
                            audio_path = video[0].get("filepath") if video else None
                            video_id = video[0].get("id") if video else None
                            run_id = runs[0].get("id") if runs else None
                            
                            if audio_path and os.path.exists(audio_path):
                                print(f"Extracting embedding for segment {segment_id}...")
                                start_time = seg.get("start_time")
                                end_time = seg.get("end_time")
                                speaker_label = seg.get("speaker_label", "UNKNOWN")
                                
                                # Extract embedding using PyAnnote
                                embedding = Embedder.extract_embedding(audio_path, start_time, end_time)
                                
                                # Generate new embedding ID
                                new_emb_id = str(uuid.uuid4())
                                
                                # Save to PostgreSQL
                                pg_client.add_embedding(
                                    external_id=new_emb_id,
                                    embedding=embedding,
                                    speaker_id=speaker_name,
                                    speaker_label=speaker_label,
                                    video_id=video_id,
                                    diarization_run_id=run_id,
                                    start_time=start_time,
                                    end_time=end_time,
                                )
                                print(f"Saved new embedding {new_emb_id} to PostgreSQL")
                                
                                # Update segment with embedding_id
                                repo._transact([
                                    ["update", "diarizationSegments", segment_id, {"embedding_id": new_emb_id}]
                                ])
                                print(f"Updated segment {segment_id} with embedding_id {new_emb_id}")
                            else:
                                print(f"Warning: Audio file not found at {audio_path}, skipping embedding extraction")
                        except Exception as e:
                            print(f"Failed to extract/save embedding: {e}")
                            import traceback
                            traceback.print_exc()

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "assignment_id": assignment_id,
                    "speaker_id": speaker_uuid,
                    "speaker_name": speaker_name
                }).encode())
                
            except Exception as e:
                print(f"Error assigning speaker: {e}")
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.send_header('Access-Control-Allow-Origin', '*')
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
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())

    return InstantDBHandler


# =========================================================================
# MAIN ENTRY POINT
# =========================================================================
if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv
    
    # Load .env from repo root (if running locally)
    # In Docker, environment variables are passed via docker-compose
    # ground_truth_server.py is at: apps/speaker-diarization-benchmark/ingestion/ground_truth_server.py
    # parents: [0]=ingestion, [1]=speaker-diarization-benchmark, [2]=apps, [3]=toolshed(repo)
    try:
        repo_root = Path(__file__).resolve().parents[3]
        if (repo_root / ".env").exists():
            load_dotenv(repo_root / ".env")
    except IndexError:
        # In Docker, path is /app/ingestion/ground_truth_server.py
        # parents[3] doesn't exist, but that's OK - env vars are passed via docker-compose
        pass
    
    parser = argparse.ArgumentParser(description="Ground Truth UI Server (InstantDB)")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    config = ServerConfig(port=args.port, host=args.host, verbose=args.verbose)
    run_server(config)