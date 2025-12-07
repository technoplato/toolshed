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

const TARGET_RUN_ID = "c22a7475-e6a1-500b-b427-9a9e553bba8d";
const TARGET_VIDEO_ID = "4417c492-cb62-546d-94f0-1f9af5546212";

async function main() {
  console.log(`Fixing Link for Run ID: ${TARGET_RUN_ID}`);
  console.log(`Target Video ID: ${TARGET_VIDEO_ID}`);

  // Create link
  await db.transact([
    db.tx.diarizationRuns[TARGET_RUN_ID].link({ video: TARGET_VIDEO_ID }),
  ]);

  console.log("✅ Link command sent.");

  // Verify
  const res = await db.query({
    diarizationRuns: {
      $: { where: { id: TARGET_RUN_ID } },
      video: {},
    },
  });

  const run = res.diarizationRuns[0];
  if (run && run.video && run.video.id === TARGET_VIDEO_ID) {
    console.log("✅ Verification Successful: Run is linked to Video.");
  } else {
    console.log("❌ Verification Failed.");
    console.log(JSON.stringify(run, null, 2));
  }
}

main();
