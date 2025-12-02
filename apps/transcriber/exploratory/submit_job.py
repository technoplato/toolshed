import sys
import os
import asyncio
import uuid
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from instantdb_admin_client import InstantDBAdminAPI, Update

APP_ID = os.environ.get("INSTANT_APP_ID")
ADMIN_TOKEN = os.environ.get("INSTANT_ADMIN_TOKEN")

async def main():
    db = InstantDBAdminAPI(app_id=APP_ID, admin_token=ADMIN_TOKEN)
    
    video_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    import random
    unique_id = random.randint(100000, 999999)
    url = f"https://www.youtube.com/watch?v=dQw4w9WgXcQ&t={unique_id}"
    
    print(f"Creating Job {job_id} for Video {video_id} ({url})...")
    
    steps = [
        Update(collection="videos", id=video_id, data={
            "original_url": url,
            "created_at": datetime.now().isoformat(),
            "title": "Pending Manual Submission",
            "platform": "unknown"
        }),
        Update(collection="jobs", id=job_id, data={
            "type": "video_download",
            "progress": "Queued",
            "created_at": datetime.now().isoformat()
        }),
        # Link them
        # We need to use the Link class or just update the link if the library supports it.
        # The library's `link` method is on the transaction builder.
        # But here we are using `transact` with steps.
        # Let's check `instantdb_admin_client.py` usage.
        # It has a `Link` class.
    ]
    
    # Import Link
    from instantdb_admin_client import Link
    
    steps.append(Link(collection="jobs", id=job_id, links={"video": video_id}))
    
    await db.transact(steps)
    print("Job submitted!")

if __name__ == "__main__":
    asyncio.run(main())
