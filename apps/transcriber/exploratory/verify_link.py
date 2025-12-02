import asyncio
from instantdb_admin_client import InstantDBAdminAPI
import os

APP_ID = os.environ.get("INSTANT_APP_ID")
ADMIN_TOKEN = os.environ.get("INSTANT_ADMIN_TOKEN")

async def main():
    db = InstantDBAdminAPI(app_id=APP_ID, admin_token=ADMIN_TOKEN)
    
    print("Querying jobs with video details...")
    try:
        # Query jobs and explicitly ask for video fields
        result = await db.query({
            "jobs": {
                "video": {
                    "$": {}
                }
            }
        })
        
        jobs = result.get("jobs", [])
        print(f"Found {len(jobs)} jobs.")
        
        for job in jobs:
            print(f"\nJob ID: {job.get('id')}")
            print(f"Type: {job.get('type')}")
            videos = job.get("video", [])
            if videos:
                print(f"Linked Videos ({len(videos)}):")
                for v in videos:
                    print(f"  - Raw Video Object: {v}")
                    print(f"  - Title: {v.get('title')}")
                    print(f"  - Platform: {v.get('platform')}")
                    print(f"  - URL: {v.get('original_url')}")
            else:
                print("No linked videos found.")
                
    except Exception as e:
        print(f"Query failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
