import sys
import os
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from instantdb_admin_client import InstantDBAdminAPI

APP_ID = "979844fa-8b96-4a83-9906-2445928f1e0d"
ADMIN_TOKEN = "b11e3fbe-e3d3-4e1e-a2d0-41bf2296ea0a"

async def main():
    db = InstantDBAdminAPI(app_id=APP_ID, admin_token=ADMIN_TOKEN)
    
    print("Querying videos collection directly...")
    try:
        # Fetch specific video
        data = await db.query({
            "videos": {
                "$": {"where": {"external_id": "dQw4w9WgXcQ"}},
                "transcriptions": {}
            }
        })
        videos = data.get("videos", [])
        print(f"Found {len(videos)} videos.")
        print(f"Raw Result: {data}")
        
        for v in videos:
            print(f"\nVideo ID: {v.get('id')}")
            print(f"Data: {v}")
                
    except Exception as e:
        print(f"Query failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
