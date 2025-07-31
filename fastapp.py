import logging
import os
import sys
import time
import uuid
import traceback
import threading
from typing import Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from pydantic import BaseModel
from werkzeug.utils import secure_filename

# Add project directories to path
sys.path.extend([
    os.path.abspath(os.path.dirname(__file__)),
    os.path.abspath(os.path.join(os.path.dirname(__file__), 'agents')),
    os.path.abspath(os.path.join(os.path.dirname(__file__), 'vector_stores')),
    os.path.abspath(os.path.join(os.path.dirname(__file__), 'tools')),
    os.path.abspath(os.path.join(os.path.dirname(__file__), 'main_graph')),
])

from vector_stores.L_vecdB import LongTermDatabase
from vector_stores.S_vecdB import ShortTermDatabase
from tools.email_scraper import EmailScraper
from pipeline.RAGnarok import RAGnarok

# --- Logging setup ---
logging.basicConfig(
    filename='rag.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app init
fastapp = FastAPI()
fastapp.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://rag-narok-ul49.onrender.com",
        "https://rag-narok.vercel.app",
        "https://rag-narok-aiclubiitropars-projects.vercel.app",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
LONG_TERM_PREFIX = "longterm_db"
SHORT_TERM_PREFIX = "shortterm_db"
os.makedirs(LONG_TERM_PREFIX, exist_ok=True)
os.makedirs(SHORT_TERM_PREFIX, exist_ok=True)

# Databases
long_db = LongTermDatabase(collection_prefix=LONG_TERM_PREFIX)
short_db = ShortTermDatabase(collection_prefix=SHORT_TERM_PREFIX, fetch_latest_email=lambda: None)

# Global state
user_rag_dict: Dict[str, Dict[str, Any]] = {}
USER_RAG_TIMEOUT = 30 * 60  # seconds
model_name = os.getenv('MODEL_NAME', 'qwen/qwen3-32b')
worker_thread: Optional[threading.Thread] = None
worker_running = False

# Pydantic models
class ChatRequest(BaseModel):
    query: str
    user_uuid: str

class ChangeModelRequest(BaseModel):
    model: str

class Credentials(BaseModel):
    email: str
    password: str

# Admin authentication endpoint (mirrors Flask verify_credentials)
@fastapp.post("/admin/verify_credentials")
async def verify_credentials(creds: Credentials):
    admin_email = os.getenv('ADMIN_EMAIL')
    admin_password = os.getenv('ADMIN_PASSWORD')
    if not creds.email or not creds.password:
        raise HTTPException(status_code=400, detail="Email and password are required.")
    if creds.email == admin_email and creds.password == admin_password:
        return JSONResponse(status_code=200, content={"message": "Authentication successful."})
    raise HTTPException(status_code=401, detail="Invalid credentials.")

# Admin dependency for other routes
async def require_admin(request: Request):
    auth = request.headers.get('Authorization')
    # Expecting a token or Basic header as pre-shared secret: ADMIN_TOKEN
    admin_token = os.getenv('ADMIN_TOKEN')
    if not auth or auth != f"Bearer {admin_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")

# Background worker and email callback (define fetch_latest_email as needed)
def shortterm_worker():
    global worker_running
    worker_running = True
    try:
        short_db.run_worker()
    except Exception as e:
        logger.error(f"Worker error: {e}\n{traceback.format_exc()}")
    finally:
        worker_running = False

@fastapp.on_event("startup")
def startup_event():
    global worker_thread, worker_running
    if not worker_thread or not worker_thread.is_alive():
        worker_thread = threading.Thread(target=shortterm_worker, daemon=True)
        worker_thread.start()
        worker_running = True
        logger.info("Short-term worker started on startup.")

# Utility to clean sessions
def cleanup_user_sessions():
    now = time.time()
    expired = [uid for uid, v in user_rag_dict.items() if now - v['last_access'] > USER_RAG_TIMEOUT]
    for uid in expired:
        user_rag_dict.pop(uid, None)

# Admin-protected endpoints
@fastapp.get("/admin/worker_status", dependencies=[Depends(require_admin)])
async def worker_status():
    return {'running': worker_running}

@fastapp.post("/admin/change_model", dependencies=[Depends(require_admin)])
async def change_model(req: ChangeModelRequest):
    global model_name
    model_name = req.model
    logger.info(f"Model changed to: {model_name}")
    return {'message': f'Model updated to {model_name}'}

@fastapp.post("/admin/upload_json", dependencies=[Depends(require_admin)])
async def upload_json(file: UploadFile = File(...)):
    if not file.filename.endswith('.json'):
        raise HTTPException(400, 'Only JSON files allowed')
    upload_dir = 'uploads'
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, secure_filename(file.filename))
    with open(path, 'wb') as f:
        f.write(await file.read())
    try:
        long_db.add_data(path)
        logger.info(f"Uploaded and ingested: {path}")
    except Exception as e:
        raise HTTPException(500, f'Ingestion failed: {e}')
    finally:
        os.remove(path)
    return {'message': 'File uploaded and ingested'}

@fastapp.get("/admin/logs", dependencies=[Depends(require_admin)])
async def get_logs():
    if not os.path.exists('rag.log'):
        raise HTTPException(404, 'Log not found')
    return FileResponse('rag.log', filename='rag.txt', media_type='text/plain')

# Public chat endpoint
@fastapp.post("/chat")
async def chat(req: ChatRequest):
    if not req.query or not req.user_uuid:
        raise HTTPException(400, 'query and user_uuid required')
    cleanup_user_sessions()
    now = time.time()
    if req.user_uuid not in user_rag_dict:
        user_rag_dict[req.user_uuid] = {
            'rag': RAGnarok(long_db, short_db, model=model_name),
            'last_access': now
        }
    else:
        user_rag_dict[req.user_uuid]['last_access'] = now
    rag = user_rag_dict[req.user_uuid]['rag']
    try:
        result = rag.invoke(req.query)
    except Exception as e:
        logger.error(f"RAG invocation failed: {e}")
        raise HTTPException(500, 'RAG processing error')
    return {'response': result}

@fastapp.get("/")
async def root():
    return PlainTextResponse("RAG-narok FastAPI backend running.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(fastapp, host="0.0.0.0", port=int(os.getenv('PORT', 5000)), reload=True)
