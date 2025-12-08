"""
HOW:   
  Run this script to ingest audio, transcribe it, and optionally run various diarization/embedding workflows.
  You can also use it to download videos from various providers supported by yt-dlp.

  [IMPORTANT: Directory Context]
  You MUST run this script from the `apps/speaker-diarization-benchmark` directory to ensure all dependencies 
  (especially those managed by `uv`) are correctly resolved.
  
  Correct usage:
    cd apps/speaker-diarization-benchmark
    uv run audio_ingestion.py <command> ...

  [Commands]
  1. Transcribe audio:
     uv run audio_ingestion.py transcribe <audio_path> --start-time 0 --end-time 60

  2. Run diarization:
     uv run audio_ingestion.py diarize <audio_path> --workflow pyannote

  3. Identify speakers:
     uv run audio_ingestion.py identify --video-id <uuid> --threshold 0.5 --execute

  4. Full pipeline (download → transcribe → diarize → identify):
     uv run audio_ingestion.py ingest <URL_or_path> --start-time 0 --end-time 240

  5. Download a video:
     uv run audio_ingestion.py download <URL> --output-dir data/clips

  [Inputs (Common)]
  - --start-time: Start time in seconds (default: 0)
  - --end-time: End time in seconds (default: full file)
  - --dry-run: Show what would happen without executing
  - --verbose: Enable verbose logging

  [Outputs]
  - Saves results to InstantDB (via TypeScript server)
  - Caches transcriptions in data/cache/transcriptions

WHO:
  Antigravity, Claude AI
  (Context: Audio Ingestion System)

WHAT:
  Main entry point for the audio ingestion system.
  It orchestrates:
  1. Audio/Video downloading via `yt-dlp`
  2. Transcription via `mlx_whisper` (cached)
  3. Diarization/Embedding via configured workflows
  4. Speaker identification via KNN search
  5. Saving to InstantDB

WHEN:
  2025-12-05
  Last Modified: 2025-12-08
  Change Log:
  - 2025-12-08: Added transcribe, identify, ingest commands
  - 2025-12-08: Added service health checks
  - 2025-12-08: Removed manifest.json support (InstantDB only)
  
WHERE:
  apps/speaker-diarization-benchmark/audio_ingestion.py

WHY:
  To provide a unified CLI for bringing audio data into the benchmarking system and running experiments.
  InstantDB is now the single source of truth - no more manifest.json.
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

# Add parent directory to sys.path for imports
sys.path.append(str(Path(__file__).parent))

from ingestion.args import parse_args
from ingestion.config import (
    TranscribeConfig,
    DiarizeConfig,
    IdentifyConfig,
    IngestConfig,
    IngestionConfig,
    DownloadConfig,
    ServerConfig,
)
from ingestion.download import download_video
from ingestion.server import run_server
from ingestion.health import check_services
from ingestion.dry_run import print_dry_run_output
from transcribe import transcribe, TranscriptionResult, Segment, Word
from utils import get_git_info

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_transcribe(config: TranscribeConfig) -> None:
    """Run transcription command."""
    if config.dry_run:
        print_dry_run_output(config)
        return
    
    logger.info(f"Transcribing: {config.audio_path}")
    logger.info(f"Time range: {config.start_time}s - {config.end_time or 'end'}s")
    
    result = transcribe(
        str(config.audio_path),
        start_time=config.start_time if config.start_time > 0 else None,
        end_time=config.end_time,
    )
    
    # Output as JSON
    print(json.dumps(result.model_dump(), indent=2))


def run_diarize(config: DiarizeConfig) -> None:
    """Run diarization command."""
    # Check services
    check_services(require_instant_server=True, require_postgres=True)
    
    if config.dry_run:
        print_dry_run_output(config)
        return
    
    logger.info(f"Diarizing: {config.audio_path}")
    logger.info(f"Workflow: {config.workflow.name}")
    logger.info(f"Time range: {config.start_time}s - {config.end_time or 'end'}s")
    
    # Get workflow
    from ingestion.args import get_workflow
    workflow = get_workflow(config.workflow)
    
    # Run transcription first (needed for some workflows)
    transcription_result = _get_or_create_transcription(
        config.audio_path,
        config.start_time,
        config.end_time,
    )
    
    # Run diarization
    segments, stats = workflow.run(config.audio_path, transcription_result)
    
    # Output results
    print(json.dumps({
        "segments": segments,
        "stats": stats,
    }, indent=2))


def run_identify(config: IdentifyConfig) -> None:
    """Run speaker identification command."""
    # Check services
    check_services(require_instant_server=True, require_postgres=True)
    
    if not config.execute:
        print_dry_run_output(config)
        return
    
    from ingestion.identify import identify_speakers, print_plan, execute_plan
    from ingestion.instant_client import InstantClient
    from src.embeddings.pgvector_client import PgVectorClient
    
    logger.info(f"Identifying speakers for video: {config.video_id[:8]}...")
    
    # Initialize clients
    instant_client = InstantClient()
    pg_dsn = os.getenv("POSTGRES_DSN") or "postgresql://diarization:diarization_dev@localhost:5433/speaker_embeddings"
    pg_client = PgVectorClient(pg_dsn)
    
    # Get audio path if not provided
    audio_path = str(config.audio_path) if config.audio_path else None
    if not audio_path:
        video = instant_client.get_video(config.video_id)
        audio_path = video.get("filepath")
    
    # Run identification
    plan = identify_speakers(
        instant_client=instant_client,
        pg_client=pg_client,
        video_id=config.video_id,
        start_time=config.start_time if config.start_time > 0 else None,
        end_time=config.end_time,
        threshold=config.threshold,
        top_k=config.top_k,
        audio_path=audio_path,
    )
    
    # Print results
    print_plan(plan)
    
    # Execute if requested
    if config.execute:
        execute_plan(instant_client, pg_client, plan)


def run_ingest(config: IngestConfig) -> None:
    """
    Run full ingestion pipeline with caching.
    
    Modes:
      --dry-run: Show plan only (no compute)
      --preview: Run compute, show preview, save to markdown, don't save to DB
      (default): Run compute, show preview, ask confirmation, save to DB
      --yes: Run compute, skip confirmation, save to DB
    """
    from ingestion.cache import (
        extract_video_id,
        TranscriptionCache,
        DiarizationCache,
        IdentificationCache,
        PreviewCache,
        get_embedding_count,
    )
    from ingestion.preview import generate_preview_markdown, save_preview, print_preview_summary
    
    # Check services
    check_services(require_instant_server=True, require_postgres=True)
    
    # Dry run = show plan only (no compute)
    if config.dry_run:
        print_dry_run_output(config)
        return
    
    logger.info("Starting full ingestion pipeline")
    start_time_global = time.time()
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 1: Download (if URL)
    # ═══════════════════════════════════════════════════════════════════
    video_id = extract_video_id(config.source)
    
    if config.is_url:
        logger.info(f"Step 1: Downloading from {config.source}")
        expected_path = config.output_dir / f"{video_id}.wav"
        
        if expected_path.exists():
            logger.info(f"   ✅ Cache HIT: {expected_path}")
            audio_path = expected_path
        else:
            download_config = DownloadConfig(
                url=config.source,
                output_dir=config.output_dir,
                verbose=config.verbose,
            )
            audio_path = download_video(download_config)
            if not audio_path:
                logger.error("Download failed")
                return
            audio_path = Path(audio_path)
    else:
        audio_path = Path(config.source)
        video_id = audio_path.stem
        logger.info(f"Step 1: Using local file {audio_path}")
    
    if not audio_path.exists():
        logger.error(f"Audio file not found: {audio_path}")
        return
    
    # Determine the end time for caching
    # If end_time is None, we need to compute full file (use a large number)
    cache_end_time = config.end_time or 99999.0
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 2: Transcribe (with caching)
    # ═══════════════════════════════════════════════════════════════════
    logger.info(f"Step 2: Transcribing {audio_path}")
    
    trans_cache = TranscriptionCache(
        video_id=video_id,
        tool="mlx-whisper",
        model="whisper-large-v3-turbo",
    )
    
    if trans_cache.has_range(cache_end_time):
        logger.info(f"   ✅ Cache HIT: transcription [0-{cache_end_time}s]")
        transcription_data = trans_cache.get_filtered(config.start_time, cache_end_time)
        # Reconstruct TranscriptionResult
        transcription_result = _dict_to_transcription_result(transcription_data)
    else:
        cached_end = trans_cache.get_cached_end()
        if cached_end:
            logger.info(f"   ⚠️ Cache MISS: have [0-{cached_end}s], need [0-{cache_end_time}s]")
        else:
            logger.info(f"   ⚠️ Cache MISS: no cache, computing [0-{cache_end_time}s]")
        
        # Compute transcription
        transcription_result = transcribe(
            str(audio_path),
            start_time=None,  # Always start from 0 for caching
            end_time=config.end_time,
        )
        
        # Save to cache
        trans_cache.save(
            result=transcription_result.model_dump() if hasattr(transcription_result, 'model_dump') else transcription_result.dict(),
            end_time=cache_end_time,
        )
    
    logger.info(f"   Transcription: {len(transcription_result.segments)} segments")
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 3: Diarize (with caching)
    # ═══════════════════════════════════════════════════════════════════
    logger.info(f"Step 3: Running diarization (workflow: {config.workflow})")
    
    diar_cache = DiarizationCache(
        video_id=video_id,
        workflow=config.workflow,
    )
    
    if diar_cache.has_range(cache_end_time):
        logger.info(f"   ✅ Cache HIT: diarization [0-{cache_end_time}s]")
        segments = diar_cache.get_filtered(config.start_time, cache_end_time)
        stats = diar_cache.get_stats() or {}
    else:
        cached_end = diar_cache.get_cached_end()
        if cached_end:
            logger.info(f"   ⚠️ Cache MISS: have [0-{cached_end}s], need [0-{cache_end_time}s]")
        else:
            logger.info(f"   ⚠️ Cache MISS: no cache, computing [0-{cache_end_time}s]")
        
        # Slice audio to requested time range for faster diarization
        # This is critical - full audio file can be 767MB (1+ hr), but we only need 60s
        from ingestion.audio_utils import slice_audio
        
        sliced_audio = slice_audio(
            audio_path=str(audio_path),
            start_time=0,  # Always start from 0 for cache consistency
            end_time=cache_end_time,
        )
        logger.info(f"   Using sliced audio: {sliced_audio.name}")
        
        # Compute diarization on sliced audio
        from ingestion.args import get_workflow
        from ingestion.config import WorkflowConfig
        
        workflow_config = WorkflowConfig(name=config.workflow)
        workflow = get_workflow(workflow_config)
        
        segments, stats = workflow.run(sliced_audio, transcription_result)
        
        # Save to cache
        diar_cache.save(segments=segments, stats=stats, end_time=cache_end_time)
    
    logger.info(f"   Diarization: {len(segments)} segments")
    
    # Prepare video data
    video_data = {
        "id": video_id,
        "title": config.title or audio_path.stem,
        "filepath": str(audio_path.resolve()),
        "source_url": config.source if config.is_url else None,
    }
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 4: Identify (with caching)
    # ═══════════════════════════════════════════════════════════════════
    identification_plan = None
    pg_client = None
    instant_client = None
    
    if not config.skip_identify:
        logger.info("Step 4: Running speaker identification")
        
        try:
            from src.embeddings.pgvector_client import PgVectorClient
            from ingestion.identify import identify_speakers
            from ingestion.instant_client import InstantClient
            
            instant_client = InstantClient()
            pg_dsn = os.getenv("POSTGRES_DSN") or "postgresql://diarization:diarization_dev@localhost:5433/speaker_embeddings"
            pg_client = PgVectorClient(pg_dsn)
            
            embedding_count = get_embedding_count()
            
            id_cache = IdentificationCache(
                video_id=video_id,
                strategy="knn",
                threshold=config.threshold,
                embedding_count=embedding_count,
            )
            
            if id_cache.has_range(cache_end_time):
                logger.info(f"   ✅ Cache HIT: identification [0-{cache_end_time}s]")
                # Note: For identification, we'd need to reconstruct the plan
                # For now, we'll recompute (identification is fast)
                identification_plan = identify_speakers(
                    instant_client=instant_client,
                    pg_client=pg_client,
                    video_id=video_id,
                    start_time=config.start_time if config.start_time > 0 else None,
                    end_time=config.end_time,
                    threshold=config.threshold,
                    audio_path=str(audio_path),
                )
            else:
                logger.info(f"   ⚠️ Cache MISS: computing identification")
                identification_plan = identify_speakers(
                    instant_client=instant_client,
                    pg_client=pg_client,
                    video_id=video_id,
                    start_time=config.start_time if config.start_time > 0 else None,
                    end_time=config.end_time,
                    threshold=config.threshold,
                    audio_path=str(audio_path),
                )
            
            logger.info(f"   Identification: {identification_plan.identified_count} identified, {identification_plan.unknown_count} unknown")
            
        except Exception as e:
            logger.warning(f"Speaker identification failed: {e}")
    else:
        logger.info("Step 4: Skipping speaker identification (--skip-identify)")
    
    # ═══════════════════════════════════════════════════════════════════
    # PREVIEW: Generate and save markdown
    # ═══════════════════════════════════════════════════════════════════
    logger.info("Step 5: Generating preview")
    
    # Print summary to console
    print_preview_summary(
        video_data=video_data,
        transcription_result=transcription_result,
        diarization_segments=segments,
        identification_plan=identification_plan,
        config=config,
    )
    
    # Generate full markdown
    preview_markdown = generate_preview_markdown(
        video_data=video_data,
        transcription_result=transcription_result,
        diarization_segments=segments,
        identification_plan=identification_plan,
        config=config,
    )
    
    # Save markdown file
    preview_path = save_preview(preview_markdown, video_id, also_print=False)
    
    # Preview mode = stop here, don't save
    if config.preview:
        print(f"\n💡 Preview mode: Nothing was saved to InstantDB.")
        print(f"   Preview file: {preview_path}")
        print(f"\n   To save, run with --yes:")
        print(f"   uv run audio_ingestion.py ingest \"{config.source}\" --start-time {config.start_time} --end-time {config.end_time or 'full'} --yes")
        return
    
    # Ask for confirmation (unless --yes is passed)
    if not config.yes:
        try:
            response = input("\n💾 Save to InstantDB? [y/N] ")
            if response.lower() != 'y':
                print("❌ Cancelled. Nothing was saved.")
                print(f"   Preview file: {preview_path}")
                return
        except EOFError:
            print("❌ Non-interactive mode. Use --yes to auto-confirm.")
            return
    
    # ═══════════════════════════════════════════════════════════════════
    # SAVE: Actually write to InstantDB
    # ═══════════════════════════════════════════════════════════════════
    logger.info("Step 6: Saving to InstantDB...")
    
    if instant_client is None:
        from ingestion.instant_client import InstantClient
        instant_client = InstantClient()
    
    try:
        # Save video
        result = instant_client.transact([
            ["update", "videos", video_data]
        ])
        logger.info(f"   ✅ Video saved: {video_id}")
        
    except Exception as e:
        logger.error(f"Failed to save to InstantDB: {e}")
        return
    
    # Save identification results
    if identification_plan and not config.skip_identify and pg_client:
        try:
            from ingestion.identify import execute_plan
            execute_plan(instant_client, pg_client, identification_plan)
            logger.info(f"   ✅ Identification saved: {identification_plan.identified_count} assignments")
        except Exception as e:
            logger.warning(f"Failed to save identification: {e}")
    
    # Summary
    total_time = time.time() - start_time_global
    print(f"""
{'═' * 60}
✅ Ingestion Complete
{'═' * 60}
   Video ID: {video_id}
   Audio: {audio_path}
   Time range: {config.start_time}s - {config.end_time or 'end'}s
   Transcription: {len(transcription_result.segments)} segments
   Diarization: {len(segments)} segments
   Identification: {identification_plan.identified_count if identification_plan else 'skipped'}
   Total time: {total_time:.1f}s
   Preview: {preview_path}
{'═' * 60}
""")


def run_legacy_diarize(config: IngestionConfig) -> None:
    """
    Run legacy diarization workflow (backward compatibility).
    This handles the old --identify and --append-to flags.
    """
    # Check services  
    check_services(require_instant_server=True, require_postgres=True)
    
    logger.info(f"Processing clip: {config.clip_path}")
    
    if not config.clip_path.exists():
        logger.error(f"Clip not found: {config.clip_path}")
        return

    # Metadata collection
    git_info = get_git_info()
    start_time_global = time.time()
    
    # 1. Transcription
    logger.info("Starting transcription...")
    transcription_start = time.time()
    
    transcription_result = _get_or_create_transcription(config.clip_path)
        
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
        from ingestion.report import generate_report
        generate_report(config, transcription_result.text, segments, stats, git_info)
        
        # Note: manifest.json is no longer supported
        # Data is now saved to InstantDB
        logger.info("Results saved. Note: manifest.json is deprecated, use InstantDB.")
    else:
        import tempfile
        logger.info("Dry run: Skipping output generation.")
        
        # Construct metadata
        metadata = {
            "command": f"python {' '.join(sys.argv)}",
            "cwd": os.getcwd(),
            "config": config.model_dump() if hasattr(config, 'model_dump') else config.dict()
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


def _print_save_preview(
    video_data: dict,
    transcription_result: TranscriptionResult,
    diarization_segments: list,
    identification_plan,
    config: IngestConfig,
) -> None:
    """Print a preview of exactly what will be saved to InstantDB."""
    print("\n" + "═" * 72)
    print("📋 PREVIEW: What will be saved to InstantDB")
    print("═" * 72)
    
    # Video entity
    print(f"""
