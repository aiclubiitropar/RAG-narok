from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from flask_cors import CORS
import threading
import os
import traceback

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
from main_graph.arch_graph import RAGGraph

app = Flask(__name__)
CORS(app)

# --- Initialize Databases and Email Scraper ---
long_db = LongTermDatabase()
short_db = ShortTermDatabase()
scraper = EmailScraper()

# --- Short-term DB background worker management ---
global_worker_thread = None
global_worker_stop_event = threading.Event()

def shortterm_worker():
    try:
        short_db.run_worker()
    except Exception as e:
        print(f"Short-term worker error: {e}")
        traceback.print_exc()

# --- API Endpoints ---
@app.route('/admin/upload_json', methods=['POST'])
def upload_json():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        os.makedirs('uploads', exist_ok=True)
        file.save(filepath)
        long_db.add_data(filepath)
        return jsonify({'message': 'File uploaded and data added to long-term DB.'}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

@app.route('/admin/start_shortterm_worker', methods=['POST'])
def start_shortterm_worker():
    global global_worker_thread
    if global_worker_thread and global_worker_thread.is_alive():
        return jsonify({'message': 'Short-term worker already running.'}), 200
    global_worker_thread = threading.Thread(target=shortterm_worker, daemon=True)
    global_worker_thread.start()
    return jsonify({'message': 'Short-term worker started.'}), 200

@app.route('/admin/stop_shortterm_worker', methods=['POST'])
def stop_shortterm_worker():
    try:
        short_db.stop_worker()
        return jsonify({'message': 'Short-term worker stopped.'}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

@app.route('/info', methods=['GET'])
def info():
    return jsonify({
        'app_name': 'RAGnarok',
        'version': '1.0',
        'description': 'RAGnarok – IIT Ropar Chatbot: Ask about IIT Ropar, campus life, academics, and more.'
    })

@app.route('/admin/logs', methods=['GET'])
def download_logs():
    log_path = 'rag.log'
    if not os.path.exists(log_path):
        return jsonify({'error': 'Log file not found.'}), 404
    return send_file(log_path, as_attachment=True)

@app.route('/admin/worker_status', methods=['GET'])
def worker_status():
    running = global_worker_thread is not None and global_worker_thread.is_alive()
    return jsonify({'running': running})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        query = data.get('query')
        if not query:
            return jsonify({'error': 'No query provided.'}), 400
        # Run the RAGnarok pipeline (arch_graph)
        graph = RAGGraph()
        compiled_graph = graph.compile()
        compiled_graph.invoke({'query': query})
        output = graph.final_invoked_response()
        # Add a 'source' field if possible (dummy logic, adapt as needed)
        source = 'RAG'
        if output.startswith('[Google Search'):
            source = 'Google'
        elif not output.strip():
            source = 'Fallback'
        return jsonify({'response': output, 'source': source}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

# --- Graceful shutdown ---
import atexit
@atexit.register
def cleanup():
    try:
        stop_shortterm_worker()
        short_db.close()
    except Exception:
        pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
