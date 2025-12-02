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
    
    url = f"{BASE_URL}/admin/schema"
    print(f"Attempting GET {url}...")
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            print(f"Status: {response.status}")
            if response.status == 200:
                text = await response.text()
                print(f"Success! Response length: {len(text)}")
                with open("schema_dump.json", "w") as f:
                    f.write(text)
            else:
                print(f"Failed. Response: {await response.text()}")

if __name__ == "__main__":
    asyncio.run(main())