┌─ Video ─────────────────────────────────────────────────────────────┐
│  id: {video_data['id']}
│  title: {video_data['title']}
│  filepath: {video_data['filepath'][:50]}...
│  source_url: {video_data.get('source_url') or '(none)'}
└─────────────────────────────────────────────────────────────────────┘
""")
    
    # Transcription summary
    word_count = sum(len(seg.words) for seg in transcription_result.segments)
    print(f"""
┌─ Transcription ─────────────────────────────────────────────────────┐
│  Segments: {len(transcription_result.segments)}
│  Words: {word_count}
│  Language: {transcription_result.language}
│  
│  Sample (first 3 segments):""")
    
    for seg in transcription_result.segments[:3]:
        text_preview = seg.text[:60] + "..." if len(seg.text) > 60 else seg.text
        print(f"│    [{seg.start:.1f}s-{seg.end:.1f}s] {text_preview}")
    
    if len(transcription_result.segments) > 3:
        print(f"│    ... and {len(transcription_result.segments) - 3} more segments")
    print("└─────────────────────────────────────────────────────────────────────┘\n")
    
    # Diarization summary
    speaker_labels = set(seg.get('speaker', 'UNKNOWN') for seg in diarization_segments)
    print(f"""
┌─ Diarization ───────────────────────────────────────────────────────┐
│  Segments: {len(diarization_segments)}
│  Unique speaker labels: {len(speaker_labels)} ({', '.join(sorted(speaker_labels)[:5])})
│  
│  Sample (first 5 segments):""")
    
    for seg in diarization_segments[:5]:
        print(f"│    [{seg.get('start', 0):.1f}s-{seg.get('end', 0):.1f}s] {seg.get('speaker', 'UNKNOWN')}: {seg.get('text', '')[:40]}...")
    
    if len(diarization_segments) > 5:
        print(f"│    ... and {len(diarization_segments) - 5} more segments")
    print("└─────────────────────────────────────────────────────────────────────┘\n")
    
    # Identification summary (if run)
    if identification_plan:
        from collections import Counter
        speaker_counts = Counter(
            r.identified_speaker for r in identification_plan.results 
            if r.status == "identified" and r.identified_speaker
        )
        
        print(f"""
