/*
  HOW:
  Start the server:
    bun run apps/speaker-diarization-benchmark/ingestion/instant_server.ts
  
  Or with specific port:
    PORT=3001 bun run apps/speaker-diarization-benchmark/ingestion/instant_server.ts

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
  A lightweight HTTP server that wraps InstantDB Admin SDK operations.
  Python scripts call this server to interact with InstantDB, keeping
  all InstantDB logic in TypeScript where it's officially supported.

  Endpoints:
  - GET  /health                    - Health check
  - POST /query                     - Execute an InstaQL query
  - POST /transact                  - Execute a transaction
  - GET  /videos/:id                - Get video with runs and segments
  - GET  /diarization-segments      - Get segments for a video/run
  - POST /speaker-assignments       - Create speaker assignments

  WHEN:
  2025-12-07

  WHERE:
  apps/speaker-diarization-benchmark/ingestion/instant_server.ts

  WHY:
  InstantDB's official SDK is TypeScript/JavaScript. The Python client
  is unofficial and unreliable. This server provides a clean interface
  for Python scripts to use InstantDB through HTTP.
*/

import { init, id, tx } from "@instantdb/admin";
import { config } from "dotenv";
import { join } from "path";

// Load .env from toolshed root
config({ path: join(__dirname, "../../../.env") });

const APP_ID = process.env.INSTANT_APP_ID!;
const ADMIN_TOKEN = process.env.INSTANT_ADMIN_SECRET!;
const PORT = parseInt(process.env.PORT || "3001");

if (!APP_ID || !ADMIN_TOKEN) {
  console.error("❌ Missing INSTANT_APP_ID or INSTANT_ADMIN_SECRET");
  process.exit(1);
}

const db = init({
  appId: APP_ID,
  adminToken: ADMIN_TOKEN,
});

