# --- Logging setup: ensure logs are written to rag.log in project root ---
import logging
logging.basicConfig(
    filename='rag.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from urllib import response
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from flask_cors import CORS
import threading
import os
import traceback
from functools import wraps
from flask import session
import uuid
from flask import make_response, g
import time
import random

# Ensure project root is on path for imports
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'agents')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'vector_stores')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'tools')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'main_graph')))

from vector_stores.L_vecdB import LongTermDatabase
from vector_stores.S_vecdB import ShortTermDatabase
from tools.email_scraper import EmailScraper
from pipeline.RAGnarok import RAGnarok

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your-default-secret-key")
CORS(app, supports_credentials=True, origins=[
    "https://rag-narok-ul49.onrender.com",
    "https://rag-narok.vercel.app",
    "https://rag-narok-aiclubiitropars-projects.vercel.app",
    "http://localhost:3000"
])

# Define persistent directories for long-term and short-term databases
LONG_TERM_PREFIX = "longterm_db"
SHORT_TERM_PREFIX = "shortterm_db"

# Ensure persistent directories exist
os.makedirs(LONG_TERM_PREFIX, exist_ok=True)
os.makedirs(SHORT_TERM_PREFIX, exist_ok=True)

# Initialize databases with Qdrant-compatible arguments
long_db = LongTermDatabase(collection_prefix=LONG_TERM_PREFIX)

# Update the fetch_latest_email callback to use EmailScraper

def fetch_latest_email():
    """
    Fetch the latest email using the EmailScraper class. If summarization fails, skip the email.
    """
    from tools.sumar import summarize_text
    from datetime import datetime
    scraper = EmailScraper()
    print("Fetching latest email...")
    emails = scraper.scrape_latest_emails(count=1)
    if not emails:
        app.logger.warning("No emails found when fetching latest email.")
        return None
    latest_email_id, latest_email = next(iter(emails.items()))
    body = latest_email.get('body', '')
    from_ = latest_email.get('from', '')
    subject = latest_email.get('subject', '')
    timestamp = latest_email.get('timestamp', datetime.utcnow().isoformat())
    try:
        summary = summarize_text(body)
        # Concatenate 'from', 'subject', and 'timestamp' to the summarized body
        summary = f"From: {from_}\nSubject: {subject}\nTimestamp: {timestamp}\n{summary}"
    except Exception as e:
        app.logger.warning(f"Summarization failed for email {latest_email_id}: {e}. Skipping email.")
        return None
    # Return as a list of dicts for objectwise ingestion, including 'from', 'subject', and 'timestamp'
    return [{
        'id': latest_email_id,
        'body': summary,
        'from': from_,
        'subject': subject,
        'timestamp': timestamp
    }]

# Pass the callback to ShortTermDatabase
short_db = ShortTermDatabase(
    collection_prefix=SHORT_TERM_PREFIX,
    fetch_latest_email=fetch_latest_email
)

# --- Short-term DB background worker management ---
global_worker_thread = None
global_worker_stop_event = threading.Event()
global_worker_running = False  # New global flag for worker status

model = 'qwen/qwen3-32b'

def shortterm_worker():
    global global_worker_running
    global_worker_running = True
    try:
        short_db.run_worker()
    except Exception as e:
        print(f"Short-term worker error: {e}")
        traceback.print_exc()
    finally:
        global_worker_running = False

def start_worker_thread_if_needed():
    global global_worker_thread, global_worker_stop_event, global_worker_running
    # Only start the worker in the main Flask process (not the reloader)
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        if not global_worker_thread or not global_worker_thread.is_alive():
            global_worker_stop_event.clear()
            global_worker_thread = threading.Thread(target=shortterm_worker)
            global_worker_thread.start()
            global_worker_running = True
            app.logger.info("Short-term worker thread started automatically on backend startup.")

# Start the worker thread at app startup
start_worker_thread_if_needed()

# --- Simple session-based decorator for admin endpoints ---
def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Removed admin email check
        return f(*args, **kwargs)
    return decorated

# --- Global dictionary for user RAGnarok objects with last access time ---
user_rag_dict = {}  # {user_uuid: {'rag': RAGnarok, 'last_access': timestamp}}
USER_RAG_TIMEOUT = 30 * 60  # 30 minutes in seconds

def cleanup_user_rag_dict():
    """Remove user sessions that have been inactive for more than USER_RAG_TIMEOUT seconds."""
    now = time.time()
    to_delete = [uuid for uuid, v in user_rag_dict.items() if now - v['last_access'] > USER_RAG_TIMEOUT]
    for uuid in to_delete:
        del user_rag_dict[uuid]

# --- Global model variable ---
# model = 'deepseek-r1-distill-llama-70b'  # Default model
@app.route('/admin/change_model', methods=['POST'])
def change_model():
    global model
    try:
        data = request.get_json()
        new_model = data.get('model')
        if not new_model:
            return jsonify({'error': 'No model provided.'}), 400
        model = new_model
        app.logger.info(f"Model changed to: {model}")
        return jsonify({'message': f'Model changed to {model}.'}), 200
    except Exception as e:
        app.logger.error(f"Error changing model: {e}")
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

