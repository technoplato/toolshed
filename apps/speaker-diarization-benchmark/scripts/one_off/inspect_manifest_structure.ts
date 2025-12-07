
import { readFile } from 'fs/promises';
import { join } from 'path';

const MANIFEST_PATH = join(__dirname, '../../data/clips/manifest.json');
const TARGET_CLIP_ID = "clip_youtube_jAlKYYr1bpY_0_60.wav";

async function main() {
  const raw = await readFile(MANIFEST_PATH, 'utf-8');
  const manifest = JSON.parse(raw);
  
  const clip = manifest.find((c: any) => c.id === TARGET_CLIP_ID);
  if (!clip) {
    console.error("Clip not found");
    return;
  }

  const keys = Object.keys(clip.transcriptions || {});
  console.log("Transcription Keys:", keys);

  for (const key of keys) {
      const data = clip.transcriptions[key];
      const count = Array.isArray(data) ? data.length : "Not Array";
      const sample = Array.isArray(data) && data.length > 0 ? data[0] : null;
      const hasWords = sample && Array.isArray(sample.words);
      
      console.log(`Key: ${key}`);
      console.log(`  Count: ${count}`);
      console.log(`  Sample keys: ${sample ? Object.keys(sample) : "N/A"}`);
      console.log(`  Has Words: ${hasWords}`);
  }
}

main();
