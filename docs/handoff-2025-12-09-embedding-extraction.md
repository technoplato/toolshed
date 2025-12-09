# 📋 Handoff Summary: Embedding Extraction & Audio Path Resolution

**Date:** December 9, 2025  
**Agent:** Claude (Architect/Code modes)  
**Session Focus:** Fixing embedding extraction for whisper_identified workflow segments

---

## 🎯 Session Objectives

The user has been building an audio ingestion framework for speaker diarization and recognition. This session focused on:

1. Fixing embedding extraction for segments created by the `whisper_identified` workflow
2. Resolving audio path mismatches between host and Docker container
3. Creating a batch embedding extraction script

---

## 📊 Current State

### The Problem

The `whisper_identified` diarization run (ID: `e2418a71`) has **175 segments with 0 embeddings**:

```
📊 SEGMENTS: 175 total
   With embedding_id: 0
   Without embedding_id: 175
   With speaker assignment: 34
```

**Root Causes Identified:**

1. **Synthetic segments have no embeddings**: The `_create_synthetic_diarization_segments()` function in [`audio_ingestion.py`](../apps/speaker-diarization-benchmark/audio_ingestion.py) creates segments from Whisper transcription boundaries but doesn't extract voice embeddings

2. **Identification doesn't save embeddings**: The [`identify.py`](../apps/speaker-diarization-benchmark/ingestion/identify.py) extracts embeddings during identification but intentionally doesn't save them to Postgres (to avoid polluting with UNKNOWN speakers)

3. **Background extraction fails due to path mismatch**: When a user assigns a speaker in the Ground Truth UI, the server tries to extract an embedding but fails because:
   - Audio path stored in InstantDB: `/Users/laptop/.../data/clips/jAlKYYr1bpY.wav` (host path)
   - Docker container expects: `/app/data/clips/jAlKYYr1bpY.wav`

---

## ✅ Changes Made This Session

### 1. Audio Path Resolution in Ground Truth Server

**File:** [`apps/speaker-diarization-benchmark/ingestion/ground_truth_server.py`](../apps/speaker-diarization-benchmark/ingestion/ground_truth_server.py)

Added `_resolve_audio_path()` method (lines 187-240) that:

- Checks if path exists as-is (local development)
- Tries `/app/data/clips/{filename}` (Docker container)
- Tries `data/clips/{filename}` (relative path)
- Extracts from pattern `.../data/clips/...` and tries known bases

The method is called in `_handle_embedding_update()` at line 704 before attempting embedding extraction.

Also fixed a duplicate exception handler (removed lines 759-766).

### 2. Batch Embedding Extraction Script

**File:** [`apps/speaker-diarization-benchmark/scripts/batch_extract_embeddings.py`](../apps/speaker-diarization-benchmark/scripts/batch_extract_embeddings.py)

Created a new script to batch-extract embeddings for segments without them:

```bash
cd apps/speaker-diarization-benchmark
uv run python scripts/batch_extract_embeddings.py --run-id <diarization_run_id>

# Options:
#   --limit N        Process only N segments
#   --dry-run        Show what would be done
#   --only-assigned  Only process segments with speaker assignments
#   --verbose        Enable verbose logging
```

Features:

- Queries InstantDB for segments without `embedding_id`
- Resolves audio paths for Docker/local environments
- Extracts embeddings using PyAnnote
- Saves to PostgreSQL with speaker_label
- Updates InstantDB segment with new embedding_id
- Memory-aware: processes one segment at a time

---

## 🔧 Files Modified

| File                                  | Change                                                                  |
| ------------------------------------- | ----------------------------------------------------------------------- |
| `ingestion/ground_truth_server.py`    | Added `_resolve_audio_path()` method, fixed duplicate exception handler |
| `scripts/batch_extract_embeddings.py` | **NEW** - Batch embedding extraction script                             |

---

## 🚧 Pending Work

### Immediate Next Steps

1. **Rebuild Docker container** to pick up the ground_truth_server.py changes:

   ```bash
   cd apps/speaker-diarization-benchmark
   docker compose --env-file ../../.env build ground-truth-server
   docker compose --env-file ../../.env up -d ground-truth-server
   ```

