import "dotenv/config";
import { init, id } from "@instantdb/admin";
import fetch from "node-fetch";

const APP_ID = process.env.INSTANT_APP_ID || "979844fa-8b96-4a83-9906-2445928f1e0d";
const ADMIN_TOKEN = process.env.INSTANT_ADMIN_TOKEN || "b11e3fbe-e3d3-4e1e-a2d0-41bf2296ea0a";
const PYTHON_SERVICE_URL = process.env.PYTHON_SERVICE_URL || "http://localhost:8000";

console.log(`Starting Job Runner for App ID: ${APP_ID}`);

// @ts-ignore
const db = init({
  appId: APP_ID,
  adminToken: ADMIN_TOKEN,
});

console.log("Subscribing to jobs...");

// Helper to log to InstantDB
async function logToDB(level: "info" | "warn" | "error", message: string, jobId?: string) {
  const logId = id();
  const timestamp = new Date().toISOString();
  
  console.log(`[${level.toUpperCase()}] ${message}`);

  try {
    const steps: any[] = [
      db.tx.logs[logId].update({
        level,
        message,
        created_at: timestamp,
        job_id: jobId,
      })
    ];

    if (jobId) {
      steps.push(db.tx.jobs[jobId].link({ logs: logId }));
    }

    await db.transact(steps);
  } catch (e) {
    console.error("Failed to write log to DB:", e);
  }
}

// Subscribe to Queued jobs
// @ts-ignore
const unsubscribe = db.subscribeQuery(
  {
    jobs: {
      $: { where: { progress: "Queued" } },
      video: {} 
    }
  },
  (resp: any) => {
    if (resp.error) {
      console.error("Subscription error:", resp.error);
      return;
    }
    
    const jobs = resp.data?.jobs || [];
    if (jobs.length > 0) {
      console.log(`Found ${jobs.length} queued jobs.`);
      jobs.forEach(processJob);
    }
  }
);

async function processJob(job: any) {
  const jobId = job.id;
  await logToDB("info", `Processing job ${jobId}...`, jobId);

  // 1. Mark as Processing
  try {
    await db.transact(
      db.tx.jobs[jobId].update({ progress: "Processing" })
    );
  } catch (e) {
    await logToDB("error", `Failed to update job ${jobId} to Processing: ${e}`, jobId);
    return;
  }

  // 2. Get Video URL
  const videos = job.video || [];
  if (videos.length === 0) {
    await logToDB("error", `Job ${jobId} has no linked video.`, jobId);
    await db.transact(
      db.tx.jobs[jobId].update({ progress: "Error", error: "No linked video" })
    );
    return;
  }
  
  const video = videos[0];
  const url = video.original_url;
  const videoId = video.id;

  if (!url) {
    await logToDB("error", `Video ${videoId} has no URL.`, jobId);
    await db.transact(
      db.tx.jobs[jobId].update({ progress: "Error", error: "Video has no URL" })
    );
    return;
  }

  // 3. Call Python Service
  try {
    await logToDB("info", `Calling Python service for ${url} (Video UUID: ${videoId})...`, jobId);
    
    const response = await fetch(`${PYTHON_SERVICE_URL}/transcribe`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, video_uuid: videoId }),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Python service error: ${response.status} ${text}`);
    }

    await logToDB("info", `Job ${jobId} completed successfully.`, jobId);
    
    // 4. Mark as Completed
    await db.transact(
      db.tx.jobs[jobId].update({ progress: "Completed" })
    );

  } catch (e: any) {
    await logToDB("error", `Job ${jobId} failed: ${e.message}`, jobId);
    await db.transact(
      db.tx.jobs[jobId].update({ progress: "Error", error: e.message })
    );
  }
}
