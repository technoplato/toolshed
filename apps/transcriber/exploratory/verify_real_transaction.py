import asyncio
import aiohttp
import json
import uuid
from instantdb_admin_client import InstantDBAdminAPI, Update
import os

APP_ID = os.environ.get("INSTANT_APP_ID")
ADMIN_TOKEN = os.environ.get("INSTANT_ADMIN_TOKEN")
BASE_URL = "https://api.instantdb.com"

async def update_perms(session, rules):
    print(f"Updating perms to: {json.dumps(rules)}")
    # Try sending rules directly
    async with session.post(f"{BASE_URL}/admin/perms", json={"rules": rules}) as response:
        if response.status != 200:
            print(f"Failed to update perms: {response.status} {await response.text()}")
            # Try without "rules" wrapper
            async with session.post(f"{BASE_URL}/admin/perms", json=rules) as response2:
                 if response2.status != 200:
                     print(f"Failed to update perms (retry): {response2.status} {await response2.text()}")
                     raise Exception("Could not update perms")
        else:
            print("Perms updated successfully.")

async def main():
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ADMIN_TOKEN}",
        "App-Id": APP_ID
    }
    
    # We use a guest user for the transaction to ensure permissions are checked
    # (Admin token often bypasses permissions)
    client = InstantDBAdminAPI(app_id=APP_ID, admin_token=ADMIN_TOKEN).as_user(guest=True)
    # CRITICAL: Remove Authorization header to ensure we are treated as a guest, 
    # otherwise Admin Token bypasses permissions!
    if "Authorization" in client.headers:
        del client.headers["Authorization"]
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # 1. Get current perms (to restore later)
        print("Fetching current perms...")
        current_perms = {}
        async with session.get(f"{BASE_URL}/admin/perms") as response:
            if response.status == 200:
                text = await response.text()
                if text:
                    try:
                        data = json.loads(text)
                        current_perms = data.get("rules", data)
                    except:
                        pass
        print(f"Current perms: {current_perms}")

        try:
            # 2. Set STRICT rules
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
                        "$default": "false"
                    }
                }
            }
            await update_perms(session, strict_rules)
            
            # 3. Attempt transaction that should FAIL
            print("\nAttempting transaction with STRICT rules (should fail)...")
            goal_id = str(uuid.uuid4())
            try:
                await client.transact([
                    Update(collection="goals", id=goal_id, data={"title": "Strict", "rogue": "fail"})
                ])
                print("❌ Transaction SUCCEEDED (Unexpected!)")
            except Exception as e:
                print(f"✅ Transaction FAILED as expected: {e}")

            # 4. Set PERMISSIVE rules
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
                        "create": "true"
                    }
                }
            }
            await update_perms(session, permissive_rules)

            # 5. Attempt transaction that should SUCCEED
            print("\nAttempting transaction with PERMISSIVE rules (should succeed)...")
            try:
                await client.transact([
                    Update(collection="goals", id=goal_id, data={"title": "Permissive", "rogue": "pass"})
                ])
                print("✅ Transaction SUCCEEDED as expected")
            except Exception as e:
                print(f"❌ Transaction FAILED (Unexpected): {e}")

        finally:
            # 6. Restore original perms
            print("\nRestoring original perms...")
            await update_perms(session, current_perms)

if __name__ == "__main__":
    asyncio.run(main())
