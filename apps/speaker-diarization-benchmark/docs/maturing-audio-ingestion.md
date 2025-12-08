# Maturing and Finalizing `audio_ingestion.py`

## Overview

This document captures the requirements for modernizing the `audio_ingestion.py` CLI to become the single entry point for the speaker diarization benchmark workflow. The goal is to move completely away from `manifest.json` to InstantDB, provide excellent dry-run output, and make the CLI self-documenting.

---

## Key Principles

1. **InstantDB is the source of truth** - No more manifest.json
2. **Dry-run by default** - Show what will happen before doing it
3. **Self-documenting** - Dry-run output explains HOW and WHERE each step works
4. **Full command output** - Always show the exact command to run
5. **Health checks first** - Verify services before starting

---

## Service Health Checks

At the start of any command that requires services, run health checks:

```python
def check_services():
    """Check that required services are running."""
    issues = []
    
    # Check instant-server
    try:
        resp = requests.get("http://localhost:3001/health", timeout=2)
        if resp.status_code != 200:
            issues.append("instant-server unhealthy")
    except requests.exceptions.ConnectionError:
        issues.append("instant-server not running (port 3001)")
    
    # Check PostgreSQL
    try:
        # Quick connection test
        import psycopg
        conn = psycopg.connect("postgresql://diarization:diarization_dev@localhost:5433/speaker_embeddings", connect_timeout=2)
        conn.close()
    except Exception as e:
        issues.append(f"PostgreSQL not running (port 5433): {e}")
    
    if issues:
        print("❌ Service Health Check Failed:")
        for issue in issues:
            print(f"   - {issue}")
        print()
        print("Please start the services:")
        print("   cd apps/speaker-diarization-benchmark")
        print("   ./start.sh")
        print()
        
        # Offer to start automatically
        response = input("Would you like me to start them now? [y/N] ")
        if response.lower() == 'y':
            import subprocess
            subprocess.run(["./start.sh"], cwd=Path(__file__).parent)
            # Re-check
            return check_services()
        else:
            sys.exit(1)
    
    return True
```

---

## CLI Subcommand Structure

### 1. `download` - Download video from URL

```bash
uv run audio_ingestion.py download <URL> [options]
```

**Arguments:**
| Flag | Default | Description |
|------|---------|-------------|
| `URL` | required | Video URL (YouTube, TikTok, etc.) |
| `--output-dir` | `data/clips` | Directory to save downloaded file |
| `--format` | `wav` | Output format (wav, mp3, etc.) |
| `--dry-run` | false | Show what would happen |

**Implementation:**
- File: `ingestion/download.py`
- Uses: `yt-dlp` library
- Saves: `{output_dir}/{video_id}.{format}`

### 2. `transcribe` - Transcribe audio with word timestamps

```bash
uv run audio_ingestion.py transcribe <audio_path> [options]
```

**Arguments:**
| Flag | Default | Description |
|------|---------|-------------|
| `audio_path` | required | Path to audio file |
| `--start-time` | 0 | Start time in seconds |
| `--end-time` | None | End time in seconds (None = full file) |
| `--runner` | `mlx-whisper` | Transcription runner |
| `--model` | `mlx-community/whisper-turbo` | Model to use |
| `--dry-run` | false | Show what would happen |

**Why MLX Whisper Turbo?**
- Fastest inference on Apple Silicon (M1/M2/M3)
- Word-level timestamps out of the box
- `mlx-community/whisper-turbo` is distilled for speed

**Implementation:**
- File: `transcribe.py`
- Cache: `data/cache/transcriptions/{audio_stem}.json`

### 3. `diarize` - Run speaker diarization

```bash
uv run audio_ingestion.py diarize <audio_path> [options]
```

**Arguments:**
| Flag | Default | Description |
|------|---------|-------------|
| `audio_path` | required | Path to audio file |
| `--start-time` | 0 | Start time in seconds |
| `--end-time` | None | End time in seconds |
| `--workflow` | `pyannote-local` | Diarization workflow |
| `--pipeline` | `pyannote/speaker-diarization-3.1` | PyAnnote pipeline |
| `--dry-run` | false | Show what would happen |

**Why pyannote-local?**
- Runs entirely on local hardware
- No API costs or rate limits
- Full control over model parameters

