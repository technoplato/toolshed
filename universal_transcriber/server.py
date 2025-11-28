from fastapi import FastAPI, BackgroundTasks, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import transcribe
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Monkeypatch DB path to be inside the volume so it persists
transcribe.DB_NAME = "transcriptions/transcriptions.db"

app = FastAPI()

# Ensure directories exist
os.makedirs("transcriptions", exist_ok=True)
os.makedirs("downloads", exist_ok=True)

def run_transcription(url: str):
    """Background task to run the transcription process."""
    logger.info(f"Starting transcription for {url}")
    conn = transcribe.init_db()
    try:
        transcribe.process_video(url, conn)
        logger.info(f"Completed transcription for {url}")
    except Exception as e:
        logger.error(f"Error transcribing {url}: {e}")
    finally:
        conn.close()

@app.post("/submit")
async def submit_video(background_tasks: BackgroundTasks, url: str = Form(...)):
    """Accepts a URL and starts the transcription process in the background."""
    background_tasks.add_task(run_transcription, url)
    # Redirect back to home page or show a message
    return RedirectResponse(url="/", status_code=303)

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Initialize DB and Index on startup
@app.on_event("startup")
async def startup_event():
    conn = transcribe.init_db()
    transcribe.update_index_html(conn)
    conn.close()

# Mount the transcriptions directory to the root
# This will serve index.html, player.html, and all generated files
app.mount("/", StaticFiles(directory="transcriptions", html=True), name="transcriptions")
