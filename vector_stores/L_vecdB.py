import os
import json
import numpy as np
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from embedding import get_embedding, to_valid_qdrant_id


class LongTermDatabase:
    def __init__(
        self,
        collection_prefix="longterm_db",
        vector_size=384,
        use_fp16=True,
        url="https://df35413f-27c8-419d-aa89-4b3901514560.us-west-1-0.aws.cloud.qdrant.io",
        api_key=None
    ):
        """
        Initialize Qdrant-based vector database with two collections:
        'main_data' and 'meta_data'.
        """
        self.collection_prefix = collection_prefix
        self.vector_size = vector_size
        self.client = QdrantClient(url=url, api_key=os.getenv('QDRANT_API_KEY', api_key))

        self.main_data_collection = f"{collection_prefix}_main_data"
        self.meta_data_collection = f"{collection_prefix}_meta_data"

        self._ensure_collections()

    def _ensure_collections(self):
        for collection_name in [self.main_data_collection, self.meta_data_collection]:
            if not self.client.collection_exists(collection_name):
                self.client.recreate_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )

    def _batch_get_embeddings(self, texts: List[str]):
        return np.array([get_embedding(text) for text in texts])

    def add_data(self, json_file: str):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        ids, full_texts, meta_texts, raw_meta = [], [], [], []
        if isinstance(data, dict):
            items = data.items()
        elif isinstance(data, list):
            items = [(str(idx), item) for idx, item in enumerate(data)]
        else:
            raise ValueError("Unsupported JSON structure: must be dict or list")

        for item_id, item in items:
            meta = item.get('metadata', {})
            ids.append(item_id)
            full_texts.append(json.dumps(item, ensure_ascii=False))
            meta_texts.append(json.dumps(meta, ensure_ascii=False))
            raw_meta.append(meta)

        data_embeddings = self._batch_get_embeddings(full_texts)
        meta_embeddings = self._batch_get_embeddings(meta_texts)

        self._upsert_collection(self.main_data_collection, ids, data_embeddings, full_texts, raw_meta)
        self._upsert_collection(self.meta_data_collection, ids, meta_embeddings, meta_texts, raw_meta)

        print(f"Added {len(ids)} items to the long-term database from {json_file}.")
        print(f"Data embeddings shape: {data_embeddings.shape}")
        print(f"Metadata embeddings shape: {meta_embeddings.shape}")

    def _upsert_collection(self, collection_name, ids, embeddings, documents, metadatas):
        points = [
            PointStruct(
                id=to_valid_qdrant_id(ids[i]),
                vector=embeddings[i].tolist(),
                payload={
                    "document": documents[i],
                    "metadata": metadatas[i]
                }
            ) for i in range(len(ids))
        ]
        self.client.upsert(collection_name=collection_name, points=points)

    def receive_data(self, ids, data_embeddings, meta_embeddings):
        empty_docs = [''] * len(ids)
        empty_meta = [{} for _ in ids]
        self._upsert_collection(self.main_data_collection, ids, data_embeddings, empty_docs, empty_meta)
        self._upsert_collection(self.meta_data_collection, ids, meta_embeddings, empty_docs, empty_meta)

    def smart_query(self, query_text: str, topk_meta: int = 10, topk_data: int = 5):
        q_emb = self._batch_get_embeddings([query_text])[0]
        meta_search = self.client.search(
            collection_name=self.meta_data_collection,
            query_vector=q_emb.tolist(),
            limit=topk_meta
        )

        candidate_ids = [hit.id for hit in meta_search]

        if not candidate_ids:
            return []

        main_data = self.client.retrieve(
            collection_name=self.main_data_collection,
            ids=candidate_ids,
            with_payload=True,
            with_vectors=True
        )

        embs = np.array([item.vector for item in main_data])
        docs = [item.payload.get("document", "") for item in main_data]
        metas = [item.payload.get("metadata", {}) for item in main_data]

        q_norm = np.linalg.norm(q_emb)
        d_norms = np.linalg.norm(embs, axis=1)
        sims = np.dot(embs, q_emb) / (d_norms * q_norm + 1e-8)
        idx_sorted = np.argsort(-sims)[:topk_data]

        results = []
        for idx in idx_sorted:
            full_item = docs[idx]
            meta_text = json.dumps(metas[idx], ensure_ascii=False)
            results.append(f"{candidate_ids[idx]} | {full_item} | {meta_text}")
        return results

    def save(self):
        # Qdrant handles persistence automatically
        pass

    @classmethod
    def load_database(cls, collection_prefix="longterm_db", **kwargs):
        return cls(collection_prefix=collection_prefix, **kwargs)


if __name__ == "__main__":
    db = LongTermDatabase(collection_prefix="longterm_db")
    json_file = r"C:\Users\dedeep vasireddy\.vscode\RAG-narok\tools\latest_emails.json"
    print(f"Adding data from {json_file} to the long-term database...")
    db.add_data(json_file)
    print("Data added and persisted.")
    db = LongTermDatabase.load_database(collection_prefix="longterm_db")
    print("Long-term database loaded successfully.")
    query = input("Enter your query: ")
    print(f"\nSmart query results for: '{query}'\n")
    results = db.smart_query(query_text=query, topk_meta=5, topk_data=3)
    for res in results:
        print(res)