**Implementation:**
- File: `ingestion/workflows/local/pyannote_local.py`
- Outputs: DiarizationSegments to InstantDB

### 4. `identify` - Identify speakers via KNN

```bash
uv run audio_ingestion.py identify <video_id> [options]
```

**Arguments:**
| Flag | Default | Description |
|------|---------|-------------|
| `video_id` | required | InstantDB video UUID |
| `--start-time` | 0 | Start time in seconds |
| `--end-time` | None | End time in seconds |
| `--threshold` | 0.5 | KNN distance threshold |
| `--top-k` | 5 | Number of nearest neighbors |
| `--execute` | false | Actually save (default is dry-run) |

**Implementation:**
- File: `scripts/one_off/identify_speakers.py`
- Uses: PostgreSQL pgvector for KNN search
- Outputs: SpeakerAssignment records to InstantDB

### 5. `ingest` - Full pipeline (composite command)

```bash
uv run audio_ingestion.py ingest <URL_or_path> [options]
```

**This command runs the full pipeline:**
1. Download (if URL provided)
2. Transcribe
3. Diarize  
4. Identify (included by default)
5. Save to InstantDB

**Arguments:**
| Flag | Default | Description |
|------|---------|-------------|
| `URL_or_path` | required | Video URL or local audio path |
| `--start-time` | 0 | Start time in seconds |
| `--end-time` | None | End time in seconds |
| `--title` | auto | Video title for InstantDB |
| `--skip-identify` | false | Skip identification step |
| `--dry-run` | false | Show what would happen |

**Note:** `ingest` runs identification by default. Use `--skip-identify` to skip it.

---

## Dry-Run Output Format

The dry-run output should be comprehensive and self-documenting:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 DRY RUN: Audio Ingestion Pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📥 Step 1: Download
───────────────────
   URL: https://www.youtube.com/watch?v=jAlKYYr1bpY
   Output: data/clips/jAlKYYr1bpY.wav
   Status: ✅ Already exists (766 MB)
   
   📁 Implementation: ingestion/download.py
   🔧 Uses: yt-dlp to download and extract audio
   
   To customize:
     --output-dir <path>    Change download directory
     --format <fmt>         Change output format (wav, mp3)
     --force                Re-download even if exists

📝 Step 2: Transcribe
─────────────────────
   Audio: data/clips/jAlKYYr1bpY.wav
   Time range: 0s - 240s
   Runner: mlx-whisper
   Model: mlx-community/whisper-turbo
   Cache: ✅ Using cached transcription
   
   📁 Implementation: transcribe.py
   🔧 Uses: MLX Whisper for fast Apple Silicon inference
   💾 Cache: data/cache/transcriptions/jAlKYYr1bpY.json
   
   Why MLX Whisper Turbo?
   • Fastest inference on Apple Silicon (M1/M2/M3)
   • Native word-level timestamps
   • Distilled model optimized for speed
   
   To customize:
     --start-time <sec>     Start time in seconds
     --end-time <sec>       End time in seconds
     --runner <name>        Change transcription runner
     --model <name>         Change model (e.g., whisper-large-v3)
     --no-cache             Force re-transcription

🎙️ Step 3: Diarize
──────────────────
   Workflow: pyannote-local
   Pipeline: pyannote/speaker-diarization-3.1
   Time range: 0s - 240s
   Expected segments: ~50-100 (estimated)
   
   📁 Implementation: ingestion/workflows/local/pyannote_local.py
   🔧 Uses: PyAnnote Audio for speaker segmentation
   
   Why pyannote-local?
   • Runs entirely on local hardware (no API costs)
   • Full control over model parameters
   • Consistent results across runs
   
   To customize:
     --workflow <name>      Change workflow (pyannote-local, pyannote-api)
     --pipeline <name>      Change PyAnnote pipeline version
     --min-speakers <n>     Minimum expected speakers
     --max-speakers <n>     Maximum expected speakers

