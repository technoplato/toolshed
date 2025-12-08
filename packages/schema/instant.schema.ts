/**
 * =============================================================================
 * INSTANT.SCHEMA.TS - Audio Ingestion Pipeline Data Model
 * =============================================================================
 *
 * HOW:
 *   To deploy this schema to InstantDB, use the Instant CLI:
 *
 *   1. Push Schema (Apply changes):
 *      `npx instant-cli@latest push schema`
 *
 *   2. Pull Schema (Sync remote changes):
 *      `npx instant-cli@latest pull schema`
 *
 *   [Troubleshooting]
 *   - "Schema mismatch": If you see errors about "Triple missing" or type errors
 *     after pushing, it means your local schema definitions conflict with existing
 *     data. You may need to wipe the DB or manually fix the data via the Dashboard.
 *   - "Auth Error": Ensure `INSTANT_APP_ID` and `INSTANT_ADMIN_SECRET` are set in `.env`.
 *
 * WHO:
 *   Antigravity, User
 *   (Context: Complete Schema Redesign for Audio Ingestion Pipeline)
 *
 * WHAT:
 *   InstantDB Schema for the Video/Audio Analysis Pipeline.
 *   Supports transcription, speaker diarization, speaker identification,
 *   and user corrections with full history preservation.
 *
 * WHEN:
 *   Created: 2025-12-07
 *   Last Modified: 2025-12-07
 *   [Change Log:
 *     - 2025-12-07: Complete redesign. Removed stable segments, added words as
 *       first-class entities, added publications, comprehensive corrections layer.
 *   ]
 *
 * WHERE:
 *   packages/schema/instant.schema.ts
 *
 * WHY:
 *   To provide a complete data model for:
 *   1. Ingesting video/audio from various platforms
 *   2. Running multiple transcription and diarization experiments
 *   3. Identifying speakers via voice embeddings
 *   4. Supporting user corrections with full audit history
 *   5. Enabling word-level sync with audio playback
 *
 * =============================================================================
 *
 * DESIGN PRINCIPLES:
 *
 * 1. Comments ABOVE code, never to the right
 * 2. Every entity documents its relationships inline
 * 3. Words are first-class entities (presentation layer aggregates to segments)
 * 4. Time-based range queries replace "stable segments" concept
 * 5. Full history preservation for all corrections and splits
 * 6. Diarization and transcription are INDEPENDENT (can be combined at query time)
 *
 * =============================================================================
 *
 * ENTITY RELATIONSHIP MAP:
 *
 * publications
 *   └── videos (one-to-many)
 *   └── regularSpeakers (many-to-many)
 *
 * videos
 *   └── publication (many-to-one)
 *   └── transcriptionRuns (one-to-many)
 *   └── diarizationRuns (one-to-many)
 *   └── shazamMatches (one-to-many)
 *
 * transcriptionRuns
 *   └── video (many-to-one)
 *   └── config (many-to-one)
 *   └── words (one-to-many)
 *
 * diarizationRuns
 *   └── video (many-to-one)
 *   └── config (many-to-one)
 *   └── diarizationSegments (one-to-many)
 *
 * diarizationSegments
 *   └── diarizationRun (many-to-one)
 *   └── speakerAssignments (one-to-many) [history preserved]
 *   └── childSegments (one-to-many) [if split]
 *   └── parentSegment (many-to-one) [if created from split]
 *   └── splits (one-to-many) [split actions that targeted this segment]
 *
 * speakers
 *   └── publications (many-to-many)
 *   └── speakerAssignments (one-to-many)
 *
 * words
 *   └── transcriptionRun (many-to-one)
 *   └── textCorrections (one-to-many) [history preserved]
 *
 * =============================================================================
 *
 * SPEAKER IDENTIFICATION FLOW:
 *
 * 1. Diarization produces segments with local labels (e.g., "SPEAKER_0")
 * 2. Voice embeddings are extracted and stored in PostgreSQL (pgvector)
 * 3. Embeddings are compared to known speaker centroids
 * 4. SpeakerAssignment records link segments to identified speakers
 * 5. Users can correct assignments; history is preserved
 *
 * CORRECTION BUSINESS LOGIC:
 *
 * Case 1: No embedding match, user labels unknown segment
 *   - If embedding_id is NULL and speaker_label is "SPEAKER_X"
 *   - User assigns a speaker to this segment
 *   - Server SHOULD propagate to ALL segments with speaker_label="SPEAKER_X" in this run
 *
 * Case 2: Embedding matched, user corrects assignment
 *   - If embedding_id IS present (we had a match)
 *   - User changes the speaker assignment
 *   - Server should NOT propagate to other segments
 *   - Only this specific segment gets the correction
 *
 * =============================================================================
 */

