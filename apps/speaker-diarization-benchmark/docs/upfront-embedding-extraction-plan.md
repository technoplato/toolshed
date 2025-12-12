# Upfront Embedding Extraction Plan

**Date:** December 9, 2025  
**Status:** Ready for Implementation

## Problem Statement

Currently, embeddings are extracted on-demand when a user labels a segment in the Ground Truth UI. This is slow and creates friction in the labeling workflow.

For the `whisper_identified` workflow (using `--segment-source whisper`), synthetic diarization segments are created from Whisper transcription boundaries, but **no embeddings are extracted**. This means:

1. KNN identification cannot run (no embeddings to compare)
2. When a user labels a segment, embedding extraction happens synchronously (slow)
3. The user experience is degraded

## Solution: Extract All Embeddings Upfront

### New Flow

```
INGESTION TIME (upfront, batch)
────────────────────────────────
1. Create DiarizationSegments in InstantDB
2. For EACH segment:
   a. Extract voice embedding from audio
   b. Save to PostgreSQL with:
      - external_id = segment.id
      - speaker_id = NULL  ← Don't know who yet
      - speaker_label = segment.speaker_label (e.g., "SPEAKER_0" or "UNKNOWN")
   c. Update InstantDB segment.embedding_id = external_id

CLUSTERING (on-demand, via UI button) - Phase 2
───────────────────────────────────────────────
1. Get all embeddings where speaker_id IS NULL for this run
2. Run HDBSCAN clustering
3. Display clusters in UI: "Cluster A (5 segments), Cluster B (3)..."
4. User labels one segment per cluster → propagates to all in cluster

IDENTIFICATION (optional, can run after clustering)
────────────────────────────────────────────────────
1. Query segments where speaker_id IS NULL
2. For each, run KNN search (WHERE speaker_id IS NOT NULL)
3. If match found: update speaker_id, create SpeakerAssignment

LABELING (user action)
──────────────────────
1. User selects segment, assigns speaker
2. Update PostgreSQL: speaker_id = "Shane Gillis"
3. Create SpeakerAssignment in InstantDB
4. NO embedding extraction needed - already done!
```

## Key Design Decisions

### 1. Use NULL for Unknown Speakers

Instead of "PENDING" or "UNKNOWN" strings, use `speaker_id = NULL`:

- Simpler semantics
- Easy to filter: `WHERE speaker_id IS NOT NULL`
- No confusion about string values

### 2. Single Table with Filter

Keep all embeddings in `speaker_embeddings` table. Update KNN search to filter:

```sql
WHERE speaker_id IS NOT NULL
```

### 3. HDBSCAN for Clustering

Use HDBSCAN (Hierarchical Density-Based Spatial Clustering of Applications with Noise):

- Auto-detects number of clusters
- Handles noise/outliers gracefully
- Works well with cosine distance

### 4. Whisper Synthetic Segments

When `--segment-source whisper` is passed:

1. Create synthetic diarization segments from Whisper transcription boundaries
2. Each segment gets `speaker_label = "UNKNOWN"` (no PyAnnote speaker labels)
3. Extract embeddings for ALL segments
4. Client logic remains consistent - just stitches transcription + diarization

## Implementation Phases

### Phase 1: Upfront Embedding Extraction (Core Fix)

| Task | File                     | Description                                                                                        |
| ---- | ------------------------ | -------------------------------------------------------------------------------------------------- |
| 1.1  | `audio_ingestion.py`     | Add embedding extraction step after segment creation in `_create_synthetic_diarization_segments()` |
| 1.2  | `audio_ingestion.py`     | Add embedding extraction for PyAnnote workflow too                                                 |
| 1.3  | `pgvector_client.py`     | Update `search_by_speaker()` to use `WHERE speaker_id IS NOT NULL`                                 |
| 1.4  | `instant_client.py`      | Add method to batch-update `embedding_id` on segments                                              |
| 1.5  | `ground_truth_server.py` | Simplify `_handle_embedding_update()` - just update speaker_id, don't extract                      |

### Phase 2: Clustering Feature (Enhancement)

| Task | File                           | Description                           |
| ---- | ------------------------------ | ------------------------------------- |
| 2.1  | `pgvector_client.py`           | Add `get_embeddings_by_run()` method  |
| 2.2  | New: `ingestion/clustering.py` | Create clustering module with HDBSCAN |
| 2.3  | `ground_truth_server.py`       | Add `/cluster` endpoint               |
| 2.4  | `ground_truth_instant.html`    | Add "Cluster Unknown Segments" button |

### Phase 3: Batch Processing Script Update

| Task | File                                  | Description                                               |
| ---- | ------------------------------------- | --------------------------------------------------------- |
| 3.1  | `scripts/batch_extract_embeddings.py` | Update to work with new flow (backfill existing segments) |

## Code Changes Detail

