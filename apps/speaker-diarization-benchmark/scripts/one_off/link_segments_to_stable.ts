/*
  HOW:
  `bun run apps/speaker-diarization-benchmark/scripts/one_off/link_segments_to_stable.ts [--execute]`

  [Inputs]
  - --execute: If provided, actually performs the linking. Otherwise runs in dry-run mode.
  - INSTANT_APP_ID (env): Required for InstantDB connection
  - INSTANT_ADMIN_SECRET (env): Required for InstantDB admin access

  [Outputs]
  - Console output showing which segments will be linked to which stable segments
  - If --execute is provided, performs the actual linking and verifies results

  [Side Effects]
  - If --execute is provided, creates links between segments and stable segments in InstantDB

  WHO:
  Antigravity, User
  (Context: Linking transcription and diarization segments to stable segments based on time containment)

  WHAT:
  Links transcription segments and diarization segments to stable segments based on time containment.
  A segment is considered contained within a stable segment if:
  - stable_segment.start_time <= segment.start_time
  - stable_segment.end_time >= segment.end_time
  
  Segments can be contained within multiple stable segments (many-to-many relationship).

  WHEN:
  2025-01-27
  Last Modified: 2025-01-27

  WHERE:
  apps/speaker-diarization-benchmark/scripts/one_off/link_segments_to_stable.ts

  WHY:
  To establish the many-to-many relationships between segments and stable segments so that
  we can query which transcription/diarization segments belong to which stable segments.
  This is needed for the video analysis pipeline to properly associate segments with their
  containing time windows.
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

/**
 * Checks if a segment is contained within a stable segment
 */
function isContained(
  segmentStart: number,
  segmentEnd: number,
  stableStart: number,
  stableEnd: number
): boolean {
  return segmentStart >= stableStart && segmentEnd <= stableEnd;
}

/**
 * Finds all stable segments that contain the given segment
 */
function findContainingStableSegments(
  segmentStart: number,
  segmentEnd: number,
  stableSegments: Array<{ id: string; start_time: number; end_time: number }>
): string[] {
  return stableSegments
    .filter((stable) =>
      isContained(segmentStart, segmentEnd, stable.start_time, stable.end_time)
    )
    .map((stable) => stable.id);
}

