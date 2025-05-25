import time
import threading
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Callable, Dict, Optional, List
import chromadb
from chromadb.config import Settings
from L_vecdB import LongTermDatabase, BGEM3FlagModel

class ShortTermDatabase:
    """
    A short-term email storage that buffers recent emails and periodically
    or size-based flushes to a LongTermDatabase.
    Stores both short-term and long-term directories for persistence.

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
        client_settings: Settings,
        short_term_folder: str,
        long_term_folder: str,
        model: Callable[[List[str]], List[List[float]]] = BGEM3FlagModel().encode,
        time_threshold: float = 1.0,
        count_threshold: int = 100,
        fetch_latest_email: Optional[Callable[[], Dict]] = None,
        poll_interval: float = 60
    ):
        # Store persistence directories
        self.short_term_folder = short_term_folder
        self.long_term_folder = long_term_folder

        # Initialize Chroma client for short-term
        self.client = chromadb.Client(Settings(persist_directory=self.short_term_folder))
        self.short_data = self.client.get_or_create_collection(
            name="short_main_data",
            persist_directory=self.short_term_folder
        )
        self.short_meta = self.client.get_or_create_collection(
            name="short_meta_data",
            persist_directory=self.short_term_folder
        )

        # Embedding model function
        self.model = model

        # Buffer control thresholds
        self.time_threshold = timedelta(days=time_threshold)
        self.count_threshold = count_threshold
        self.fetch_latest_email = fetch_latest_email
        self.poll_interval = poll_interval

        # Internal tracking
        self._last_flush_time = datetime.utcnow()
        self._last_email_id: Optional[str] = None
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def vectorize_and_add(self, email: Dict):
        """
        Vectorize the email body and metadata, then add to short-term collections and persist.
        """
        eid = email['id']
        raw = email['body']
        meta = {k: email[k] for k in email if k != 'body'}

        # Vectorize text and metadata
        data_vec = self.model([raw])[0]
        meta_vec = self.model([json.dumps(meta)])[0]

        # Add vectors to ChromaDB
        self.short_data.add(ids=[eid], embeddings=[data_vec], metadatas=[email], documents=[raw])
        self.short_meta.add(ids=[eid], embeddings=[meta_vec], metadatas=[meta], documents=[json.dumps(meta)])

        # Persist after adding
        self.persist()

        # Check and flush if needed
        self._maybe_flush()

    # Alias for backward compatibility
    add_email = vectorize_and_add

    def _maybe_flush(self):
        now = datetime.utcnow()
        count = len(self.short_data.get(ids=[], include=['ids'])['ids'])
        if (now - self._last_flush_time) > self.time_threshold or count >= self.count_threshold:
            self.flush_to_long_term()

    def flush_to_long_term(self):
        """
        Move all buffered emails to the long-term database and persist both sides.
        """
        # Initialize long-term DB
        long_db = LongTermDatabase(
            persist_directory=self.long_term_folder,
            model_name=None,
            use_fp16=None
        )

        # Retrieve buffered data
        entries = self.short_data.get(include=['ids', 'embeddings', 'metadatas'])
        meta_entries = self.short_meta.get(include=['ids', 'embeddings'])

        # Transfer to long-term
        long_db.receive_data(
            ids=entries['ids'],
            data_embeddings=entries['embeddings'],
            data_metadatas=entries['metadatas'],
            meta_embeddings=meta_entries['embeddings']
        )

        # Clear short-term buffers
        self.short_data.delete(ids=entries['ids'])
        self.short_meta.delete(ids=entries['ids'])
        self._last_flush_time = datetime.utcnow()

        # Persist both databases
        self.persist()
        long_db.save()

    def start_polling(self):
        """
        Begin background polling: fetch latest email and sync; persist state.
        """
        if not self.fetch_latest_email:
            raise ValueError("fetch_latest_email callback not provided.")
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        self.persist()

    def stop_polling(self):
        """
        Stop the background polling thread and persist.
        """
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        self.persist()

    def _poll_loop(self):
        while not self._stop_event.is_set():
            try:
                email = self.fetch_latest_email()
                if email and email.get('id') != self._last_email_id:
                    self._last_email_id = email['id']
                    self.vectorize_and_add(email)
            except Exception:
                pass
            time.sleep(self.poll_interval)

    def smart_query(self, query_text: str, topk_meta: int = 10, topk_data: int = 5) -> List[str]:
        """
        Two-stage retrieval on short-term data:
        1. Retrieve top-k_meta IDs from metadata similarity.
        2. Re-rank those by content similarity and return topk_data results.
        """
        # Encode query
        q_emb = self.model([query_text])[0]
        # Stage 1: metadata similarity
        meta_res = self.short_meta.query(query_embeddings=[q_emb], n_results=topk_meta)
        candidate_ids = meta_res['ids'][0]

        # Stage 2: fetch and rank by main content similarity
        full_res = self.short_data.get(ids=candidate_ids, include=['documents', 'embeddings', 'metadatas'])
        docs = full_res['documents']
        embs = full_res['embeddings']
        metas = full_res['metadatas']

        # Compute cosine similarities
        q_norm = np.linalg.norm(q_emb)
        d_norms = np.linalg.norm(embs, axis=1)
        sims = np.dot(embs, q_emb) / (d_norms * q_norm + 1e-8)
        idx_sorted = np.argsort(-sims)[:topk_data]

        results = []
        for idx in idx_sorted:
            item_id = candidate_ids[idx]
            full_doc = docs[idx]
            meta = metas[idx]
            results.append(f"{item_id} | {full_doc} | {json.dumps(meta, ensure_ascii=False)}")
        return results

    def persist(self):
        """
        Force persist short-term state to disk.
        """
        self.client.persist()

    def close(self):
        """
        Clean shutdown: stop polling and persist.
        """
        self.stop_polling()
        self.persist()