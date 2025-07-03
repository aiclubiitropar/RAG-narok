import os
import sys
import time
import threading
import json
import numpy as np
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Callable, Dict, Optional, List
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


# Fix import errors for direct script execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from L_vecdB import LongTermDatabase
from embedding import get_dense_embedding, to_valid_qdrant_id

from tools.email_scraper import EmailScraper
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

class ShortTermDatabase:
    def __init__(
        self,
        collection_prefix: str = "shortterm_db",
        vector_size: int = 768,
        time_threshold_days: float = 1.0,
        count_threshold: int = 100,
        fetch_latest_email: Optional[Callable[[], Dict]] = None,
        poll_interval: float = 60,
        qdrant_url: str = "https://df35413f-27c8-419d-aa89-4b3901514560.us-west-1-0.aws.cloud.qdrant.io",
        qdrant_api_key: Optional[str] = None
    ):
        self.collection_prefix = collection_prefix
        self.vector_size = vector_size
        self.client = QdrantClient(url=qdrant_url, api_key=os.getenv('QDRANT_API_KEY', qdrant_api_key))
        self.collection_name = "short_rag"
        self._ensure_collection()  # Ensure multi-vector config
        self.time_threshold = timedelta(days=time_threshold_days)
        self.count_threshold = count_threshold
        self.fetch_latest_email = fetch_latest_email
        self.poll_interval = poll_interval
        self._last_flush_time = datetime.utcnow()
        self._last_email_id: Optional[str] = None
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _ensure_collection(self):
        from qdrant_client.models import MultiVectorConfig, MultiVectorComparator, HnswConfigDiff
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in existing:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "dense": VectorParams(size=self.vector_size, distance=Distance.COSINE),
                    "late": VectorParams(
                        size=768,
                        distance=Distance.COSINE,
                        multivector_config=MultiVectorConfig(
                            comparator=MultiVectorComparator.MAX_SIM
                        ),
                        hnsw_config=HnswConfigDiff(m=0)
                    )
                }
            )

    def _batch_get_embeddings(self, texts: List[str]):
        # Multi-embedding: dense and late (ColBERT-style)
        from embedding import get_dense_embedding, get_late_embedding
        dense_embs = [get_dense_embedding(text) for text in texts]
        late_embs = [get_late_embedding(text) for text in texts]
        return list(zip(dense_embs, late_embs))

    # add_email removed: use add_emails_batch for all ingestion

    def add_emails_batch(self, emails: List[Dict], batch_size: int = 4):
        """
        Batch add multiple emails efficiently using upsert (multi-embedding).
        Uses unique IDs for each email. Does NOT store metadata in the payload.
        """
        ids, raws = [], []
        for email in emails:
            eid = email['id']
            ids.append(eid)
            raws.append(email['body'])
        emb_pairs = self._batch_get_embeddings(raws)
        points = []
        for i, eid in enumerate(ids):
            dense_vec, late_vec = emb_pairs[i]
            points.append(
                PointStruct(
                    id=to_valid_qdrant_id(eid),
                    vector={"dense": dense_vec, "late": late_vec},
                    payload={"document": raws[i]}
                )
            )
        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
            time.sleep(1)  # short pause between batches

    def _maybe_flush(self):
        now = datetime.utcnow()
        print(f"[MAYBE FLUSH] Checking if flush is needed at {now}...")
        count = self.client.count(collection_name=self.collection_name).count
        if (now - self._last_flush_time) > self.time_threshold or count >= self.count_threshold:
            self.flush_to_long_term()

    def flush_to_long_term(self):
        count = self.client.count(collection_name=self.collection_name).count
        print(f"[FLUSH] Short-term DB size before flush: {count} emails")
        # Ensure long-term DB collection name matches convention (e.g., "long_rag")
        long_db = LongTermDatabase(collection_prefix="longterm_db")
        long_db.collection_name = "long_rag"  # Ensure consistent collection name
        scroll = self.client.scroll(collection_name=self.collection_name, with_vectors=True, with_payload=True)
        ids, vectors, documents = [], [], []
        for point in scroll[0]:
            ids.append(to_valid_qdrant_id(point.id))
            vectors.append(point.vector)
            documents.append(point.payload.get("document", ""))
        print(f"[FLUSH] Fetched {len(ids)} items from '{self.collection_name}' for flushing.")
        # Pass empty list for metadatas to long_db, since we do not store metadata in short-term DB
        long_db._upsert_collection(long_db.collection_name, ids, vectors, documents, [{} for _ in ids])
        long_db.save()
        self.client.delete(collection_name=self.collection_name, points=ids)
        self._last_flush_time = datetime.utcnow()
        count_after = self.client.count(collection_name=self.collection_name).count
        print(f"[FLUSH] Short-term DB size after flush: {count_after} emails")

    def _worker_loop(self):
        blocklist = [
            "no-reply@accounts.google.com", "Security alert", "unstop", "linkedin", "kaggle", "Team Unstop",
            "Canva", "noreply@github.com", "noreply", "feed, onrender, UptimeRobot"
        ]
        while not self._stop_event.is_set():
            if self.fetch_latest_email:
                emails = self.fetch_latest_email()
                if not emails:
                    logging.info("No new email found. Skipping this iteration.")
                    self._maybe_flush()
                    time.sleep(self.poll_interval)
                    continue
                # Always treat as a list for robustness
                if isinstance(emails, dict):
                    emails = [emails]
                for email in emails:
                    subject = email.get('subject', '')
                    from_ = email.get('from', '')
                    if any(k in subject for k in blocklist) or any(k in from_ for k in blocklist):
                        logging.info(f"Blocked email from: {from_}, subject: {subject}")
                    elif email['id'] != self._last_email_id:
                        self._last_email_id = email['id']
                        self.add_emails_batch([email])
            self._maybe_flush()
            count = self.client.count(collection_name=self.collection_name).count
            print(f"Short-term DB size: {count} emails")
            time.sleep(self.poll_interval)

    def run_worker(self):
        if not self.fetch_latest_email:
            raise ValueError("fetch_latest_email callback not provided.")
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def stop_worker(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join()

    def smart_query(self, query_text: str, topk: int = 20, top_l: int = 5, use_late: bool = True, doc_search: bool = True):
        """
        Hybrid query: first prefetch with dense (topk), then rerank with late embedding (ColBERT-style) and return top_l.
        If use_late is False, does dense-only search. If True, does dense prefetch + late rerank.
        If doc_search is True, also filter by fuzzy/substring/keyword in the document (case-insensitive) after reranking, and concatenate all fuzzy/substring/keyword matches in the collection.
        """
        import re
        from embedding import get_dense_embedding, get_late_embedding
        dense_vec = get_dense_embedding(query_text)
        late_vec = get_late_embedding(query_text)
        # Vector search
        if use_late:
            from qdrant_client.models import Prefetch
            results = self.client.query_points(
                collection_name=self.collection_name,
                prefetch=Prefetch(query=dense_vec, using="dense"),
                query=late_vec,
                using="late",
                limit=topk,
                with_payload=True
            )
        else:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=dense_vec,
                limit=topk,
                with_payload=True,
                with_vectors=False
            )

        # Normalize Qdrant results to always be a list of ScoredPoint-like objects
        points_list = None
        if isinstance(results, tuple) and len(results) == 2 and isinstance(results[1], list):
            points_list = results[1]
        elif isinstance(results, list):
            points_list = results
        elif hasattr(results, 'points') and isinstance(results.points, list):
            points_list = results.points
        else:
            points_list = []

        hits = []
        for hit in points_list:
            if hasattr(hit, 'id') and hasattr(hit, 'payload'):
                payload = hit.payload if isinstance(hit.payload, dict) else {}
                hits.append({"id": hit.id, "document": payload.get('document', '')})
            elif isinstance(hit, tuple) and len(hit) >= 2:
                _id = hit[0]
                _payload = hit[1] if isinstance(hit[1], dict) else {}
                hits.append({"id": _id, "document": _payload.get('document', '')})

        # After reranking, take top_l
        hits = hits[:top_l]

        # Optionally filter by fuzzy/substring/keyword match if doc_search is True
        if doc_search:
            query_words = set(re.findall(r"\w+", query_text.lower()))
            def fuzzy_match(doc):
                doc_text = doc.lower()
                # Exact substring
                if query_text.lower() in doc_text:
                    return True
                # Any query word present (partial/keyword match)
                for word in query_words:
                    if word and word in doc_text:
                        return True
                # Fuzzy: allow up to 1 char difference for each word (very basic)
                for word in query_words:
                    for token in re.findall(r"\w+", doc_text):
                        if word and token and abs(len(word) - len(token)) <= 1 and sum(a != b for a, b in zip(word, token)) <= 1:
                            return True
                return False

            filtered_hits = [hit for hit in hits if fuzzy_match(hit['document'])]
            # Now also get all docs in the collection that match the substring/keyword/fuzzy (outside top_l reranked)
            doc_hits = []
            next_offset = None
            while True:
                scroll_result = self.client.scroll(collection_name=self.collection_name, with_payload=True, offset=next_offset)
                points = scroll_result[0]
                next_offset = scroll_result[1]
                for point in points:
                    doc = point.payload.get('document', '') if hasattr(point, 'payload') else ''
                    if fuzzy_match(doc):
                        doc_hits.append({"id": point.id, "document": doc})
                if not next_offset:
                    break
            # Merge and deduplicate by id, prioritizing reranked hits
            seen_ids = set()
            merged = []
            for hit in filtered_hits:
                if hit['id'] not in seen_ids:
                    merged.append(hit)
                    seen_ids.add(hit['id'])
            for hit in doc_hits:
                if hit['id'] not in seen_ids:
                    merged.append(hit)
                    seen_ids.add(hit['id'])
            return [f"{hit['id']} | {hit['document']}" for hit in merged] if merged else []
        else:
            return [f"{hit['id']} | {hit['document']}" for hit in hits] if hits else []

    def close(self):
        self.stop_worker()

    def run_worker(self):
        if not self.fetch_latest_email:
            raise ValueError("fetch_latest_email callback not provided.")
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def stop_worker(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join()

    # Remove smart_query (use query method instead)


    def close(self):
        self.stop_worker()


if __name__ == "__main__":
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
