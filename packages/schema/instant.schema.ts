/*
  HOW:
  To deploy this schema to InstantDB, use the Instant CLI:
  
  1. Push Schema (Apply changes):
     `npx instant-cli@latest push schema`
     
  2. Pull Schema (Sync remote changes):
     `npx instant-cli@latest pull schema`
     
  [Troubleshooting]
  - "Schema mismatch": If you see errors about "Triple missing" or type errors after pushing, 
    it means your local schema definitions (e.g. `indexed()` fields) conflict with existing data. 
    You may need to wipe the DB or manually fix the data via the Dashboard.
  - "Auth Error": Ensure `INSTANT_APP_ID` and `INSTANT_ADMIN_SECRET` are set in `.env`.
 
  WHO:
  Antigravity, User
  (Context: Schema Definition)

  WHAT:
  InstantDB Schema for the Video Analysis Pipeline.
  Entities: videos, transcriptionRuns, diarizationRuns, stableSegments, speakers, shazamMatches.
*/

import { i } from "@instantdb/core";

const graph = i.graph(
  {
    // ---------------------------------------------------------
    // Legacy / Core
    // ---------------------------------------------------------
    videos: i.entity({
      title: i.string(),
      url: i.string(), // "titleUrl"
      filepath: i.string(),
      duration: i.number(),

      // Legacy Metadata
      channel_id: i.string(),
      upload_date: i.string(),
      view_count: i.number(),
      
      created_at: i.string(),
    }),

    stableSegments: i.entity({
      video_id: i.string().indexed(),
      index: i.number().indexed(), // 0, 1, 2...
      start_time: i.number(),
      end_time: i.number(),
      created_at: i.string(),
    }),

    correctedSegments: i.entity({
      stable_segment_id: i.string().indexed(), 
      video_id: i.string().indexed(),
      text: i.string(),
      speaker_id: i.string().indexed(),
      created_at: i.string(),
    }),

    transcriptionRuns: i.entity({
      video_id: i.string().indexed(),
      name: i.string(),
      model: i.string().indexed(),
      created_at: i.string(),
      segmentation_threshold: i.number().indexed(),
      context_window: i.number().indexed(),
    }),

    transcriptionSegments: i.entity({
      run_id: i.string().indexed(),
      start_time: i.number().indexed(),
      end_time: i.number(),
      text: i.string(),
    }),

    diarizationRuns: i.entity({
      video_id: i.string().indexed(),
      transcription_run_id: i.string().indexed(),
      created_at: i.string(),
      clustering_threshold: i.number().indexed(),
      identification_threshold: i.number().indexed(),
      embedding_model: i.string().indexed(),
    }),

    diarizationSegments: i.entity({
      run_id: i.string().indexed(),
      start_time: i.number().indexed(),
      end_time: i.number(),
      speaker_id: i.string().indexed(),
    }),

    speakers: i.entity({
      name: i.string().indexed(),
      is_human: i.boolean(),
      created_at: i.string(),
    }),

    shazamMatches: i.entity({
      video_id: i.string().indexed(),
      start_time: i.number().indexed(),
      end_time: i.number(),
      shazam_track_id: i.string().indexed(),
      title: i.string(),
      artist: i.string(),
      match_offset: i.number(),
      created_at: i.string(),
    }),
  },
  {
      videoStableSegments: {
        forward: { on: "videos", has: "many", label: "stableSegments" },
        reverse: { on: "stableSegments", has: "one", label: "video" },
      },
      videoCorrectedSegments: {
        forward: { on: "videos", has: "many", label: "correctedSegments" },
        reverse: { on: "correctedSegments", has: "one", label: "video" },
      },
      stableSegmentCorrectedSegments: {
        forward: { on: "stableSegments", has: "many", label: "corrections" },
        reverse: { on: "correctedSegments", has: "one", label: "stableSegment" },
      },
      videoTranscriptionRuns: {
        forward: { on: "videos", has: "many", label: "transcriptionRuns" },
        reverse: { on: "transcriptionRuns", has: "one", label: "video" },
      },
      runTranscriptionSegments: {
        forward: { on: "transcriptionRuns", has: "many", label: "segments" },
        reverse: { on: "transcriptionSegments", has: "one", label: "run" },
      },
      videoDiarizationRuns: {
        forward: { on: "videos", has: "many", label: "diarizationRuns" },
        reverse: { on: "diarizationRuns", has: "one", label: "video" },
      },
      diarizationRunTranscriptionRun: {
        forward: { on: "diarizationRuns", has: "one", label: "transcriptionRun" },
        reverse: { on: "transcriptionRuns", has: "many", label: "diarizationRuns" },
      },
      runDiarizationSegments: {
        forward: { on: "diarizationRuns", has: "many", label: "segments" },
        reverse: { on: "diarizationSegments", has: "one", label: "run" },
      },
      diarizationSegmentSpeaker: {
        forward: { on: "diarizationSegments", has: "one", label: "speaker" },
        reverse: { on: "speakers", has: "many", label: "diarizationSegments" },
      },
      correctedSegmentSpeaker: {
        forward: { on: "correctedSegments", has: "one", label: "speaker" },
        reverse: { on: "speakers", has: "many", label: "correctedSegments" },
      },
      videoShazamMatches: {
          forward: { on: "videos", has: "many", label: "shazamMatches" },
          reverse: { on: "shazamMatches", has: "one", label: "video" },
      },
  }
);

export default graph;
