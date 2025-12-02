from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
import os

app = FastAPI()

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Depends(api_key_header)):
    expected_key = os.getenv("API_KEY")
    if not expected_key:
        # If no key configured on server, allow all (or fail safe, your choice)
        return None
    if api_key_header == expected_key:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials",
    )

@app.get("/")
def read_root():
    return {"Hello": "World", "Auth": "Public (but protected by Traefik if configured)"}

@app.get("/secure-data", dependencies=[Depends(get_api_key)])
def read_secure_data():
    return {"secret_data": "This is only visible with a valid API Key!"}
