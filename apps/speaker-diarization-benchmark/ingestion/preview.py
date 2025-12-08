"""
HOW:
  from ingestion.preview import generate_preview_markdown, save_preview
  
  markdown = generate_preview_markdown(
      video_data=video_data,
      transcription_result=transcription_result,
      diarization_segments=segments,
      identification_plan=plan,
      config=config,
  )
  
  filepath = save_preview(markdown, video_id)

  [Inputs]
  - Computed data from each pipeline step
  - Config used for the run

  [Outputs]
  - Markdown string showing what will be saved
  - Saved markdown file path

  [Side Effects]
  - Writes markdown file to data/cache/preview/

WHO:
  Claude AI, User
  (Context: Preview output for audio ingestion pipeline)

WHAT:
  Generates human-readable preview of what will be saved to InstantDB.
  Output is structured around the InstantDB schema entities:
  - videos
  - transcriptionConfigs, transcriptionRuns, words
  - diarizationConfigs, diarizationRuns, diarizationSegments
  - speakerAssignments

WHEN:
  2025-12-08

WHERE:
  apps/speaker-diarization-benchmark/ingestion/preview.py

WHY:
  Users need to see exactly what data will be inserted into InstantDB
  before committing. This prevents cleanup headaches from bad data.
  
  The markdown file can be reviewed offline and serves as documentation
  of what was computed.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from collections import Counter

from .config import IngestConfig


PREVIEW_DIR = Path(__file__).parent.parent / "data" / "cache" / "preview"


def generate_preview_markdown(
    video_data: Dict[str, Any],
    transcription_result: Any,  # TranscriptionResult
    diarization_segments: List[Dict[str, Any]],
    identification_plan: Optional[Any],  # IdentificationPlan
    config: IngestConfig,
    transcription_metrics: Optional[Dict[str, Any]] = None,
    diarization_metrics: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a markdown preview of what will be saved to InstantDB.
    
    Structured around the InstantDB schema entities.
    
    Args:
        video_data: Video entity data
        transcription_result: TranscriptionResult from whisper
        diarization_segments: List of diarization segments
        identification_plan: Optional identification results
        config: Pipeline configuration
        transcription_metrics: Optional dict with processing_time_seconds, peak_memory_mb, cost_usd
        diarization_metrics: Optional dict with processing_time_seconds, peak_memory_mb, cost_usd
    """
    lines = []
    now = datetime.now().isoformat()
    
    # Header
    lines.append(f"# Audio Ingestion Preview")
    lines.append(f"")
    lines.append(f"**Generated**: {now}")
    lines.append(f"**Source**: `{config.source}`")
    lines.append(f"**Time Range**: {config.start_time}s - {config.end_time or 'end'}s")
    lines.append(f"**Workflow**: {config.workflow}")
    lines.append(f"")
    
    # Run metrics summary
    if transcription_metrics or diarization_metrics:
        lines.append(f"### Run Metrics")
        lines.append(f"")
        lines.append(f"| Step | Duration | Memory | Cost | Realtime Factor |")
        lines.append(f"|------|----------|--------|------|-----------------|")
        
        input_duration = config.end_time or 0
        
        if transcription_metrics:
            proc_time = transcription_metrics.get('processing_time_seconds', 0)
            memory = transcription_metrics.get('peak_memory_mb')
            cost = transcription_metrics.get('cost_usd')
            rt_factor = f"{input_duration / proc_time:.1f}x" if proc_time > 0 else "N/A"
            lines.append(f"| Transcription | {proc_time:.2f}s | {f'{memory:.1f}MB' if memory else 'N/A'} | {f'${cost:.4f}' if cost else 'Free'} | {rt_factor} |")
        
        if diarization_metrics:
            proc_time = diarization_metrics.get('processing_time_seconds', 0)
            memory = diarization_metrics.get('peak_memory_mb')
            cost = diarization_metrics.get('cost_usd')
            rt_factor = f"{input_duration / proc_time:.1f}x" if proc_time > 0 else "N/A"
            lines.append(f"| Diarization | {proc_time:.2f}s | {f'{memory:.1f}MB' if memory else 'N/A'} | {f'${cost:.4f}' if cost else 'Free'} | {rt_factor} |")
        
        total_time = (transcription_metrics or {}).get('processing_time_seconds', 0) + (diarization_metrics or {}).get('processing_time_seconds', 0)
        total_cost = ((transcription_metrics or {}).get('cost_usd') or 0) + ((diarization_metrics or {}).get('cost_usd') or 0)
        lines.append(f"| **Total** | **{total_time:.2f}s** | - | **{f'${total_cost:.4f}' if total_cost else 'Free'}** | - |")
        lines.append(f"")
    
    lines.append(f"---")
    lines.append(f"")
    
    # =========================================================================
    # VIDEO ENTITY
    # =========================================================================
    lines.append(f"## 1. Video Entity")
    lines.append(f"")
    lines.append(f"```yaml")
    lines.append(f"# Entity: videos")
    lines.append(f"id: {video_data.get('id')}")
    lines.append(f"title: {video_data.get('title')}")
    lines.append(f"url: {video_data.get('source_url') or '(local file)'}")
    lines.append(f"filepath: {video_data.get('filepath')}")
    lines.append(f"duration: {config.end_time or '(unknown)'}")
    lines.append(f"ingested_at: {now}")
    lines.append(f"```")
    lines.append(f"")
    
    # =========================================================================
    # TRANSCRIPTION CONFIG
    # =========================================================================
    lines.append(f"## 2. Transcription Config")
    lines.append(f"")
    lines.append(f"```yaml")
    lines.append(f"# Entity: transcriptionConfigs")
    lines.append(f"model: whisper-large-v3-turbo")
    lines.append(f"tool: mlx-whisper")
    lines.append(f"language: {transcription_result.language if hasattr(transcription_result, 'language') else 'en'}")
    lines.append(f"word_timestamps: true")
    lines.append(f"```")
    lines.append(f"")
    
    # =========================================================================
    # TRANSCRIPTION RUN
    # =========================================================================
    lines.append(f"## 3. Transcription Run")
    lines.append(f"")
    
    word_count = sum(len(seg.words) for seg in transcription_result.segments) if hasattr(transcription_result, 'segments') else 0
    segment_count = len(transcription_result.segments) if hasattr(transcription_result, 'segments') else 0
    
    lines.append(f"```yaml")
    lines.append(f"# Entity: transcriptionRuns")
    lines.append(f"tool_version: mlx-whisper-0.4.x")
    lines.append(f"pipeline_script: audio_ingestion.py")
    lines.append(f"is_preferred: true")
    
    # Add metrics if available
    if transcription_metrics:
        input_dur = transcription_metrics.get('input_duration_seconds')
        proc_time = transcription_metrics.get('processing_time_seconds')
        memory = transcription_metrics.get('peak_memory_mb')
        cost = transcription_metrics.get('cost_usd')
        if input_dur:
            lines.append(f"input_duration_seconds: {input_dur}")
        if proc_time:
            lines.append(f"processing_time_seconds: {proc_time:.2f}")
        if memory:
            lines.append(f"peak_memory_mb: {memory:.1f}")
        if cost:
            lines.append(f"cost_usd: {cost:.4f}")
    
    lines.append(f"executed_at: {now}")
    lines.append(f"```")
    lines.append(f"")
    lines.append(f"**Summary**: {segment_count} segments, {word_count} words")
    lines.append(f"")
    
    # =========================================================================
    # WORDS (SAMPLE)
    # =========================================================================
    lines.append(f"## 4. Words ({word_count} total)")
    lines.append(f"")
    lines.append(f"```yaml")
    lines.append(f"# Entity: words (sample of first 10)")
    
    word_samples = []
    if hasattr(transcription_result, 'segments'):
        for seg in transcription_result.segments[:3]:
            for w in seg.words[:5]:
                word_samples.append(w)
                if len(word_samples) >= 10:
                    break
            if len(word_samples) >= 10:
                break
    
    for w in word_samples:
        lines.append(f"- text: \"{w.word if hasattr(w, 'word') else w.get('word', '')}\"")
        lines.append(f"  start_time: {w.start if hasattr(w, 'start') else w.get('start', 0):.3f}")
        lines.append(f"  end_time: {w.end if hasattr(w, 'end') else w.get('end', 0):.3f}")
        lines.append(f"  confidence: {w.probability if hasattr(w, 'probability') else w.get('probability', 0):.3f}")
    
    if word_count > 10:
        lines.append(f"# ... and {word_count - 10} more words")
    lines.append(f"```")
    lines.append(f"")
    
    # =========================================================================
    # DIARIZATION CONFIG
    # =========================================================================
    lines.append(f"## 5. Diarization Config")
    lines.append(f"")
    lines.append(f"```yaml")
    lines.append(f"# Entity: diarizationConfigs")
    lines.append(f"embedding_model: pyannote/wespeaker-voxceleb-resnet34")
    lines.append(f"tool: {config.workflow}")
    lines.append(f"clustering_method: AgglomerativeClustering")
    lines.append(f"```")
    lines.append(f"")
    
    # =========================================================================
    # DIARIZATION RUN
    # =========================================================================
    speaker_labels = set(seg.get('speaker', 'UNKNOWN') for seg in diarization_segments)
    
    lines.append(f"## 6. Diarization Run")
    lines.append(f"")
    lines.append(f"```yaml")
    lines.append(f"# Entity: diarizationRuns")
    lines.append(f"workflow: {config.workflow}")
    lines.append(f"tool_version: pyannote-audio-3.1.x")
    lines.append(f"pipeline_script: audio_ingestion.py")
    lines.append(f"is_preferred: true")
    lines.append(f"num_speakers_detected: {len(speaker_labels)}")
    
    # Add metrics if available
    if diarization_metrics:
        input_dur = diarization_metrics.get('input_duration_seconds')
        proc_time = diarization_metrics.get('processing_time_seconds')
        memory = diarization_metrics.get('peak_memory_mb')
        cost = diarization_metrics.get('cost_usd')
        if input_dur:
            lines.append(f"input_duration_seconds: {input_dur}")
        if proc_time:
            lines.append(f"processing_time_seconds: {proc_time:.2f}")
        if memory:
            lines.append(f"peak_memory_mb: {memory:.1f}")
        if cost:
            lines.append(f"cost_usd: {cost:.4f}")
    
    lines.append(f"executed_at: {now}")
    lines.append(f"```")
    lines.append(f"")
    lines.append(f"**Summary**: {len(diarization_segments)} segments, {len(speaker_labels)} unique labels ({', '.join(sorted(speaker_labels)[:5])})")
    lines.append(f"")
    
    # =========================================================================
    # DIARIZATION SEGMENTS (SAMPLE)
    # =========================================================================
    lines.append(f"## 7. Diarization Segments ({len(diarization_segments)} total)")
    lines.append(f"")
    lines.append(f"```yaml")
    lines.append(f"# Entity: diarizationSegments (sample of first 10)")
    
    for seg in diarization_segments[:10]:
        lines.append(f"- start_time: {seg.get('start', 0):.2f}")
        lines.append(f"  end_time: {seg.get('end', 0):.2f}")
        lines.append(f"  speaker_label: {seg.get('speaker', 'UNKNOWN')}")
        text_preview = seg.get('text', '')[:40]
        if text_preview:
            lines.append(f"  text_preview: \"{text_preview}...\"")
    
    if len(diarization_segments) > 10:
        lines.append(f"# ... and {len(diarization_segments) - 10} more segments")
    lines.append(f"```")
    lines.append(f"")
    
    # =========================================================================
    # SPEAKER ASSIGNMENTS
    # =========================================================================
    lines.append(f"## 8. Speaker Assignments")
    lines.append(f"")
    
    if identification_plan:
        identified = [r for r in identification_plan.results if r.status == "identified"]
        unknown = [r for r in identification_plan.results if r.status == "unknown"]
        skipped = [r for r in identification_plan.results if r.status in ("already_assigned", "skipped")]
        
        speaker_counts = Counter(
            r.identified_speaker for r in identification_plan.results 
            if r.status == "identified" and r.identified_speaker
        )
        
        lines.append(f"```yaml")
        lines.append(f"# Entity: speakerAssignments")
        lines.append(f"total_processed: {len(identification_plan.results)}")
        lines.append(f"identified: {len(identified)}")
        lines.append(f"unknown: {len(unknown)}")
        lines.append(f"skipped: {len(skipped)}")
        lines.append(f"threshold: {identification_plan.threshold}")
        lines.append(f"strategy: knn")
        lines.append(f"")
        lines.append(f"# Assignments by speaker:")
        for speaker, count in speaker_counts.most_common():
            lines.append(f"  {speaker}: {count} segments")
        lines.append(f"```")
        lines.append(f"")
        
        # Sample assignments
        lines.append(f"### Sample Assignments (first 5)")
        lines.append(f"")
        lines.append(f"```yaml")
        for r in identified[:5]:
            lines.append(f"- segment: [{r.segment_start:.1f}s - {r.segment_end:.1f}s]")
            lines.append(f"  original_label: {r.original_label}")
            lines.append(f"  identified_speaker: {r.identified_speaker}")
            lines.append(f"  distance: {r.distance:.3f}")
            lines.append(f"  source: auto_identify")
        lines.append(f"```")
    elif config.skip_identify:
        lines.append(f"*Skipped (--skip-identify flag)*")
    else:
        lines.append(f"*No identification results*")
    
    lines.append(f"")
    
    # =========================================================================
    # EXECUTION COMMAND
    # =========================================================================
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## Execute Command")
    lines.append(f"")
    lines.append(f"To save this data to InstantDB, run:")
    lines.append(f"")
    lines.append(f"```bash")
    lines.append(f"uv run audio_ingestion.py ingest \\")
    lines.append(f"  \"{config.source}\" \\")
    lines.append(f"  --start-time {config.start_time} \\")
    if config.end_time:
        lines.append(f"  --end-time {config.end_time} \\")
    lines.append(f"  --workflow {config.workflow} \\")
    lines.append(f"  --yes")
    lines.append(f"```")
    lines.append(f"")
    
    return "\n".join(lines)


