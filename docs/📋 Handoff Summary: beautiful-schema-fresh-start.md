📋 Handoff Summary: beautiful-schema-fresh-restart Branch
Branch Info
Branch: beautiful-schema-fresh-restartCommit: 7abbe54Base: main (worktree at /Users/laptop/.cursor/worktrees/toolshed/yde)
✅ What Was Completed

1. Complete Schema Redesign (packages/schema/instant.schema.ts)
   1,119 lines of fully documented schema with:
   Entity Purpose
   publications Generic source platforms (YouTube channels, podcasts, X accounts)
   videos Ingested media with yt-dlp metadata
   speakers Global speaker identities with embedding centroids
   transcriptionConfigs Reusable transcription configurations
   diarizationConfigs Reusable diarization configurations
   transcriptionRuns Individual transcription executions
   diarizationRuns Individual diarization executions
   words First-class word entities with timing (indexed for range queries)
   diarizationSegments Speaker turns with business logic documented
   speakerAssignments Links segments to speakers (history preserved)
   segmentSplits Records segment split actions
   wordTextCorrections Word text correction history
   shazamMatches Music detection results
2. Key Design Decisions
   Removed stableSegments - Replaced by time-based range queries on indexed start_time/end_time
   Words are first-class - Not buried in JSON blobs
   Diarization independent of transcription - Combined at query time
   Full history preservation - Corrections and splits keep audit trail
   Comments above, never right - Added to AGENTS.md
3. AGENTS.md Updated
   Added "Code Style Guidelines" section with comment placement rules.
   🔴 What Needs To Be Done Next
4. Nuke the Database
   cd apps/speaker-diarization-benchmark# Need .env file with:# INSTANT_APP_ID=<your-app-id># INSTANT_ADMIN_SECRET=<your-admin-secret>uv run python scripts/one_off/nuke_db.py
5. Push New Schema to InstantDB
   cd packages/schemanpx instant-cli@latest push schema
6. Update instant_db_adapter.py
   The adapter at apps/speaker-diarization-benchmark/src/data/impl/instant_db_adapter.py still uses the old schema with:
   stableSegments (removed)
   transcriptionSegments (now words)
   Old field names
   Needs rewrite to match new schema.
7. Test Audio Ingestion Pipeline
   cd apps/speaker-diarization-benchmark# Dry run firstuv run audio_ingestion.py diarize data/clips/clip_youtube_jAlKYYr1bpY_0_60.wav --dry-run# Full runuv run audio_ingestion.py diarize data/clips/clip_youtube_jAlKYYr1bpY_0_60.wav --workflow pyannote
   📁 Key Files
   File Status Notes
   packages/schema/instant.schema.ts ✅ Complete 1,119 lines, fully documented
   AGENTS.md ✅ Updated Comment placement rules added
   apps/speaker-diarization-benchmark/src/data/impl/instant_db_adapter.py ❌ Needs update Still uses old schema
   apps/speaker-diarization-benchmark/src/data/models.py ❌ Needs update Python models need to match new schema
   🎯 Test Data Available
   File Description
   data/clips/clip_youtube_jAlKYYr1bpY_0_60.wav 60-second clip
   data/clips/clip_youtube_jAlKYYr1bpY_0_60_ground_truth.txt Ground truth with 4 speakers
   joe-derosa-mssp-0-60-s-verified.json Verified transcription segments
   Speakers in clip: Joe DeRosa, Matt McCusker, Shane Gillis, MSSP Theme Music
   🔑 Environment Variables Needed
   INSTANT_APP_ID=<from InstantDB dashboard>INSTANT_ADMIN_SECRET=<from InstantDB dashboard>HF_TOKEN=<for PyAnnote diarization>
   Ready for the next agent to pick up in the main repo! 🦜