async function main() {
  console.log(DRY_RUN ? "🔍 DRY RUN MODE" : "🚀 EXECUTION MODE");
  console.log("=".repeat(50));

  // Query all stable segments
  console.log("\n📊 Loading stable segments...");
  const stableSegmentsQuery = await db.query({
    stableSegments: {
      $: {},
    },
  });
  const stableSegments = stableSegmentsQuery.stableSegments || [];
  console.log(`Found ${stableSegments.length} stable segments`);

  // Query all transcription segments
  console.log("\n📊 Loading transcription segments...");
  const transcriptionSegmentsQuery = await db.query({
    transcriptionSegments: {
      $: {},
      stableSegments: {}, // Load existing links to check what's already linked
    },
  });
  const transcriptionSegments =
    transcriptionSegmentsQuery.transcriptionSegments || [];
  console.log(`Found ${transcriptionSegments.length} transcription segments`);

  // Query all diarization segments
  console.log("\n📊 Loading diarization segments...");
  const diarizationSegmentsQuery = await db.query({
    diarizationSegments: {
      $: {},
      stableSegments: {}, // Load existing links to check what's already linked
    },
  });
  const diarizationSegments =
    diarizationSegmentsQuery.diarizationSegments || [];
  console.log(`Found ${diarizationSegments.length} diarization segments`);

  if (stableSegments.length === 0) {
    console.log("\n⚠️  No stable segments found. Exiting.");
    return;
  }

  // Process transcription segments
  console.log("\n🔗 Processing transcription segments...");
  const transcriptionLinks: Array<{
    segmentId: string;
    stableSegmentIds: string[];
    segmentStart: number;
    segmentEnd: number;
  }> = [];

  for (const segment of transcriptionSegments) {
    const containingStableIds = findContainingStableSegments(
      segment.start_time,
      segment.end_time,
      stableSegments
    );

    if (containingStableIds.length > 0) {
      // Check if links already exist
      const existingLinks =
        segment.stableSegments?.map((s: { id: string }) => s.id) || [];
      const newLinks = containingStableIds.filter(
        (id) => !existingLinks.includes(id)
      );

      if (newLinks.length > 0) {
        transcriptionLinks.push({
          segmentId: segment.id,
          stableSegmentIds: newLinks,
          segmentStart: segment.start_time,
          segmentEnd: segment.end_time,
        });
      }
    }
  }

  console.log(
    `Found ${transcriptionLinks.length} transcription segments to link`
  );

  // Process diarization segments
  console.log("\n🔗 Processing diarization segments...");
  const diarizationLinks: Array<{
    segmentId: string;
    stableSegmentIds: string[];
    segmentStart: number;
    segmentEnd: number;
  }> = [];

  for (const segment of diarizationSegments) {
    const containingStableIds = findContainingStableSegments(
      segment.start_time,
      segment.end_time,
      stableSegments
    );

    if (containingStableIds.length > 0) {
      // Check if links already exist
      const existingLinks =
        segment.stableSegments?.map((s: { id: string }) => s.id) || [];
      const newLinks = containingStableIds.filter(
        (id) => !existingLinks.includes(id)
      );

      if (newLinks.length > 0) {
        diarizationLinks.push({
          segmentId: segment.id,
          stableSegmentIds: newLinks,
          segmentStart: segment.start_time,
          segmentEnd: segment.end_time,
        });
      }
    }
  }

  console.log(`Found ${diarizationLinks.length} diarization segments to link`);

  // Display summary
  console.log("\n📋 SUMMARY");
  console.log("=".repeat(50));
  console.log(`Stable Segments: ${stableSegments.length}`);
  console.log(
    `Transcription Segments to Link: ${transcriptionLinks.length} (out of ${transcriptionSegments.length})`
  );
  console.log(
    `Diarization Segments to Link: ${diarizationLinks.length} (out of ${diarizationSegments.length})`
  );

  // Show some examples
  if (transcriptionLinks.length > 0) {
    console.log("\n📝 Example Transcription Links:");
    transcriptionLinks.slice(0, 3).forEach((link) => {
      const stableInfo = link.stableSegmentIds
        .map((id) => {
          const stable = stableSegments.find((s) => s.id === id);
          return stable ? `[${stable.start_time}s-${stable.end_time}s]` : id;
        })
        .join(", ");
      console.log(
        `  Segment [${link.segmentStart}s-${link.segmentEnd}s] -> ${stableInfo}`
      );
    });
  }

  if (diarizationLinks.length > 0) {
    console.log("\n📝 Example Diarization Links:");
    diarizationLinks.slice(0, 3).forEach((link) => {
      const stableInfo = link.stableSegmentIds
        .map((id) => {
          const stable = stableSegments.find((s) => s.id === id);
          return stable ? `[${stable.start_time}s-${stable.end_time}s]` : id;
        })
        .join(", ");
      console.log(
        `  Segment [${link.segmentStart}s-${link.segmentEnd}s] -> ${stableInfo}`
      );
    });
  }

  if (DRY_RUN) {
    console.log(
      "\n💡 This was a dry run. Use --execute to perform the actual linking."
    );
    return;
  }

  // Execute the linking
  console.log("\n🚀 Executing links...");

  const transactions: any[] = [];

  // Create transactions for transcription segments
  for (const link of transcriptionLinks) {
    transactions.push(
      db.tx.transcriptionSegments[link.segmentId].link({
        stableSegments: link.stableSegmentIds,
      })
    );
  }

  // Create transactions for diarization segments
  for (const link of diarizationLinks) {
    transactions.push(
      db.tx.diarizationSegments[link.segmentId].link({
        stableSegments: link.stableSegmentIds,
      })
    );
  }

  if (transactions.length === 0) {
    console.log("✅ No new links to create. All segments are already linked.");
    return;
  }

  // Batch transactions (100 at a time)
  const batchSize = 100;
  let linkedCount = 0;

  for (let i = 0; i < transactions.length; i += batchSize) {
    const batch = transactions.slice(i, i + batchSize);
    await db.transact(batch);
    linkedCount += batch.length;
    console.log(`  Linked ${linkedCount}/${transactions.length} segments...`);
  }

  console.log("✅ All links created successfully!");

  // Verify a sample of links
  console.log("\n🔍 Verifying links...");

  if (transcriptionLinks.length > 0) {
    const sampleId = transcriptionLinks[0].segmentId;
    const verifyQuery = await db.query({
      transcriptionSegments: {
        $: { where: { id: sampleId } },
        stableSegments: {},
      },
    });

    const sample = verifyQuery.transcriptionSegments[0];
    if (sample && sample.stableSegments) {
      console.log(
        `✅ Sample transcription segment has ${sample.stableSegments.length} linked stable segments`
      );
    } else {
      console.log(
        "⚠️  Verification: Could not find sample transcription segment"
      );
    }
  }

  if (diarizationLinks.length > 0) {
    const sampleId = diarizationLinks[0].segmentId;
    const verifyQuery = await db.query({
      diarizationSegments: {
        $: { where: { id: sampleId } },
        stableSegments: {},
      },
    });

    const sample = verifyQuery.diarizationSegments[0];
    if (sample && sample.stableSegments) {
      console.log(
        `✅ Sample diarization segment has ${sample.stableSegments.length} linked stable segments`
      );
    } else {
      console.log(
        "⚠️  Verification: Could not find sample diarization segment"
      );
    }
  }

  console.log("\n✅ Done!");
}

main().catch((error) => {
  console.error("❌ Error:", error);
  process.exit(1);
});