def save_preview(
    markdown: str,
    video_id: str,
    also_print: bool = True,
) -> Path:
    """
    Save preview markdown to file.
    
    Args:
        markdown: The preview content
        video_id: For filename
        also_print: Whether to also print to console
        
    Returns:
        Path to the saved file
    """
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{video_id}_preview_{timestamp}.md"
    filepath = PREVIEW_DIR / filename
    
    with open(filepath, "w") as f:
        f.write(markdown)
    
    if also_print:
        print(markdown)
    
    print(f"\n📄 Preview saved to: {filepath}")
    
    return filepath


def print_preview_summary(
    video_data: Dict[str, Any],
    transcription_result: Any,
    diarization_segments: List[Dict[str, Any]],
    identification_plan: Optional[Any],
    config: IngestConfig,
) -> None:
    """Print a condensed preview summary to console."""
    print("\n" + "═" * 72)
    print("📋 PREVIEW: What will be saved to InstantDB")
    print("═" * 72)
    
    word_count = sum(len(seg.words) for seg in transcription_result.segments) if hasattr(transcription_result, 'segments') else 0
    speaker_labels = set(seg.get('speaker', 'UNKNOWN') for seg in diarization_segments)
    
    print(f"""
┌─ videos ────────────────────────────────────────────────────────────┐
│  id: {video_data.get('id')}
│  title: {video_data.get('title')}
│  filepath: {str(video_data.get('filepath', ''))[:50]}...
└─────────────────────────────────────────────────────────────────────┘

┌─ transcriptionRuns + words ─────────────────────────────────────────┐
│  Segments: {len(transcription_result.segments) if hasattr(transcription_result, 'segments') else 0}
│  Words: {word_count}
│  Tool: mlx-whisper / whisper-large-v3-turbo
└─────────────────────────────────────────────────────────────────────┘

┌─ diarizationRuns + diarizationSegments ─────────────────────────────┐
│  Segments: {len(diarization_segments)}
│  Speaker labels: {len(speaker_labels)} ({', '.join(sorted(speaker_labels)[:4])})
│  Workflow: {config.workflow}
└─────────────────────────────────────────────────────────────────────┘
""")
    
    if identification_plan:
        speaker_counts = Counter(
            r.identified_speaker for r in identification_plan.results 
            if r.status == "identified" and r.identified_speaker
        )
        
        print(f"""┌─ speakerAssignments ────────────────────────────────────────────────┐
│  ✅ Identified: {identification_plan.identified_count}
│  ❓ Unknown: {identification_plan.unknown_count}
│  ⏭️  Skipped: {identification_plan.skipped_count}
│  Threshold: {identification_plan.threshold}
│""")
        for speaker, count in speaker_counts.most_common(5):
            print(f"│    • {speaker}: {count}")
        print("└─────────────────────────────────────────────────────────────────────┘")
    elif config.skip_identify:
        print("""┌─ speakerAssignments ────────────────────────────────────────────────┐
│  ⏭️  SKIPPED (--skip-identify flag)
└─────────────────────────────────────────────────────────────────────┘""")
    
    print("\n" + "═" * 72)