🔍 Step 4: Identify
───────────────────
   Method: KNN search (PostgreSQL pgvector)
   Threshold: 0.5 (cosine distance)
   Top-K: 5 nearest neighbors
   Known speakers: 207 embeddings across 6 speakers
     • Shane Gillis: 105 embeddings
     • Matt McCusker: 66 embeddings
     • Joe DeRosa: 14 embeddings
     • Phil Gillis: 10 embeddings
     • MSSP Theme Music: 1 embedding
   
   📁 Implementation: scripts/one_off/identify_speakers.py
   🔧 Uses: pgvector for fast KNN search
   💾 Cache: data/cache/identify/{hash}.json
   
   Why KNN identification?
   • Compares voice embeddings to known speakers
   • Sub-second search across 200+ embeddings
   • Threshold controls confidence level
   
   To customize:
     --threshold <float>    Distance threshold (lower = stricter)
     --top-k <int>          Number of nearest neighbors
     --skip-identify        Skip this step entirely

💾 Step 5: Save to InstantDB
────────────────────────────
   Will create:
     • 1 Video entity
     • 1 TranscriptionRun with ~600 words
     • 1 DiarizationRun with ~80 segments
     • ~80 SpeakerAssignment records
   
   📁 Implementation: ingestion/instant_client.py → instant_server.ts
   🔧 Uses: TypeScript server wrapping InstantDB Admin SDK
   
   Why InstantDB?
   • Real-time sync to UI (WebSocket)
   • Official TypeScript SDK (reliable)
   • Schema validation and relationships

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 To execute this pipeline, run:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

uv run audio_ingestion.py ingest \
  "https://www.youtube.com/watch?v=jAlKYYr1bpY" \
  --start-time 0 \
  --end-time 240 \
  --title "Ep 569 - A Derosa Garden (feat. Joe Derosa)"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Files to Modify

### 1. `audio_ingestion.py` - Main entry point

**Changes:**
- Add service health checks at startup
- Remove all `manifest.json` references
- Update docstring to reflect new workflow
- Add `transcribe`, `identify`, and `ingest` subcommands
- Implement dry-run output format

### 2. `ingestion/args.py` - Argument parsing

**Changes:**
- Add `--start-time` and `--end-time` to all subcommands
- Add `transcribe` subcommand
- Add `identify` subcommand
- Add `ingest` subcommand
- Rename `--model` to clarify runner vs model
- Add `--skip-identify` flag to ingest

### 3. `ingestion/config.py` - Configuration models

**Changes:**
- Add `TranscribeConfig`
- Add `IdentifyConfig`
- Add `IngestConfig`
- Add `start_time` and `end_time` to all configs

### 4. Delete/Deprecate

- `ingestion/manifest.py` - DELETE
- Remove `update_manifest()` calls from all files
- Remove manifest.json references from documentation

### 5. `pyproject.toml` - Dependencies

**Changes:**
```toml
"pyannote.audio>=4.0.0",  # Upgrade from 3.x
```

---

## Implementation Notes

### Time Range Handling

For `--start-time` and `--end-time`:
- Apply at transcription level (slice audio or filter results)
- Apply at diarization level (filter segments)
- Apply at identification level (filter segments to process)

### Caching Strategy

- Transcription: Cache by audio file stem + model + time range hash
- Diarization: Cache by audio file stem + workflow + time range hash
- Identification: Cache by video_id + time range + embedding count (auto-invalidate)

### Error Handling

Each step should:
1. Check prerequisites
2. Show clear error message if failed
3. Suggest how to fix
4. Exit gracefully (don't leave partial state)

---

## Test Command for First 240s

Once implemented, the command to process the first 4 minutes of Joe DeRosa episode:

```bash
cd apps/speaker-diarization-benchmark

# Ensure services are running
./start.sh

# Run full pipeline
uv run audio_ingestion.py ingest \
  data/clips/jAlKYYr1bpY.wav \
  --start-time 0 \
  --end-time 240 \
  --title "Ep 569 - A Derosa Garden (feat. Joe Derosa)"
```

Or with dry-run first:

```bash
uv run audio_ingestion.py ingest \
  data/clips/jAlKYYr1bpY.wav \
  --start-time 0 \
  --end-time 240 \
  --dry-run
```

---

## Success Criteria

1. ✅ `manifest.json` completely removed
2. ✅ All subcommands have `--start-time` and `--end-time`
3. ✅ Dry-run shows comprehensive, self-documenting output
4. ✅ Health checks run before any operation
5. ✅ `ingest` includes identification by default
6. ✅ Full command shown at end of dry-run
7. ✅ PyAnnote upgraded to 4.0.x
8. ✅ First 240s of Joe DeRosa episode processed and viewable in UI


