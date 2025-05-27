import os
import sys
import time
import threading
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Callable, Dict, Optional, List
import chromadb
from chromadb.config import Settings
from vector_stores.L_vecdB import LongTermDatabase
from sentence_transformers import SentenceTransformer

# Ensure project root is on path for tool imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.email_scraper import EmailScraper
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ShortTermDatabase:
    """
    A short-term email storage that buffers recent emails and periodically
    or size-based flushes to a LongTermDatabase.

    Parameters:
        client_settings: ChromaDB client settings.
        short_term_folder: Directory for short-term persistence.
        long_term_folder: Directory for long-term persistence.
        model: Embedding function taking List[str] -> List[List[float]].
        time_threshold: Flush interval in **days** (default: 1 day).
        count_threshold: Number of emails to buffer before flush.
        fetch_latest_email: Optional callback to retrieve latest email dict.
        poll_interval: Seconds between fetch calls in polling loop.
    """
    def __init__(
        self,
        client_settings: Settings = Settings(persist_directory="shortterm_db"),
        short_term_folder: str = "shortterm_db",
        long_term_folder: str = "longterm_db",
        model: Callable[[List[str]], List[List[float]]] = None,
        time_threshold: float = 1.0,
        count_threshold: int = 100,
        fetch_latest_email: Optional[Callable[[], Dict]] = None,
        poll_interval: float = 60
    ):
        self.short_term_folder = short_term_folder
        self.long_term_folder = long_term_folder

        # Initialize Chroma client for short-term
        self.client = chromadb.Client(settings=client_settings)
        self.short_data = self.client.get_or_create_collection(name="short_main_data")
        self.short_meta = self.client.get_or_create_collection(name="short_meta_data")

        # Embedding model
        self.model = model or SentenceTransformer(
            'paraphrase-multilingual-MiniLM-L12-v2'
        ).encode

        # Flush thresholds
        self.time_threshold = timedelta(days=time_threshold)
        self.count_threshold = count_threshold
        self.fetch_latest_email = fetch_latest_email
        self.poll_interval = poll_interval

        # Internal state
        self._last_flush_time = datetime.utcnow()
        self._last_email_id: Optional[str] = None
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def vectorize_and_add(self, email: Dict):
        """
        Vectorize the email body and metadata, then add to short-term collections.
        """
        eid = email['id']
        raw = email['body']
        metadata = email.get('metadata', {})

        data_vec = self.model([raw])[0]
        meta_vec = self.model([json.dumps(metadata)])[0]

        # Add to main data store
        self.short_data.add(
            ids=[eid],
            embeddings=[data_vec],
            metadatas=[metadata],
            documents=[raw]
        )
        # Add to metadata store
        self.short_meta.add(
            ids=[eid],
            embeddings=[meta_vec],
            metadatas=[metadata],
            documents=[json.dumps(metadata)]
        )

    # Alias
    add_email = vectorize_and_add

    def _maybe_flush(self):
        now = datetime.utcnow()
        count = self.short_data.count()
        if (now - self._last_flush_time) > self.time_threshold or count >= self.count_threshold:
            self.flush_to_long_term()

    def flush_to_long_term(self):
        """
        Move all buffered emails to the long-term database.
        """
        long_db = LongTermDatabase(persist_directory=self.long_term_folder)
        short_data = self.short_data.get(include=["documents", "embeddings", "metadatas"])
        short_meta = self.short_meta.get(include=["documents", "embeddings", "metadatas"])

        # Add data to long-term database
        long_db.main_data.add(
            ids=short_data["ids"],
            embeddings=short_data["embeddings"],
            metadatas=short_data["metadatas"],
            documents=short_data["documents"]
        )
        long_db.meta_data.add(
            ids=short_meta["ids"],
            embeddings=short_meta["embeddings"],
            metadatas=short_meta["metadatas"],
            documents=short_meta["documents"]
        )

        # Persist changes to long-term database
        long_db.save()

        # Clear short-term database
        self.short_data.delete(ids=short_data["ids"])
        self.short_meta.delete(ids=short_meta["ids"])
        self._last_flush_time = datetime.utcnow()

    def _worker_loop(self):
        """
        Internal loop: fetch, add, flush, sleep.
        """
        blocklist = [
            "no-reply@accounts.google.com", "Security alert", "unstop", "linkedin", "kaggle", "Team Unstop", "Canva", "noreply@github.com", "noreply", "feed"
        ]
        while not self._stop_event.is_set():
            if self.fetch_latest_email:
                email = self.fetch_latest_email()
                # Blocklist filtering
                if email:
                    subject = email.get('subject', '')
                    from_ = email.get('from', '')
                    if any(keyword in (subject or "") for keyword in blocklist) or any(keyword in (from_ or "") for keyword in blocklist):
                        logging.info(f"Blocked email from: {from_}, subject: {subject}")
                    elif email['id'] != self._last_email_id:
                        self._last_email_id = email['id']
                        self.vectorize_and_add(email)
            self._maybe_flush()
            time.sleep(self.poll_interval)

    def run_worker(self):
        """
        Launch the background ingestion thread.
        """
        if not self.fetch_latest_email:
            raise ValueError("fetch_latest_email callback not provided.")
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def stop_worker(self):
        """
        Stop the ingestion thread.
        """
        self._stop_event.set()
        if self._thread:
            self._thread.join()

    def smart_query(self,
                    query_text: str,
                    topk_meta: int = 10,
                    topk_data: int = 5) -> List[str]:
        """
        Two-stage retrieval: metadata then content.
        """
        q_emb = self.model([query_text])[0]
        meta_res = self.short_meta.query(
            query_embeddings=[q_emb], n_results=topk_meta
        )
        candidate_ids = meta_res['ids'][0]

        try:
            full_res = self.short_data.get(
                ids=candidate_ids,
                include=['documents', 'embeddings', 'metadatas']
            )
        except ValueError as e:
            logging.error(f"Error retrieving data from short-term database: {e}")
            return []

        docs = full_res['documents']
        embs = np.array(full_res['embeddings'])
        metas = full_res['metadatas']

        q_norm = np.linalg.norm(q_emb)
        d_norms = np.linalg.norm(embs, axis=1)
        sims = embs.dot(q_emb) / (d_norms * q_norm + 1e-8)
        idx_sorted = np.argsort(-sims)[:topk_data]

        return [
            f"{candidate_ids[i]} | {docs[i]} | {json.dumps(metas[i], ensure_ascii=False)}"
            for i in idx_sorted
        ]

    def close(self):
        """
        Clean shutdown.
        """
        self.stop_worker()


if __name__ == "__main__":
    # Initialize EmailScraper and ShortTermDatabase
    scraper = EmailScraper()

    def fetch_latest_email():
        raw_map = scraper.scrape_latest_emails(count=1)
        if raw_map:
            eid, data = next(iter(raw_map.items()))
            data['id'] = eid
            return data
        return None

    db = ShortTermDatabase(fetch_latest_email=fetch_latest_email)
    logging.info("Starting email ingestion worker...")
    db.run_worker()

    try:
        while True:
            query = input("Enter query (or 'exit'): ")
            if query.lower() == 'exit':
                break
            results = db.smart_query(query_text=query)
            for r in results:
                print(r)
    finally:
        logging.info("Shutting down worker...")
        db.close()