import { i } from "@instantdb/core";

const schema = i.schema({
  entities: {
    // =========================================================================
    // PUBLICATION
    // =========================================================================
    /**
     * PUBLICATION
     *
     * A source of media content. Generic term that covers:
     * - YouTube channels
     * - Podcast feeds
     * - X (Twitter) accounts
     * - News outlets
     * - Twitch streams
     *
     * RELATIONSHIPS:
     * - videos: All videos from this publication (one-to-many)
     * - regularSpeakers: Speakers who frequently appear (many-to-many)
     */
    publications: i.entity({
      /**
       * Display name of the publication.
       * Example: "Matt and Shane's Secret Podcast"
       */
      name: i.string().indexed(),

      /**
       * Type of publication. Used to understand the source platform.
       * Examples: "youtube_channel", "podcast", "x_account", "news_outlet", "twitch_channel"
       */
      publication_type: i.string().indexed(),

      /**
       * URL to the publication's main page/feed.
       * Example: "https://www.youtube.com/@MattandShanesSecretPodcast"
       */
      url: i.string().unique().indexed(),

      /**
       * External ID on the source platform.
       * For YouTube: channel ID like "UCzQUP1qoWDoEbmsQxvdjxgQ"
       * For podcasts: RSS feed URL or Apple Podcasts ID
       */
      external_id: i.string().indexed().optional(),

      /**
       * Raw metadata from the source platform, preserved for future use.
       */
      raw_metadata: i.json().optional(),

      /**
       * Timestamp when this publication was added to our system.
       * ISO 8601 format.
       */
      ingested_at: i.string(),
    }),

    // =========================================================================
    // VIDEO
    // =========================================================================
    /**
     * VIDEO
     *
     * Represents a media file (video/audio) that has been ingested into the system.
     * Metadata is acquired from yt-dlp upon ingestion and stored here.
     *
     * RELATIONSHIPS:
     * - publication: The source publication (many-to-one)
     * - transcriptionRuns: All transcription attempts (one-to-many)
     * - diarizationRuns: All diarization attempts (one-to-many)
     * - shazamMatches: Music detection results (one-to-many)
     */
    videos: i.entity({
      /**
       * Title of the video as retrieved from the source platform.
       * Example: "Ep 569 - A Derosa Garden (feat. Joe Derosa)"
       */
      title: i.string(),

      /**
       * Unique URL of the video on its source platform.
       * Used as the canonical identifier for deduplication.
       * Example: "https://www.youtube.com/watch?v=jAlKYYr1bpY"
       */
      url: i.string().unique().indexed(),

      /**
       * Local filesystem path where the downloaded video/audio file resides.
       * Null if the video has not been downloaded for local processing.
       * Example: "/data/downloads/youtube_jAlKYYr1bpY.wav"
       */
      filepath: i.string().optional(),

      /**
       * Duration of the video in seconds.
       * Acquired from yt-dlp metadata.
       */
      duration: i.number(),

      /**
       * Description/summary from the source platform.
       * Preserved exactly as provided by yt-dlp.
       */
      description: i.string().optional(),

      /**
       * Date the video was published on the source platform.
       * ISO 8601 format. This is EXTERNAL metadata, not when we ingested it.
       * Example: "2024-03-15T14:30:00Z"
       */
      external_published_at: i.string().optional(),

      /**
       * Raw metadata blob from yt-dlp.
       * Preserved for future use cases and debugging.
       * Contains: thumbnails, tags, view_count, like_count, etc.
       */
      raw_metadata: i.json().optional(),

      /**
       * Timestamp when this video was ingested into our system.
       * ISO 8601 format.
       */
      ingested_at: i.string(),
    }),

    // =========================================================================
    // SPEAKER
    // =========================================================================
    /**
     * SPEAKER
     *
     * A real-world person or entity that speaks in media.
     * Speakers are global across the entire system and can appear in
     * multiple videos across multiple publications.
     *
     * RELATIONSHIPS:
     * - publications: Publications this speaker regularly appears on (many-to-many)
     * - speakerAssignments: All diarization segments attributed to this speaker (one-to-many)
     *
     * EMBEDDING STRATEGY:
     * Speaker voice embeddings are stored in PostgreSQL (pgvector).
     * The `embedding_centroid_id` links to a computed centroid of all
     * confirmed voice samples for this speaker, enabling identification
     * of the speaker in new audio.
     */
    speakers: i.entity({
      /**
       * Full name of the speaker.
       * Example: "Joe DeRosa"
       */
      name: i.string().indexed(),

      /**
       * Whether this is a human speaker vs. AI/synthetic voice, music, etc.
       */
      is_human: i.boolean(),

      /**
       * Reference to the centroid embedding in PostgreSQL.
       * The centroid is the average of all confirmed voice embeddings
       * for this speaker. Used for speaker identification.
       * Example: "pgv_speaker_centroid_abc123"
       */
      embedding_centroid_id: i.string().optional(),

      /**
       * Freeform metadata about the speaker.
       * Can include: bio, social links, known aliases, etc.
       */
      metadata: i.json().optional(),

      /**
       * Timestamp when this speaker was added to our system.
       * ISO 8601 format.
       */
      ingested_at: i.string(),
    }),

    // =========================================================================
    // TRANSCRIPTION CONFIG
    // =========================================================================
    /**
     * TRANSCRIPTION CONFIG
     *
     * Captures the exact configuration used for a transcription run.
     * Configs are reusable - multiple runs can reference the same config.
     *
     * RELATIONSHIPS:
     * - transcriptionRuns: All runs that used this config (one-to-many)
     */
    transcriptionConfigs: i.entity({
      /**
       * The transcription model used.
       * Examples: "whisper-large-v3", "whisper-large-v3-turbo", "distil-whisper-large-v3"
       */
      model: i.string().indexed(),

      /**
       * The tool/library used to run the transcription.
       * This is distinct from the model - same model can be run with different tools.
       * Examples: "mlx-whisper", "whisper.cpp", "faster-whisper", "openai-api"
       */
      tool: i.string().indexed(),

      /**
       * Language code for transcription.
       * ISO 639-1 format. Null means auto-detect.
       * Examples: "en", "es", "ja"
       */
      language: i.string().optional(),

      /**
       * Word-level timestamp generation enabled.
       */
      word_timestamps: i.boolean(),

      /**
       * Voice Activity Detection (VAD) filter enabled.
       */
      vad_filter: i.boolean().optional(),

      /**
       * Beam size for decoding (affects accuracy vs. speed).
       */
      beam_size: i.number().optional(),

      /**
       * Temperature for sampling (0 = deterministic).
       */
      temperature: i.number().optional(),

      /**
       * Additional tool-specific parameters.
       * Preserved for reproducibility.
       */
      additional_params: i.json().optional(),

      /**
       * Timestamp when this config was created.
       * ISO 8601 format.
       */
      created_at: i.string(),
    }),

    // =========================================================================
    // DIARIZATION CONFIG
    // =========================================================================
    /**
     * DIARIZATION CONFIG
     *
     * Captures the exact configuration used for a diarization run.
     *
     * Note: Diarization can be performed via local models OR APIs.
     * The `tool` field distinguishes these (e.g., "pyannote-local" vs "pyannote-api").
     *
     * RELATIONSHIPS:
     * - diarizationRuns: All runs that used this config (one-to-many)
     */
    diarizationConfigs: i.entity({
      /**
       * The embedding model used for speaker representation.
       * Examples:
       * - "pyannote/wespeaker-voxceleb-resnet34" (local)
       * - "pyannote-api" (when using PyAnnote AI API)
       * - "speechbrain/spkrec-ecapa-voxceleb"
       */
      embedding_model: i.string().indexed(),

      /**
       * The tool/library used for diarization.
       * Examples: "pyannote-local", "pyannote-api", "speechbrain", "nemo"
       */
      tool: i.string().indexed(),

      /**
       * Clustering algorithm used to group speaker embeddings.
       * Examples: "AgglomerativeClustering", "SpectralClustering", "HDBSCAN"
       */
      clustering_method: i.string().optional(),

      /**
       * Distance threshold for clustering.
       * Lower = more speakers detected, higher = fewer speakers.
       */
      cluster_threshold: i.number().optional(),

      /**
       * Minimum similarity score required to identify a speaker
       * against known speakers in the database.
       * Range: 0.0 to 1.0
       */
      identification_threshold: i.number().optional(),

      /**
       * Additional tool-specific parameters.
       */
      additional_params: i.json().optional(),

      /**
       * Timestamp when this config was created.
       * ISO 8601 format.
       */
      created_at: i.string(),
    }),

    // =========================================================================
    // TRANSCRIPTION RUN
    // =========================================================================
    /**
     * TRANSCRIPTION RUN
     *
     * A single execution of transcription on a video.
     * Multiple runs allow experimentation with different configs/tools.
     *
     * RELATIONSHIPS:
     * - video: The video that was transcribed (many-to-one)
     * - config: The configuration used (many-to-one)
     * - words: All words produced by this run (one-to-many)
     */
    transcriptionRuns: i.entity({
      /**
       * The specific tool/library version used.
       * More specific than config.tool - includes version info.
       * Examples: "mlx-whisper-0.4.1", "whisper.cpp-1.5.4", "faster-whisper-0.10.0"
       */
      tool_version: i.string(),

      /**
       * Git commit SHA of our codebase when this run was executed.
       * Enables exact reproduction of the pipeline.
       */
      git_commit_sha: i.string().optional(),

      /**
       * The script/file that orchestrated this transcription.
       * Useful for debugging and understanding the pipeline.
       * Example: "audio_ingestion.py"
       */
      pipeline_script: i.string().optional(),

      /**
       * Whether this is the preferred run for display.
       * Only one run per video should be marked preferred.
       */
      is_preferred: i.boolean().indexed(),

      /**
       * Duration of input audio that was processed (in seconds).
       * May be less than full video duration if --start-time/--end-time used.
       * Useful for cost calculations and performance comparisons.
       */
      input_duration_seconds: i.number().optional(),

      /**
       * Processing time in seconds (wall clock time).
       * Compare with input_duration_seconds to get real-time factor.
       */
      processing_time_seconds: i.number().optional(),

      /**
       * Peak memory usage during processing (in MB).
       * Tracked via psutil or similar.
       */
      peak_memory_mb: i.number().optional(),

      /**
       * Cost in USD when using paid APIs (e.g., OpenAI Whisper API).
       * NULL for local processing (cost is compute time only).
       */
      cost_usd: i.number().optional(),

      /**
       * Any errors or warnings encountered.
       */
      logs: i.json().optional(),

      /**
       * Timestamp when this run was executed.
       * ISO 8601 format.
       */
      executed_at: i.string(),
    }),

    // =========================================================================
    // DIARIZATION RUN
    // =========================================================================
    /**
     * DIARIZATION RUN
     *
     * A single execution of speaker diarization on a video.
     * Independent of transcription runs - they can be combined at query time.
     *
     * RELATIONSHIPS:
     * - video: The video that was diarized (many-to-one)
     * - config: The configuration used (many-to-one)
     * - diarizationSegments: All segments produced by this run (one-to-many)
     */
    diarizationRuns: i.entity({
      /**
       * The workflow/tool used for this run.
       * Examples: "pyannote-local", "pyannote-api", "speechbrain", "custom-vad-clustering"
       */
      workflow: i.string().indexed(),

      /**
       * Specific version of the tool.
       * Example: "pyannote-audio-3.1.1"
       */
      tool_version: i.string().optional(),

      /**
       * Git commit SHA of our codebase when this run was executed.
       */
      git_commit_sha: i.string().optional(),

      /**
       * The script that orchestrated this diarization.
       */
      pipeline_script: i.string().optional(),

      /**
       * Whether this is the preferred run for display.
       */
      is_preferred: i.boolean().indexed(),

      /**
       * Duration of input audio that was processed (in seconds).
       * May be less than full video duration if --start-time/--end-time used.
       * Useful for cost calculations and performance comparisons.
       */
      input_duration_seconds: i.number().optional(),

      /**
       * Processing time in seconds (wall clock time).
       * Compare with input_duration_seconds to get real-time factor.
       */
      processing_time_seconds: i.number().optional(),

      /**
       * Peak memory usage during processing (in MB).
       * Tracked via psutil or similar.
       */
      peak_memory_mb: i.number().optional(),

      /**
       * Cost in USD when using paid APIs (e.g., PyAnnote AI API).
       * NULL for local processing (cost is compute time only).
       */
      cost_usd: i.number().optional(),

      /**
       * Number of unique speakers detected.
       */
      num_speakers_detected: i.number().optional(),

      /**
       * Any errors or warnings encountered.
       */
      logs: i.json().optional(),

      /**
       * Timestamp when this run was executed.
       * ISO 8601 format.
       */
      executed_at: i.string(),
    }),

    // =========================================================================
    // WORD
    // =========================================================================
    /**
     * WORD
     *
     * A single word from a transcription, with precise timing.
     * Words are the atomic unit of transcription output.
     *
     * At display time, words are grouped into visual segments and
     * correlated with diarization segments via time-range queries:
     *
     *   // Find speaker for a word at time T:
     *   diarizationSegments: {
     *     $: {
     *       where: {
     *         start_time: { $lte: word.start_time },
     *         end_time: { $gte: word.end_time }
     *       }
     *     }
     *   }
     *
     * RELATIONSHIPS:
     * - transcriptionRun: The run that produced this word (many-to-one)
     * - textCorrections: User corrections to the text (one-to-many, history preserved)
     */
    words: i.entity({
      /**
       * The transcribed text of this word.
       * Example: "Hello"
       */
      text: i.string(),

      /**
       * Start time in seconds from the beginning of the audio.
       * Indexed for efficient range queries.
       */
      start_time: i.number().indexed(),

      /**
       * End time in seconds from the beginning of the audio.
       * Indexed for efficient range queries.
       */
      end_time: i.number().indexed(),

      /**
       * Model confidence score for this word.
       * Range: 0.0 to 1.0
       */
      confidence: i.number().optional(),

      /**
       * Index of the transcription segment this word belongs to.
       * This is the segment from the TRANSCRIPTION model (not diarization).
       * Whisper groups words into segments based on pauses/punctuation.
       * Useful for display: words with same index can be shown together.
       *
       * Note: This is NOT a diarization segment. Speaker attribution
       * is determined by correlating word times with diarization segments.
       */
      transcription_segment_index: i.number().optional(),

      /**
       * Timestamp when this word was ingested.
       * ISO 8601 format.
       */
      ingested_at: i.string(),
    }),

    // =========================================================================
    // DIARIZATION SEGMENT
    // =========================================================================
    /**
     * DIARIZATION SEGMENT
     *
     * A contiguous time range where a single speaker is talking.
     * Produced by the diarization model.
     *
     * SPEAKER LABEL SEMANTICS:
     * - `speaker_label` is the raw output from the model (e.g., "SPEAKER_0")
     * - Labels are LOCAL to the diarization run
     * - The actual speaker identity is determined via `speakerAssignments`
     *
     * BUSINESS LOGIC FOR CORRECTIONS:
     *
     * Case 1: No embedding match, user labels unknown segment
     *   - If embedding_id is NULL and speaker_label is "SPEAKER_X"
     *   - User assigns a speaker to this segment
     *   - Server SHOULD propagate this label to ALL segments with
     *     speaker_label="SPEAKER_X" in this run (they're likely the same person)
     *
     * Case 2: Embedding matched, user corrects assignment
     *   - If embedding_id IS present (we had a match)
     *   - User changes the speaker assignment
     *   - Server should NOT propagate to other segments
     *   - Only this specific segment gets the correction
     *   - The embedding may need to be moved to a different speaker's corpus
     *
     * RELATIONSHIPS:
     * - diarizationRun: The run that produced this segment (many-to-one)
     * - speakerAssignments: History of speaker attributions (one-to-many)
     * - parentSegment: If created from splitting another segment (many-to-one)
     * - childSegments: Segments created when this was split (one-to-many)
     * - splits: Split actions that targeted this segment (one-to-many)
     */
    diarizationSegments: i.entity({
      /**
       * Start time in seconds.
       * Indexed for range queries to match with words.
       */
      start_time: i.number().indexed(),

      /**
       * End time in seconds.
       * Indexed for range queries.
       */
      end_time: i.number().indexed(),

      /**
       * Raw speaker label from the diarization model.
       * Local to this run - "SPEAKER_0" in run A is unrelated to "SPEAKER_0" in run B.
       * Examples: "SPEAKER_0", "SPEAKER_1", "UNKNOWN"
       */
      speaker_label: i.string().indexed(),

      /**
       * Reference to the voice embedding in PostgreSQL (pgvector).
       * NULL if:
       * - Embedding extraction failed
       * - Segment is too short for reliable embedding
       * - This is a split segment pending re-embedding
       *
       * When present, this can be used to:
       * 1. Identify the speaker by comparing to known speaker centroids
       * 2. Train/update a speaker's voice model
       */
      embedding_id: i.string().optional(),

      /**
       * Confidence score from the diarization model.
       * Range: 0.0 to 1.0
       */
      confidence: i.number().optional(),

      /**
       * Whether this segment has been invalidated (e.g., by splitting).
       * Invalidated segments are kept for history but not displayed.
       */
      is_invalidated: i.boolean().optional(),

      /**
       * Timestamp when this segment was created.
       * ISO 8601 format.
       */
      created_at: i.string(),
    }),

    // =========================================================================
    // SPEAKER ASSIGNMENT
    // =========================================================================
    /**
     * SPEAKER ASSIGNMENT
     *
     * Links a diarization segment to an identified speaker.
     * Multiple assignments can exist for the same segment (history preserved).
     * The most recent assignment is the "current" one.
     *
     * EXAMPLE FLOW:
     * 1. Diarization runs, creates segment with speaker_label="SPEAKER_0"
     * 2. Embedding is compared to known speakers, finds 87% match to "Joe DeRosa"
     * 3. SpeakerAssignment created: source="model", speaker=JoeDeRosa, confidence=0.87
     * 4. User reviews, realizes it's actually "Matt McCusker"
     * 5. NEW SpeakerAssignment created: source="user", speaker=MattMcCusker
     * 6. Both assignments preserved; UI shows most recent
     *
     * RELATIONSHIPS:
     * - diarizationSegment: The segment this assignment is for (many-to-one)
     * - speaker: The identified speaker (many-to-one)
     */
    speakerAssignments: i.entity({
      /**
       * How this assignment was made.
       * "model" = automatic identification from embedding comparison (real-time)
       * "user" = manual correction by a human
       * "propagated" = automatically applied from another segment's correction
       * "auto_identify" = batch identification from identify workflow
       * "ground_truth" = verified human-labeled ground truth data
       */
      source: i.string().indexed(),

      /**
       * Confidence of the assignment.
       * For model: cosine similarity score (0.0 to 1.0)
       * For user: typically 1.0 (certain)
       */
      confidence: i.number().optional(),

      /**
       * Metadata about this assignment stored as JSON.
       *
       * For user corrections:
       *   { "reason": "Clearly Matt's voice, not Joe's" }
       *
       * For auto-identification:
       *   {
       *     "method": "knn_identify",
       *     "script_version": "v1",
       *     "knn_distance": 0.42,
       *     "top_matches": [
       *       {"speaker": "Shane Gillis", "distance": 0.42, "count": 8},
       *       {"speaker": "Matt McCusker", "distance": 0.58, "count": 2}
       *     ],
       *     "threshold": 0.5,
       *     "cache_hit": true
       *   }
       */
      note: i.json().optional(),

      /**
       * User ID who made this assignment. REQUIRED.
       * We always track who made changes.
       * For model assignments, use "system" or a service account ID.
       */
      assigned_by: i.string().indexed(),

      /**
       * Timestamp of assignment.
       * ISO 8601 format.
       */
      assigned_at: i.string(),
    }),

    // =========================================================================
    // SEGMENT SPLIT
    // =========================================================================
    /**
     * SEGMENT SPLIT
     *
     * Records the action of splitting one diarization segment into multiple segments.
     * This is always because the segment was misidentified as a single speaker.
     *
     * WHAT HAPPENS WHEN A SEGMENT IS SPLIT:
     *
     * 1. User identifies that segment [10.0s - 25.0s] contains multiple speakers
     * 2. User splits at 17.5s
     * 3. System creates:
     *    - This SegmentSplit record (split_time=17.5, originalSegment=<link>)
     *    - Two new DiarizationSegments:
     *      - [10.0s - 17.5s], createdFromSplit=<this split>, embedding_id=NULL (pending)
     *      - [17.5s - 25.0s], createdFromSplit=<this split>, embedding_id=NULL (pending)
     * 4. Original segment is marked is_invalidated=true
     * 5. Server recomputes embeddings for new segments
     * 6. User assigns speakers to new segments
     *
     * RELATIONSHIPS:
     * - originalSegment: The segment that was split (many-to-one)
     * - resultingSegments: The new segments created (one-to-many)
     */
    segmentSplits: i.entity({
      /**
       * Timestamp (in seconds) where the split occurred.
       */
      split_time: i.number(),

      /**
       * User who performed the split.
       */
      split_by: i.string().indexed(),

      /**
       * Timestamp when the split was performed.
       * ISO 8601 format.
       */
      split_at: i.string(),
    }),

    // =========================================================================
    // WORD TEXT CORRECTION
    // =========================================================================
    /**
     * WORD TEXT CORRECTION
     *
     * A user correction to a word's transcribed text.
     * Multiple corrections can exist for the same word (history preserved).
     * The most recent correction is the "current" text.
     *
     * RELATIONSHIPS:
     * - word: The word being corrected (many-to-one)
     */
    wordTextCorrections: i.entity({
      /**
       * The corrected text.
       * Example: Original "their" corrected to "there"
       */
      corrected_text: i.string(),

      /**
       * Optional explanation of why this correction was made.
       * Example: "Homophone error - context makes it clear it's 'there'"
       */
      note: i.string().optional(),

      /**
       * User who made this correction. REQUIRED.
       */
      corrected_by: i.string().indexed(),

      /**
       * Timestamp of correction.
       * ISO 8601 format.
       */
      corrected_at: i.string(),
    }),

    // =========================================================================
    // SHAZAM MATCH
    // =========================================================================
    /**
     * SHAZAM MATCH
     *
     * Music detection result from Shazam or similar service.
     * Used to identify music playing in the background of videos.
     *
     * RELATIONSHIPS:
     * - video: The video containing this music (many-to-one)
     */
    shazamMatches: i.entity({
      /**
       * Start time of the detected music in seconds.
       */
      start_time: i.number().indexed(),

      /**
       * End time of the detected music in seconds.
       */
      end_time: i.number(),

      /**
       * Shazam's track identifier.
       */
      shazam_track_id: i.string().indexed(),

      /**
       * Song title.
       */
      title: i.string(),

      /**
       * Artist name.
       */
      artist: i.string(),

      /**
       * Offset into the track where the match was found.
       */
      match_offset: i.number().optional(),

      /**
       * Timestamp when this match was recorded.
       * ISO 8601 format.
       */
      created_at: i.string(),
    }),
  },

  // ===========================================================================
  // LINKS
  // ===========================================================================
  links: {
    // =========================================================================
    // PUBLICATION RELATIONSHIPS
    // =========================================================================

    /**
     * Links a video to its source publication.
     *
     * Example:
     *   Video "Ep 569 - A Derosa Garden" → Publication "MSSP YouTube Channel"
     */
    videoPublication: {
      forward: { on: "videos", has: "one", label: "publication" },
      reverse: { on: "publications", has: "many", label: "videos" },
    },

    /**
     * Links speakers to publications they regularly appear on.
     *
     * Example:
     *   Speaker "Joe DeRosa" → [Publication "MSSP", Publication "Legion of Skanks"]
     *   Publication "MSSP" → [Speaker "Matt McCusker", Speaker "Shane Gillis"]
     */
    speakerPublications: {
      forward: { on: "speakers", has: "many", label: "publications" },
      reverse: { on: "publications", has: "many", label: "regularSpeakers" },
    },

    // =========================================================================
    // VIDEO → RUN RELATIONSHIPS
    // =========================================================================

    /**
     * Links a video to all transcription runs performed on it.
     *
     * Example:
     *   Video "Ep 569" → [
     *     TranscriptionRun(mlx-whisper, 2024-03-01),
     *     TranscriptionRun(faster-whisper, 2024-03-02)
     *   ]
     */
    videoTranscriptionRuns: {
      forward: { on: "videos", has: "many", label: "transcriptionRuns" },
      reverse: { on: "transcriptionRuns", has: "one", label: "video" },
    },

    /**
     * Links a video to all diarization runs performed on it.
     *
     * Example:
     *   Video "Ep 569" → [
     *     DiarizationRun(pyannote-local, 2024-03-01),
     *     DiarizationRun(speechbrain, 2024-03-02)
     *   ]
     */
    videoDiarizationRuns: {
      forward: { on: "videos", has: "many", label: "diarizationRuns" },
      reverse: { on: "diarizationRuns", has: "one", label: "video" },
    },

    /**
     * Links a video to Shazam music detection results.
     *
     * Example:
     *   Video "Ep 569" → [ShazamMatch("Immigrant Song", 45.0s-78.0s)]
     */
    videoShazamMatches: {
      forward: { on: "videos", has: "many", label: "shazamMatches" },
      reverse: { on: "shazamMatches", has: "one", label: "video" },
    },

    // =========================================================================
    // RUN → CONFIG RELATIONSHIPS
    // =========================================================================

    /**
     * Links a transcription run to its configuration.
     *
     * Example:
     *   TranscriptionRun(2024-03-01) → TranscriptionConfig(whisper-large-v3, mlx-whisper, en)
     */
    transcriptionRunConfig: {
      forward: { on: "transcriptionRuns", has: "one", label: "config" },
      reverse: {
        on: "transcriptionConfigs",
        has: "many",
        label: "transcriptionRuns",
      },
    },

    /**
     * Links a diarization run to its configuration.
     *
     * Example:
     *   DiarizationRun(2024-03-01) → DiarizationConfig(pyannote/wespeaker, AgglomerativeClustering)
     */
    diarizationRunConfig: {
      forward: { on: "diarizationRuns", has: "one", label: "config" },
      reverse: {
        on: "diarizationConfigs",
        has: "many",
        label: "diarizationRuns",
      },
    },

    // =========================================================================
    // RUN → OUTPUT RELATIONSHIPS
    // =========================================================================

    /**
     * Links a transcription run to all words it produced.
     *
     * Example:
     *   TranscriptionRun(mlx-whisper) → [
     *     Word("Hello", 0.0s-0.5s),
     *     Word("world", 0.5s-1.0s),
     *     ...
     *   ]
     */
    transcriptionRunWords: {
      forward: { on: "transcriptionRuns", has: "many", label: "words" },
      reverse: { on: "words", has: "one", label: "transcriptionRun" },
    },

    /**
     * Links a diarization run to all segments it produced.
     *
     * Example:
     *   DiarizationRun(pyannote) → [
     *     DiarizationSegment("SPEAKER_0", 0.0s-15.0s),
     *     DiarizationSegment("SPEAKER_1", 15.0s-30.0s),
     *     ...
     *   ]
     */
    diarizationRunSegments: {
      forward: {
        on: "diarizationRuns",
        has: "many",
        label: "diarizationSegments",
      },
      reverse: {
        on: "diarizationSegments",
        has: "one",
        label: "diarizationRun",
      },
    },

    // =========================================================================
    // SPEAKER ASSIGNMENT RELATIONSHIPS
    // =========================================================================

    /**
     * Links a diarization segment to its speaker assignment history.
     * Multiple assignments can exist; UI shows most recent.
     *
     * Example:
     *   DiarizationSegment[10s-15s] → [
     *     SpeakerAssignment(source="model", speaker=JoeDeRosa, confidence=0.87, assigned_at=T1),
     *     SpeakerAssignment(source="user", speaker=MattMcCusker, confidence=1.0, assigned_at=T2)
     *   ]
     *   UI displays: "Matt McCusker" (most recent)
     */
    diarizationSegmentSpeakerAssignments: {
      forward: {
        on: "diarizationSegments",
        has: "many",
        label: "speakerAssignments",
      },
      reverse: {
        on: "speakerAssignments",
        has: "one",
        label: "diarizationSegment",
      },
    },

    /**
     * Links a speaker assignment to the identified speaker.
     *
     * Example:
     *   SpeakerAssignment(source="user") → Speaker("Matt McCusker")
     */
    speakerAssignmentSpeaker: {
      forward: { on: "speakerAssignments", has: "one", label: "speaker" },
      reverse: { on: "speakers", has: "many", label: "speakerAssignments" },
    },

    // =========================================================================
    // SEGMENT SPLIT RELATIONSHIPS
    // =========================================================================

    /**
     * Links a split action to the original segment that was split.
     *
     * Example:
     *   SegmentSplit(split_time=17.5s) → DiarizationSegment[10s-25s] (original, now invalidated)
     */
    segmentSplitOriginalSegment: {
      forward: { on: "segmentSplits", has: "one", label: "originalSegment" },
      reverse: { on: "diarizationSegments", has: "many", label: "splits" },
    },

    /**
     * Links a split action to the segments it created.
     *
     * Example:
     *   SegmentSplit(split_time=17.5s) → [
     *     DiarizationSegment[10s-17.5s] (new),
     *     DiarizationSegment[17.5s-25s] (new)
     *   ]
     */
    segmentSplitResultingSegments: {
      forward: { on: "segmentSplits", has: "many", label: "resultingSegments" },
      reverse: {
        on: "diarizationSegments",
        has: "one",
        label: "createdFromSplit",
      },
    },

    // =========================================================================
    // WORD CORRECTION RELATIONSHIPS
    // =========================================================================

    /**
     * Links a word to its text correction history.
     * Multiple corrections can exist; UI shows most recent.
     *
     * Example:
     *   Word("their") → [
     *     WordTextCorrection(corrected_text="there", corrected_by=user123, corrected_at=T1)
     *   ]
     *   UI displays: "there" (corrected)
     */
    wordTextCorrectionHistory: {
      forward: { on: "words", has: "many", label: "textCorrections" },
      reverse: { on: "wordTextCorrections", has: "one", label: "word" },
    },
  },
});

export default schema;
