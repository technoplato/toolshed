"""
WHO:
  Antigravity
  (Context: Audio Ingestion System)

WHAT:
  Overlapped Speech Detection Workflow.
  Uses pyannote/segmentation-3.0 to find overlapping speech segments.

WHEN:
  2025-12-04

WHERE:
  apps/speaker-diarization-benchmark/ingestion/workflows/local/overlapped_speech.py

WHY:
  To detect and report segments where multiple speakers are talking simultaneously.
"""

import os
import time
import logging
from typing import List, Dict, Any, Tuple
from pathlib import Path
from ingestion.workflows.base import Workflow
from ingestion.config import WorkflowConfig

logger = logging.getLogger(__name__)

class OverlappedSpeechDetectionWorkflow(Workflow):
    def run(self, clip_path: Path, transcription_result: Any) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        stats = {'embedding_time': 0, 'segmentation_time': 0, 'clustering_time': 0}
        
        logger.info("Running Overlapped Speech Detection Workflow...")
        start_time = time.time()
        
        try:
            import torch
            import numpy as np
            from pyannote.audio import Model, Inference
            from pyannote.core import Segment, Timeline
            from ingestion.safe_globals import get_safe_globals
        except ImportError:
            logger.error("pyannote.audio or dependencies not installed.")
            return [], stats

        try:
            device = "mps" if os.uname().sysname == "Darwin" else "cpu"
            
            # Load model with safe globals
            with torch.serialization.safe_globals(get_safe_globals()):
                model = Model.from_pretrained(
                    "pyannote/segmentation-3.0",
                    token=os.getenv("HF_TOKEN")
                )
            
            if model is None:
                logger.error("Failed to load pyannote/segmentation-3.0 model. Check HF_TOKEN.")
                return [], stats

            model.to(torch.device(device))
            
            # Run inference
            # Configure Inference to return chunks (duration=10s, step=0.1s)
            # We will process chunks manually to avoid aggregation issues.
            inference = Inference(model, duration=10.0, step=0.1)
            segmentation = inference(str(clip_path))
            
            data = segmentation.data # (NumChunks, NumFrames, NumSpeakers) usually
            
            # Check if data is 3D
            if len(data.shape) == 3:
                num_chunks, num_frames, num_speakers = data.shape
                chunk_duration = segmentation.sliding_window.duration
                frame_duration = chunk_duration / num_frames
                
                timeline = Timeline()
                
                for i, chunk_data in enumerate(data):
                    chunk_start_time = segmentation.sliding_window[i].start
                    
                    # Thresholding
                    active = chunk_data > 0.5
                    overlap = np.sum(active, axis=1) > 1
                    
                    # Find overlap regions in this chunk
                    start_frame = None
                    for f, is_ov in enumerate(overlap):
                        if is_ov and start_frame is None:
                            start_frame = f
                        elif not is_ov and start_frame is not None:
                            start_t = chunk_start_time + start_frame * frame_duration
                            end_t = chunk_start_time + f * frame_duration
                            timeline.add(Segment(start_t, end_t))
                            start_frame = None
                    
                    if start_frame is not None:
                        start_t = chunk_start_time + start_frame * frame_duration
                        end_t = chunk_start_time + num_frames * frame_duration
                        timeline.add(Segment(start_t, end_t))
                
                # Merge overlapping segments
                overlap_timeline = timeline.support()
                
            else:
                # If 2D (aggregated), use simple logic
                # (NumFrames, NumSpeakers)
                num_frames, num_speakers = data.shape
                # Actually sliding_window.step is the resolution
                frame_duration = segmentation.sliding_window.step
                
                active = data > 0.5
                overlap = np.sum(active, axis=1) > 1
                
                timeline = Timeline()
                start_frame = None
                for f, is_ov in enumerate(overlap):
                    if is_ov and start_frame is None:
                        start_frame = f
                    elif not is_ov and start_frame is not None:
                        start_t = segmentation.sliding_window[start_frame].start
                        end_t = segmentation.sliding_window[f].start
                        timeline.add(Segment(start_t, end_t))
                        start_frame = None
                
                if start_frame is not None:
                    start_t = segmentation.sliding_window[start_frame].start
                    end_t = segmentation.sliding_window[num_frames-1].end
                    timeline.add(Segment(start_t, end_t))
                
                overlap_timeline = timeline.support()

            # Apply smoothing:
            # 1. Merge gaps smaller than min_duration_off (e.g., 0.3s)
            # 2. Remove segments smaller than min_duration_on (e.g., 0.1s)
            
            min_duration_off = 0.3
            min_duration_on = 0.1
            
            # Merge gaps
            if len(overlap_timeline) > 0:
                merged_timeline = Timeline()
                current_segment = overlap_timeline[0]
                
                for next_segment in overlap_timeline[1:]:
                    if next_segment.start - current_segment.end < min_duration_off:
                        # Merge
                        current_segment = Segment(current_segment.start, next_segment.end)
                    else:
                        merged_timeline.add(current_segment)
                        current_segment = next_segment
                merged_timeline.add(current_segment)
                overlap_timeline = merged_timeline
            
            # Filter short segments
            final_overlap_timeline = Timeline()
            for segment in overlap_timeline:
                if segment.duration >= min_duration_on:
                    final_overlap_timeline.add(segment)
            
            # Merge with existing transcript
            # Strategy: Iterate through transcript segments.
            # If a segment significantly overlaps with the overlap timeline, mark it.
            
            merged_segments = []
            
            # If no transcript, just return the overlap segments
            if not transcription_result:
                 for segment in final_overlap_timeline:
                    merged_segments.append({
                        "start": segment.start,
                        "end": segment.end,
                        "text": "[OVERLAPPED SPEECH]",
                        "speaker": "OVERLAP"
                    })
            else:
                # Handle TranscriptionResult object or list
                if hasattr(transcription_result, 'segments'):
                    items = transcription_result.segments
                else:
                    items = transcription_result

                for item in items:
                    # Handle Pydantic models (Segment) or dicts
                    if hasattr(item, 'start'):
                        start = item.start
                        end = item.end
                        text = item.text
                        speaker = getattr(item, 'speaker', 'UNKNOWN')
                    elif isinstance(item, dict):
                        start = item.get('start', 0.0)
                        end = item.get('end', 0.0)
                        text = item.get('text', '')
                        speaker = item.get('speaker', 'UNKNOWN')
                    else:
                        logger.warning(f"Skipping unexpected item type: {type(item)}")
                        continue
                    
                    seg = Segment(start, end)
                    
                    # Calculate overlap duration with the detected overlaps
                    # crop() returns a Timeline of intersections
                    intersection = final_overlap_timeline.crop(seg)
                    overlap_duration = intersection.duration()
                    
                    # If overlap is significant (e.g., > 20% of segment or > 0.5s)
                    if overlap_duration > 0.0 and (overlap_duration / seg.duration > 0.2 or overlap_duration > 0.5):
                        speaker = "OVERLAP"
                        if "[OVERLAP]" not in text:
                            text = f"[OVERLAP] {text}"
                    
                    merged_segments.append({
                        "start": start,
                        "end": end,
                        "text": text,
                        "speaker": speaker
                    })

            stats['segmentation_time'] = time.time() - start_time
            return merged_segments, stats

        except Exception as e:
            logger.error(f"Overlapped Speech Detection failed: {e}")
            return [], stats
