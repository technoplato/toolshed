import asyncio
from instantdb_admin_client import InstantDBAdminAPI
from job_model import Job, JobType

APP_ID = "979844fa-8b96-4a83-9906-2445928f1e0d"
ADMIN_TOKEN = "b11e3fbe-e3d3-4e1e-a2d0-41bf2296ea0a"

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
