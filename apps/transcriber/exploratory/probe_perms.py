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
    
    # Try to GET perms
    print("Attempting to GET /admin/perms...")
    async with aiohttp.ClientSession(headers=headers) as session:
        # Try various potential endpoints
        endpoints = [
            "/admin/perms",
            "/admin/rules",
            "/admin/apps/perms",
            f"/admin/apps/{APP_ID}/perms",
            "/admin/schema"
        ]
        
        for ep in endpoints:
            url = f"{BASE_URL}{ep}"
            print(f"Trying GET {url}...")
            async with session.get(url) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    print(f"Success! Response: {await response.text()}")
                    return

    print("Could not find perms endpoint via guessing.")

if __name__ == "__main__":
    asyncio.run(main())
