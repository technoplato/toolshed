import asyncio
from instantdb_admin_client import InstantDBAdminAPI
from job_model import Job, JobType
import os

APP_ID = os.environ.get("INSTANT_APP_ID")
ADMIN_TOKEN = os.environ.get("INSTANT_ADMIN_TOKEN")

async def main():
    db = InstantDBAdminAPI(app_id=APP_ID, admin_token=ADMIN_TOKEN)
    
    # Create a new Job instance
    new_job = Job(
        type=JobType.VIDEO_DOWNLOAD,
        progress="Downloading video...",
        error=None
    )
    
    print(f"Created Job object: {new_job}")
    
    # Convert to InstantDB Update step
    update_step = new_job.to_instant_update()
    print(f"Generated Update step: {update_step}")
    
    try:
        print("Inserting job into InstantDB...")
        await db.transact([update_step])
        print("Job inserted successfully!")
        
        # Verify insertion
        print("Verifying insertion...")
        result = await db.query({
            "jobs": {
                "$": {
                    "where": {"id": str(new_job.id)}
                }
            }
        })
        print("Verification result:", result)
        
    except Exception as e:
        print(f"Failed to insert job: {e}")

if __name__ == "__main__":
    asyncio.run(main())
