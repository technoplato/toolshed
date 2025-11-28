from fastapi import FastAPI, BackgroundTasks, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import transcribe
import os
import logging

# Configure logging to file and console
LOG_FILE = "transcriptions/app.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Monkeypatch DB path to be inside the volume so it persists
transcribe.DB_NAME = "transcriptions/transcriptions.db"

app = FastAPI()

# Ensure directories exist
os.makedirs("transcriptions", exist_ok=True)
os.makedirs("downloads", exist_ok=True)

from fastapi import UploadFile, File

@app.post("/upload-cookies")
async def upload_cookies(file: UploadFile = File(...)):
    """Uploads a cookies.txt file for yt-dlp."""
    file_location = "cookies.txt"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
    logger.info("cookies.txt uploaded successfully")
    return RedirectResponse(url="/", status_code=303)

@app.get("/logs")
def get_logs():
    """Returns the last 100 lines of the log file."""
    if not os.path.exists(LOG_FILE):
        return {"logs": ["Log file not found."]}
    
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()
        return {"logs": lines[-100:]}

@app.get("/logs-view", response_class=HTMLResponse)
def view_logs():
    """Simple HTML page to view logs in real-time."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live Logs</title>
        <style>
            body { background: #1e1e1e; color: #d4d4d4; font-family: monospace; padding: 1rem; }
            #logs { white-space: pre-wrap; word-wrap: break-word; }
        </style>
        <script>
            function fetchLogs() {
                fetch('/logs')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('logs').textContent = data.logs.join('');
                        window.scrollTo(0, document.body.scrollHeight);
                    });
            }
            setInterval(fetchLogs, 2000);
            window.onload = fetchLogs;
        </script>
    </head>
    <body>
        <h1>Live Logs</h1>
        <div id="logs">Loading...</div>
    </body>
    </html>
    """

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
