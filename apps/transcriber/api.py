from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import os
import sys

# Ensure we can import from universal_transcriber
# apps/transcriber is the current directory
sys.path.append(os.path.dirname(__file__))

from universal_transcriber.transcribe import process_video

app = FastAPI()

class TranscribeRequest(BaseModel):
    url: str
    video_uuid: str = None

@app.post("/transcribe")
async def transcribe_endpoint(req: TranscribeRequest):
    print(f"Received transcription request for {req.url} (UUID: {req.video_uuid})")
    try:
        await process_video(req.url, req.video_uuid)
        return {"status": "success"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}
