import asyncio
import uuid
import json
from instantdb_admin_client import InstantDBAdminAPI

APP_ID = "979844fa-8b96-4a83-9906-2445928f1e0d"
ADMIN_TOKEN = "b11e3fbe-e3d3-4e1e-a2d0-41bf2296ea0a"

async def main():
    # We use a guest user to simulate a client-side request, 
    # as the Admin API (without as_user) often bypasses permissions.
    db = InstantDBAdminAPI(app_id=APP_ID, admin_token=ADMIN_TOKEN).as_user(guest=True)
    
    goal_id = str(uuid.uuid4())
    
    # 1. Define "Strict" Rules
    # These rules disallow creating/modifying attributes (schema changes)
    # but allow reading/writing to 'goals' if the attributes already exist (conceptually).
    # Actually, to strictly demonstrate "fail if schema not respected" (i.e. adding new attrs),
    # we set 'attrs' (schema modification) to false.
    strict_rules = {
        "goals": {
            "allow": {
                "create": "true",
                "update": "true",
                "delete": "true",
                "read": "true"
            }
        },
        "attrs": {
            "allow": {
                "$default": "false" # Disallow schema changes (adding new attributes)
            }
        }
    }

    print("--- Demonstration: Enforcing Schema via Permissions ---")
    print("Scenario: Attempting to add a goal with a 'rogue' attribute that is NOT in the schema.")
    print("Note: In this simulated environment, we assume 'rogue_attribute' does not exist yet.")
    
    # We use debug_transact to inject our strict rules without modifying the actual app
    try:
        print("\nAttempting transaction with STRICT rules (attrs.$default = false)...")
        result = await db.debug_transact(
            steps=[
                ["update", "goals", goal_id, {"title": "Valid Title", "rogue_attribute": "I should fail"}]
            ],
            rules=strict_rules
        )
        
        # Check if it was allowed
        # debug_transact returns a structure like:
        # {'all-checks-ok?': False, 'check-results': [...]}
        
        if result.get("all-checks-ok?") is False:
            print(f"\n❌ Transaction BLOCKED by permissions!")
            # Find the failing check to print details
            for check in result.get("check-results", []):
                if check.get("check-pass?") is False:
                    print(f"Failing Check: {json.dumps(check, indent=2)}")
        else:
            print("\n✅ Transaction ALLOWED (Unexpected if schema enforcement is working)")
            print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")

    # 2. Contrast with Permissive Rules
    permissive_rules = {
        "goals": {
            "allow": {
                "create": "true",
                "update": "true",
                "delete": "true",
                "read": "true"
            }
        },
        "attrs": {
            "allow": {
                "create": "true" # Allow schema changes
            }
        }
    }

    try:
        print("\n---------------------------------------------------")
        print("Attempting transaction with PERMISSIVE rules (attrs.create = true)...")
        result = await db.debug_transact(
            steps=[
                ["update", "goals", goal_id, {"title": "Valid Title", "rogue_attribute": "I should pass"}]
            ],
            rules=permissive_rules
        )
        
        if result.get("all-checks-ok?") is False:
             print(f"\n❌ Transaction BLOCKED!")
        else:
            print("\n✅ Transaction ALLOWED (As expected with permissive rules)")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
