/*
  HOW:
  `bun run apps/speaker-diarization-benchmark/scripts/one_off/create_transcription_segments_from_json.ts [--execute]`

  [Inputs]
  - --execute: If provided, actually performs the creation. Otherwise runs in dry-run mode.
  - INSTANT_APP_ID (env): Required for InstantDB connection
  - INSTANT_ADMIN_SECRET (env): Required for InstantDB admin access

  [Outputs]
  - Console output showing which transcription segments will be created
  - If --execute is provided, creates the segments and links them to the transcription run

  [Side Effects]
  - If --execute is provided, creates transcription segments in InstantDB and links them to the run

  WHO:
  Antigravity, User
  (Context: Creating transcription segments from verified JSON file)

  WHAT:
  Creates transcription segments from the verified JSON file and links them to the existing
  transcription run. Assumes confidence of 1.0 for all segments and creates words array with
  single word entries based on the text.

  WHEN:
  2025-01-27
  Last Modified: 2025-01-27

  WHERE:
  apps/speaker-diarization-benchmark/scripts/one_off/create_transcription_segments_from_json.ts

  WHY:
  To populate transcription segments from verified ground truth data for schema establishment
  and testing purposes.
*/

import { init, id } from "@instantdb/admin";
import { config } from "dotenv";
import { join } from "path";
import { readFileSync } from "fs";
import instantSchema from "../../../../packages/schema/instant.schema";

// Load .env from toolshed root
config({ path: join(__dirname, "../../../../.env") });

const APP_ID = process.env.INSTANT_APP_ID!;
const ADMIN_TOKEN = process.env.INSTANT_ADMIN_SECRET!;

if (!APP_ID || !ADMIN_TOKEN) {
  console.error("Missing INSTANT_APP_ID or INSTANT_ADMIN_SECRET");
  process.exit(1);
}

const db = init({
  appId: APP_ID,
  adminToken: ADMIN_TOKEN,
  schema: instantSchema,
});

const DRY_RUN = !process.argv.includes("--execute");

const JSON_FILE_PATH = join(
  __dirname,
  "../../joe-derosa-mssp-0-60-s-verified.json"
);

/**
 * Creates words array from text, assuming confidence of 1.0
 * Splits text into words and distributes time evenly across the segment
 */
function createWordsArray(
  text: string,
  startTime: number,
  endTime: number
): Array<{ word: string; start: number; end: number; conf: number }> {
  const words = text.trim().split(/\s+/).filter((w) => w.length > 0);
  if (words.length === 0) {
    return [];
  }

  const duration = endTime - startTime;
  const wordDuration = duration / words.length;

  return words.map((word, index) => ({
    word,
    start: startTime + index * wordDuration,
    end: startTime + (index + 1) * wordDuration,
    conf: 1.0,
  }));
}

