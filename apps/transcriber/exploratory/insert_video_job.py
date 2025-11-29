import asyncio
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from instantdb_admin_client import InstantDBAdminAPI, Link
from job_model import Job, JobType, Video

APP_ID = "979844fa-8b96-4a83-9906-2445928f1e0d"
ADMIN_TOKEN = "b11e3fbe-e3d3-4e1e-a2d0-41bf2296ea0a"

async def main():
    db = InstantDBAdminAPI(app_id=APP_ID, admin_token=ADMIN_TOKEN)
    
    # 1. Create Video object
    video = Video(
        platform="youtube",
        original_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title="Rick Astley - Never Gonna Give You Up (Official Music Video)",
        duration=212.0,
        channel="Rick Astley",
        upload_date="2009-10-25"
    )
    print(f"Created Video: {video}")

    # 2. Create Job object
    job = Job(
        type=JobType.VIDEO_DOWNLOAD,
        progress="Processing video metadata...",
        error=None
    )
    print(f"Created Job: {job}")
    
    # 3. Create Transaction Steps
    video_update = video.to_instant_update()
    job_update = job.to_instant_update()
    
    # Link job to video (assuming 'video' link on jobs entity)
    # Note: You might need to define this link in your schema or just use it if schema is permissive
    link_step = Link(
        collection="jobs",
        id=str(job.id),
        links={"video": str(video.id)}
    )
    
    try:
        print("Executing transaction (Create Video + Create Job + Link)...")
        await db.transact([video_update, job_update, link_step])
        print("Transaction successful!")
        
        # 4. Verify
        print("Verifying data...")
        result = await db.query({
            "jobs": {
                "$": {
                    "where": {"id": str(job.id)}
                },
                "video": {}
            }
        })
        print("Verification result:", result)
        
    except Exception as e:
        print(f"Transaction failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
