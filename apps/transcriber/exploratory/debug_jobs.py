import sys
import os
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from instantdb_admin_client import InstantDBAdminAPI

APP_ID = "979844fa-8b96-4a83-9906-2445928f1e0d"
ADMIN_TOKEN = "b11e3fbe-e3d3-4e1e-a2d0-41bf2296ea0a"

async def main():
    db = InstantDBAdminAPI(app_id=APP_ID, admin_token=ADMIN_TOKEN)
    
    print("Querying jobs...")
    try:
        data = await db.query({
            "jobs": {
                "$": {"limit": 10, "order": {"created_at": "desc"}},
                "video": {}
            }
        })
        jobs = data.get("jobs", [])
        print(f"Found {len(jobs)} jobs.")
        for j in jobs:
            print(f"ID: {j.get('id')} | Status: {j.get('progress')} | Type: {j.get('type')}")
            if j.get('video'):
                print(f"  Video: {j['video'][0].get('original_url')}")
            if j.get('error'):
                print(f"  Error: {j.get('error')}")
                
    except Exception as e:
        print(f"Query failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
