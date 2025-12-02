/**
 * =================================================================================================
 * INSTANTDB DEBUG TOOL
 * =================================================================================================
 * 
 * CONTEXT:
 * This script is a utility for developers to interact with the InstantDB instance used by the
 * Toolshed application. It utilizes the @instantdb/admin SDK to perform administrative operations,
 * bypass permissions, and inspect the raw state of the database.
 * 
 * PURPOSE:
 * - Verify data integrity (e.g., check if a job was created, if a video has a transcription).
 * - Debug real-time flows by subscribing to changes in entities.
 * - Quickly inspect the schema or specific records without using the web dashboard.
 * 
 * INSTRUCTIONS:
 * 1. Ensure you have the necessary environment variables set in `apps/job-runner/.env`:
 *    - INSTANT_APP_ID
 *    - INSTANT_ADMIN_TOKEN
 * 
 * 2. Run the script using `ts-node` from the `apps/job-runner` directory:
 *    $ npx ts-node scripts/instant_debug.ts <command> [arguments]
 * 
 * COMMANDS:
 * 
 * 1. query <entity> [limit]
 *    Fetches the latest items for a given entity.
 *    - entity: The name of the entity (e.g., 'jobs', 'videos', 'logs').
 *    - limit: (Optional) Number of items to fetch. Default is 5.
 * 
 * 2. subscribe <entity>
 *    Starts a real-time subscription for the given entity and logs any changes to the console.
 *    - entity: The name of the entity to watch.
 * 
 * 3. get <entity> <id>
 *    Fetches a specific record by its ID.
 * 
 * SAMPLE INPUT/OUTPUT:
 * 
 * Input:
 * $ npx ts-node scripts/instant_debug.ts query jobs 2
 * 
 * Output:
 * [INFO] Querying 'jobs' (Limit: 2)...
 * [INFO] Found 2 records:
 * {
 *   "id": "ce799a63-2c2f-4a01-b498-7f20804a3351",
 *   "progress": "Completed",
 *   "type": "video_download",
 *   ...
 * }
 * ...
 * 
 * Input:
 * $ npx ts-node scripts/instant_debug.ts subscribe jobs
 * 
 * Output:
 * [INFO] Subscribing to 'jobs'... Press Ctrl+C to stop.
 * [DATA] Initial data received: 5 jobs.
 * [UPDATE] Job ce799a63... changed progress to 'Processing'.
 * 
 * =================================================================================================
 */

import "dotenv/config";
import { init } from "@instantdb/admin";

// Configuration
const APP_ID = process.env.INSTANT_APP_ID;
const ADMIN_TOKEN = process.env.INSTANT_ADMIN_TOKEN;

if (!APP_ID || !ADMIN_TOKEN) {
  console.error("[ERROR] Missing INSTANT_APP_ID or INSTANT_ADMIN_TOKEN in .env");
  process.exit(1);
}

// Initialize InstantDB Admin Client
const db = init({
  appId: APP_ID,
  adminToken: ADMIN_TOKEN,
}) as any;

// Helper: Print JSON nicely
const printJSON = (data: any) => console.log(JSON.stringify(data, null, 2));

async function handleQuery(entity: string, limit: number = 5) {
  console.log(`[INFO] Querying '${entity}' (Limit: ${limit})...`);
  try {
    const query = {
      [entity]: {
        $: { limit, order: { created_at: "desc" } }
      }
    };
    
    // @ts-ignore
    const result = await db.query(query);
    const items = result[entity] || [];
    
    console.log(`[INFO] Found ${items.length} records.`);
    if (items.length > 0) {
      printJSON(items);
    }
  } catch (e) {
    console.error("[ERROR] Query failed:", e);
  }
}

async function handleGet(entity: string, id: string) {
  console.log(`[INFO] Fetching '${entity}' with ID '${id}'...`);
  try {
    const query = {
      [entity]: {
        $: { where: { id } }
      }
    };
    
    // @ts-ignore
    const result = await db.query(query);
    const items = result[entity] || [];
    
    if (items.length > 0) {
      printJSON(items[0]);
    } else {
      console.log("[WARN] Record not found.");
    }
  } catch (e) {
    console.error("[ERROR] Get failed:", e);
  }
}

function handleSubscribe(entity: string) {
  console.log(`[INFO] Subscribing to '${entity}'... Press Ctrl+C to stop.`);
  
  const query = {
    [entity]: {
      $: { limit: 10, order: { created_at: "desc" } }
    }
  };

  // @ts-ignore
  const unsubscribe = db.subscribeQuery(query, (resp: any) => {
    if (resp.error) {
      console.error("[ERROR] Subscription error:", resp.error);
      return;
    }
    
    const items = resp.data?.[entity] || [];
    console.log(`\n[${new Date().toISOString()}] Update received. Current count: ${items.length}`);
    
    // Print a summary of items (id and status/title if available)
    items.forEach((item: any) => {
      const summary = {
        id: item.id,
        status: item.progress || item.status,
        title: item.title,
        created_at: item.created_at
      };
      // Remove undefined keys
      Object.keys(summary).forEach(key => (summary as any)[key] === undefined && delete (summary as any)[key]);
      console.log("-", JSON.stringify(summary));
    });
  });

  // Handle exit
  process.on("SIGINT", () => {
    console.log("\n[INFO] Unsubscribing...");
    unsubscribe();
    process.exit(0);
  });
}

// Main CLI Logic
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  if (!command) {
    console.log(`
Usage:
  npx ts-node scripts/instant_debug.ts <command> [args]

Commands:
  query <entity> [limit]   List recent items
  get <entity> <id>        Get item by ID
  subscribe <entity>       Watch for changes
    `);
    return;
  }

  switch (command) {
    case "query":
      await handleQuery(args[1], args[2] ? parseInt(args[2]) : 5);
      break;
    case "get":
      if (!args[2]) {
        console.error("[ERROR] Missing ID argument.");
        return;
      }
      await handleGet(args[1], args[2]);
      break;
    case "subscribe":
      handleSubscribe(args[1]);
      // Keep process alive
      await new Promise(() => {}); 
      break;
    default:
      console.error(`[ERROR] Unknown command: ${command}`);
  }
}

main().catch(console.error);