┌─ Speaker Identification ────────────────────────────────────────────┐
│  Total processed: {len(identification_plan.results)}
│  ✅ Identified: {identification_plan.identified_count}
│  ❓ Unknown: {identification_plan.unknown_count}
│  ⏭️  Skipped: {identification_plan.skipped_count}
│  
│  Identifications by speaker:""")
        
        for speaker, count in speaker_counts.most_common(5):
            print(f"│    • {speaker}: {count} segments")
        
        if len(speaker_counts) > 5:
            print(f"│    ... and {len(speaker_counts) - 5} more speakers")
        print("└─────────────────────────────────────────────────────────────────────┘\n")
    elif config.skip_identify:
        print("""
┌─ Speaker Identification ────────────────────────────────────────────┐
│  ⏭️  SKIPPED (--skip-identify flag)
└─────────────────────────────────────────────────────────────────────┘
""")
    
    print("═" * 72)


def _dict_to_transcription_result(data: dict) -> TranscriptionResult:
    """
    Convert a cached dict back to a TranscriptionResult object.
    
    Args:
        data: Dict from cache with text, segments, language
        
    Returns:
        TranscriptionResult object
    """
    segments = []
    for s in data.get('segments', []):
        words = [Word(**w) for w in s.get('words', [])]
        segments.append(Segment(
            start=s['start'],
            end=s['end'],
            text=s['text'],
            words=words,
            speaker=s.get('speaker', 'UNKNOWN')
        ))
    
    return TranscriptionResult(
        text=data.get('text', ''),
        segments=segments,
        language=data.get('language', 'en')
    )


def _get_or_create_transcription(
    audio_path: Path,
    start_time: float = 0,
    end_time: float = None,
) -> TranscriptionResult:
    """
    Get transcription from cache or create new one.
    
    Args:
        audio_path: Path to audio file
        start_time: Start time in seconds
        end_time: End time in seconds (None = full file)
        
    Returns:
        TranscriptionResult object
    """
    # Caching logic
    cache_dir = Path(__file__).parent / "data/cache/transcriptions"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Include time range in cache key if specified
    cache_key = audio_path.stem
    if start_time > 0 or end_time is not None:
        cache_key = f"{audio_path.stem}_{int(start_time)}_{int(end_time) if end_time else 'end'}"
    cache_file = cache_dir / f"{cache_key}.json"
    
    if cache_file.exists():
        logger.info(f"Loading transcription from cache: {cache_file}")
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                # Reconstruct Pydantic models
                segments = []
                for s in data['segments']:
                    words = [Word(**w) for w in s.get('words', [])]
                    segments.append(Segment(
                        start=s['start'],
                        end=s['end'],
                        text=s['text'],
                        words=words,
                        speaker=s.get('speaker', 'UNKNOWN')
                    ))
                return TranscriptionResult(
                    text=data['text'],
                    segments=segments,
                    language=data.get('language', 'en')
                )
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}. Re-running transcription.")
    
    # Run transcription
    try:
        result = transcribe(
            str(audio_path),
            start_time=start_time if start_time > 0 else None,
            end_time=end_time,
        )
        
        # Save to cache
        with open(cache_file, 'w') as f:
            data = result.model_dump() if hasattr(result, 'model_dump') else result.dict()
            json.dump(data, f, indent=2)
        logger.info(f"Saved transcription to cache: {cache_file}")
        
        return result
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise


def main():
    config = parse_args()
    
    if hasattr(config, 'verbose') and config.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Route to appropriate handler
    if isinstance(config, ServerConfig):
        run_server(config)
    elif isinstance(config, DownloadConfig):
        download_video(config)
    elif isinstance(config, TranscribeConfig):
        run_transcribe(config)
    elif isinstance(config, DiarizeConfig):
        run_diarize(config)
    elif isinstance(config, IdentifyConfig):
        run_identify(config)
    elif isinstance(config, IngestConfig):
        run_ingest(config)
    elif isinstance(config, IngestionConfig):
        # Legacy diarize command
        run_legacy_diarize(config)
    else:
        logger.error(f"Unknown config type: {type(config)}")


if __name__ == "__main__":
    main()
