"use strict";
/*
  HOW:
  Start the server:
    bun run apps/speaker-diarization-benchmark/ingestion/instant_proxy.ts
  
  Or with specific port:
    PORT=3001 bun run apps/speaker-diarization-benchmark/ingestion/instant_proxy.ts

  Or via Docker:
    docker compose up -d instant-proxy

  [Inputs]
  - INSTANT_APP_ID (env): Required for InstantDB connection
  - INSTANT_ADMIN_SECRET (env): Required for InstantDB admin access
  - PORT (env): Server port (default: 3001)

  [Outputs]
  - HTTP server on localhost:{PORT}
  - JSON responses for all endpoints

  [Side Effects]
  - Reads/writes to InstantDB via Admin SDK

  WHO:
  Claude AI, User
  (Context: TypeScript server for InstantDB operations)

  WHAT:
  A REST API server that wraps InstantDB Admin SDK operations.
  Python scripts call this server to interact with InstantDB, keeping
  all InstantDB logic in TypeScript where it's officially supported.

  Endpoints:
  - GET  /health                    - Health check
  - GET  /videos/:id                - Get video with runs and segments
  - POST /videos                    - Create or update a video
  - PUT  /videos/:id                - Update video metadata
  - GET  /diarization-segments      - Get segments for a video/run
  - POST /diarization-segments      - Save diarization segments (batch)
  - POST /ingestion-runs            - Save video + transcription + diarization runs with metrics
  - POST /words                     - Save transcription words (batch)
  - POST /speaker-assignments       - Create speaker assignments
  - GET  /speakers                  - List all speakers
  - POST /speakers                  - Create or get speaker by name
  - DELETE /speakers/:id            - Delete a speaker

  WHEN:
  2025-12-07
  Last Modified: 2025-12-09
  [Change Log:
    - 2025-12-08: Refactored to proper REST verbs
    - 2025-12-09: Added DELETE /speakers/:id endpoint
    - 2025-12-09: Renamed from instant_server.ts to instant_proxy.ts for clarity
  ]

  WHERE:
  apps/speaker-diarization-benchmark/ingestion/instant_proxy.ts

  WHY:
  InstantDB's official SDK is TypeScript/JavaScript. The Python client
  is unofficial and unreliable. This server provides a clean REST interface
  for Python scripts to use InstantDB through HTTP.
*/
Object.defineProperty(exports, "__esModule", { value: true });
const admin_1 = require("@instantdb/admin");
const dotenv_1 = require("dotenv");
const path_1 = require("path");
const fs_1 = require("fs");
// Load .env from various possible locations
const envPaths = [
    (0, path_1.join)(__dirname, "../../../.env"), // Local: toolshed root
    (0, path_1.join)(__dirname, "../../.env"), // Local: apps/speaker-diarization
    ".env", // Docker or current dir
];
for (const envPath of envPaths) {
    if ((0, fs_1.existsSync)(envPath)) {
        (0, dotenv_1.config)({ path: envPath });
        break;
    }
}
const APP_ID = process.env.INSTANT_APP_ID;
const ADMIN_TOKEN = process.env.INSTANT_ADMIN_SECRET;
const PORT = parseInt(process.env.PORT || "3001");
if (!APP_ID || !ADMIN_TOKEN) {
    console.error("❌ Missing INSTANT_APP_ID or INSTANT_ADMIN_SECRET");
    process.exit(1);
}
const db = (0, admin_1.init)({
    appId: APP_ID,
    adminToken: ADMIN_TOKEN,
});
console.log(`🚀 InstantDB Proxy starting...`);
console.log(`   App ID: ${APP_ID.slice(0, 8)}...`);
// Helper to get current ISO timestamp
const now = () => new Date().toISOString();
// Simple HTTP server using Bun
const server = Bun.serve({
    port: PORT,
    async fetch(req) {
        const url = new URL(req.url);
        const path = url.pathname;
        const method = req.method;
        // CORS headers for local development
        const headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        };
        // Handle CORS preflight
        if (method === "OPTIONS") {
            return new Response(null, { status: 204, headers });
        }
        try {
            // =========================================================================
            // Health check
            // =========================================================================
            if (path === "/health" && method === "GET") {
                return Response.json({ status: "ok", appId: APP_ID.slice(0, 8) }, { headers });
            }
            // =========================================================================
            // GET /videos - List videos or filter by source_id
            // =========================================================================
            if (path === "/videos" && method === "GET") {
                const sourceId = url.searchParams.get("source_id");
                const result = await db.query({
                    videos: {
                        transcriptionRuns: {},
                        diarizationRuns: {},
                    },
                });
                let videos = result.videos || [];
                // Filter by source_id if provided
                if (sourceId) {
                    videos = videos.filter((v) => v.source_id === sourceId);
                }
                return Response.json({ videos }, { headers });
            }
            // =========================================================================
            // POST /videos - Create or update a video
            // =========================================================================
            if (path === "/videos" && method === "POST") {
                const body = await req.json();
                const { id: videoId, title, url: videoUrl, filepath, duration, description, } = body;
                if (!videoId || !title) {
                    return Response.json({ error: "id and title required" }, { status: 400, headers });
                }
                await db.transact(admin_1.tx.videos[videoId].update({
                    title,
                    url: videoUrl || `file://${filepath}`,
                    filepath,
                    duration: duration || 0,
                    description,
                    ingested_at: now(),
                }));
                return Response.json({ success: true, video_id: videoId }, { headers });
            }
            // =========================================================================
            // PUT /videos/:id - Update video metadata (partial update)
            // =========================================================================
            if (path.startsWith("/videos/") && method === "PUT") {
                const videoId = path.split("/")[2];
                const body = await req.json();
                // Only update provided fields
                const updateData = {};
                if (body.title !== undefined)
                    updateData.title = body.title;
                if (body.source_id !== undefined)
                    updateData.source_id = body.source_id;
                if (body.url !== undefined)
                    updateData.url = body.url;
                if (body.filepath !== undefined)
                    updateData.filepath = body.filepath;
                if (body.duration !== undefined)
                    updateData.duration = body.duration;
                if (body.description !== undefined)
                    updateData.description = body.description;
                if (Object.keys(updateData).length === 0) {
                    return Response.json({ error: "No fields to update" }, { status: 400, headers });
                }
                await db.transact(admin_1.tx.videos[videoId].update(updateData));
                return Response.json({ success: true, video_id: videoId }, { headers });
            }
            // =========================================================================
            // GET /videos/:id - Get video with runs and segments
            // =========================================================================
            if (path.startsWith("/videos/") && method === "GET") {
                const videoId = path.split("/")[2];
                const result = await db.query({
                    videos: {
                        $: { where: { id: videoId } },
                        diarizationRuns: {
                            diarizationSegments: {
                                speakerAssignments: {
                                    speaker: {},
                                },
                            },
                        },
                        transcriptionRuns: {
                            words: {},
                        },
                    },
                });
                if (result.videos.length === 0) {
                    return Response.json({ error: "Video not found" }, { status: 404, headers });
                }
                return Response.json(result.videos[0], { headers });
            }
            // =========================================================================
            // POST /ingestion-runs - Save video + transcription + diarization runs
            //
            // This is the main endpoint for the audio ingestion pipeline.
            // If a video with the same source_id exists, reuses it. Otherwise creates new.
            // IDs are generated by InstantDB using id() - the source_id (e.g., YouTube ID)
            // is stored as an attribute.
            // =========================================================================
            if (path === "/ingestion-runs" && method === "POST") {
                const body = await req.json();
                const { video, transcriptionRun, diarizationRun } = body;
                if (!video) {
                    return Response.json({ error: "video object required" }, { status: 400, headers });
                }
                const transRunId = (0, admin_1.id)();
                const diarRunId = (0, admin_1.id)();
                const timestamp = now();
                // Check if video with this source_id already exists
                let videoId;
                let isNewVideo = false;
                if (video.source_id) {
                    const existing = await db.query({
                        videos: {
                            $: { where: { source_id: video.source_id } },
                        },
                    });
                    if (existing.videos && existing.videos.length > 0) {
                        videoId = existing.videos[0].id;
                        console.log(`Found existing video for source_id=${video.source_id}: ${videoId}`);
                    }
                    else {
                        videoId = (0, admin_1.id)();
                        isNewVideo = true;
                    }
                }
                else {
                    videoId = (0, admin_1.id)();
                    isNewVideo = true;
                }
                try {
                    // Step 1: Create or update video
                    // source_id stores the original identifier (e.g., YouTube video ID)
                    if (isNewVideo) {
                        await db.transact(admin_1.tx.videos[videoId].update({
                            source_id: video.source_id,
                            title: video.title || video.source_id || "Untitled",
                            url: video.url || `file://${video.filepath}`,
                            filepath: video.filepath,
                            duration: video.duration || 0,
                            description: video.description,
                            ingested_at: timestamp,
                        }));
                    }
                    else {
                        // Update existing video metadata (optional fields only)
                        const updateData = { ingested_at: timestamp };
                        if (video.title)
                            updateData.title = video.title;
                        if (video.duration)
                            updateData.duration = video.duration;
                        if (video.description)
                            updateData.description = video.description;
                        await db.transact(admin_1.tx.videos[videoId].update(updateData));
                    }
                    // Step 2: Create transcription run with metrics (if provided)
                    if (transcriptionRun) {
                        await db.transact(admin_1.tx.transcriptionRuns[transRunId]
                            .update({
                            tool_version: transcriptionRun.tool_version || "mlx-whisper",
                            pipeline_script: transcriptionRun.pipeline_script || "audio_ingestion.py",
                            is_preferred: transcriptionRun.is_preferred ?? true,
                            input_duration_seconds: transcriptionRun.input_duration_seconds,
                            processing_time_seconds: transcriptionRun.processing_time_seconds,
                            peak_memory_mb: transcriptionRun.peak_memory_mb,
                            cost_usd: transcriptionRun.cost_usd,
                            executed_at: timestamp,
                        })
                            .link({ video: videoId }));
                    }
                    // Step 3: Create diarization run with metrics (if provided)
                    if (diarizationRun) {
                        await db.transact(admin_1.tx.diarizationRuns[diarRunId]
                            .update({
                            workflow: diarizationRun.workflow || "pyannote",
                            tool_version: diarizationRun.tool_version || "pyannote-audio-3.1",
                            pipeline_script: diarizationRun.pipeline_script || "audio_ingestion.py",
                            is_preferred: diarizationRun.is_preferred ?? true,
                            num_speakers_detected: diarizationRun.num_speakers_detected,
                            input_duration_seconds: diarizationRun.input_duration_seconds,
                            processing_time_seconds: diarizationRun.processing_time_seconds,
                            peak_memory_mb: diarizationRun.peak_memory_mb,
                            cost_usd: diarizationRun.cost_usd,
                            executed_at: timestamp,
                        })
                            .link({ video: videoId }));
                    }
                    return Response.json({
                        success: true,
                        video_id: videoId,
                        transcription_run_id: transcriptionRun ? transRunId : null,
                        diarization_run_id: diarizationRun ? diarRunId : null,
                    }, { headers });
                }
                catch (txError) {
                    console.error("Transaction error:", txError.message);
                    console.error("Transaction hint:", txError.hint);
                    return Response.json({
                        error: txError.message,
                        hint: txError.hint,
                    }, { status: 500, headers });
                }
            }
            // =========================================================================
            // POST /diarization-segments - Save diarization segments (batch)
            // =========================================================================
            if (path === "/diarization-segments" && method === "POST") {
                const body = await req.json();
                const { run_id, segments } = body;
                if (!run_id || !segments || !Array.isArray(segments)) {
                    return Response.json({ error: "run_id and segments array required" }, { status: 400, headers });
                }
                const timestamp = now();
                const segmentIds = [];
                // Create segments in batches to avoid timeout
                for (const seg of segments) {
                    const segId = (0, admin_1.id)();
                    segmentIds.push(segId);
                    await db.transact(admin_1.tx.diarizationSegments[segId]
                        .update({
                        start_time: seg.start_time,
                        end_time: seg.end_time,
                        speaker_label: seg.speaker_label || seg.speaker || "UNKNOWN",
                        confidence: seg.confidence,
                        embedding_id: seg.embedding_id,
                        is_invalidated: false,
                        created_at: timestamp,
                    })
                        .link({ diarizationRun: run_id }));
                }
                return Response.json({ success: true, count: segmentIds.length, segment_ids: segmentIds }, { headers });
            }
            // =========================================================================
            // POST /words - Save transcription words (batch)
            // =========================================================================
            if (path === "/words" && method === "POST") {
                const body = await req.json();
                const { run_id, words } = body;
                if (!run_id || !words || !Array.isArray(words)) {
                    return Response.json({ error: "run_id and words array required" }, { status: 400, headers });
                }
                const timestamp = now();
                const wordIds = [];
                // Create words in batches
                for (const word of words) {
                    const wordId = (0, admin_1.id)();
                    wordIds.push(wordId);
                    await db.transact(admin_1.tx.words[wordId]
                        .update({
                        text: word.text ?? word.word,
                        start_time: word.start_time ?? word.start,
                        end_time: word.end_time ?? word.end,
                        confidence: word.confidence ?? word.probability,
                        transcription_segment_index: word.transcription_segment_index,
                        ingested_at: timestamp,
                    })
                        .link({ transcriptionRun: run_id }));
                }
                return Response.json({ success: true, count: wordIds.length }, { headers });
            }
            // =========================================================================
            // GET /diarization-segments - Get segments for a video or run
            // =========================================================================
            if (path === "/diarization-segments" && method === "GET") {
                const videoId = url.searchParams.get("video_id");
                const runId = url.searchParams.get("run_id");
                const startTime = url.searchParams.get("start_time");
                const endTime = url.searchParams.get("end_time");
                if (runId) {
                    // Query by run ID
                    const result = await db.query({
                        diarizationRuns: {
                            $: { where: { id: runId } },
                            diarizationSegments: {
                                speakerAssignments: {
                                    speaker: {},
                                },
                            },
                        },
                    });
                    let segments = result.diarizationRuns[0]?.diarizationSegments || [];
                    // Filter by time range
                    if (startTime !== null) {
                        segments = segments.filter((s) => s.end_time >= parseFloat(startTime));
                    }
                    if (endTime !== null) {
                        segments = segments.filter((s) => s.start_time <= parseFloat(endTime));
                    }
                    segments.sort((a, b) => a.start_time - b.start_time);
                    return Response.json({ segments }, { headers });
                }
                if (videoId) {
                    // Query through video - get all diarization runs with segments
                    const result = await db.query({
                        videos: {
                            $: { where: { id: videoId } },
                            diarizationRuns: {
                                diarizationSegments: {
                                    speakerAssignments: {
                                        speaker: {},
                                    },
                                },
                            },
                        },
                    });
                    const video = result.videos[0];
                    if (!video) {
                        return Response.json({ error: "Video not found" }, { status: 404, headers });
                    }
                    // Select the run with the most segments
                    const runs = video.diarizationRuns || [];
                    const bestRun = runs
                        .filter((r) => r.diarizationSegments && r.diarizationSegments.length > 0)
                        .sort((a, b) => (b.diarizationSegments?.length || 0) -
                        (a.diarizationSegments?.length || 0))[0];
                    let segments = bestRun?.diarizationSegments || [];
                    if (startTime !== null) {
                        segments = segments.filter((s) => s.end_time >= parseFloat(startTime));
                    }
                    if (endTime !== null) {
                        segments = segments.filter((s) => s.start_time <= parseFloat(endTime));
                    }
                    segments.sort((a, b) => a.start_time - b.start_time);
                    return Response.json({
                        segments,
                        video_id: video.id,
                        run_id: bestRun?.id,
                    }, { headers });
                }
                return Response.json({ error: "video_id or run_id required" }, { status: 400, headers });
            }
            // =========================================================================
            // POST /speaker-assignments - Create speaker assignments (batch)
            // =========================================================================
            if (path === "/speaker-assignments" && method === "POST") {
                const body = await req.json();
                const assignments = body.assignments;
                if (!assignments || !Array.isArray(assignments)) {
                    return Response.json({ error: "assignments array required" }, { status: 400, headers });
                }
                // Build transactions, finding/creating speakers by name if needed
                const transactions = [];
                const speakerIdCache = {};
                for (const a of assignments) {
                    let speakerId = a.speaker_id;
                    // If no speaker_id but we have speaker_name, find or create speaker
                    if (!speakerId && a.speaker_name) {
                        // Check cache first
                        if (speakerIdCache[a.speaker_name]) {
                            speakerId = speakerIdCache[a.speaker_name];
                        }
                        else {
                            // Query for existing speaker by name
                            const existing = await db.query({
                                speakers: { $: { where: { name: a.speaker_name } } },
                            });
                            if (existing.speakers && existing.speakers.length > 0) {
                                speakerId = existing.speakers[0].id;
                            }
                            else {
                                // Create new speaker
                                speakerId = (0, admin_1.id)();
                                transactions.push(admin_1.tx.speakers[speakerId].update({
                                    name: a.speaker_name,
                                    is_human: true,
                                    ingested_at: now(),
                                }));
                            }
                            speakerIdCache[a.speaker_name] = speakerId;
                        }
                    }
                    if (!speakerId) {
                        console.log(`Skipping assignment - no speaker_id or speaker_name for segment ${a.segment_id}`);
                        continue;
                    }
                    const assignmentId = (0, admin_1.id)();
                    const noteValue = typeof a.note === "object" ? JSON.stringify(a.note) : a.note;
                    transactions.push(admin_1.tx.speakerAssignments[assignmentId]
                        .update({
                        source: a.source,
                        confidence: a.confidence,
                        note: noteValue,
                        assigned_by: a.assigned_by,
                        assigned_at: now(),
                    })
                        .link({ diarizationSegment: a.segment_id })
                        .link({ speaker: speakerId }));
                }
                const result = await db.transact(transactions);
                return Response.json({ success: true, count: assignments.length, result }, { headers });
            }
            // =========================================================================
            // GET /speakers - List all speakers
            // =========================================================================
            if (path === "/speakers" && method === "GET") {
                const result = await db.query({ speakers: {} });
                return Response.json({ speakers: result.speakers }, { headers });
            }
            // =========================================================================
            // POST /speakers - Create or get speaker by name
            // =========================================================================
            if (path === "/speakers" && method === "POST") {
                const body = await req.json();
                const name = body.name;
                if (!name) {
                    return Response.json({ error: "name required" }, { status: 400, headers });
                }
                // Check if speaker exists
                const existing = await db.query({
                    speakers: {
                        $: { where: { name } },
                    },
                });
                if (existing.speakers.length > 0) {
                    return Response.json({ speaker: existing.speakers[0], created: false }, { headers });
                }
                // Create new speaker
                const speakerId = (0, admin_1.id)();
                await db.transact(admin_1.tx.speakers[speakerId].update({
                    name,
                    is_human: true,
                    ingested_at: now(),
                }));
                const result = await db.query({
                    speakers: {
                        $: { where: { id: speakerId } },
                    },
                });
                return Response.json({ speaker: result.speakers[0], created: true }, { headers });
            }
            // =========================================================================
            // DELETE /speakers/:id - Delete a speaker
            // =========================================================================
            if (path.startsWith("/speakers/") && method === "DELETE") {
                const speakerId = path.split("/")[2];
                if (!speakerId) {
                    return Response.json({ error: "speaker_id required" }, { status: 400, headers });
                }
                try {
                    // Delete the speaker
                    await db.transact(admin_1.tx.speakers[speakerId].delete());
                    return Response.json({ success: true, deleted_id: speakerId }, { headers });
                }
                catch (error) {
                    console.error(`Failed to delete speaker ${speakerId}:`, error);
                    return Response.json({ error: error.message || "Failed to delete speaker" }, { status: 500, headers });
                }
            }
            // =========================================================================
            // PUT /diarization-segments/embedding-ids - Update embedding_ids for segments
            // =========================================================================
            if (path === "/diarization-segments/embedding-ids" && method === "PUT") {
                const body = await req.json();
                const updates = body.updates;
                if (!updates || !Array.isArray(updates)) {
                    return Response.json({ error: "updates array required" }, { status: 400, headers });
                }
                const transactions = [];
                for (const update of updates) {
                    transactions.push(admin_1.tx.diarizationSegments[update.segment_id].update({
                        embedding_id: update.embedding_id,
                    }));
                }
                await db.transact(transactions);
                return Response.json({ success: true, count: updates.length }, { headers });
            }
            // 404 for unknown routes
            return Response.json({ error: "Not found", path }, { status: 404, headers });
        }
        catch (error) {
            console.error("Error:", error.message);
            return Response.json({ error: error.message || "Internal server error" }, { status: 500, headers });
        }
    },
});
console.log(`✅ InstantDB Proxy running on http://localhost:${PORT}`);
console.log(`   Endpoints:`);
console.log(`   - GET  /health`);
console.log(`   - POST /videos`);
console.log(`   - GET  /videos/:id`);
console.log(`   - PUT  /videos/:id`);
console.log(`   - POST /ingestion-runs`);
console.log(`   - GET  /diarization-segments`);
console.log(`   - POST /diarization-segments`);
console.log(`   - POST /words`);
console.log(`   - POST /speaker-assignments`);
console.log(`   - GET  /speakers`);
console.log(`   - POST /speakers`);
console.log(`   - DELETE /speakers/:id`);
console.log(`   - PUT  /diarization-segments/embedding-ids`);
