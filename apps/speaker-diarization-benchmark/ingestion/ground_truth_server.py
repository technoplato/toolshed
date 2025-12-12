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
    - 2025-12-09: Simplified _handle_embedding_update() for upfront embedding extraction:
                  Fast path checks PostgreSQL directly, legacy fallback extracts from audio
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
from ingestion.clustering import cluster_embeddings, get_cluster_representatives
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
            import torch
            from pyannote.audio import Inference, Model
            from ingestion.safe_globals import get_safe_globals
            
            # Load the model first, then create Inference
            # pyannote.audio 3.1 requires Model.from_pretrained before Inference
            # Use safe_globals context manager for PyTorch 2.6+ compatibility
            with torch.serialization.safe_globals(get_safe_globals()):
                model = Model.from_pretrained("pyannote/embedding", use_auth_token=os.environ.get("HF_TOKEN"))
            cls._pipeline = Inference(model, window="whole")
        return cls._pipeline

    @staticmethod
    def extract_embedding(audio_path: str, start: float, end: float) -> List[float]:
        pipeline = Embedder.get_pipeline()
        from pyannote.audio.core.io import Audio
        from pyannote.core import Segment
        
        loader = Audio(sample_rate=16000, mono="downmix")
        
        # Load audio snippet for the specified time range
        # Audio.crop returns (waveform, sample_rate)
        waveform, sr = loader.crop(audio_path, Segment(start, end))
        
        # Run inference to get embedding
        embedding = pipeline({"waveform": waveform, "sample_rate": sr})
        # embedding can be (1, D) or (D,) depending on pyannote version
        # Flatten to 1D and convert to list
        import numpy as np
        emb_array = np.array(embedding).flatten()
        return emb_array.tolist()

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
        
        def _resolve_audio_path(self, audio_path: str) -> str:
            """
            Resolve audio path for the current environment.
            
            The filepath stored in InstantDB is typically the host path where the file
            was originally ingested. When running in Docker, we need to convert this
            to the container path where files are mounted.
            
            Host path examples:
              - /Users/laptop/Development/.../data/clips/jAlKYYr1bpY.wav
              - /home/user/projects/.../data/clips/jAlKYYr1bpY.wav
              
            Container path:
              - /app/data/clips/jAlKYYr1bpY.wav
              
            Local development (no Docker):
              - Returns the original path if it exists
              - Falls back to relative path if original doesn't exist
            """
            if not audio_path:
                return None
            
            # If the path exists as-is, use it (local development)
            if os.path.exists(audio_path):
                return audio_path
            
            # Try to extract the filename and look in known locations
            filename = os.path.basename(audio_path)
            
            # Docker container path
            docker_path = f"/app/data/clips/{filename}"
            if os.path.exists(docker_path):
                print(f"[{time.time():.3f}] 📁 Resolved path: {audio_path} → {docker_path}")
                return docker_path
            
            # Relative path from current working directory
            relative_path = f"data/clips/{filename}"
            if os.path.exists(relative_path):
                print(f"[{time.time():.3f}] 📁 Resolved path: {audio_path} → {relative_path}")
                return relative_path
            
            # Try extracting from common path patterns
            # Pattern: .../apps/speaker-diarization-benchmark/data/clips/filename.wav
            if "data/clips/" in audio_path:
                suffix = audio_path.split("data/clips/")[-1]
                for base in ["/app/data/clips/", "data/clips/"]:
                    candidate = base + suffix
                    if os.path.exists(candidate):
                        print(f"[{time.time():.3f}] 📁 Resolved path: {audio_path} → {candidate}")
                        return candidate
            
            # Could not resolve - return original (will fail with file not found)
            print(f"[{time.time():.3f}] ⚠️ Could not resolve audio path: {audio_path}")
            return audio_path
        
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
            elif self.path == "/bulk_confirm":
                self.handle_bulk_confirm()
            elif self.path == "/cluster":
                self.handle_cluster_request()
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
            4. If segment has no embedding, extract one and save to PostgreSQL (in background thread)
            5. Update PostgreSQL speaker_id for the embedding
            
            History is preserved - previous assignments remain but UI shows most recent.
            
            ARCHITECTURE: Response is sent immediately after InstantDB transaction.
            Embedding operations run in a background thread to avoid blocking.
            """
            try:
                import uuid
                from datetime import datetime
                
                # Start timing
                t_start = time.time()
                
                length = int(self.headers['Content-Length'])
                data = json.loads(self.rfile.read(length))
                print(f"[{time.time():.3f}] 📥 Received speaker assignment: {data.get('speaker_name')} -> {data.get('segment_id', '')[:8]}...")
                
                segment_id = data.get("segment_id")
                speaker_name = data.get("speaker_name") or data.get("new_speaker_id")
                source = data.get("source", "user")
                assigned_by = data.get("assigned_by", "ground_truth_ui")
                confidence = data.get("confidence", 1.0 if source == "user" else None)
                note = data.get("note")
                
                if not segment_id or not speaker_name:
                    raise ValueError("Missing segment_id or speaker_name")
                
                t_parse = time.time()
                print(f"[{t_parse:.3f}] ⏱️ Parse time: {(t_parse - t_start)*1000:.1f}ms")
                
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
                
                t_before_transact = time.time()
                print(f"[{t_before_transact:.3f}] 📝 Prepared transaction steps")
                
                repo._transact(steps)
                
                t_after_transact = time.time()
                print(f"[{t_after_transact:.3f}] ✅ InstantDB transaction complete: {(t_after_transact - t_before_transact)*1000:.1f}ms")
                print(f"[{t_after_transact:.3f}] Created speaker assignment: {speaker_name} -> segment {segment_id}")
                
                # SEND RESPONSE IMMEDIATELY - don't block on embedding extraction
                t_response = time.time()
                print(f"[{t_response:.3f}] ✅ InstantDB done in {(t_response - t_start)*1000:.0f}ms, sending response")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response_body = json.dumps({
                    "success": True,
                    "assignment_id": assignment_id,
                    "speaker_id": speaker_uuid,
                    "speaker_name": speaker_name
                }).encode()
                self.wfile.write(response_body)
                self.wfile.flush()  # Force send the response immediately
                print(f"[{time.time():.3f}] 📤 Response flushed to client ({len(response_body)} bytes)")
                
                # Run embedding operations in a BACKGROUND THREAD
                # This way the HTTP response is truly non-blocking
                def background_embedding():
                    self._handle_embedding_update(segment_id, speaker_name, repo, pg_client)
                
                thread = threading.Thread(target=background_embedding, daemon=True)
                thread.start()
                print(f"[{time.time():.3f}] 🧵 Started background thread for embedding")
                
            except Exception as e:
                print(f"[{time.time():.3f}] ❌ Error assigning speaker: {e}")
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(str(e).encode())
        
        def _handle_embedding_update(self, segment_id, speaker_name, repo, pg_client):
            """
            Update speaker_id for an existing embedding, or extract if missing (legacy fallback).
            
            With upfront embedding extraction, embeddings should already exist in PostgreSQL
            with speaker_id = NULL. This method now primarily just updates the speaker_id.
            
            FAST PATH: Check PostgreSQL directly for existing embedding (no InstantDB query needed)
            LEGACY FALLBACK: Extract embedding from audio if not found (for old data)
            
            This runs synchronously but in a background thread, so it doesn't block the client.
            """
            import uuid
            
            if not pg_client:
                print(f"[{time.time():.3f}] ⚠️ No pg_client, skipping embedding update")
                return
            
            t_emb_start = time.time()
            print(f"[{t_emb_start:.3f}] 🔄 Starting embedding update for segment {segment_id[:8]}...")
            
            try:
                # FAST PATH: Check PostgreSQL directly for existing embedding
                # With upfront extraction, embeddings are stored with segment_id as external_id
                t_before_check = time.time()
                existing = pg_client.get_embedding(segment_id)
                t_after_check = time.time()
                print(f"[{t_after_check:.3f}] 🔍 PostgreSQL lookup: {(t_after_check - t_before_check)*1000:.1f}ms")
                
                if existing and existing.get("embedding"):
                    # Fast path: embedding exists, just update speaker_id
                    t_before_update = time.time()
                    try:
                        pg_client.update_speaker_id(segment_id, speaker_name)
                        t_after_update = time.time()
                        print(f"[{t_after_update:.3f}] ✅ FAST PATH: Updated speaker_id for segment {segment_id[:8]}... to '{speaker_name}': {(t_after_update - t_before_update)*1000:.1f}ms")
                        print(f"[{t_after_update:.3f}] ⏱️ TOTAL embedding update time: {(t_after_update - t_emb_start)*1000:.1f}ms")
                        return
                    except Exception as e:
                        print(f"[{time.time():.3f}] ❌ Failed to update speaker_id in Postgres: {e}")
                        return
                
                # LEGACY FALLBACK: No embedding found, need to extract from audio
                print(f"[{time.time():.3f}] 📦 LEGACY FALLBACK: No embedding found for segment {segment_id[:8]}..., extracting from audio")
                
                # Fetch segment with video info for embedding extraction
                q_seg = {
                    "diarizationSegments": {
                        "$": {"where": {"id": segment_id}},
                        "diarizationRun": {
                            "video": {}
                        }
                    }
                }
                
                t_before_query = time.time()
                res = repo._query(q_seg)
                t_after_query = time.time()
                print(f"[{t_after_query:.3f}] 📊 Segment query: {(t_after_query - t_before_query)*1000:.1f}ms")
                
                segs = res.get("diarizationSegments", [])
                
                if not segs:
                    print(f"[{time.time():.3f}] ⚠️ Segment not found in InstantDB for embedding extraction")
                    return
                
                seg = segs[0]
                
                # Extract embedding from audio
                try:
                    # Get audio path from video
                    runs = seg.get("diarizationRun", [])
                    video = runs[0].get("video", []) if runs else []
                    audio_path = video[0].get("filepath") if video else None
                    video_id = video[0].get("id") if video else None
                    run_id = runs[0].get("id") if runs else None
                    
                    # Resolve audio path for Docker container
                    # The filepath in InstantDB is the host path, but in Docker
                    # the files are mounted at /app/data/clips/
                    audio_path = self._resolve_audio_path(audio_path)
                    
                    if audio_path and os.path.exists(audio_path):
                        start_time = seg.get("start_time")
                        end_time = seg.get("end_time")
                        speaker_label = seg.get("speaker_label", "UNKNOWN")
                        
                        print(f"[{time.time():.3f}] 🎤 Extracting embedding for segment {segment_id[:8]}... ({start_time:.1f}s - {end_time:.1f}s)...")
                        
                        # Extract embedding using PyAnnote
                        t_before_extract = time.time()
                        embedding = Embedder.extract_embedding(audio_path, start_time, end_time)
                        t_after_extract = time.time()
                        print(f"[{t_after_extract:.3f}] 🎤 Embedding extracted: {(t_after_extract - t_before_extract)*1000:.1f}ms")
                        
                        # Save to PostgreSQL using segment_id as external_id
                        # This matches the upfront extraction convention
                        t_before_save = time.time()
                        pg_client.add_embedding(
                            external_id=segment_id,
                            embedding=embedding,
                            speaker_id=speaker_name,
                            speaker_label=speaker_label,
                            video_id=video_id,
                            diarization_run_id=run_id,
                            start_time=start_time,
                            end_time=end_time,
                        )
                        t_after_save = time.time()
                        print(f"[{t_after_save:.3f}] 💾 Saved embedding to PostgreSQL: {(t_after_save - t_before_save)*1000:.1f}ms")
                        
                        # Update segment with embedding_id (same as segment_id for consistency)
                        t_before_link = time.time()
                        repo._transact([
                            ["update", "diarizationSegments", segment_id, {"embedding_id": segment_id}]
                        ])
                        t_after_link = time.time()
                        print(f"[{t_after_link:.3f}] 🔗 Updated segment with embedding_id: {(t_after_link - t_before_link)*1000:.1f}ms")
                        
                        t_emb_end = time.time()
                        print(f"[{t_emb_end:.3f}] ⏱️ TOTAL embedding update time (legacy path): {(t_emb_end - t_emb_start)*1000:.1f}ms")
                    else:
                        print(f"[{time.time():.3f}] ⚠️ Audio file not found at {audio_path}, skipping embedding extraction")
                except Exception as e:
                    print(f"[{time.time():.3f}] ❌ Failed to extract/save embedding: {e}")
                    import traceback
                    traceback.print_exc()
                
            except Exception as e:
                print(f"[{time.time():.3f}] ❌ Error in embedding update: {e}")
                import traceback
                traceback.print_exc()

        def handle_bulk_confirm(self):
            """
            POST /bulk_confirm
            
            Bulk confirm speaker assignments for multiple segments.
            Used to confirm all segments in a cluster at once.
            
            Request body:
            {
                "segment_ids": ["uuid1", "uuid2", ...],
                "speaker_name": "Shane Gillis"
            }
            
            Response:
            {
                "success": true,
                "updated_count": 5,
                "speaker_name": "Shane Gillis"
            }
            """
            try:
                length = int(self.headers['Content-Length'])
                data = json.loads(self.rfile.read(length))
                
                segment_ids = data.get("segment_ids", [])
                speaker_name = data.get("speaker_name")
                
                if not segment_ids:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": "segment_ids is required"
                    }).encode())
                    return
                
                if not speaker_name:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": "speaker_name is required"
                    }).encode())
                    return
                
                print(f"[{time.time():.3f}] 📦 Bulk confirming {len(segment_ids)} segments as '{speaker_name}'")
                
                # 1. Update PostgreSQL embeddings with speaker_id
                pg_updated = 0
                if pg_client:
                    try:
                        pg_updated = pg_client.bulk_update_speaker_id(segment_ids, speaker_name)
                        print(f"[{time.time():.3f}] ✅ Updated {pg_updated} embeddings in PostgreSQL")
                    except Exception as e:
                        print(f"[{time.time():.3f}] ⚠️ PostgreSQL bulk update failed: {e}")
                
                # 2. Create speaker assignments in InstantDB via the TypeScript proxy
                # This uses the proper InstantDB SDK instead of raw Admin API calls
                from ingestion.instant_client import InstantClient
                
                try:
                    instant_client = InstantClient(base_url="http://instant-proxy:3001")
                except RuntimeError:
                    # Fallback to localhost for local development
                    try:
                        instant_client = InstantClient(base_url="http://localhost:3001")
                    except RuntimeError as e:
                        print(f"[{time.time():.3f}] ⚠️ InstantDB proxy not available: {e}")
                        # Return success for PostgreSQL update, note InstantDB failure
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "success": True,
                            "updated_count": len(segment_ids),
                            "pg_updated": pg_updated,
                            "speaker_name": speaker_name,
                            "warning": "InstantDB proxy not available, speaker assignments not created"
                        }).encode())
                        return
                
                # Build assignments for the proxy
                assignments = [
                    {
                        "segment_id": seg_id,
                        "speaker_name": speaker_name,  # Proxy will find/create speaker
                        "source": "user",
                        "confidence": 1.0,
                        "note": {"method": "bulk_confirm"},
                        "assigned_by": "bulk_confirm",
                    }
                    for seg_id in segment_ids
                ]
                
                result = instant_client.create_speaker_assignments(assignments)
                print(f"[{time.time():.3f}] ✅ Created {len(segment_ids)} speaker assignments via InstantDB proxy")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "updated_count": len(segment_ids),
                    "pg_updated": pg_updated,
                    "speaker_name": speaker_name
                }).encode())
                
            except Exception as e:
                print(f"[{time.time():.3f}] ❌ Bulk confirm failed: {e}")
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": str(e)
                }).encode())


        def handle_cluster_request(self):
            """
            POST /cluster
            
            Clusters unlabeled embeddings for a diarization run using HDBSCAN.
            Returns cluster assignments and representative segments.
            Saves cluster assignments to PostgreSQL for persistence.
            
            Request body:
            {
                "diarization_run_id": "uuid-string",
                "min_cluster_size": 2,  // optional, default 2
                "min_samples": 1,       // optional, default 1
                "cluster_selection_method": "leaf"  // optional, 'leaf' or 'eom'
            }
            
            Response:
            {
                "success": true,
                "clusters": {
                    "0": ["embedding_id_1", "embedding_id_2"],
                    "1": ["embedding_id_3", "embedding_id_4", "embedding_id_5"]
                },
                "noise": ["embedding_id_6"],
                "representatives": {
                    "0": "embedding_id_1",
                    "1": "embedding_id_3"
                },
                "cluster_run_id": "uuid-of-this-clustering-run",
                "stats": {
                    "total_embeddings": 7,
                    "num_clusters": 2,
                    "noise_count": 1
                }
            }
            """
            try:
                import uuid
                length = int(self.headers['Content-Length'])
                data = json.loads(self.rfile.read(length))
                
                diarization_run_id = data.get("diarization_run_id")
                
                if not diarization_run_id:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": "diarization_run_id is required"
                    }).encode())
                    return
                
                min_cluster_size = data.get("min_cluster_size", 2)
                min_samples = data.get("min_samples", 1)
                # 'leaf' tends to find more, smaller clusters (better for distinct speakers)
                # 'eom' (Excess of Mass) finds fewer, larger clusters
                cluster_selection_method = data.get("cluster_selection_method", "leaf")
                
                print(f"[{time.time():.3f}] 🔬 Clustering embeddings for run {diarization_run_id} (method={cluster_selection_method})")
                
                if not pg_client:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": "PostgreSQL client not available"
                    }).encode())
                    return
                
                # Get embeddings from PostgreSQL
                embeddings = pg_client.get_embeddings_by_run(
                    diarization_run_id=diarization_run_id,
                    only_unlabeled=True  # Only cluster unlabeled segments
                )
                
                if not embeddings:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": True,
                        "clusters": {},
                        "noise": [],
                        "representatives": {},
                        "segment_info": {},
                        "stats": {
                            "total_embeddings": 0,
                            "num_clusters": 0,
                            "noise_count": 0
                        },
                        "message": "No unlabeled embeddings found for this run"
                    }).encode())
                    return
                
                # Run HDBSCAN clustering
                result = cluster_embeddings(
                    embeddings=embeddings,
                    min_cluster_size=min_cluster_size,
                    min_samples=min_samples,
                    cluster_selection_method=cluster_selection_method,
                )
                
                # Get representative segment for each cluster
                representatives = get_cluster_representatives(embeddings, result)
                
                # Save cluster assignments to PostgreSQL
                cluster_run_id = str(uuid.uuid4())
                cluster_assignments = {}
                for cluster_id, segment_ids in result.clusters.items():
                    for seg_id in segment_ids:
                        cluster_assignments[seg_id] = cluster_id
                for seg_id in result.noise:
                    cluster_assignments[seg_id] = -1  # -1 for noise
                
                try:
                    pg_client.update_cluster_assignments(cluster_run_id, cluster_assignments)
                    print(f"[{time.time():.3f}] 💾 Saved {len(cluster_assignments)} cluster assignments to PostgreSQL")
                except Exception as e:
                    print(f"[{time.time():.3f}] ⚠️ Failed to save cluster assignments: {e}")
                
                # Build segment_info map for UI to use (segment_id -> {start_time, end_time, speaker_label})
                # This allows the UI to display segment info without querying the DOM
                segment_info = {}
                for emb in embeddings:
                    segment_info[emb['external_id']] = {
                        'start_time': emb.get('start_time'),
                        'end_time': emb.get('end_time'),
                        'speaker_label': emb.get('speaker_label'),
                    }
                
                print(
                    f"[{time.time():.3f}] ✅ Clustering complete: {result.num_clusters} clusters, "
                    f"{result.noise_count} noise points from {len(embeddings)} embeddings"
                )
                
                # Convert cluster keys to strings for JSON serialization
                clusters_json = {str(k): v for k, v in result.clusters.items()}
                representatives_json = {str(k): v for k, v in representatives.items()}
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "clusters": clusters_json,
                    "noise": result.noise,
                    "representatives": representatives_json,
                    "segment_info": segment_info,
                    "cluster_run_id": cluster_run_id,
                    "stats": {
                        "total_embeddings": len(embeddings),
                        "num_clusters": result.num_clusters,
                        "noise_count": result.noise_count
                    }
                }).encode())
                
            except Exception as e:
                print(f"[{time.time():.3f}] ❌ Clustering failed: {e}")
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": str(e)
                }).encode())

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