
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
            1. Fetch segment to get start_time, end_time, and parent run
            2. Create SegmentSplit record (audit trail)
            3. Mark original segment is_invalidated=true (NOT deleted - history preserved)
            4. Create N new DiarizationSegments with speaker_label="SPLIT_X"
            5. Link everything together
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
                
                # Get run_id from the linked diarizationRun
                runs = segment.get("diarizationRun", [])
                if not runs:
                    raise ValueError(f"Segment has no parent diarization run")
                run_id = runs[0].get("id")
                
                print(f"  Segment: {start_time:.2f}s - {end_time:.2f}s, Run: {run_id}")
                
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
                
                # TODO: Background job to extract embeddings for new segments
                # This requires audio file access and pyannote embedding model
                
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
                
                # Update Postgres if we have embedding
                q_seg = {"diarizationSegments": {"$": {"where": {"id": segment_id}}}}
                res = repo._query(q_seg)
                segs = res.get("diarizationSegments", [])
                if segs and pg_client:
                    seg = segs[0]
                    emb_id = seg.get("embedding_id")
                    if emb_id:
                        try:
                            pg_client.update_speaker_id(emb_id, speaker_name)
                            print(f"Updated Postgres speaker for embedding {emb_id}")
                        except Exception as e:
                            print(f"Failed to update Postgres: {e}")

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
    
    # Load .env from repo root
    # server.py is at: apps/speaker-diarization-benchmark/ingestion/server.py
    # parents: [0]=ingestion, [1]=speaker-diarization-benchmark, [2]=apps, [3]=toolshed(repo)
    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env")
    
    parser = argparse.ArgumentParser(description="Ground Truth UI Server (InstantDB)")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    config = ServerConfig(port=args.port, host=args.host, verbose=args.verbose)
    run_server(config)
