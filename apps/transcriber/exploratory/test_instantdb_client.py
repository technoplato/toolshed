import asyncio
from instantdb_admin_client import InstantDBAdminAPI

APP_ID = "979844fa-8b96-4a83-9906-2445928f1e0d"
ADMIN_TOKEN = "b11e3fbe-e3d3-4e1e-a2d0-41bf2296ea0a"

async def main():
    print(f"Initializing InstantDB Admin API with App ID: {APP_ID}")
    db = InstantDBAdminAPI(
        app_id=APP_ID,
        admin_token=ADMIN_TOKEN
    )
    
    print("Querying for goals...")
    try:
        # Simple query to verify connection
        result = await db.query({"goals": {}})
        print("Query successful!")
        print(result)
    except Exception as e:
        print(f"Query failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
