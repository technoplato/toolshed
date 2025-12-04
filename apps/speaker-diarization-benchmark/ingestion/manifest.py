"""
WHO:
  Antigravity
  (Context: Audio Ingestion System)

WHAT:
  Logic for updating the manifest.json file.

WHEN:
  2025-12-03

WHERE:
  apps/speaker-diarization-benchmark/ingestion/manifest.py

WHY:
  To centralize database-like operations on the manifest file.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def update_manifest(clip_path: Path, workflow_name: str, segments: List[Dict[str, Any]], transcription_text: str):
    manifest_path = Path(__file__).parent.parent / "data/clips/manifest.json"
    if not manifest_path.exists():
        logger.error(f"Manifest not found at {manifest_path}")
        return

    try:
        with open(manifest_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Failed to decode manifest at {manifest_path}")
        return

    # Find entry by ID (filename)
    clip_id = clip_path.name
    entry = next((item for item in data if item['id'] == clip_id), None)

    if not entry:
        logger.error(f"Clip ID {clip_id} not found in manifest.")
        return

    if 'transcriptions' not in entry:
        entry['transcriptions'] = {}

    # Format segments for manifest
    manifest_segments = []
    for seg in segments:
        manifest_seg = {
            "start": seg['start'],
            "end": seg['end'],
            "text": seg['text'],
            "speaker": seg.get('speaker', 'UNKNOWN')
        }
        if 'match_info' in seg:
             manifest_seg['match_info'] = seg['match_info']
        manifest_segments.append(manifest_seg)

    entry['transcriptions'][workflow_name] = manifest_segments
    
    with open(manifest_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Updated manifest.json for {clip_id} with workflow {workflow_name}")
