import asyncio
from instantdb_admin_client import InstantDBAdminAPI, Update, Link
import os

APP_ID = os.environ.get("INSTANT_APP_ID")
ADMIN_TOKEN = os.environ.get("INSTANT_ADMIN_TOKEN")

async def main():
    db = InstantDBAdminAPI(app_id=APP_ID, admin_token=ADMIN_TOKEN)
    
    print("1. Creating goal-123 explicitly...")
    try:
        await db.transact([
            Update(collection="goals", id="goal-123", data={"title": "Test Goal"})
        ])
        print("Goal created.")
    except Exception as e:
        print(f"Goal creation failed: {e}")

    print("\n2. Creating todo-uuid explicitly...")
    import uuid
    todo_id = str(uuid.uuid4())
    try:
        await db.transact([
            Update(collection="todos", id=todo_id, data={"title": "Test Todo"})
        ])
        print("Todo created with UUID.")
    except Exception as e:
        print(f"Todo creation failed: {e}")

    print("\n3. Linking using Link step...")
    try:
        await db.transact([
            Link(collection="goals", id="goal-123", links={"todos": todo_id})
        ])
        print("Link step successful.")
    except Exception as e:
        print(f"Link step failed: {e}")

    print("\n4. Linking using Update step...")
    try:
        await db.transact([
            Update(collection="goals", id="goal-123", data={"todos": [todo_id]})
        ])
        print("Update step linking successful.")
    except Exception as e:
        print(f"Update step linking failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