2. **Test embedding extraction** by assigning a speaker in the Ground Truth UI and checking Docker logs:

   ```bash
   docker compose logs -f ground-truth-server
   ```

3. **Run batch extraction** for segments with speaker assignments:
   ```bash
   uv run python scripts/batch_extract_embeddings.py \
     --run-id e2418a71-... \
     --only-assigned \
     --verbose
   ```

### Known Issues

1. **The batch script needs testing** - It was just created and hasn't been run yet

2. **Memory considerations** - The PyAnnote embedding model uses significant memory. The batch script processes one segment at a time, but if running in Docker, ensure the container has enough memory allocated.

3. **Speaker propagation not implemented** - When a user labels a segment with `speaker_label="SPEAKER_0"`, the system should propagate that label to all other segments with the same speaker_label in the run. This is documented in the schema but not yet implemented.

---

## 📁 Key Files Reference

### Core Pipeline

- [`audio_ingestion.py`](../apps/speaker-diarization-benchmark/audio_ingestion.py) - Main CLI entry point
- [`ingestion/ground_truth_server.py`](../apps/speaker-diarization-benchmark/ingestion/ground_truth_server.py) - Ground Truth UI server
- [`ingestion/identify.py`](../apps/speaker-diarization-benchmark/ingestion/identify.py) - Speaker identification via KNN

### Database

- [`packages/schema/instant.schema.ts`](../packages/schema/instant.schema.ts) - InstantDB schema
- [`src/embeddings/pgvector_client.py`](../apps/speaker-diarization-benchmark/src/embeddings/pgvector_client.py) - PostgreSQL/pgvector client

### UI

- [`data/clips/ground_truth_instant.html`](../apps/speaker-diarization-benchmark/data/clips/ground_truth_instant.html) - Ground Truth labeling UI

### Docker

- [`docker-compose.yml`](../apps/speaker-diarization-benchmark/docker-compose.yml) - Service definitions
- [`Dockerfile.ground-truth-server`](../apps/speaker-diarization-benchmark/Dockerfile.ground-truth-server) - Ground Truth server image

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Audio Ingestion Pipeline                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. DOWNLOAD (yt-dlp)                                           │
│     └── data/clips/{video_id}.wav                               │
│                                                                  │
│  2. TRANSCRIBE (MLX Whisper)                                    │
│     └── TranscriptionRun → Words (InstantDB)                    │
│                                                                  │
│  3. DIARIZE (PyAnnote or Whisper boundaries)                    │
│     └── DiarizationRun → DiarizationSegments (InstantDB)        │
│     └── Embeddings → PostgreSQL (pgvector)                      │
│                                                                  │
│  4. IDENTIFY (KNN search)                                       │
│     └── SpeakerAssignments (InstantDB)                          │
│                                                                  │
│  5. LABEL (Ground Truth UI)                                     │
│     └── User corrections → SpeakerAssignments                   │
│     └── Embedding extraction on assignment                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Whisper Identified Workflow

The `whisper_identified` workflow creates diarization segments from Whisper transcription boundaries instead of PyAnnote:

```
Whisper Transcription → Segments (by pause/punctuation)
                      ↓
              DiarizationSegments (synthetic)
                      ↓
              NO EMBEDDINGS (speaker unknown)
                      ↓
              User labels speaker in UI
                      ↓
              Embedding extracted & saved
```

This produces better segmentation (175 segments vs ~50 from PyAnnote) because Whisper naturally segments by speaker turns based on pauses and punctuation.

---

## 📝 Session Notes

- The user mentioned wanting a "memory-aware queue processor" for embedding extraction - the batch script is a first step but could be enhanced with proper job queuing
- The Ground Truth UI is working well for labeling but the embedding extraction was silently failing due to path issues
- Consider adding a status indicator in the UI to show when embedding extraction is in progress/complete

---

## 🔗 Related Documents

- [`docs/speaker-reidentification-plan.md`](../apps/speaker-diarization-benchmark/docs/speaker-reidentification-plan.md) - Original implementation plan
- [`docs/maturing-audio-ingestion.md`](../apps/speaker-diarization-benchmark/docs/maturing-audio-ingestion-plan.md) - Architecture evolution notes
- [`AGENTS.md`](../AGENTS.md) - Agent guidelines and documentation standards
