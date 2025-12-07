
import { init } from '@instantdb/admin';
import { config } from 'dotenv';
import { join } from 'path';
import { readFile } from 'fs/promises';
import { v4 as uuidv4 } from 'uuid';
import schema from '../../../../packages/schema/instant.schema';

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
  schema,
});

const TARGET_RUN_ID = "c22a7475-e6a1-500b-b427-9a9e553bba8d";
const TARGET_CLIP_ID = "clip_youtube_jAlKYYr1bpY_0_60.wav";
const MANIFEST_PATH = join(__dirname, '../../data/clips/manifest.json');

async function main() {
  console.log(`=== ONE-OFF CLEANUP & RESTORE ===`);
  console.log(`Target Run ID: ${TARGET_RUN_ID}`);
  console.log(`App ID: ${APP_ID}`);

  // 1. Fetch existing segments for this run
  console.log("Fetching existing segments...");
  const qExisting = {
    diarizationSegments: {
      $: {
        where: {
          run_id: TARGET_RUN_ID
        }
      }
    }
  };
  
  const existingRes = await db.query(qExisting);
  const segmentsToDelete = existingRes.diarizationSegments;
  console.log(`Found ${segmentsToDelete.length} segments to delete.`);

  // 2. Delete them in batches
  if (segmentsToDelete.length > 0) {
    const chunk_size = 50;
    for (let i = 0; i < segmentsToDelete.length; i += chunk_size) {
      const chunk = segmentsToDelete.slice(i, i + chunk_size);
      console.log(`Deleting chunk ${i} to ${i + chunk.length}...`);
      const steps = chunk.map(s => db.tx.diarizationSegments[s.id].delete());
      await db.transact(steps);
    }
    console.log("Deletion complete.");
  }

  // 3. Read Manifest
  console.log("Reading manifest.json...");
  const manifestRaw = await readFile(MANIFEST_PATH, 'utf-8');
  const manifest = JSON.parse(manifestRaw);
  
  const clipData = manifest.find((c: any) => c.id === TARGET_CLIP_ID);
  if (!clipData) {
    console.error("Target clip not found in manifest!");
    return;
  }

  const segs = clipData.transcriptions?.mlx_whisper_turbo_seg_level || [];
  console.log(`Found ${segs.length} new segments in manifest.`);

  // 4. Fetch Speakers to map Name -> ID
  console.log("Fetching speakers for linking...");
  const qSpeakers = { speakers: {} };
  const spkRes = await db.query(qSpeakers);
  const speakerMap = new Map();
  spkRes.speakers.forEach((s: any) => {
    if (s.name) speakerMap.set(s.name, s.id);
  });
  console.log("Speaker Map:", Object.fromEntries(speakerMap));

  // 5. Create and Link New Segments
  console.log("Creating and linking new segments...");
  const newSegmentSteps = [];
  
  for (const s of segs) {
    const newId = uuidv4();
    
    // attributes
    const attrs = {
      start_time: s.start,
      end_time: s.end,
      run_id: TARGET_RUN_ID,
      embedding_id: s.embedding_id || "", 
      created_at: new Date().toISOString()
    };

    // Base create
    let tx = db.tx.diarizationSegments[newId].update(attrs);

    // Link to Run
    tx = tx.link({ run: TARGET_RUN_ID });

    // Link to Speaker (if exists)
    if (s.speaker && speakerMap.has(s.speaker)) {
      const spkId = speakerMap.get(s.speaker);
      tx = tx.link({ speaker: spkId });
    } else {
      console.warn(`Warning: Speaker '${s.speaker}' not found in DB. Segment will be unlinked.`);
    }

    // Link to Stable Segment (Best effort match? Or just ignore for now?)
    // User logic previously was complex overlap matching. 
    // For now, let's skip StableSegment linking to focus on Speakers, unless critical.
    
    newSegmentSteps.push(tx);
  }

  // Batch insert
  const chunk_size = 50;
  for (let i = 0; i < newSegmentSteps.length; i += chunk_size) {
    const chunk = newSegmentSteps.slice(i, i + chunk_size);
    console.log(`Inserting chunk ${i} to ${i + chunk.length}...`);
    await db.transact(chunk);
  }

  console.log("Restore complete.");
  
  // 6. Verify One Link
  console.log("Verifying a sample link...");
  const vRes = await db.query({
      diarizationSegments: {
          $: { where: { run_id: TARGET_RUN_ID }, limit: 1 },
          speaker: { }
      }
  });
  if (vRes.diarizationSegments.length > 0) {
      const s = vRes.diarizationSegments[0];
      console.log(`Sample Segment: ${s.id}`);
      console.log(`Linked Speaker:`, JSON.stringify(s.speaker, null, 2));
  }
}

main();
