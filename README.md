# RAGnarok

RAGnarok is an advanced Retrieval-Augmented Generation (RAG) chatbot system for IIT Ropar. It combines LLM-based reasoning with robust retrieval from both long-term and short-term memory, and features a modern React frontend and a Flask backend.

## Features
- **Chatbot for IIT Ropar:** Ask about campus life, academics, and more.
- **RAG Pipeline:** Combines LLM output with context from vector databases.
- **Admin Panel:** Start/stop worker, upload JSON data, download logs, and monitor worker status.
- **Robust Worker Management:** Background thread for short-term memory, with status tracking and error handling.
- **Frontend:** Modern React UI with custom branding and admin controls.
- **Backend:** Flask API with endpoints for chat, admin, and file management.

## Quick Start

### Backend
1. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
2. Run the backend:
   ```sh
   python app.py
   ```

### Frontend
1. Go to the client directory:
   ```sh
   cd client
   ```
2. Install dependencies:
   ```sh
   npm install
   ```
3. Start the frontend:
   ```sh
   npm start
   ```

### Usage
- Access the chatbot at [http://localhost:3000](http://localhost:3000)
- Use the Admin Panel for worker and data management.

## File Structure
- `app.py` — Flask backend
- `client/` — React frontend
- `longterm_db/`, `shortterm_db/` — Vector DB storage
- `uploads/` — Uploaded files
- `tools/`, `agents/`, `pipeline/` — Core logic

## Notes
- Large DB files (e.g., `chroma.sqlite3`) are ignored by git and should not be pushed to GitHub.
- For production, use a WSGI server (e.g., gunicorn) for the backend.

---

© 2025 IIT Ropar RAGnarok Team