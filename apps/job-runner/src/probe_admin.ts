import "dotenv/config";
import { init } from "@instantdb/admin";

const APP_ID = process.env.INSTANT_APP_ID || "979844fa-8b96-4a83-9906-2445928f1e0d";
const ADMIN_TOKEN = process.env.INSTANT_ADMIN_TOKEN || "b11e3fbe-e3d3-4e1e-a2d0-41bf2296ea0a";

// @ts-ignore
const db = init({
  appId: APP_ID,
  adminToken: ADMIN_TOKEN,
});

console.log("Keys:", Object.keys(db));
console.log("Prototype:", Object.getPrototypeOf(db));
try {
    console.log("db.tx:", db.tx);
} catch (e) {}
