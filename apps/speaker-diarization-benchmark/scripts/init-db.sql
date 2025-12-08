/*
HOW:
  This script runs automatically on first `docker compose up`.
  It's mounted as /docker-entrypoint-initdb.d/init.sql in the container.
  
  Manual run (if needed):
    psql -U diarization -d speaker_embeddings -f scripts/init-db.sql

  [Inputs]
  - PostgreSQL with pgvector extension available
  
  [Outputs]
  - Creates speaker_embeddings table with vector(512) column
  - Creates indexes for cosine similarity search
  - Creates helper view for debugging
  
  [Side Effects]
  - Modifies database schema (idempotent - safe to re-run)

WHO:
  Claude AI, User
  (Context: Setting up pgvector for speaker embedding KNN search)

WHAT:
  Database initialization script for speaker embedding storage.
  - Enables pgvector extension
  - Creates speaker_embeddings table with 512-dimensional vectors
  - Uses IVFFlat index for fast approximate nearest neighbor search
  - Includes metadata columns linking to InstantDB entities

WHEN:
  2025-12-07
  
  [Change Log]
  - 2025-12-07: Initial creation with 512-dim vectors

WHERE:
  apps/speaker-diarization-benchmark/scripts/init-db.sql

WHY:
  Enable fast KNN search on per-segment speaker embeddings.
  512 dimensions matches pyannote/embedding model output.
  Per-segment embeddings (not centroids) allow:
  - Better handling of speaker variation (mood, mic distance)
  - Clustering to discover speakers
  - Comparing unknown segments to known speakers
*/

-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Speaker embeddings table (per-segment embeddings for KNN)
CREATE TABLE IF NOT EXISTS speaker_embeddings (
    id SERIAL PRIMARY KEY,
    
    /*
     * Link to InstantDB entities.
     * external_id maps to DiarizationSegment.id in InstantDB.
     */
    external_id UUID UNIQUE NOT NULL,
    
    /*
     * Reference to the source video in InstantDB.
     */
    video_id UUID,
    
    /*
     * Reference to the diarization run that produced this embedding.
     */
    diarization_run_id UUID,
    
    /*
     * Current speaker label (can be updated by user corrections).
     * Initially set to UNKNOWN or the model's prediction.
     */
    speaker_id TEXT DEFAULT 'UNKNOWN',
    
    /*
     * Original label from diarization model (SPEAKER_00, etc).
     * Preserved for debugging and analysis.
     */
    speaker_label TEXT,
    
    /*
     * The embedding vector.
     * 512 dimensions from pyannote/embedding model.
     */
    embedding vector(512) NOT NULL,
    
    /*
     * Segment timing in seconds.
     * Matches the diarization segment boundaries.
     */
    start_time FLOAT,
    end_time FLOAT,
    
    /*
     * Flexible metadata storage.
     * Can include: source_file, confidence, extraction_params, etc.
     */
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

/*
 * IVFFlat index for approximate nearest neighbor search.
 * Uses cosine distance (vector_cosine_ops) for similarity.
 * lists=100 is a good default for datasets up to ~100k vectors.
 */
CREATE INDEX IF NOT EXISTS speaker_embedding_cosine_idx 
    ON speaker_embeddings 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

/*
 * Index for filtering by video before KNN search.
 */
CREATE INDEX IF NOT EXISTS speaker_embedding_video_idx 
    ON speaker_embeddings(video_id);

/*
 * Index for looking up all embeddings for a known speaker.
 */
CREATE INDEX IF NOT EXISTS speaker_embedding_speaker_idx 
    ON speaker_embeddings(speaker_id);

/*
 * Function to auto-update the updated_at timestamp.
 */
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

/*
 * Trigger to call update_updated_at on row updates.
 */
DROP TRIGGER IF EXISTS speaker_embeddings_updated_at ON speaker_embeddings;
CREATE TRIGGER speaker_embeddings_updated_at
    BEFORE UPDATE ON speaker_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

/*
 * Helper view for debugging - shows speaker statistics.
 */
CREATE OR REPLACE VIEW embedding_stats AS
SELECT 
    speaker_id,
    COUNT(*) as segment_count,
    MIN(start_time) as first_appearance,
    MAX(end_time) as last_appearance
FROM speaker_embeddings
GROUP BY speaker_id
ORDER BY segment_count DESC;
