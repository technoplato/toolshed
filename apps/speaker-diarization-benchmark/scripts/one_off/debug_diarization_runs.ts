
import { init } from '@instantdb/admin';
import { config } from 'dotenv';
import { join } from 'path';

// Load .env from toolshed root
config({ path: join(__dirname, '../../../../.env') });

const APP_ID = process.env.INSTANT_APP_ID!;
const ADMIN_TOKEN = process.env.INSTANT_ADMIN_SECRET!;

if (!APP_ID || !ADMIN_TOKEN) {
  console.error("Missing INSTANT_APP_ID or INSTANT_ADMIN_SECRET");
  process.exit(1);
}

const db = init({
  appId: APP_ID,
  adminToken: ADMIN_TOKEN,
});

const VIDEO_ID = "a85ae635-963a-4c8f-9716-146b31e4446a";

async function main() {
  console.log(`\n🔍 Debugging Diarization Runs for Video: ${VIDEO_ID}\n`);

  const res = await db.query({
    videos: {
      $: { where: { id: VIDEO_ID } },
      diarizationRuns: {
        $: { }, // Get all runs
        config: {},
        diarizationSegments: {
            // Get count only effectively by getting IDs, or small limit
        }
      }
    }
  });

  const video = res.videos[0];
  if (!video) {
    console.error("❌ Video 'jAlKYYr1bpY' not found via ID lookup.");
    console.log("Listing first 10 videos in DB to verify IDs:");
    const allVideos = await db.query({ videos: { $: { limit: 10 } } });
    allVideos.videos.forEach(v => console.log(` - ${v.id} (${v.title})`));
    process.exit(1);
  }

  const runs = video.diarizationRuns || [];
  console.log(`Found ${runs.length} Diarization Runs:\n`);

  for (const run of runs) {
    const segments = run.diarizationSegments || [];
    const config = run.config ? run.config[0] : {};
    
    console.log(`🔸 Run ID: ${run.id}`);
    console.log(`   Workflow: ${run.workflow}`);
    console.log(`   Preferred: ${run.is_preferred ? '✅ YES' : '❌ NO'}`);
    console.log(`   Config: ${JSON.stringify(config)}`);
    console.log(`   Segments Linked: ${segments.length}`);
    console.log(`   Created At: ${run.created_at}`);
    
    // Check if segments are truly empty in DB or just link missing
    if (segments.length === 0) {
        console.log("   ❌ ZERO SEGMENTS LINKED! Checking if orphaned segments exist for this run...");
        // Reverse query: find segments pointing to this run
        try {
            const segRes = await db.query({
                diarizationSegments: {
                    $: { where: { runId: run.id }, limit: 5 }
                }
            });
            const orphans = segRes.diarizationSegments || [];
            if (orphans.length > 0) {
                 console.log(`   ⚠️ FOUND ${orphans.length}+ segments that reference this runId via 'runId' attribute, but are not linked via graph!`);
            } else {
                 console.log(`   ❌ No segments found even via 'runId' attribute search.`);
            }
        } catch (e) {
            console.error("   Error querying segments:", e);
        }
    }
    console.log("-".repeat(50));
  }
}

main();
