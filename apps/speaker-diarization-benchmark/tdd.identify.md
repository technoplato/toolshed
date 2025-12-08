# TDD: Speaker Identification Workflow

## 📋 Implementation Plan: `identify` Subcommand

### Core Principles

**1. Deferred Side Effects Pattern** (for dry-run support):
```
┌─────────────────────────────────────────────────────────────┐
│  WORKFLOW EXECUTION PATTERN                                 │
│                                                             │
│  1. COMPUTE phase: All processing, no side effects          │
│     - Extract embeddings                                    │
│     - Run KNN search                                        │
│     - Build result objects                                  │
│                                                             │
│  2. COLLECT phase: Build list of planned actions            │
│     - InstantDB transactions                                │
│     - PostgreSQL inserts                                    │
│     - File writes                                           │
│                                                             │
│  3. PREVIEW phase: Display what would happen                │
│     - Print planned speaker assignments                     │
│     - Show confidence scores                                │
│     - Preview database updates                              │
│                                                             │
│  4. EXECUTE phase: Only if --execute flag                   │
│     - Execute all collected side effects                    │
│     - Atomic where possible                                 │
└─────────────────────────────────────────────────────────────┘
```

**2. Intelligent Caching**:
- Hash: `sha256(config + clip_path + start_time + end_time)`
- Cache location: `data/cache/identify/{hash}.json`
- Contains: embedding extraction results, KNN results
- Invalidate if: config changes, audio file modified, DB embeddings updated

### Architecture Decision: TypeScript Server for InstantDB

**Pattern:**
- Python handles: Embedding extraction (pyannote), KNN search (PostgreSQL)
- TypeScript server handles: All InstantDB operations
- Communication: Python calls TypeScript server via HTTP

```
┌──────────────────────┐         ┌──────────────────────┐
│   Python Scripts     │  HTTP   │  TypeScript Server   │
│   - audio_ingestion  │ ◄─────► │  - InstantDB Admin   │
│   - embedding extract│         │  - Query/Transact    │
│   - KNN search       │         │  - Schema validation │
└──────────────────────┘         └──────────────────────┘
          │                                │
          │                                │
          ▼                                ▼
┌──────────────────────┐         ┌──────────────────────┐
│     PostgreSQL       │         │      InstantDB       │
│  (pgvector - embeds) │         │  (metadata, runs,    │
│                      │         │   segments, etc.)    │
└──────────────────────┘         └──────────────────────┘
```

### Files to Create/Modify

| File | Purpose |
|------|---------|
| `scripts/one_off/identify_speakers.py` | **Main script** - Python orchestrates identification |
| `ingestion/instant_server.ts` | **NEW** - TypeScript server for InstantDB ops |
| `ingestion/instant_client.py` | **NEW** - Python client to call TS server |
| `audio_ingestion.py` | Update docstring with workflow pattern |
| `packages/schema/instant.schema.ts` | Update `note` field to JSON type |

### CLI Design

```bash
# Dry run (default) - shows what would happen
uv run audio_ingestion.py identify \
  --video-id "20dbb029-5729-5072-8c6b-ef1f0a0cab0a" \
  --start-time 0 \
  --end-time 60

# Execute - actually saves to DB
uv run audio_ingestion.py identify \
  --video-id "20dbb029-5729-5072-8c6b-ef1f0a0cab0a" \
  --execute

# Full episode with time range
uv run audio_ingestion.py identify \
  --clip-path "data/clips/jAlKYYr1bpY.wav" \
  --start-time 0 \
  --end-time 30 \
  --threshold 0.4
```

### Data Flow

```
                    ┌──────────────────┐
                    │   Audio File     │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ Get Diarization  │ (from InstantDB or run fresh)
                    │    Segments      │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
    ┌─────────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
    │  Segment 1     │ │ Segment 2  │ │ Segment N  │
    │ [10s - 15s]    │ │[15s - 20s] │ │   ...      │
    └───────┬────────┘ └─────┬──────┘ └─────┬──────┘
            │                │              │
    ┌───────▼────────┐ ┌─────▼──────┐ ┌─────▼──────┐
    │ Extract 512d   │ │ Extract    │ │ Extract    │
    │   Embedding    │ │ Embedding  │ │ Embedding  │
    └───────┬────────┘ └─────┬──────┘ └─────┬──────┘
            │                │              │
            └────────────────┼──────────────┘
                             │
                    ┌────────▼─────────┐
                    │  PostgreSQL KNN  │
                    │   (207 known     │
                    │    embeddings)   │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Speaker Label   │
                    │  Assignments     │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
     ┌────────▼─────────┐        ┌──────────▼──────────┐
     │   DRY RUN        │        │     EXECUTE         │
     │   - Preview      │        │   - Create IDs      │
     │   - Show matches │        │   - Save to Instant │
     │   - Exit         │        │   - Update segments │
     └──────────────────┘        └─────────────────────┘
```

### InstantDB Schema Updates

**Change `note` field in `speakerAssignments` to JSON type:**

The `speakerAssignments.note` field will store identification metadata as JSON:

```typescript
{
  // Identification source info
  "method": "knn_identify",
  "script_version": "v1",
  "timestamp": "2025-12-07T...",
  
  // KNN results
  "knn_distance": 0.42,
  "top_matches": [
    {"speaker": "Shane Gillis", "distance": 0.42, "count": 8},
    {"speaker": "Matt McCusker", "distance": 0.58, "count": 2}
  ],
  
  // Config used
  "threshold": 0.5,
  "top_k": 10,
  
  // Cache info
  "cache_hit": true,
  "cache_key": "abc123..."
}
```

### Cache Auto-Invalidation

**Decision: YES - Auto-invalidate when new embeddings added**

Pros:
- Ensures identification always uses latest speaker data
- Prevents stale results if user adds new labeled segments
- Simple to implement (track embedding count or last-modified)

Cons:
- May cause unnecessary recomputation
- Could be slow if frequently adding embeddings

**Implementation:**
- Store `embedding_count` and `last_embedding_id` in cache metadata
- On cache read, quick check: `SELECT COUNT(*), MAX(id) FROM speaker_embeddings`
- If different, invalidate and recompute

### Questions Resolved

1. ✅ **TypeScript for embedding extraction?** No - Python only for embeddings
2. ✅ **Architecture:** TypeScript server for InstantDB, Python for everything else
3. ✅ **Cache invalidation:** Yes, auto-invalidate on new embeddings
4. ✅ **Identification Run entity:** No - use `note` JSON field instead