# --- API Endpoints ---
@app.route('/admin/upload_json', methods=['POST'])
@require_admin
def upload_json():
    try:
        if 'file' not in request.files:
            app.logger.error("No file part in the request.")
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            app.logger.error("No file selected for upload.")
            return jsonify({'error': 'No selected file'}), 400

        if not file.filename.endswith('.json'):
            app.logger.error("Uploaded file is not a JSON file.")
            return jsonify({'error': 'Invalid file type. Only JSON files are allowed.'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        os.makedirs('uploads', exist_ok=True)
        file.save(filepath)

        app.logger.info(f"File {filename} saved successfully at {filepath}.")

        # Add the uploaded JSON data to the long-term database
        try:
            app.logger.info(f"Adding data from {filename} to the long-term database...")
            long_db.add_data(filepath)
            app.logger.info(f"Data from {filename} added to the long-term database successfully.")
        except Exception as e:
            app.logger.error(f"Failed to add data from {filename} to the long-term database: {e}")
            return jsonify({'error': 'Failed to process the file.', 'details': str(e)}), 500

        return jsonify({'message': 'File uploaded and data added to long-term DB.'}), 200
    except Exception as e:
        app.logger.error(f"Unexpected error during file upload: {e}")
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500
    finally:
        # Clean up the uploaded file to save space
        if os.path.exists(filepath):
            os.remove(filepath)

# Ensure the worker thread persists across sessions
@app.route('/admin/start_shortterm_worker', methods=['POST'])
@require_admin
def start_shortterm_worker():
    global global_worker_thread, global_worker_stop_event, global_worker_running
    if global_worker_thread and global_worker_thread.is_alive():
        app.logger.info("Worker thread is already running.")
        return jsonify({'message': 'Short-term worker already running.'}), 200

    # Reset the stop event to ensure the thread runs continuously
    global_worker_stop_event.clear()
    global_worker_thread = threading.Thread(target=shortterm_worker)
    global_worker_thread.start()
    global_worker_running = True
    app.logger.info("Worker thread has been started and will save updates to the short-term directory.")
    return jsonify({'message': 'Short-term worker started.'}), 200

@app.route('/admin/stop_shortterm_worker', methods=['POST'])
@require_admin
def stop_shortterm_worker():
    global global_worker_stop_event, global_worker_running
    try:
        global_worker_stop_event.set()  # Signal the thread to stop
        short_db.stop_worker()
        global_worker_running = False
        return jsonify({'message': 'Short-term worker stopped.'}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

@app.route('/admin/worker_status', methods=['GET'])
@require_admin
def worker_status():
    global global_worker_running
    running = global_worker_running
    status = {
        'running': running
    }
    if not running:
        app.logger.warning("Worker thread is not running.")
    else:
        app.logger.info("Worker thread is running.")
    return jsonify(status)

# # Ensure RAGnarok is instantiated correctly
# rg = RAGnarok(long_db, short_db)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        query = data.get('query')
        user_uuid = data.get('user_uuid')
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        if not user_uuid:
            return jsonify({'error': 'No user_uuid provided'}), 400

        global user_rag_dict, model, api_keys
        cleanup_user_rag_dict()  # Clean up expired sessions on each chat

        app.logger.info(f"Received user_uuid: {user_uuid}")
        app.logger.info(f"Current user_rag_dict keys: {list(user_rag_dict.keys())}")

        now = time.time()
        if user_uuid not in user_rag_dict:
            user_rag_dict[user_uuid] = {
                'rag': RAGnarok(long_db, short_db, model=model),
                'last_access': now
            }
        else:
            user_rag_dict[user_uuid]['last_access'] = now

        user_rg = user_rag_dict[user_uuid]['rag']
        response_text = user_rg.invoke(query)
        app.logger.info(f"RAGnarok response: {response_text}")

        resp = make_response(jsonify({'response': response_text}), 200)
        return resp
    except Exception as e:
        app.logger.error(f"Unexpected error in /chat endpoint: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred. Please try again later.'}), 500


# --- Admin Authentication Endpoint ---
@app.route('/admin/verify_credentials', methods=['POST'])
def verify_credentials():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required.'}), 400

        admin_email = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')

        if email == admin_email and password == admin_password:
            return jsonify({'message': 'Authentication successful.'}), 200
        else:
            return jsonify({'error': 'Invalid credentials.'}), 401

    except Exception as e:
        app.logger.error(f"Error during admin authentication: {e}")
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


# Flag to ensure initialization logic runs only once
initialized = False

@app.before_request
def initialize_databases():
    global initialized
    if not initialized:
        initialized = True
        try:
            if not os.listdir(LONG_TERM_PREFIX):
                app.logger.info("Long-term database is empty. Initializing with default data.")
                # Add logic to populate long-term database with initial data if needed

            if not os.listdir(SHORT_TERM_PREFIX):
                app.logger.info("Short-term database is empty. Initializing with default data.")
                # Add logic to populate short-term database with initial data if needed

        except Exception as e:
            app.logger.error(f"Error during database initialization: {e}")

# --- Graceful shutdown ---
import atexit
@atexit.register
def cleanup():
    try:
        stop_shortterm_worker()
        short_db.close()
    except Exception:
        pass
    
@app.route('/admin/logs', methods=['GET'])
def download_logs():
    log_path = 'rag.log'  # Adjust path if your log file is elsewhere
    if not os.path.exists(log_path):
        return jsonify({'error': 'Log file not found.'}), 404
    return send_file(log_path, as_attachment=True, download_name='rag.txt')

@app.route('/', methods=['GET'])
def index():
    return "RAG-narok backend is running.", 200

@app.before_request
def before_request():
    pass

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=True, threaded=True)
