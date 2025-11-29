import asyncio
import aiohttp
import json

APP_ID = "979844fa-8b96-4a83-9906-2445928f1e0d"
ADMIN_TOKEN = "b11e3fbe-e3d3-4e1e-a2d0-41bf2296ea0a"
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
