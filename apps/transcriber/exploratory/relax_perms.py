import asyncio
import aiohttp
import json
import os

APP_ID = os.environ.get("INSTANT_APP_ID")
ADMIN_TOKEN = os.environ.get("INSTANT_ADMIN_TOKEN")
BASE_URL = "https://api.instantdb.com"

async def main():
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ADMIN_TOKEN}",
        "App-Id": APP_ID
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # 1. Get current perms
        print("Fetching current perms...")
        async with session.get(f"{BASE_URL}/admin/perms") as response:
            if response.status == 200:
                print(f"Current perms: {await response.text()}")
            else:
                print(f"Failed to get perms: {response.status}")

        # 2. Set permissive rules
        permissive_rules = {
            "attrs": {
                "allow": {
                    "create": "true",
                    "delete": "true",
                    "update": "true",
                    "read": "true"
                }
            }
        }
        
        print(f"Setting permissive rules: {json.dumps(permissive_rules)}")
        async with session.post(f"{BASE_URL}/admin/perms", json={"rules": permissive_rules}) as response:
            if response.status == 200:
                print("Perms updated successfully.")
            else:
                print(f"Failed to update perms: {response.status} {await response.text()}")

if __name__ == "__main__":
    asyncio.run(main())
