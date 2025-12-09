/*
  HOW:
  `bun run apps/speaker-diarization-benchmark/scripts/one_off/link_diarization_to_transcription_run.ts [--execute]`

  [Inputs]
  - --execute: If provided, actually performs the linking. Otherwise runs in dry-run mode.
  - INSTANT_APP_ID (env): Required for InstantDB connection
  - INSTANT_ADMIN_SECRET (env): Required for InstantDB admin access

  [Outputs]
  - Console output showing which diarization runs will be linked to which transcription runs
  - If --execute is provided, performs the actual linking and verifies results

  [Side Effects]
  - If --execute is provided, creates links between diarization runs and transcription runs in InstantDB

  WHO:
  Antigravity, User
  (Context: Linking diarization runs to transcription runs)

  WHAT:
  Links diarization runs to transcription runs based on matching transcription_run_id.
  If transcription_run_id is missing, links the single diarization run to the single transcription run.

  WHEN:
  2025-01-27
  Last Modified: 2025-01-27

  WHERE:
  apps/speaker-diarization-benchmark/scripts/one_off/link_diarization_to_transcription_run.ts

  WHY:
  To establish the one-to-many relationship between transcription runs and diarization runs so that
  we can query which diarization runs belong to which transcription runs.
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

  // Query all transcription runs
  console.log("\n📊 Loading transcription runs...");
  const transcriptionRunsQuery = await db.query({
    transcriptionRuns: {
      $: {},
    },
  });
  const transcriptionRuns = transcriptionRunsQuery.transcriptionRuns || [];
  console.log(`Found ${transcriptionRuns.length} transcription runs`);

  // Create a map of transcription run IDs for quick lookup
  const transcriptionRunMap = new Map(
    transcriptionRuns.map((r: { id: string }) => [r.id, r])
  );

  // Query all diarization runs
  console.log("\n📊 Loading diarization runs...");
  const diarizationRunsQuery = await db.query({
    diarizationRuns: {
      $: {},
      transcriptionRun: {}, // Load existing links to check what's already linked
    },
  });
  const diarizationRuns = diarizationRunsQuery.diarizationRuns || [];
  console.log(`Found ${diarizationRuns.length} diarization runs`);

  if (transcriptionRuns.length === 0) {
    console.log("\n⚠️  No transcription runs found. Exiting.");
    return;
  }

  if (diarizationRuns.length === 0) {
    console.log("\n⚠️  No diarization runs found. Exiting.");
    return;
  }

  // Process diarization runs
  console.log("\n🔗 Processing diarization runs...");
  const links: Array<{
    diarizationRunId: string;
    transcriptionRunId: string;
    reason: string;
  }> = [];

  for (const diarizationRun of diarizationRuns) {
    const existingLink = diarizationRun.transcriptionRun?.id;
    const transcriptionRunId = diarizationRun.transcription_run_id;

    // If already linked, skip
    if (existingLink) {
      console.log(
        `✓ Diarization run ${diarizationRun.id.slice(0, 8)}... is already linked to transcription run ${existingLink.slice(0, 8)}...`
      );
      continue;
    }

    // If transcription_run_id is set, try to match by it
    if (transcriptionRunId) {
      const transcriptionRun = transcriptionRunMap.get(transcriptionRunId);
      if (transcriptionRun) {
        links.push({
          diarizationRunId: diarizationRun.id,
          transcriptionRunId: transcriptionRunId,
          reason: `matched by transcription_run_id`,
        });
        continue;
      } else {
        console.log(
          `⚠️  Diarization run ${diarizationRun.id.slice(0, 8)}... references transcription_run_id ${transcriptionRunId.slice(0, 8)}... which doesn't exist`
        );
      }
    }

    // If transcription_run_id is missing, and we have exactly one of each, link them
    if (
      !transcriptionRunId &&
      transcriptionRuns.length === 1 &&
      diarizationRuns.length === 1
    ) {
      links.push({
        diarizationRunId: diarizationRun.id,
        transcriptionRunId: transcriptionRuns[0].id,
        reason: `single run match (transcription_run_id missing)`,
      });
      console.log(
        `📌 Will link diarization run ${diarizationRun.id.slice(0, 8)}... to single transcription run ${transcriptionRuns[0].id.slice(0, 8)}... (transcription_run_id was missing)`
      );
    } else if (!transcriptionRunId) {
      console.log(
        `⚠️  Diarization run ${diarizationRun.id.slice(0, 8)}... has no transcription_run_id and cannot be auto-matched (${transcriptionRuns.length} transcription runs, ${diarizationRuns.length} diarization runs), skipping`
      );
    }
  }

  console.log(`Found ${links.length} diarization runs to link`);

  // Display summary
  console.log("\n📋 SUMMARY");
  console.log("=".repeat(50));
  console.log(`Transcription Runs: ${transcriptionRuns.length}`);
  console.log(
    `Diarization Runs to Link: ${links.length} (out of ${diarizationRuns.length})`
  );

  if (links.length > 0) {
    console.log("\n📝 Links to Create:");
    links.forEach((link) => {
      console.log(
        `  - Diarization Run ${link.diarizationRunId.slice(0, 8)}... -> Transcription Run ${link.transcriptionRunId.slice(0, 8)}... (${link.reason})`
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

  if (links.length === 0) {
    console.log("✅ No new links to create. All runs are already linked.");
    return;
  }

  const transactions: any[] = [];

  // Create transactions for linking diarization runs to transcription runs
  for (const link of links) {
    transactions.push(
      db.tx.diarizationRuns[link.diarizationRunId].link({
        transcriptionRun: link.transcriptionRunId,
      })
    );
  }

  // Batch transactions (100 at a time)
  const batchSize = 100;
  let linkedCount = 0;

  for (let i = 0; i < transactions.length; i += batchSize) {
    const batch = transactions.slice(i, i + batchSize);
    await db.transact(batch);
    linkedCount += batch.length;
    console.log(`  Linked ${linkedCount}/${transactions.length} runs...`);
  }

  console.log("✅ All links created successfully!");

  // Verify links
  console.log("\n🔍 Verifying links...");

  const verifyQuery = await db.query({
    diarizationRuns: {
      $: {},
      transcriptionRun: {},
    },
  });

  const linkedCountFinal = verifyQuery.diarizationRuns.filter(
    (run: { transcriptionRun?: { id: string } }) => run.transcriptionRun?.id
  ).length;

  console.log(
    `✅ Verification complete: ${linkedCountFinal}/${diarizationRuns.length} diarization runs are now linked to transcription runs`
  );

  // Verify a sample
  if (links.length > 0) {
    const sampleId = links[0].diarizationRunId;
    const sampleQuery = await db.query({
      diarizationRuns: {
        $: { where: { id: sampleId } },
        transcriptionRun: {},
      },
    });

    const sample = sampleQuery.diarizationRuns[0];
    if (sample && sample.transcriptionRun) {
      console.log(
        `✅ Sample diarization run is linked to transcription run: ${sample.transcriptionRun.id}`
      );
    }
  }

  console.log("\n✅ Done!");
}

main().catch((error) => {
  console.error("❌ Error:", error);
  process.exit(1);
});



