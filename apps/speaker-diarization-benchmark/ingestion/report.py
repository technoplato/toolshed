"""
WHO:
  Antigravity
  (Context: Audio Ingestion System)

WHAT:
  Logic for generating benchmark reports.

WHEN:
  2025-12-03

WHERE:
  apps/speaker-diarization-benchmark/ingestion/report.py

WHY:
  To separate reporting logic from the main execution flow.
"""

import time
import logging
from pathlib import Path
from typing import Dict, Any, List
from .config import IngestionConfig

logger = logging.getLogger(__name__)

def generate_report(config: IngestionConfig, 
                   transcription_text: str, 
                   segments: List[Dict[str, Any]], 
                   stats: Dict[str, float],
                   git_info: Dict[str, Any]):
    
    if config.append_to:
        output_path = config.append_to
        mode = 'a'
        logger.info(f"Appending results to {output_path}")
    else:
        output_filename = f"plain_text_transcription_{config.clip_path.stem}_{int(time.time())}.txt"
        output_path = config.output_dir / output_filename
        mode = 'w'
    
    # Comparison logic (placeholder for now, can be moved here)
    comparison_report = ""
    # if output_path.exists():
    #     comparison_report = compare_with_gold_standard(output_path, segments)

    with open(output_path, mode) as f:
        if mode == 'a':
            f.write("\n\n\n") # Separator
            
        # Header
        f.write("--- Benchmark Report ---\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Clip: {config.clip_path.name}\n")
        f.write(f"Workflow: {config.workflow.name}\n")
        f.write(f"Commit: {git_info['commit_hash']} (Dirty: {git_info['is_dirty']})\n")
        f.write(f"Arguments: {config.workflow}\n")
        f.write("\n")
        
        # Timing Stats
        f.write("--- Timing Stats ---\n")
        f.write(f"Transcription: {stats.get('transcription_time', 0):.2f}s\n")
        f.write(f"Embedding:     {stats.get('embedding_time', 0):.2f}s\n")
        f.write(f"Segmentation:  {stats.get('segmentation_time', 0):.2f}s\n")
        f.write(f"Clustering:    {stats.get('clustering_time', 0):.2f}s\n")
        f.write(f"Total:         {stats.get('total_time', 0):.2f}s\n")
        f.write("\n")
        
        # Full Transcription
        f.write("--- Full Transcription ---\n")
        f.write(transcription_text)
        f.write("\n\n")
        
        # Segments
        f.write("--- Segmentation & Diarization ---\n")
        for seg in segments:
            speaker = seg.get('speaker', 'UNKNOWN')
            start = seg['start']
            end = seg['end']
            text = seg['text']
            
            f.write(f"[{start:6.2f} - {end:6.2f}] {speaker}: {text}\n")
            
            if 'match_info' in seg and (speaker.startswith("SPEAKER_") or speaker.startswith("UNKNOWN")):
                mi = seg['match_info']
                f.write(f"       Best Guess: {mi['best_match']} (Dist: {mi['distance']:.4f}, Thr: {config.workflow.id_threshold})\n")
            
        if comparison_report:
            f.write("\n\n--- Comparison vs Gold Standard ---\n")
            f.write(comparison_report)

    logger.info(f"Benchmark report saved to {output_path}")
    print(f"\nResults saved to: {output_path}")
