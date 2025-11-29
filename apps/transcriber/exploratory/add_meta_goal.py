import asyncio
import uuid
from instantdb_admin_client import InstantDBAdminAPI, Update

APP_ID = "979844fa-8b96-4a83-9906-2445928f1e0d"
ADMIN_TOKEN = "b11e3fbe-e3d3-4e1e-a2d0-41bf2296ea0a"

async def main():
    db = InstantDBAdminAPI(app_id=APP_ID, admin_token=ADMIN_TOKEN)
    
    goal_id = str(uuid.uuid4())
    # A very meta goal
    meta_title = "Use the InstantDB Admin Client to create a goal about using the InstantDB Admin Client"
    
    print(f"Adding goal: '{meta_title}'")
    
    try:
        await db.transact([
            Update(
                collection="goals",
                id=goal_id,
                data={
                    "title": meta_title, 
                    "is_meta": True,
                    "recursion_level": "infinite",
                    "self_referential": True
                }
            )
        ])
        print("Goal added successfully!")
        
        # Verify
        print("Verifying addition...")
        result = await db.query({
            "goals": {
                "$": {
                    "where": {"id": goal_id}
                }
            }
        })
        print("Verification query result:", result)
        
    except Exception as e:
        print(f"Failed to add goal: {e}")

if __name__ == "__main__":
    asyncio.run(main())
