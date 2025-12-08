/*
  HOW:
  `bun run apps/speaker-diarization-benchmark/scripts/one_off/delete_all_transcription_segments.ts [--execute]`

  [Inputs]
  - --execute: If provided, actually performs the deletion. Otherwise runs in dry-run mode.
  - INSTANT_APP_ID (env): Required for InstantDB connection
  - INSTANT_ADMIN_SECRET (env): Required for InstantDB admin access

  [Outputs]
  - Console output showing how many transcription segments will be deleted
  - If --execute is provided, performs the actual deletion and verifies results

  [Side Effects]
  - If --execute is provided, deletes all transcription segments from InstantDB

  WHO:
  Antigravity, User
  (Context: Cleaning up transcription segments)

  WHAT:
  Deletes all transcription segments from the database. This is useful for cleaning up
  test data or resetting the transcription segments while keeping other entities intact.

  WHEN:
  2025-01-27
  Last Modified: 2025-01-27

  WHERE:
  apps/speaker-diarization-benchmark/scripts/one_off/delete_all_transcription_segments.ts

  WHY:
  To remove all transcription segments from the database, typically for cleanup or
  reset purposes during schema development.
*/

import { init } from "@instantdb/admin";
import { config } from "dotenv";
import { join } from "path";
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

async function main() {
  console.log(DRY_RUN ? "🔍 DRY RUN MODE" : "🚀 EXECUTION MODE");
  console.log("=".repeat(50));

  // Query all transcription segments
  console.log("\n📊 Loading transcription segments...");
  const transcriptionSegmentsQuery = await db.query({
    transcriptionSegments: {
      $: {},
    },
  });
  const transcriptionSegments =
    transcriptionSegmentsQuery.transcriptionSegments || [];
  console.log(`Found ${transcriptionSegments.length} transcription segments`);

  if (transcriptionSegments.length === 0) {
    console.log("\n✅ No transcription segments found. Nothing to delete.");
    return;
  }

  // Display summary
  console.log("\n📋 SUMMARY");
  console.log("=".repeat(50));
  console.log(`Transcription Segments to Delete: ${transcriptionSegments.length}`);

  // Show some examples
  if (transcriptionSegments.length > 0) {
    console.log("\n📝 Example Segments to Delete:");
    transcriptionSegments.slice(0, 5).forEach((segment: any) => {
      const textPreview =
        segment.text && segment.text.length > 50
          ? segment.text.substring(0, 50) + "..."
          : segment.text || "(no text)";
      console.log(
        `  - [${segment.start_time}s-${segment.end_time}s]: ${textPreview}`
      );
    });
    if (transcriptionSegments.length > 5) {
      console.log(`  ... and ${transcriptionSegments.length - 5} more`);
    }
  }

  if (DRY_RUN) {
    console.log(
      "\n💡 This was a dry run. Use --execute to perform the actual deletion."
    );
    return;
  }

  // Execute the deletion
  console.log("\n🚀 Executing deletion...");

  const transactions: any[] = [];

  // Create transactions for deleting segments
  for (const segment of transcriptionSegments) {
    transactions.push(db.tx.transcriptionSegments[segment.id].delete());
  }

  // Batch transactions (100 at a time)
  const batchSize = 100;
  let deletedCount = 0;

  for (let i = 0; i < transactions.length; i += batchSize) {
    const batch = transactions.slice(i, i + batchSize);
    await db.transact(batch);
    deletedCount += batch.length;
    console.log(`  Deleted ${deletedCount}/${transactions.length} segments...`);
  }

  console.log("✅ All segments deleted successfully!");

  // Verify deletion
  console.log("\n🔍 Verifying deletion...");

  const verifyQuery = await db.query({
    transcriptionSegments: {
      $: {},
    },
  });

  const remainingCount = verifyQuery.transcriptionSegments?.length || 0;

  if (remainingCount === 0) {
    console.log(
      `✅ Verification complete: All ${transcriptionSegments.length} transcription segments have been deleted.`
    );
  } else {
    console.log(
      `⚠️  Verification: ${remainingCount} transcription segments still remain.`
    );
  }

  console.log("\n✅ Done!");
}

main().catch((error) => {
  console.error("❌ Error:", error);
  process.exit(1);
});



