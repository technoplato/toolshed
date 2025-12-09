# Speaker Re-Identification System: Comprehensive Plan

**Created**: December 9, 2025
**Authors**: Claude AI, User
**Status**: Phase 1 ✅ Complete | Phase 2 ✅ Complete | Phase 3 ✅ Complete

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Key Findings](#key-findings)
4. [Current Issues](#current-issues)
5. [Implementation Plan](#implementation-plan)
6. [Technical Specifications](#technical-specifications)
7. [Docker Configuration](#docker-configuration)
8. [Testing Strategy](#testing-strategy)

---

## Executive Summary

This document outlines the comprehensive plan for improving the speaker re-identification system in the audio ingestion pipeline. The key discovery is that **Whisper's transcription produces more accurate segment boundaries than PyAnnote's diarization**, leading to a new "whisper_identified" workflow.

### Goals

1. **Verify and fix** the existing speaker relabeling and segment splitting logic
2. **Add Whisper-based segmentation** as an alternative to PyAnnote diarization
3. **Dockerize all services** with comprehensive documentation
4. **Clean up naming** for clarity and consistency

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Audio Ingestion Pipeline                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐  │
│  │   yt-dlp     │───▶│  MLX Whisper │───▶│  Transcription + Words   │  │
│  │  (download)  │    │ (transcribe) │    │  (InstantDB)             │  │
│  └──────────────┘    └──────────────┘    └──────────────────────────┘  │
│                             │                                            │
│                             ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Segmentation Strategy                          │   │
│  │  ┌─────────────────────┐    ┌─────────────────────────────────┐  │   │
│  │  │  PyAnnote Diarize   │ OR │  Whisper Segments (synthetic)   │  │   │
│  │  │  (speaker change)   │    │  (natural pauses)               │  │   │
│  │  └─────────────────────┘    └─────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                             │                                            │
│                             ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Speaker Identification                         │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐  │   │
│  │  │ PyAnnote Embed  │───▶│  PostgreSQL     │───▶│  KNN Search  │  │   │
│  │  │ (512-dim)       │    │  (pgvector)     │    │  (cosine)    │  │   │
│  │  └─────────────────┘    └─────────────────┘    └──────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                             │                                            │
│                             ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Ground Truth UI                                │   │
│  │  • View segments with audio playback                              │   │
│  │  • Assign speakers to segments                                    │   │
│  │  • Split segments with multiple speakers                          │   │
│  │  • Keyboard shortcuts for efficient labeling                      │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Service Architecture

| Service               | Port  | Technology            | Purpose                                            |
| --------------------- | ----- | --------------------- | -------------------------------------------------- |
| `instant-proxy`       | 3001  | Bun + TypeScript      | REST API proxy to InstantDB Admin SDK              |
| `ground-truth-server` | 8000  | Python + HTTP         | Ground Truth UI server, handles splits/assignments |
| `postgres`            | 5433  | PostgreSQL + pgvector | Voice embedding storage and KNN search             |
| InstantDB             | Cloud | InstantDB             | Metadata storage (videos, segments, speakers)      |

### Data Flow

```mermaid
sequenceDiagram
    participant CLI as audio_ingestion.py
    participant TS as instant-proxy:3001
    participant IDB as InstantDB Cloud
    participant PG as PostgreSQL:5433
    participant UI as Ground Truth UI
    participant PY as ground-truth-server:8000

    Note over CLI: Ingestion Pipeline
    CLI->>TS: POST /ingestion-runs
    TS->>IDB: Create video, runs
    CLI->>TS: POST /diarization-segments
    TS->>IDB: Create segments
    CLI->>PG: Store embeddings

    Note over UI: Labeling Workflow
    UI->>IDB: Subscribe to segments
    UI->>PY: POST /assign_speaker
    PY->>TS: Create speakerAssignment
    TS->>IDB: Save assignment
    PY->>PG: Update embedding speaker_id

    Note over UI: Splitting Workflow
    UI->>PY: POST /split_segment
    PY->>TS: Invalidate original, create new
    TS->>IDB: Save changes
    PY->>PG: Delete original embedding
```

---

## Key Findings

### 🔍 Finding 1: Whisper Produces Better Segmentation

**Discovery**: For the Matt and Shane's Secret Podcast episode "A DeRosa Garden" (feat. Joe DeRosa), Whisper's transcription produced **175 segments** with more natural boundaries than PyAnnote's diarization.

**Why This Matters**:

- Whisper segments are based on **natural speech pauses and punctuation**
- PyAnnote segments are based on **speaker change detection**, which can be noisy
- For podcasts with clear turn-taking, Whisper's approach often works better

**Solution**: Add `--segment-source whisper` flag to create "synthetic" diarization segments from Whisper's transcription segments.

### 🔍 Finding 2: Embedding ID Must Always Exist

**Issue**: When a segment is relabeled, the code only updates PostgreSQL if `embedding_id` exists:

```python
# server.py:476-487
if segs and pg_client:
    seg = segs[0]
    emb_id = seg.get("embedding_id")
    if emb_id:  # ⚠️ Only updates if embedding exists
        pg_client.update_speaker_id(emb_id, speaker_name)
```

**Problem**: If a segment doesn't have an embedding yet (e.g., newly created from split), the PostgreSQL update is skipped.

**Solution**:

1. Always create embeddings for segments, even if speaker is unknown
2. Use a placeholder speaker_id (e.g., the segment's speaker_label) until identified
3. When relabeling, if no embedding exists, extract and save it first

### 🔍 Finding 3: Split Segments Don't Delete Original Embedding

**Issue**: When a segment is split, the original segment's embedding remains in PostgreSQL:

```python
# server.py:332-335 - Original is invalidated
steps.append(["update", "diarizationSegments", segment_id, {
    "is_invalidated": True
}])
# ⚠️ But embedding is NOT deleted from PostgreSQL
```

**Problem**: The original embedding (which may span multiple speakers) pollutes the KNN search.

**Solution**: Delete the original embedding from PostgreSQL when splitting:

```python
if pg_client and segment.get("embedding_id"):
    pg_client.delete_embedding(segment["embedding_id"])
```

### 🔍 Finding 4: UNKNOWN Should Not Be a Speaker

**Issue**: The speakers list in InstantDB may contain "UNKNOWN" as a speaker entity.

**Solution**: Create a migration script to delete any speaker named "UNKNOWN".

---

## Current Issues

### Issue 1: Embedding Lifecycle

| Scenario            | Current Behavior           | Expected Behavior               |
| ------------------- | -------------------------- | ------------------------------- |
| New segment created | No embedding               | Extract embedding immediately   |
| Segment relabeled   | Update if embedding exists | Extract if missing, then update |
| Segment split       | Original embedding kept    | Delete original embedding       |
| Segment deleted     | Embedding deleted ✅       | Embedding deleted ✅            |

### Issue 2: Server Naming Confusion

| Current Name        | Purpose                 | Proposed Name            |
| ------------------- | ----------------------- | ------------------------ |
| `instant_server.ts` | REST proxy to InstantDB | `instant_proxy.ts`       |
| `server.py`         | Ground Truth UI server  | `ground_truth_server.py` |

### Issue 3: Partial Dockerization

| Service             | Dockerized? | Notes                     |
| ------------------- | ----------- | ------------------------- |
| PostgreSQL          | ✅ Yes      | In docker-compose.yml     |
| instant-proxy       | ✅ Yes      | Dockerfile.instant-server |
| ground-truth-server | ❌ No       | Needs Dockerfile          |

---

## Implementation Plan

### Phase 1: Verification and Fixes

#### 1.1 Create Verification Script

Create `scripts/verification/verify_speaker_workflow.py`:

```python
"""
Verify the speaker relabeling and splitting workflows work correctly.

Tests:
1. Assign speaker to segment → InstantDB updated, PostgreSQL updated
2. Split segment → Original invalidated, new segments created, embedding deleted
3. Delete segment → Segment removed, embedding deleted
"""
```

#### 1.2 Fix Embedding Deletion on Split

Modify `ground_truth_server.py:handle_split_segment()`:

```python
# After fetching segment, before invalidating
if pg_client and segment.get("embedding_id"):
    try:
        pg_client.delete_embedding(segment["embedding_id"])
        print(f"Deleted embedding {segment['embedding_id']} from PostgreSQL")
    except Exception as e:
        print(f"Warning: Failed to delete embedding: {e}")
```

#### 1.3 Fix Embedding Creation on Relabel

Modify `ground_truth_server.py:handle_assign_speaker()`:

```python
# If segment has no embedding, extract one
if not seg.get("embedding_id") and audio_path:
    try:
        embedding = Embedder.extract_embedding(audio_path, seg["start_time"], seg["end_time"])
        emb_id = str(uuid.uuid4())
        pg_client.save_embedding(
            external_id=segment_id,
            speaker_id=speaker_name,
            embedding=embedding,
            video_id=video_id,
            start_time=seg["start_time"],
            end_time=seg["end_time"],
        )
        # Update segment with embedding_id
        repo._transact([["update", "diarizationSegments", segment_id, {"embedding_id": emb_id}]])
    except Exception as e:
        print(f"Warning: Failed to extract embedding: {e}")
```

#### 1.4 Remove UNKNOWN Speaker

Create `scripts/migrations/delete_unknown_speakers.py`:

```python
"""
Delete any speaker entity named "UNKNOWN" from InstantDB.
"""
```

### Phase 2: Whisper Segmentation Support ✅ COMPLETE

#### 2.1 Add `--segment-source` Flag ✅

Modified `ingestion/args.py`:

```python
SEGMENT_SOURCE_CHOICES = ["pyannote", "whisper"]

ingest_parser.add_argument(
    "--segment-source",
    type=str,
    default="pyannote",
    choices=SEGMENT_SOURCE_CHOICES,
    help="Source for diarization segments: 'pyannote' (default) or 'whisper' (synthetic from transcription)"
)
```

Modified `ingestion/config.py`:

```python
class IngestConfig(BaseModel):
    # ...
    segment_source: str = "pyannote"  # "pyannote" or "whisper"
```

#### 2.2 Create Synthetic Diarization Segments ✅

Added `_create_synthetic_diarization_segments()` function to `audio_ingestion.py`:

```python
def _create_synthetic_diarization_segments(
    transcription_result: TranscriptionResult,
) -> tuple[list[dict], dict]:
    """
    Create synthetic diarization segments from Whisper transcription segments.
    Each segment gets speaker_label="UNKNOWN" initially.
    """
    segments = []
    for idx, seg in enumerate(transcription_result.segments):
        segments.append({
            "start": float(seg.start),
            "end": float(seg.end),
            "speaker": "UNKNOWN",
            "text": seg.text.strip(),
            "confidence": None,
            "source": "whisper_transcription",
            "transcription_segment_index": idx,
        })

    stats = {
        "segment_count": len(segments),
        "total_duration": sum(s["end"] - s["start"] for s in segments),
        "source": "whisper_transcription",
        "workflow": "whisper_identified",
    }
    return segments, stats
```

Modified `run_ingest()` Step 3 to branch based on `config.segment_source`:

```python
if config.segment_source == "whisper":
    workflow_name = "whisper_identified"
    segments, stats = _create_synthetic_diarization_segments(transcription_result)
else:
    workflow_name = config.workflow
    segments, stats = workflow.run(sliced_audio, transcription_result)
```

**Usage**:

```bash
# Use Whisper transcription segments instead of PyAnnote diarization
uv run audio_ingestion.py ingest "https://youtube.com/..." --segment-source whisper --end-time 240

# Compare with PyAnnote diarization (default)
uv run audio_ingestion.py ingest "https://youtube.com/..." --segment-source pyannote --end-time 240
```

#### 2.3 Update Schema Documentation

Add to `packages/schema/instant.schema.ts` header:

```typescript
/**
 * SYNTHETIC DIARIZATION SEGMENTS (whisper_identified workflow):
 *
 * When using `--segment-source whisper`, diarization segments are created
 * synthetically from Whisper's transcription segments. This is useful when
 * Whisper's natural pause detection produces better segment boundaries than
 * PyAnnote's speaker change detection.
 *
 * Characteristics:
 * - speaker_label = "UNKNOWN" (no speaker detection from Whisper)
 * - workflow = "whisper_identified" in the parent diarizationRun
 * - Segments align with transcription segments (same boundaries)
 *
 * Discovered: For the MSSP episode "A DeRosa Garden" (feat. Joe DeRosa),
 * Whisper produced 175 segments with more natural boundaries than PyAnnote.
 */
```

### Phase 3: Dockerization and Cleanup ✅ COMPLETE

#### 3.1 Rename Files ✅

| Old Path                      | New Path                           | Status |
| ----------------------------- | ---------------------------------- | ------ |
| `ingestion/server.py`         | `ingestion/ground_truth_server.py` | ✅     |
| `ingestion/instant_server.ts` | `ingestion/instant_proxy.ts`       | ✅     |
| `Dockerfile.instant-server`   | `Dockerfile.instant-proxy`         | ✅     |

All imports and references updated in:

- `audio_ingestion.py`
- `instant_client.py`
- `delete_unknown_speakers.py`
- `README.md`
- `start.sh`

#### 3.2 Create Ground Truth Server Dockerfile ✅

Create `Dockerfile.ground-truth-server`:

```dockerfile
# =============================================================================
# DOCKERFILE: Ground Truth Server (Python)
# =============================================================================
#
# HOW:
#   # Build and run via docker compose (recommended)
#   docker compose up -d ground-truth-server
#
#   # Build standalone
#   docker build -f Dockerfile.ground-truth-server -t ground-truth-server ../..
#
#   # Run standalone
#   docker run -p 8000:8000 \
#     -e INSTANT_APP_ID=your-app-id \
#     -e INSTANT_ADMIN_SECRET=your-secret \
#     -e POSTGRES_DSN=postgresql://... \
#     -v /path/to/audio:/data \
#     ground-truth-server
#
#   [Inputs]
#   - INSTANT_APP_ID (env): Required for InstantDB connection
#   - INSTANT_ADMIN_SECRET (env): Required for InstantDB admin access
#   - POSTGRES_DSN (env): PostgreSQL connection string for embeddings
#   - PORT (env): Server port (default: 8000)
#
#   [Outputs]
#   - HTTP server on localhost:{PORT}
#   - Serves Ground Truth UI at /data/clips/ground_truth_instant.html
#
#   [Side Effects]
#   - Reads/writes to InstantDB via instant-proxy
#   - Reads/writes to PostgreSQL for embeddings
#   - Serves audio files for playback
#
# WHO:
#   Claude AI, User
#   (Context: Ground Truth labeling UI server)
#
# WHAT:
#   Python HTTP server that:
#   1. Serves the Ground Truth labeling UI (HTML/JS)
#   2. Handles speaker assignment requests
#   3. Handles segment splitting requests
#   4. Serves audio files with HTTP Range support for seeking
#
# WHEN:
#   2025-12-09
#
# WHERE:
#   apps/speaker-diarization-benchmark/Dockerfile.ground-truth-server
#
# WHY:
#   Containerizing the server ensures:
#   - Consistent Python environment with all dependencies
#   - Easy deployment alongside PostgreSQL and instant-proxy
#   - Volume mounting for audio file access
#   - Healthchecks and restart policies via Docker
# =============================================================================

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install uv

# Copy project files
COPY apps/speaker-diarization-benchmark/pyproject.toml ./
COPY apps/speaker-diarization-benchmark/ingestion ./ingestion
COPY apps/speaker-diarization-benchmark/src ./src
COPY apps/speaker-diarization-benchmark/data ./data

# Install dependencies
RUN uv pip install --system -e .

# Environment variables
ENV PORT=8000
ENV INSTANT_APP_ID=""
ENV INSTANT_ADMIN_SECRET=""
ENV POSTGRES_DSN=""

EXPOSE 8000

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=30s \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the server
CMD ["python", "-m", "ingestion.ground_truth_server", "--port", "8000"]
```

#### 3.3 Update Docker Compose ✅

Update `docker-compose.yml`:

```yaml
# =============================================================================
# DOCKER COMPOSE: Speaker Diarization Benchmark Services
# =============================================================================
#
# HOW:
#   # Start all services
#   docker compose up -d
#
#   # Start specific service
#   docker compose up -d postgres instant-proxy ground-truth-server
#
#   # View logs
#   docker compose logs -f
#
#   # Stop all services
#   docker compose down
#
#   [Required Environment Variables]
#   Create a .env file with:
#   - INSTANT_APP_ID: Your InstantDB app ID
#   - INSTANT_ADMIN_SECRET: Your InstantDB admin secret
#   - HF_TOKEN: HuggingFace token for PyAnnote models
#
# WHO:
#   Claude AI, User
#
# WHAT:
#   Docker Compose configuration for the speaker diarization benchmark system.
#   Includes PostgreSQL (pgvector), InstantDB proxy, and Ground Truth server.
#
# WHEN:
#   2025-12-09
#
# WHERE:
#   apps/speaker-diarization-benchmark/docker-compose.yml
#
# WHY:
#   Provides a complete, reproducible development environment with:
#   - PostgreSQL with pgvector for embedding storage
#   - TypeScript proxy for InstantDB Admin SDK
#   - Python server for Ground Truth UI
#   - Proper networking and health checks
# =============================================================================

version: "3.8"

services:
  # ===========================================================================
  # PostgreSQL with pgvector
  # ===========================================================================
  # Stores voice embeddings (512-dimensional vectors) for speaker identification.
  # Uses IVFFlat index for efficient KNN search.
  postgres:
    image: pgvector/pgvector:pg16
    container_name: speaker-embeddings-db
    environment:
      POSTGRES_USER: diarization
      POSTGRES_PASSWORD: diarization_dev
      POSTGRES_DB: speaker_embeddings
    ports:
      - "5433:5432" # Map to 5433 to avoid conflicts with local postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U diarization -d speaker_embeddings"]
      interval: 5s
      timeout: 5s
      retries: 5

  # ===========================================================================
  # InstantDB Proxy (TypeScript)
  # ===========================================================================
  # REST API that wraps InstantDB Admin SDK.
  # Python scripts call this to interact with InstantDB.
  instant-proxy:
    build:
      context: ../..
      dockerfile: apps/speaker-diarization-benchmark/Dockerfile.instant-proxy
    container_name: instant-proxy
    environment:
      - INSTANT_APP_ID=${INSTANT_APP_ID}
      - INSTANT_ADMIN_SECRET=${INSTANT_ADMIN_SECRET}
      - PORT=3001
    ports:
      - "3001:3001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 10s

  # ===========================================================================
  # Ground Truth Server (Python)
  # ===========================================================================
  # Serves the Ground Truth labeling UI and handles speaker assignments.
  ground-truth-server:
    build:
      context: ../..
      dockerfile: apps/speaker-diarization-benchmark/Dockerfile.ground-truth-server
    container_name: ground-truth-server
    environment:
      - INSTANT_APP_ID=${INSTANT_APP_ID}
      - INSTANT_ADMIN_SECRET=${INSTANT_ADMIN_SECRET}
      - POSTGRES_DSN=postgresql://diarization:diarization_dev@postgres:5432/speaker_embeddings
      - HF_TOKEN=${HF_TOKEN}
      - PORT=8000
    ports:
      - "8000:8000"
    volumes:
      # Mount audio files for playback
      - ./data:/app/data
    depends_on:
      postgres:
        condition: service_healthy
      instant-proxy:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s

volumes:
  postgres_data:
```

---

## Technical Specifications

### Embedding Lifecycle

```mermaid
stateDiagram-v2
    [*] --> NoEmbedding: Segment created
    NoEmbedding --> HasEmbedding: Extract embedding
    HasEmbedding --> HasEmbedding: Relabel speaker
    HasEmbedding --> Deleted: Split segment
    HasEmbedding --> Deleted: Delete segment
    Deleted --> [*]

    note right of NoEmbedding
        speaker_label = "SPEAKER_X" or "UNKNOWN"
        embedding_id = NULL
    end note

    note right of HasEmbedding
        embedding_id = UUID
        PostgreSQL has embedding
    end note
```

### Speaker Assignment Flow

```mermaid
flowchart TD
    A[User clicks speaker label] --> B{Has embedding?}
    B -->|Yes| C[Update PostgreSQL speaker_id]
    B -->|No| D[Extract embedding from audio]
    D --> E[Save to PostgreSQL]
    E --> F[Update segment embedding_id]
    F --> C
    C --> G[Create SpeakerAssignment in InstantDB]
    G --> H[Link to Speaker entity]
```

### Segment Split Flow

```mermaid
flowchart TD
    A[User splits segment] --> B[Calculate split times from text]
    B --> C{Has embedding?}
    C -->|Yes| D[Delete embedding from PostgreSQL]
    C -->|No| E[Skip deletion]
    D --> F[Mark original is_invalidated=true]
    E --> F
    F --> G[Create SegmentSplit record]
    G --> H[Create new segments with SPLIT_X labels]
    H --> I[Link new segments to run]
    I --> J[Background: Extract embeddings for new segments]
```

---

## Docker Configuration

### Environment Variables

Create `.env` file:

```bash
# =============================================================================
# Environment Variables for Speaker Diarization Benchmark
# =============================================================================

# InstantDB Configuration
INSTANT_APP_ID=your-app-id-here
INSTANT_ADMIN_SECRET=your-admin-secret-here

# HuggingFace Token (for PyAnnote models)
HF_TOKEN=your-huggingface-token-here

# PostgreSQL (optional - defaults work for docker-compose)
# SPEAKER_DB_DSN=postgresql://diarization:diarization_dev@localhost:5433/speaker_embeddings
```

### Quick Start

```bash
# 1. Navigate to the app directory
cd apps/speaker-diarization-benchmark

# 2. Copy and configure environment
cp ../../.env.example .env
# Edit .env with your credentials

# 3. Start all services
docker compose up -d

# 4. Check health
docker compose ps
curl http://localhost:3001/health  # instant-proxy
curl http://localhost:8000/health  # ground-truth-server

# 5. Open Ground Truth UI
open http://localhost:8000/data/clips/ground_truth_instant.html
```

---

## Testing Strategy

### Unit Tests

1. **Embedding extraction**: Verify PyAnnote produces 512-dim vectors
2. **KNN search**: Verify cosine distance calculation
3. **Cache invalidation**: Verify cache key changes when embeddings change

### Integration Tests

1. **Speaker assignment flow**:
   - Assign speaker → Check InstantDB → Check PostgreSQL
2. **Segment split flow**:
   - Split segment → Check original invalidated → Check new segments → Check embedding deleted

3. **Whisper segmentation**:
   - Ingest with `--segment-source whisper` → Verify segments match transcription

### Manual Testing Checklist

- [ ] Assign speaker to segment in UI
- [ ] Verify speaker appears in autocomplete
- [ ] Split segment with multiple speakers
- [ ] Verify new segments have SPLIT_X labels
- [ ] Play audio and verify seeking works
- [ ] Navigate with keyboard shortcuts

---

## Appendix: File Changes Summary

| File                                              | Action | Description                          |
| ------------------------------------------------- | ------ | ------------------------------------ |
| `ingestion/server.py`                             | Rename | → `ground_truth_server.py`           |
| `ingestion/instant_server.ts`                     | Rename | → `instant_proxy.ts`                 |
| `Dockerfile.instant-server`                       | Rename | → `Dockerfile.instant-proxy`         |
| `Dockerfile.ground-truth-server`                  | Create | New Dockerfile for Python server     |
| `docker-compose.yml`                              | Update | Add ground-truth-server service      |
| `ingestion/args.py`                               | Update | Add `--segment-source` flag          |
| `audio_ingestion.py`                              | Update | Support whisper segmentation         |
| `packages/schema/instant.schema.ts`               | Update | Add synthetic segments documentation |
| `scripts/migrations/delete_unknown_speakers.py`   | Create | Remove UNKNOWN speaker               |
| `scripts/verification/verify_speaker_workflow.py` | Create | Verification tests                   |