async function main() {
  console.log(DRY_RUN ? "🔍 DRY RUN MODE" : "🚀 EXECUTION MODE");
  console.log("=".repeat(50));

  // Load JSON file
  console.log("\n📄 Loading JSON file...");
  const jsonData = JSON.parse(readFileSync(JSON_FILE_PATH, "utf-8"));
  const transcriptionKey = Object.keys(jsonData.transcriptions)[0];
  const segments = jsonData.transcriptions[transcriptionKey] || [];
  console.log(`Found ${segments.length} segments in JSON file`);

  if (segments.length === 0) {
    console.log("\n⚠️  No segments found in JSON file. Exiting.");
    return;
  }

  // Query for the transcription run
  console.log("\n📊 Loading transcription run...");
  const transcriptionRunsQuery = await db.query({
    transcriptionRuns: {
      $: {},
    },
  });
  const transcriptionRuns = transcriptionRunsQuery.transcriptionRuns || [];

  if (transcriptionRuns.length === 0) {
    console.log("\n⚠️  No transcription runs found. Exiting.");
    return;
  }

  if (transcriptionRuns.length > 1) {
    console.log(
      `\n⚠️  Found ${transcriptionRuns.length} transcription runs. Using the first one.`
    );
  }

  const transcriptionRun = transcriptionRuns[0];
  console.log(`Using transcription run: ${transcriptionRun.id}`);

  // Prepare segments for creation
  console.log("\n🔗 Preparing segments...");
  const segmentsToCreate = segments.map((segment: any) => {
    const segmentId = id();
    const words = createWordsArray(segment.text, segment.start, segment.end);
    const createdAt = new Date().toISOString();

    return {
      id: segmentId,
      run_id: transcriptionRun.id,
      start_time: segment.start,
      end_time: segment.end,
      text: segment.text,
      words: words,
      created_at: createdAt,
    };
  });

  console.log(`Prepared ${segmentsToCreate.length} segments for creation`);

  // Display summary
  console.log("\n📋 SUMMARY");
  console.log("=".repeat(50));
  console.log(`Transcription Run ID: ${transcriptionRun.id}`);
  console.log(`Segments to Create: ${segmentsToCreate.length}`);

  // Show some examples
  if (segmentsToCreate.length > 0) {
    console.log("\n📝 Example Segments:");
    segmentsToCreate.slice(0, 5).forEach((segment) => {
      const textPreview =
        segment.text.length > 50
          ? segment.text.substring(0, 50) + "..."
          : segment.text;
      console.log(
        `  - [${segment.start_time}s-${segment.end_time}s]: ${textPreview} (${segment.words.length} words)`
      );
    });
    if (segmentsToCreate.length > 5) {
      console.log(`  ... and ${segmentsToCreate.length - 5} more`);
    }
  }

  if (DRY_RUN) {
    console.log(
      "\n💡 This was a dry run. Use --execute to perform the actual creation."
    );
    return;
  }

  // Execute the creation
  console.log("\n🚀 Creating segments...");

  const transactions: any[] = [];

  // Create transactions for creating segments and linking them
  for (const segment of segmentsToCreate) {
    transactions.push(
      db.tx.transcriptionSegments[segment.id]
        .update({
          run_id: segment.run_id,
          start_time: segment.start_time,
          end_time: segment.end_time,
          text: segment.text,
          words: segment.words,
          created_at: segment.created_at,
        })
        .link({ run: segment.run_id })
    );
  }

  // Batch transactions (100 at a time)
  const batchSize = 100;
  let createdCount = 0;

  for (let i = 0; i < transactions.length; i += batchSize) {
    const batch = transactions.slice(i, i + batchSize);
    await db.transact(batch);
    createdCount += batch.length;
    console.log(`  Created ${createdCount}/${transactions.length} segments...`);
  }

  console.log("✅ All segments created successfully!");

  // Verify creation
  console.log("\n🔍 Verifying creation...");

  const verifyQuery = await db.query({
    transcriptionSegments: {
      $: { where: { run_id: transcriptionRun.id } },
    },
  });

  const createdCountFinal = verifyQuery.transcriptionSegments?.length || 0;

  if (createdCountFinal === segmentsToCreate.length) {
    console.log(
      `✅ Verification complete: All ${segmentsToCreate.length} transcription segments have been created and linked.`
    );
  } else {
    console.log(
      `⚠️  Verification: Expected ${segmentsToCreate.length} segments, found ${createdCountFinal}.`
    );
  }

  // Verify link
  const runQuery = await db.query({
    transcriptionRuns: {
      $: { where: { id: transcriptionRun.id } },
      transcriptionSegments: {},
    },
  });

  const linkedRun = runQuery.transcriptionRuns[0];
  if (linkedRun && linkedRun.transcriptionSegments) {
    console.log(
      `✅ Link verification: Transcription run has ${linkedRun.transcriptionSegments.length} linked segments.`
    );
  }

  console.log("\n✅ Done!");
}

main().catch((error) => {
  console.error("❌ Error:", error);
  process.exit(1);
});



