import os
import json
import numpy as np
import time
from typing import List
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    SparseVectorParams,
    Modifier,
    MultiVectorConfig,
    MultiVectorComparator,
    HnswConfigDiff
)

# Fix import for both direct and module execution
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from embedding import (
    get_dense_embedding,
    get_sparse_embedding,
    get_late_embedding,
    to_valid_qdrant_id
)

load_dotenv()

class LongTermDatabase:
    def __init__(
        self,
        collection_prefix: str = "longterm_db",
        vector_size: int = 384,
        url: str = "https://df35413f-27c8-419d-aa89-4b3901514560.us-west-1-0.aws.cloud.qdrant.io",
        api_key: str = os.getenv('QDRANT_API_KEY')
    ):
        self.api_key = api_key or os.getenv('QDRANT_API_KEY')
        if not self.api_key:
            raise RuntimeError("Missing QDRANT_API_KEY environment variable.")

        self.client = QdrantClient(url=url, api_key=self.api_key)
        self.collection_name = "long_rag"
        self.vector_size = vector_size
        # Only dense vectors are used
        self._ensure_collection()

    def _ensure_collection(self):
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

    def _batch_get_embeddings(self, docs: List[str]):
        dense_embs = [get_dense_embedding(doc) for doc in docs]
        late_embs = [get_late_embedding(doc) for doc in docs]
        return list(zip(dense_embs, late_embs))

    def add_data(self, json_file: str, max_chunk_chars: int = 1500):
        """
        Add each object in a JSON file as its own document. If the file is a list, each item is a document.
        If the file is a dict, each value is a document. If a document is too large, it is split into chunks.
        For objectwise JSON (list of dicts), each dict is a document.
        """
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        ids, docs = [], []
        # Objectwise: if data is a list of dicts, treat each dict as a document
        file_prefix = os.path.splitext(os.path.basename(json_file))[0]
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            for i, item in enumerate(data):
                doc_json = json.dumps(item, ensure_ascii=False)
                if len(doc_json) > max_chunk_chars:
                    n_chunks = (len(doc_json) + max_chunk_chars - 1) // max_chunk_chars
                    for j in range(n_chunks):
                        chunk = doc_json[j * max_chunk_chars : (j + 1) * max_chunk_chars]
                        ids.append(f"{file_prefix}_{i}_{j}")
                        docs.append(chunk)
                else:
                    ids.append(f"{file_prefix}_{i}")
                    docs.append(doc_json)
        elif isinstance(data, dict):
            # If dict, treat each value as a document
            for k, v in data.items():
                doc_json = json.dumps(v, ensure_ascii=False)
                if len(doc_json) > max_chunk_chars:
                    n_chunks = (len(doc_json) + max_chunk_chars - 1) // max_chunk_chars
                    for j in range(n_chunks):
                        chunk = doc_json[j * max_chunk_chars : (j + 1) * max_chunk_chars]
                        ids.append(f"{file_prefix}_{k}_{j}")
                        docs.append(chunk)
                else:
                    ids.append(f"{file_prefix}_{k}")
                    docs.append(doc_json)
        else:
            # Fallback: treat the whole thing as one document
            doc_json = json.dumps(data, ensure_ascii=False)
            if len(doc_json) > max_chunk_chars:
                n_chunks = (len(doc_json) + max_chunk_chars - 1) // max_chunk_chars
                for j in range(n_chunks):
                    chunk = doc_json[j * max_chunk_chars : (j + 1) * max_chunk_chars]
                    ids.append(f"{file_prefix}_0_{j}")
                    docs.append(chunk)
            else:
                ids.append(f"{file_prefix}_0")
                docs.append(doc_json)
        print(f"Adding {len(docs)} document(s) to the database...")
        emb_pairs = self._batch_get_embeddings(docs)
        points = []
        for i, doc_id in enumerate(ids):
            dense_vec, late_vec = emb_pairs[i]
            points.append(
                PointStruct(
                    id=to_valid_qdrant_id(doc_id),
                    vector={"dense": dense_vec, "late": late_vec},
                    payload={"document": docs[i]}
                )
            )
        # Use upsert in small batches to avoid timeouts
        BATCH_SIZE = 4  # or even 2 if needed
        for i in range(0, len(points), BATCH_SIZE):
            batch = points[i:i+BATCH_SIZE]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
            time.sleep(1)  # short pause between batches
        print(f"Indexed {len(points)} document(s).")

    def smart_query(self, query_text: str, topk: int = 20, top_l: int = 5, use_late: bool = True, doc_search: bool = True) -> List[str]:
        """
        Hybrid query: first prefetch with dense (topk), then rerank with late embedding (ColBERT-style) and return top_l.
        If use_late is False, does dense-only search. If True, does dense prefetch + late rerank.
        If doc_search is True, also filter by substring in the document (case-insensitive) after reranking.
        """
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
            # Qdrant >=1.7 returns ScoredPoint objects
            if hasattr(hit, 'id') and hasattr(hit, 'payload'):
                payload = hit.payload if isinstance(hit.payload, dict) else {}
                hits.append({"id": hit.id, "document": payload.get('document', '')})
            # Defensive: handle tuple (id, payload) fallback
            elif isinstance(hit, tuple) and len(hit) >= 2:
                _id = hit[0]
                _payload = hit[1] if isinstance(hit[1], dict) else {}
                hits.append({"id": _id, "document": _payload.get('document', '')})

        # After reranking, take top_l
        hits = hits[:top_l]

        # Optionally filter by substring match if doc_search is True
        if doc_search:
            filtered_hits = [hit for hit in hits if query_text.lower() in hit['document'].lower()]
            # Now also get all docs in the collection that match the substring (outside top_l reranked)
            # Scroll through all points (handle pagination)
            doc_hits = []
            next_offset = None
            while True:
                scroll_result = self.client.scroll(collection_name=self.collection_name, with_payload=True, offset=next_offset)
                points = scroll_result[0]
                next_offset = scroll_result[1]
                for point in points:
                    doc = point.payload.get('document', '') if hasattr(point, 'payload') else ''
                    if query_text.lower() in doc.lower():
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
            return [f"{hit['document']}" for hit in merged] if merged else []
        else:
            return [f"{hit['document']}" for hit in hits] if hits else []

    def save(self):
        pass  # Qdrant persists automatically

    @classmethod
    def load_database(cls, collection_prefix: str = "longterm_db", **kwargs):
        return cls(collection_prefix=collection_prefix, **kwargs)


if __name__ == "__main__":
    db = LongTermDatabase()

    paths = [
        r"C:\Users\dedeep vasireddy\Downloads\file3_literary_board_objectwise.json",
        r"C:\Users\dedeep vasireddy\Downloads\file2_cultural_board_objectwise.json",
        r"C:\Users\dedeep vasireddy\Downloads\file5_overall_coordinators_objectwise.json",
        r"C:\Users\dedeep vasireddy\Downloads\file4_scitech_board_objectwise.json",
        r"C:\Users\dedeep vasireddy\Downloads\file1_metadata_student_council_objectwise_full.json"
    ]
    # for path in paths:
    #     db.add_data(path)
    # db.add_data(paths[0])  # For testing, just add the first file
    print("Total points in DB:", db.client.count(collection_name=db.collection_name).count)
    query = input("Query: ")
    res = db.smart_query(query, topk=10, top_l=5, use_late=True)
    print("Final Results:", res)
