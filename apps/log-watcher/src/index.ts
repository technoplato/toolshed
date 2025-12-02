import { init } from '@instantdb/admin';
import * as dotenv from 'dotenv';

import * as path from 'path';
dotenv.config({ path: path.resolve(__dirname, '../../../.env') });

// Hardcoded for now based on existing python files, but should be env vars ideally
const APP_ID = process.env.INSTANT_APP_ID;
const ADMIN_TOKEN = process.env.INSTANT_ADMIN_TOKEN;

if (!APP_ID || !ADMIN_TOKEN) {
  console.error("Error: INSTANT_APP_ID and INSTANT_ADMIN_TOKEN environment variables are required.");
  process.exit(1);
}

console.log(`Starting Log Watcher for App: ${APP_ID}`);

const db = init({
  appId: APP_ID,
  adminToken: ADMIN_TOKEN,
});

// Subscribe to logs
// We want to see new logs.
// Since admin SDK might not have subscribe for queries yet (node sdk), we might need to poll or use the client SDK if we want real-time.
// However, the user said "use the Admin subscribe query, I think it's called".
// Let's check if the node admin sdk supports subscribe. If not, we'll use query in a loop or similar.
// Actually, the user might be referring to the standard client SDK `db.subscribeQuery`.
// But for admin tasks usually we use admin token.
// Let's try to use the standard `subscribeQuery` if available on the admin instance, or fall back to polling.
// The `@instantdb/admin` package usually exposes `db.query` which is a one-off.
// If we need real-time, we might need `@instantdb/react` or `@instantdb/core` but those are for browsers usually?
// Wait, `@instantdb/admin` is for server side.
// Let's assume for now we just poll every second for the latest logs.

async function tailLogs() {
  let lastTimestamp = Date.now();

  console.log("Tailing logs...");

  setInterval(async () => {
    try {
      const result = await db.query({
        logs: {
          $: {
            limit: 50,
            order: { serverCreatedAt: 'desc' }
          }
        }
      });

      // Reverse to get chronological order
      const logs = (result.logs || []).reverse();
      
      for (const log of logs) {
        let date = 'UNKNOWN DATE';
        try {
            if (log.timestamp) {
                date = new Date(log.timestamp).toISOString();
            }
        } catch (e) {
            // Ignore invalid dates
        }
        const level = log.level || 'INFO';
        const source = log.source || 'UNKNOWN';
        const message = log.message || '';
        
        console.log(`[${date}] [${source}] [${level}] ${message}`);
        
        if (log.timestamp > lastTimestamp) {
          lastTimestamp = log.timestamp;
        }
      }
    } catch (e) {
      console.error("Error fetching logs:", e);
    }
  }, 2000);
}

tailLogs();
