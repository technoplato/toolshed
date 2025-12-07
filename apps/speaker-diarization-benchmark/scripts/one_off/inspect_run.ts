
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

const TARGET_RUN_ID = "c22a7475-e6a1-500b-b427-9a9e553bba8d";

async function main() {
  console.log(`Checking Run ID: ${TARGET_RUN_ID}`);

  const res = await db.query({
    diarizationRuns: {
      $: { where: { id: TARGET_RUN_ID } },
      video: {},
      diarizationSegments: { $: { limit: 5 } }
    }
  });

  const run = res.diarizationRuns[0];

  if (!run) {
    console.log("❌ Run NOT found in DB.");
  } else {
    console.log("✅ Run FOUND.");
    console.log("Linked Video:", run.video ? run.video.id : "❌ NONE");
    console.log(`Segment Count (sample): ${res.diarizationRuns[0].diarizationSegments.length}`);
  }

  // Also check if any video exists for relevant criteria
  const vidRes = await db.query({
    videos: {
       $: { where: { url: "https://www.youtube.com/watch?v=jAlKYYr1bpY" } }
    }
  });
  console.log("Video check:", vidRes.videos.length > 0 ? `Found: ${vidRes.videos[0].id}` : "Not found");
}

main();
