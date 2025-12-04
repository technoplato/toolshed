"""
WHO:
  Antigravity
  (Context: Audio Ingestion System)

WHAT:
  Main entry point for the audio ingestion system.

WHEN:
  2025-12-03

WHERE:
  apps/speaker-diarization-benchmark/audio_ingestion.py

WHY:
  To orchestrate the audio ingestion process using modular components.
"""

import os
import sys
import time
import logging
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to sys.path to import transcribe
sys.path.append(str(Path(__file__).parent))

from ingestion.args import parse_args
from ingestion.config import IngestionConfig
from ingestion.manifest import update_manifest
from ingestion.report import generate_report
from transcribe import transcribe, TranscriptionResult, Segment, Word
from utils import get_git_info

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    config = parse_args()
    
    if config.verbose:
        logger.setLevel(logging.DEBUG)
        
    logger.info(f"Starting audio ingestion for {config.clip_path}")
    
    if not config.clip_path.exists():
        logger.error(f"Clip not found: {config.clip_path}")
        return

    # Metadata collection
    git_info = get_git_info()
    start_time_global = time.time()
    
    # 1. Transcription
    logger.info("Starting transcription...")
    transcription_start = time.time()
    
    # Caching logic (Simplified for now, can be moved to a module)
    cache_dir = Path(__file__).parent / "data/cache/transcriptions"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{config.clip_path.stem}.json"
    
    transcription_result = None
    if cache_file.exists():
        logger.info(f"Loading transcription from cache: {cache_file}")
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                # Reconstruct Pydantic models
                segments = []
                for s in data['segments']:
                    words = [Word(**w) for w in s['words']]
                    segments.append(Segment(start=s['start'], end=s['end'], text=s['text'], words=words))
                transcription_result = TranscriptionResult(text=data['text'], segments=segments, language=data['language'])
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}. Re-running transcription.")
    
    if transcription_result is None:
        try:
            transcription_result = transcribe(str(config.clip_path))
            # Save to cache
            with open(cache_file, 'w') as f:
                if hasattr(transcription_result, 'model_dump'):
                    data = transcription_result.model_dump()
                else:
                    data = transcription_result.dict()
                json.dump(data, f, indent=2)
            logger.info(f"Saved transcription to cache: {cache_file}")
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return
        
    transcription_time = time.time() - transcription_start
    logger.info(f"Transcription complete in {transcription_time:.2f}s")

    # 2. Workflow Execution
    try:
        from ingestion.args import get_workflow
        workflow = get_workflow(config.workflow)
    except Exception as e:
        logger.error(f"Failed to initialize workflow: {e}")
        return

    segments, stats = workflow.run(config.clip_path, transcription_result)
    
    # Add transcription time to stats
    stats['transcription_time'] = transcription_time
    stats['total_time'] = time.time() - start_time_global
    
    # 3. Output Generation
    if not config.dry_run:
        generate_report(config, transcription_result.text, segments, stats, git_info)
        
        try:
            update_manifest(
                clip_path=config.clip_path,
                workflow_name=config.workflow.name,
                segments=segments,
                transcription_text=transcription_result.text
            )
            logger.info(f"Manifest updated for {config.clip_path}")
        except Exception as e:
            logger.error(f"Failed to update manifest: {e}")
    else:
        import tempfile
        logger.info("Dry run: Skipping manifest update.")
        
        # Construct metadata
        metadata = {
            "command": f"python {' '.join(sys.argv)}",
            "cwd": os.getcwd(),
            "config": json.loads(config.json()) if hasattr(config, 'json') else config.dict()
        }
        
        output_data = {
            "metadata": metadata,
            "transcript": segments
        }
        
        # Print metadata to console (human-readable)
        print("\n--- Dry Run Metadata ---")
        print(f"Command: {metadata['command']}")
        print(f"CWD: {metadata['cwd']}")
        print(f"Workflow: {config.workflow.name}")
        print("------------------------\n")
        
        # Print transcript preview
        print(json.dumps(output_data, indent=2))
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', prefix='dry_run_') as tmp:
            json.dump(output_data, tmp, indent=2)
            logger.info(f"Dry run results saved to temp file: {tmp.name}")
            print(f"\nDry run results saved to: {tmp.name}")

if __name__ == "__main__":
    main()
