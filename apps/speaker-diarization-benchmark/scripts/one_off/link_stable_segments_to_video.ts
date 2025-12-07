
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

const TARGET_VIDEO_ID = "4417c492-cb62-546d-94f0-1f9af5546212";

async function main() {
  console.log(`=== LINKING STABLE SEGMENTS TO VIDEO ===`);
  console.log(`Target Video ID: ${TARGET_VIDEO_ID}`);

  // 1. Verify Video Exists
  const vRes = await db.query({ videos: { $: { where: { id: TARGET_VIDEO_ID } } } });
  if (vRes.videos.length === 0) {
      console.error("❌ Target Video NOT found!");
      return;
  }
  console.log("✅ Video found.");

  // 2. Fetch Stable Segments
  const sRes = await db.query({ stableSegments: {} });
  const segments = sRes.stableSegments;
  console.log(`Found ${segments.length} Stable Segments.`);

  if (segments.length !== 6) {
      console.warn(`WARNING: Expected 6 segments, found ${segments.length}. Proceeding anyway...`);
  }

  // 3. Link Them
  if (segments.length > 0) {
      console.log("Linking segments...");
      const txs = segments.map(seg => db.tx.stableSegments[seg.id].link({ video: TARGET_VIDEO_ID }));
      await db.transact(txs);
      console.log("✅ Link transactions sent.");
  }

  // 4. Verify
  console.log("Verifying links...");
  const verifyRes = await db.query({
      stableSegments: {
          video: {}
      }
  });
  
  let validCount = 0;
  for (const seg of verifyRes.stableSegments) {
      if (seg.video && seg.video.length > 0 && seg.video[0].id === TARGET_VIDEO_ID) {
          validCount++;
      }
  }

  if (validCount === segments.length) {
      console.log(`✅ SUCCESS: All ${validCount} segments linked to video.`);
  } else {
      console.error(`❌ FAILURE: Only ${validCount}/${segments.length} segments linked.`);
  }
}

main();