### 1. `_create_synthetic_diarization_segments()` Update

```python
def _create_synthetic_diarization_segments(
    transcription_result: TranscriptionResult,
    audio_path: Path,  # NEW: need audio path for embedding extraction
) -> tuple[list[dict], dict]:
    """
    Create synthetic diarization segments from Whisper transcription segments.
    Now also extracts embeddings for each segment.
    """
    from src.embeddings.pyannote_extractor import PyAnnoteEmbeddingExtractor

    extractor = PyAnnoteEmbeddingExtractor()
    segments = []

    for idx, seg in enumerate(transcription_result.segments):
        start = seg.start if hasattr(seg, 'start') else seg.get('start', 0)
        end = seg.end if hasattr(seg, 'end') else seg.get('end', 0)
        text = seg.text if hasattr(seg, 'text') else seg.get('text', '')

        # Extract embedding for this segment
        embedding = extractor.extract_embedding(
            audio_path=str(audio_path),
            start_time=float(start),
            end_time=float(end),
        )

        segments.append({
            "start": float(start),
            "end": float(end),
            "speaker": "UNKNOWN",
            "text": text.strip(),
            "confidence": None,
            "source": "whisper_transcription",
            "transcription_segment_index": idx,
            "embedding": embedding.tolist() if embedding is not None else None,  # NEW
        })

    # ... rest of function
```

### 2. Save Embeddings to PostgreSQL

After saving segments to InstantDB, save embeddings to PostgreSQL:

```python
# After instant_client.save_diarization_segments()
if segments_to_save:
    from src.embeddings.pgvector_client import PgVectorClient

    pg_dsn = os.getenv("SPEAKER_DB_DSN") or "postgresql://..."
    pg_client = PgVectorClient(pg_dsn)

    for seg, saved_seg in zip(segments, saved_segments):
        if seg.get("embedding"):
            pg_client.add_embedding(
                external_id=saved_seg["id"],  # InstantDB segment ID
                embedding=seg["embedding"],
                speaker_id=None,  # Unknown
                speaker_label=seg.get("speaker", "UNKNOWN"),
                video_id=video_id,
                diarization_run_id=diar_run_id,
                start_time=seg["start"],
                end_time=seg["end"],
            )

            # Update InstantDB segment with embedding_id
            instant_client.update_segment_embedding_id(
                segment_id=saved_seg["id"],
                embedding_id=saved_seg["id"],  # Same as external_id
            )
```

### 3. Update `search_by_speaker()` Filter

```python
def search_by_speaker(
    self,
    embedding: List[float],
    limit: int = 5
) -> List[Tuple[str, float, int]]:
    """Find nearest speakers by averaging distance to their embeddings."""
    with self._get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    speaker_id,
                    AVG(embedding <=> %s::vector) as avg_dist,
                    COUNT(*) as num_embeddings
                FROM speaker_embeddings
                WHERE speaker_id IS NOT NULL  -- Changed from != 'UNKNOWN'
                GROUP BY speaker_id
                ORDER BY avg_dist ASC
                LIMIT %s
            """, (embedding, limit))
            return cur.fetchall()
```

### 4. Simplify Ground Truth Server

```python
async def _handle_embedding_update(self, segment_id: str, speaker_name: str):
    """
    Update speaker_id for an existing embedding.
    Embedding should already exist from ingestion time.
    """
    # Just update the speaker_id - no extraction needed
    self.pg_client.update_speaker_id(segment_id, speaker_name)

    # If embedding doesn't exist (legacy data), extract it
    existing = self.pg_client.get_embedding(segment_id)
    if not existing:
        # Fallback: extract embedding (for backwards compatibility)
        await self._extract_and_save_embedding(segment_id, speaker_name)
```

## Memory Considerations

Extracting 175 embeddings at once could use significant memory. Mitigations:

1. **Process one at a time** - Don't batch load the model
2. **Clear GPU cache** - After each extraction if using GPU
3. **Stream to PostgreSQL** - Don't hold all embeddings in memory

The PyAnnote embedding model uses ~500MB of memory. Processing segments sequentially keeps memory stable.

## Testing Plan

1. **Unit Tests**
   - Test `_create_synthetic_diarization_segments()` returns embeddings
   - Test `search_by_speaker()` filters NULL speaker_id

2. **Integration Tests**
   - Run full ingestion with `--segment-source whisper`
   - Verify all segments have `embedding_id` in InstantDB
   - Verify all embeddings exist in PostgreSQL with `speaker_id = NULL`

3. **Manual Testing**
   - Open Ground Truth UI
   - Label a segment
   - Verify it's fast (no embedding extraction)
   - Verify speaker_id updated in PostgreSQL

## Rollback Plan

If issues arise:

1. The old on-demand extraction code remains in `ground_truth_server.py`
2. Segments without `embedding_id` will still trigger extraction
3. No data migration needed - additive changes only