console.log(`🚀 InstantDB Server starting...`);
console.log(`   App ID: ${APP_ID.slice(0, 8)}...`);

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
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };

    // Handle CORS preflight
    if (method === "OPTIONS") {
      return new Response(null, { status: 204, headers });
    }

    try {
      // Health check
      if (path === "/health" && method === "GET") {
        return Response.json({ status: "ok", appId: APP_ID.slice(0, 8) }, { headers });
      }

      // Generic query endpoint
      if (path === "/query" && method === "POST") {
        const body = await req.json();
        const result = await db.query(body.query);
        return Response.json(result, { headers });
      }

      // Generic transact endpoint
      if (path === "/transact" && method === "POST") {
        const body = await req.json();
        const result = await db.transact(body.transactions);
        return Response.json(result, { headers });
      }

      // Get video with diarization data
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

      // Get diarization segments for a video or run
      if (path === "/diarization-segments" && method === "GET") {
        const videoId = url.searchParams.get("video_id");
        const runId = url.searchParams.get("run_id");
        const startTime = url.searchParams.get("start_time");
        const endTime = url.searchParams.get("end_time");

        let query: any = {
          diarizationSegments: {
            $: { where: {} },
            diarizationRun: {},
            speakerAssignments: {
              speaker: {},
            },
          },
        };

        // Build where clause
        // Note: InstantDB doesn't support complex joins, so we may need to filter client-side
        if (runId) {
          // Query by run ID through the relationship
          query = {
            diarizationRuns: {
              $: { where: { id: runId } },
              diarizationSegments: {
                speakerAssignments: {
                  speaker: {},
                },
              },
            },
          };
          
          const result = await db.query(query);
          let segments = result.diarizationRuns[0]?.diarizationSegments || [];
          
          // Filter by time range if provided
          if (startTime !== null) {
            segments = segments.filter((s: any) => s.end_time >= parseFloat(startTime!));
          }
          if (endTime !== null) {
            segments = segments.filter((s: any) => s.start_time <= parseFloat(endTime!));
          }
          
          // Sort by start time
          segments.sort((a: any, b: any) => a.start_time - b.start_time);
          
          return Response.json({ segments }, { headers });
        }

        if (videoId) {
          // Query through video -> diarizationRuns -> segments
          query = {
            videos: {
              $: { where: { id: videoId } },
              diarizationRuns: {
                $: { where: { is_preferred: true } },
                diarizationSegments: {
                  speakerAssignments: {
                    speaker: {},
                  },
                },
              },
            },
          };
          
          const result = await db.query(query);
          const video = result.videos[0];
          if (!video) {
            return Response.json({ error: "Video not found" }, { status: 404, headers });
          }
          
          let segments = video.diarizationRuns[0]?.diarizationSegments || [];
          
          // Filter by time range if provided
          if (startTime !== null) {
            segments = segments.filter((s: any) => s.end_time >= parseFloat(startTime!));
          }
          if (endTime !== null) {
            segments = segments.filter((s: any) => s.start_time <= parseFloat(endTime!));
          }
          
          // Sort by start time
          segments.sort((a: any, b: any) => a.start_time - b.start_time);
          
          return Response.json({ 
            segments,
            video_id: video.id,
            run_id: video.diarizationRuns[0]?.id,
          }, { headers });
        }

        return Response.json({ error: "video_id or run_id required" }, { status: 400, headers });
      }

      // Create speaker assignments (batch)
      if (path === "/speaker-assignments" && method === "POST") {
        const body = await req.json();
        const assignments = body.assignments as Array<{
          segment_id: string;
          speaker_id: string;
          source: string;
          confidence: number;
          note: any;
          assigned_by: string;
        }>;

        if (!assignments || !Array.isArray(assignments)) {
          return Response.json({ error: "assignments array required" }, { status: 400, headers });
        }

      // Build transactions
      const transactions = assignments.map((a) => {
        const assignmentId = id();
        // Note might be object or string - serialize if object
        const noteValue = typeof a.note === 'object' ? JSON.stringify(a.note) : a.note;
        
        return tx.speakerAssignments[assignmentId]
          .update({
            source: a.source,
            confidence: a.confidence,
            note: noteValue,
            assigned_by: a.assigned_by,
            assigned_at: new Date().toISOString(),
          })
          .link({ diarizationSegment: a.segment_id })
          .link({ speaker: a.speaker_id });
      });

        const result = await db.transact(transactions);
        return Response.json({ success: true, count: assignments.length, result }, { headers });
      }

      // Get or create speaker by name
      if (path === "/speakers" && method === "POST") {
        const body = await req.json();
        const name = body.name as string;

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
        const speakerId = id();
        await db.transact(
          tx.speakers[speakerId].update({
            name,
            is_human: true,
            ingested_at: new Date().toISOString(),
          })
        );

        // Fetch and return
        const result = await db.query({
          speakers: {
            $: { where: { id: speakerId } },
          },
        });

        return Response.json({ speaker: result.speakers[0], created: true }, { headers });
      }

      // List all speakers
      if (path === "/speakers" && method === "GET") {
        const result = await db.query({ speakers: {} });
        return Response.json({ speakers: result.speakers }, { headers });
      }

      // 404 for unknown routes
      return Response.json({ error: "Not found", path }, { status: 404, headers });
      
    } catch (error: any) {
      console.error("Error:", error);
      return Response.json(
        { error: error.message || "Internal server error" },
        { status: 500, headers }
      );
    }
  },
});

console.log(`✅ InstantDB Server running on http://localhost:${PORT}`);
console.log(`   Endpoints:`);
console.log(`   - GET  /health`);
console.log(`   - POST /query`);
console.log(`   - POST /transact`);
console.log(`   - GET  /videos/:id`);
console.log(`   - GET  /diarization-segments?video_id=...&start_time=...&end_time=...`);
console.log(`   - POST /speaker-assignments`);
console.log(`   - GET  /speakers`);
console.log(`   - POST /speakers`);

