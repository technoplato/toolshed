# 📋 Handoff Summary: Embedding Extraction & Audio Path Resolution

**Date:** December 9-10, 2025
**Agent:** Claude (Architect/Code modes)
**Session Focus:** Fixing embedding extraction for whisper_identified workflow segments, ID alignment, and clustering

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

### 3. HDBSCAN Clustering Module

**File:** [`apps/speaker-diarization-benchmark/ingestion/clustering.py`](../apps/speaker-diarization-benchmark/ingestion/clustering.py)

Created a new module for clustering unknown speaker embeddings:

- Uses HDBSCAN with cosine metric and 'leaf' cluster selection method
- `cluster_embeddings()` function returns cluster assignments
- Filters to only include segments with `speaker_id IS NULL` (truly unconfirmed)

### 4. Ground Truth UI Enhancements

**File:** [`apps/speaker-diarization-benchmark/data/clips/ground_truth_instant.html`](../apps/speaker-diarization-benchmark/data/clips/ground_truth_instant.html)

Added multiple features:

- **Cluster Unknown Segments button** - Triggers HDBSCAN clustering
- **Cluster results panel** - Shows clusters with representative segments
- **Bulk confirm feature** - Confirm all segments in a cluster at once
- **One-click confirm button** - Quick confirmation for individual segments
- **Cluster badges** - Visual indicator on segments showing cluster assignment
- **Visual distinction** - Different styling for auto-identified vs user-confirmed labels

### 5. ID Alignment Migration

**File:** [`apps/speaker-diarization-benchmark/scripts/migrations/fix_embedding_external_ids.py`](../apps/speaker-diarization-benchmark/scripts/migrations/fix_embedding_external_ids.py)

Created migration script to fix PostgreSQL `external_id` values:

- Updates `external_id` to match InstantDB segment `id`
- Critical for proper linking between databases
- Successfully migrated 152 segments

---

## 🔧 Files Modified

| File                                               | Change                                                                  |
| -------------------------------------------------- | ----------------------------------------------------------------------- |
| `ingestion/ground_truth_server.py`                 | Added `_resolve_audio_path()` method, `/cluster` endpoint, bulk confirm |
| `ingestion/clustering.py`                          | **NEW** - HDBSCAN clustering module                                     |
| `scripts/batch_extract_embeddings.py`              | **NEW** - Batch embedding extraction script                             |
| `scripts/migrations/fix_embedding_external_ids.py` | **NEW** - ID alignment migration                                        |
| `data/clips/ground_truth_instant.html`             | Clustering UI, bulk confirm, one-click confirm, cluster badges          |
| `src/embeddings/pgvector_client.py`                | Added `get_embeddings_by_run()`, `bulk_update_speaker_id()`             |
| `packages/schema/instant.schema.ts`                | Updated documentation for embedding workflow                            |
| `docs/speaker-reidentification-plan.md`            | Added Phase 4 documentation                                             |
| `README.md`                                        | Added Embedding Workflow section                                        |

---

## ✅ Completed Work

### Phase 1: Embedding Extraction for All Segments

- ✅ Embeddings extracted for ALL segments (not just identified ones)
- ✅ PostgreSQL uses `speaker_id = NULL` for unknown speakers
- ✅ Audio path resolution for Docker/local environments

### Phase 2: HDBSCAN Clustering

- ✅ Clustering module with cosine metric and 'leaf' method
- ✅ `/cluster` endpoint in ground_truth_server.py
- ✅ Cluster results UI with representative segments
- ✅ Bulk confirm feature for clusters

### Phase 3: UI Enhancements

- ✅ One-click confirm button for individual segments
- ✅ Cluster badges on segments
- ✅ Visual distinction between auto-identified and user-confirmed labels
- ✅ Debug panel improvements

### Phase 4: ID Alignment

- ✅ Migration script to fix `external_id` values
- ✅ All 152 segments now properly aligned
- ✅ Documentation updated in schema and README

---

## 🚧 Potential Future Work

### Enhancements to Consider

1. **Speaker propagation** - When a user labels a segment with `speaker_label="SPEAKER_0"`, propagate that label to all other segments with the same speaker_label in the run.

2. **Confidence thresholds** - Add configurable thresholds for auto-identification confidence.

3. **Cluster persistence** - Currently clusters are computed on-demand. Could cache cluster assignments.

4. **Memory optimization** - The PyAnnote embedding model uses significant memory. Consider lazy loading or model sharing.

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

## 🔧 December 10, 2025 Updates

### Critical ID Alignment Fix

**Problem Discovered**: The `batch_extract_embeddings.py` script was generating **new UUIDs** for embeddings instead of using the **segment ID** from InstantDB:

```python
# BUG: Was generating new UUID
embedding_id = str(uuid.uuid4())
pg_client.add_embedding(external_id=embedding_id, ...)  # Wrong!

# FIXED: Use segment_id
pg_client.add_embedding(external_id=segment_id, ...)  # Correct!
```

This caused bulk confirm to fail because PostgreSQL `external_id` didn't match InstantDB segment IDs.

**Solution Applied**:

1. Fixed `batch_extract_embeddings.py` to use `segment_id` as `external_id`
2. Created migration script `fix_embedding_external_ids.py` to fix existing data
3. Ran migration on 152 segments to align IDs

### Embedding Extraction Workflow Clarification

**Key Finding**: Embeddings ARE already extracted for ALL segments in `_create_synthetic_diarization_segments()`. The design is:

- **PostgreSQL `speaker_id`**: NULL for unknown, speaker name for confirmed
- **PostgreSQL `speaker_label`**: Original diarization label (preserved)
- **No need for two tables**: Single table with NULL/non-NULL speaker_id works well

### Schema Documentation Updated

Updated [`packages/schema/instant.schema.ts`](../packages/schema/instant.schema.ts):

- Added "EMBEDDING EXTRACTION STRATEGY" section
- Added "CLUSTERING WORKFLOW" section
- Clarified `embedding_id` must equal segment `id`

Updated [`docs/speaker-reidentification-plan.md`](../apps/speaker-diarization-benchmark/docs/speaker-reidentification-plan.md):

- Added Phase 4: Embedding Workflow Improvements
- Documented ID alignment fix
- Added clustering workflow details

---

## 🔗 Related Documents

- [`docs/speaker-reidentification-plan.md`](../apps/speaker-diarization-benchmark/docs/speaker-reidentification-plan.md) - Original implementation plan
- [`docs/maturing-audio-ingestion.md`](../apps/speaker-diarization-benchmark/docs/maturing-audio-ingestion-plan.md) - Architecture evolution notes
- [`AGENTS.md`](../AGENTS.md) - Agent guidelines and documentation standards
