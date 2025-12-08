/*
  HOW:
  `bun run apps/speaker-diarization-benchmark/scripts/one_off/check_diarization_data.ts`

  [Inputs]
  - INSTANT_APP_ID (env): Required for InstantDB connection
  - INSTANT_ADMIN_SECRET (env): Required for InstantDB admin access

  [Outputs]
  - Console output showing diarization data for Joe DeRosa episode

  [Side Effects]
  - None (read-only query)

  WHO:
  Claude AI, User
  (Context: Checking InstantDB for existing diarization data)

  WHAT:
  Queries InstantDB to find the Joe DeRosa episode (jAlKYYr1bpY) and display
  its diarization runs and segments. This helps verify data exists before
  running identification workflows.

  WHEN:
  2025-12-07

  WHERE:
  apps/speaker-diarization-benchmark/scripts/one_off/check_diarization_data.ts

  WHY:
  To verify existing diarization data in InstantDB before implementing
  the speaker identification workflow.
*/

import { init } from "@instantdb/admin";
import { config } from "dotenv";
import { join } from "path";

// Load .env from toolshed root
config({ path: join(__dirname, "../../../../.env") });

const APP_ID = process.env.INSTANT_APP_ID!;
const ADMIN_TOKEN = process.env.INSTANT_ADMIN_SECRET!;

if (!APP_ID || !ADMIN_TOKEN) {
  console.error("Missing INSTANT_APP_ID or INSTANT_ADMIN_SECRET");
  console.error("Make sure your .env file has these variables set");
  process.exit(1);
}

const db = init({
  appId: APP_ID,
  adminToken: ADMIN_TOKEN,
});

async function main() {
  console.log("🔍 Checking InstantDB for Joe DeRosa episode data...\n");

  // Query all videos with their diarization runs
  const result = await db.query({
    videos: {
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

  const videos = result.videos || [];
  console.log(`📹 Found ${videos.length} videos in InstantDB\n`);

  // Find Joe DeRosa episode
  const joeDeRosaVideos = videos.filter(
    (v) =>
      v.url?.includes("jAlKYYr1bpY") ||
      v.title?.toLowerCase().includes("derosa") ||
      v.title?.includes("569")
  );

  if (joeDeRosaVideos.length === 0) {
    console.log("❌ No Joe DeRosa episode found in InstantDB");
    console.log("\nAll video titles:");
    videos.forEach((v) => console.log(`  - ${v.title || v.id}`));
    return;
  }

  for (const video of joeDeRosaVideos) {
    console.log("═".repeat(60));
    console.log(`📼 ${video.title}`);
    console.log("═".repeat(60));
    console.log(`ID: ${video.id}`);
    console.log(`URL: ${video.url}`);
    console.log(`Duration: ${video.duration}s`);
    console.log(`Filepath: ${video.filepath}`);

    // Diarization Runs
    const diarRuns = video.diarizationRuns || [];
    console.log(`\n🎙️ Diarization Runs: ${diarRuns.length}`);

    for (const run of diarRuns) {
      const segments = run.diarizationSegments || [];
      console.log(`\n  Run: ${run.id.slice(0, 8)}...`);
      console.log(`    Workflow: ${run.workflow}`);
      console.log(`    Executed: ${run.executed_at}`);
      console.log(`    Segments: ${segments.length}`);
      console.log(`    Preferred: ${run.is_preferred}`);

      // Show first few segments
      if (segments.length > 0) {
        console.log(`    Sample segments:`);
        segments.slice(0, 5).forEach((seg) => {
          const assignments = seg.speakerAssignments || [];
          const speaker =
            assignments[0]?.speaker?.[0]?.name ||
            seg.speaker_label ||
            "UNKNOWN";
          console.log(
            `      ${seg.start_time?.toFixed(1)}s - ${seg.end_time?.toFixed(1)}s: ${speaker}`
          );
        });
        if (segments.length > 5) {
          console.log(`      ... and ${segments.length - 5} more`);
        }
      }
    }

    // Transcription Runs
    const transRuns = video.transcriptionRuns || [];
    console.log(`\n📝 Transcription Runs: ${transRuns.length}`);

    for (const run of transRuns) {
      const words = run.words || [];
      console.log(`\n  Run: ${run.id.slice(0, 8)}...`);
      console.log(`    Tool: ${run.tool_version}`);
      console.log(`    Words: ${words.length}`);
      console.log(`    Preferred: ${run.is_preferred}`);
    }
  }

  // Also list all videos for reference
  console.log("\n\n📋 All Videos in DB:");
  videos.forEach((v) => {
    const diarCount = v.diarizationRuns?.length || 0;
    const transCount = v.transcriptionRuns?.length || 0;
    console.log(
      `  - ${v.title || v.id.slice(0, 8)} (${diarCount} diar, ${transCount} trans)`
    );
  });
}

main().catch(console.error);

