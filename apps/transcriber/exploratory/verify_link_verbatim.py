import asyncio
from instantdb_admin_client import InstantDBAdminAPI, Update, Link, Delete
import os

APP_ID = os.environ.get("INSTANT_APP_ID")
ADMIN_TOKEN = os.environ.get("INSTANT_ADMIN_TOKEN")

async def main():
    db = InstantDBAdminAPI(app_id=APP_ID, admin_token=ADMIN_TOKEN)
    
    print("Executing Create and Link transaction (debug)...")
    # Create and link objects
    steps = [
        Update(
            collection="todos",
            id="todo-123",
            data={"title": "Go running"}
        ),
        Link(
            collection="goals",
            id="goal-123",
            links={"todos": "todo-123"}
        )
    ]
    # Convert steps to list format for debug_transact
    steps_list = [s.to_list() for s in steps]
    
    result = await db.debug_transact(steps_list)
    print(f"Debug Result: {result}")
    
    print("Verifying link...")
    result = await db.query({
        "goals": {
            "$": {
                "where": {"id": "goal-123"}
            },
            "todos": {}
        }
    })
    print(f"Verification Result: {result}")

    print("Executing Delete transaction...")
    # Delete an object
    await db.transact([
        Delete(
            collection="goals",
            id="goal-123"
        )
    ])
    print("Delete complete.")

if __name__ == "__main__":
    asyncio.run(main())
