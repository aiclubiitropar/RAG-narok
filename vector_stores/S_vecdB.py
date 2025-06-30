import os
import sys
import time
import threading
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Callable, Dict, Optional, List
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from vector_stores.L_vecdB import LongTermDatabase
from vector_stores.embedding import get_embedding, to_valid_qdrant_id

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.email_scraper import EmailScraper
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ShortTermDatabase:
    def __init__(
        self,
        short_term_prefix: str = "shortterm_db",
        long_term_prefix: str = "longterm_db",
        model: Callable[[List[str]], List[List[float]]] = None,
        vector_size: int = 384,
        time_threshold: float = 1.0,
        count_threshold: int = 100,
        fetch_latest_email: Optional[Callable[[], Dict]] = None,
        poll_interval: float = 60,
        qdrant_url: str = "https://df35413f-27c8-419d-aa89-4b3901514560.us-west-1-0.aws.cloud.qdrant.io",
        qdrant_api_key: Optional[str] = None
    ):
        self.short_term_prefix = short_term_prefix
        self.long_term_prefix = long_term_prefix
        self.vector_size = vector_size

        self.client = QdrantClient(url=qdrant_url, api_key=os.getenv('QDRANT_API_KEY', qdrant_api_key))
        self.short_data_collection = f"{short_term_prefix}_main_data"
        self.short_meta_collection = f"{short_term_prefix}_meta_data"

        for collection_name in [self.short_data_collection, self.short_meta_collection]:
            if not self.client.collection_exists(collection_name):
                self.client.recreate_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )

        def embedding_batch(texts):
            results = []
            for text in texts:
                result = get_embedding(text)
                results.append(result)
                time.sleep(2)  # Wait 2 seconds between API calls
            return results

        self.model = model or embedding_batch
        self.time_threshold = timedelta(days=time_threshold)
        self.count_threshold = count_threshold
        self.fetch_latest_email = fetch_latest_email
        self.poll_interval = poll_interval

        self._last_flush_time = datetime.utcnow()
        self._last_email_id: Optional[str] = None
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def vectorize_and_add(self, email: Dict):
        eid = email['id']
        raw = email['body']
        metadata = email.get('metadata', {})

        data_vec = self.model([raw])[0]
        meta_vec = self.model([json.dumps(metadata)])[0]

        self.client.upsert(
            collection_name=self.short_data_collection,
            points=[PointStruct(id=to_valid_qdrant_id(eid), vector=data_vec, payload={"document": raw, "metadata": metadata})]
        )
        self.client.upsert(
            collection_name=self.short_meta_collection,
            points=[PointStruct(id=to_valid_qdrant_id(eid), vector=meta_vec, payload={"document": json.dumps(metadata), "metadata": metadata})]
        )

    add_email = vectorize_and_add

    def _maybe_flush(self):
        now = datetime.utcnow()
        count = self.client.count(collection_name=self.short_data_collection).count
        if (now - self._last_flush_time) > self.time_threshold or count >= self.count_threshold:
            self.flush_to_long_term()

    def flush_to_long_term(self):
        # Print the size of the short-term database before flushing
        count = self.client.count(collection_name=self.short_data_collection).count
        print(f"[FLUSH] Short-term DB size before flush: {count} emails")
        long_db = LongTermDatabase(collection_prefix=self.long_term_prefix)

        def retrieve_all(collection_name):
            scroll = self.client.scroll(collection_name=collection_name, with_vectors=True, with_payload=True)
            ids, vectors, documents, metadatas = [], [], [], []
            for point in scroll[0]:
                ids.append(to_valid_qdrant_id(point.id))
                vectors.append(point.vector)
                documents.append(point.payload.get("document", ""))
                metadatas.append(point.payload.get("metadata", {}))
            print(f"[FLUSH] Fetched {len(ids)} items from '{collection_name}' for flushing.")
            return ids, vectors, documents, metadatas

        ids_d, vecs_d, docs_d, metas_d = retrieve_all(self.short_data_collection)
        ids_m, vecs_m, docs_m, metas_m = retrieve_all(self.short_meta_collection)

        long_db._upsert_collection(long_db.main_data_collection, ids_d, vecs_d, docs_d, metas_d)
        long_db._upsert_collection(long_db.meta_data_collection, ids_m, vecs_m, docs_m, metas_m)
        long_db.save()

        self.client.delete(collection_name=self.short_data_collection, points=ids_d)
        self.client.delete(collection_name=self.short_meta_collection, points=ids_m)
        self._last_flush_time = datetime.utcnow()
        # Print the size of the short-term database after flushing
        count_after = self.client.count(collection_name=self.short_data_collection).count
        print(f"[FLUSH] Short-term DB size after flush: {count_after} emails")

    def _worker_loop(self):
        blocklist = [
            "no-reply@accounts.google.com", "Security alert", "unstop", "linkedin", "kaggle", "Team Unstop",
            "Canva", "noreply@github.com", "noreply", "feed"
        ]
        while not self._stop_event.is_set():
            if self.fetch_latest_email:
                email = self.fetch_latest_email()
                if email is None:
                    logging.info("No new email found. Skipping this iteration.")
                    self._maybe_flush()
                    time.sleep(self.poll_interval)
                    continue

                subject = email.get('subject', '')
                from_ = email.get('from', '')
                if any(k in subject for k in blocklist) or any(k in from_ for k in blocklist):
                    logging.info(f"Blocked email from: {from_}, subject: {subject}")
                elif email['id'] != self._last_email_id:
                    self._last_email_id = email['id']
                    self.vectorize_and_add(email)

            self._maybe_flush()
            count = self.client.count(collection_name=self.short_data_collection).count
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

    def smart_query(self, query_text: str, topk_data: int = 20) -> List[str]:
        q_emb = self.model([query_text])[0]
        main_search = self.client.search(
            collection_name=self.short_data_collection,
            query_vector=q_emb,
            limit=topk_data,
            with_payload=True,
            with_vectors=True
        )
        if not main_search:
            return []
        results = []
        for hit in main_search:
            doc = hit.payload.get("document", "")
            meta = hit.payload.get("metadata", {})
            meta_text = json.dumps(meta, ensure_ascii=False)
            results.append(f"{hit.id} | {doc} | {meta_text}")
        return results

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
