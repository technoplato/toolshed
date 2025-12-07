/*
  HOW:
  `bun run apps/speaker-diarization-benchmark/scripts/one_off/link_transcription_runs_to_videos.ts [--execute]`

  [Inputs]
  - --execute: If provided, actually performs the linking. Otherwise runs in dry-run mode.
  - INSTANT_APP_ID (env): Required for InstantDB connection
  - INSTANT_ADMIN_SECRET (env): Required for InstantDB admin access

  [Outputs]
  - Console output showing which transcription runs will be linked to which videos
  - If --execute is provided, performs the actual linking and verifies results

  [Side Effects]
  - If --execute is provided, creates links between transcription runs and videos in InstantDB

  WHO:
  Antigravity, User
  (Context: Linking transcription runs to videos based on video_id matching)

  WHAT:
  Links transcription runs to videos based on matching video_id.
  A transcription run is linked to a video if transcriptionRun.video_id matches video.id.

  WHEN:
  2025-01-27
  Last Modified: 2025-01-27

  WHERE:
  apps/speaker-diarization-benchmark/scripts/one_off/link_transcription_runs_to_videos.ts

  WHY:
  To establish the one-to-many relationship between videos and transcription runs so that
  we can query which transcription runs belong to which videos. This is needed for the
  video analysis pipeline to properly associate runs with their source videos.
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

  // Query all videos
  console.log("\n📊 Loading videos...");
  const videosQuery = await db.query({
    videos: {
      $: {},
    },
  });
  const videos = videosQuery.videos || [];
  console.log(`Found ${videos.length} videos`);

  // Create a map of video IDs for quick lookup
  const videoMap = new Map(videos.map((v: { id: string }) => [v.id, v]));

  // Query all transcription runs
  console.log("\n📊 Loading transcription runs...");
  const transcriptionRunsQuery = await db.query({
    transcriptionRuns: {
      $: {},
      video: {}, // Load existing links to check what's already linked
    },
  });
  const transcriptionRuns = transcriptionRunsQuery.transcriptionRuns || [];
  console.log(`Found ${transcriptionRuns.length} transcription runs`);

  if (videos.length === 0) {
    console.log("\n⚠️  No videos found. Exiting.");
    return;
  }

  if (transcriptionRuns.length === 0) {
    console.log("\n⚠️  No transcription runs found. Exiting.");
    return;
  }

  // Process transcription runs
  console.log("\n🔗 Processing transcription runs...");
  const links: Array<{
    runId: string;
    videoId: string;
    videoTitle?: string;
    runVideoId?: string; // The video_id stored in the run (may be missing)
    reason: string; // Why we're linking this
  }> = [];

  for (const run of transcriptionRuns) {
    const runVideoId = run.video_id;
    const existingLink = run.video?.id;

    // If already linked, skip
    if (existingLink) {
      console.log(
        `✓ Transcription run ${run.id.slice(0, 8)}... is already linked to video ${existingLink.slice(0, 8)}...`
      );
      continue;
    }

    // If video_id is set, try to match by video_id
    if (runVideoId) {
      const video = videoMap.get(runVideoId);
      if (video) {
        links.push({
          runId: run.id,
          videoId: runVideoId,
          videoTitle: (video as { title?: string }).title,
          runVideoId,
          reason: `matched by video_id`,
        });
        continue;
      } else {
        console.log(
          `⚠️  Transcription run ${run.id.slice(0, 8)}... references video_id ${runVideoId.slice(0, 8)}... which doesn't exist`
        );
      }
    }

    // If video_id is missing or doesn't match, and we have exactly one video and one run, link them
    if (!runVideoId && videos.length === 1 && transcriptionRuns.length === 1) {
      const video = videos[0];
      links.push({
        runId: run.id,
        videoId: video.id,
        videoTitle: (video as { title?: string }).title,
        reason: `single video/run match (video_id missing)`,
      });
      console.log(
        `📌 Will link transcription run ${run.id.slice(0, 8)}... to single video ${(video as { title?: string })?.title || video.id.slice(0, 8) + "..."} (video_id was missing)`
      );
    } else if (!runVideoId) {
      console.log(
        `⚠️  Transcription run ${run.id.slice(0, 8)}... has no video_id and cannot be auto-matched (${videos.length} videos, ${transcriptionRuns.length} runs), skipping`
      );
    }
  }

  console.log(`Found ${links.length} transcription runs to link`);

  // Display summary
  console.log("\n📋 SUMMARY");
  console.log("=".repeat(50));
  console.log(`Videos: ${videos.length}`);
  console.log(
    `Transcription Runs to Link: ${links.length} (out of ${transcriptionRuns.length})`
  );

  // Group by video
  const linksByVideo = new Map<string, typeof links>();
  for (const link of links) {
    if (!linksByVideo.has(link.videoId)) {
      linksByVideo.set(link.videoId, []);
    }
    linksByVideo.get(link.videoId)!.push(link);
  }

  console.log("\n📝 Links by Video:");
  for (const [videoId, videoLinks] of linksByVideo.entries()) {
    const video = videoMap.get(videoId);
    const title = (video as { title?: string })?.title || "Unknown";
    console.log(
      `  ${title} (${videoId.slice(0, 8)}...): ${videoLinks.length} run(s)`
    );
    // Show first few run IDs with reasons
    videoLinks.slice(0, 3).forEach((link) => {
      console.log(
        `    - Run ${link.runId.slice(0, 8)}... (${link.reason})`
      );
    });
    if (videoLinks.length > 3) {
      console.log(`    ... and ${videoLinks.length - 3} more`);
    }
  }

  if (DRY_RUN) {
    console.log("\n💡 This was a dry run. Use --execute to perform the actual linking.");
    return;
  }

  // Execute the linking
  console.log("\n🚀 Executing links...");

  if (links.length === 0) {
    console.log("✅ No new links to create. All runs are already linked.");
    return;
  }

  const transactions: any[] = [];

  // Create transactions for linking runs to videos
  for (const link of links) {
    transactions.push(
      db.tx.transcriptionRuns[link.runId].link({
        video: link.videoId,
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

  // Verify a sample of links
  console.log("\n🔍 Verifying links...");

  if (links.length > 0) {
    const sampleId = links[0].runId;
    const verifyQuery = await db.query({
      transcriptionRuns: {
        $: { where: { id: sampleId } },
        video: {},
      },
    });

    const sample = verifyQuery.transcriptionRuns[0];
    if (sample && sample.video) {
      console.log(
        `✅ Sample transcription run is linked to video: ${(sample.video as { title?: string })?.title || sample.video.id}`
      );
    } else {
      console.log("⚠️  Verification: Could not find sample transcription run link");
    }
  }

  // Verify all links
  const finalQuery = await db.query({
    transcriptionRuns: {
      $: {},
      video: {},
    },
  });

  const linkedCountFinal = finalQuery.transcriptionRuns.filter(
    (run: { video?: { id: string } }) => run.video?.id
  ).length;

  console.log(
    `✅ Verification complete: ${linkedCountFinal}/${transcriptionRuns.length} runs are now linked to videos`
  );

  console.log("\n✅ Done!");
}

main().catch((error) => {
  console.error("❌ Error:", error);
  process.exit(1);
});

