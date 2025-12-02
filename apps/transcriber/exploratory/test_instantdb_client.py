import asyncio
from instantdb_admin_client import InstantDBAdminAPI
import os

APP_ID = os.environ.get("INSTANT_APP_ID")
ADMIN_TOKEN = os.environ.get("INSTANT_ADMIN_TOKEN")

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
