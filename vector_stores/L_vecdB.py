from chromadb import PersistentClient
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import json
import os
import numpy as np

class LongTermDatabase:
    def __init__(
        self,
        persist_directory="longterm_db",
        model_name='paraphrase-multilingual-MiniLM-L12-v2',
        use_fp16=True
    ):
        """
        Initialize long-term databases for both full-data and metadata embeddings.
        Creates two ChromaDB collections: 'main_data' and 'meta_data'.
        """
        self.persist_directory = persist_directory
        os.makedirs(self.persist_directory, exist_ok=True)

        # Use PersistentClient with Settings for on-disk persistence
        settings = Settings(
            persist_directory=self.persist_directory,
            anonymized_telemetry=False
        )
        self.client = PersistentClient(settings=settings)

        self.main_data = self.client.get_or_create_collection(name="main_data")
        self.meta_data = self.client.get_or_create_collection(name="meta_data")

        # Load embedding model
        self.embedding_model = SentenceTransformer(model_name)

    def add_data(self, json_file: str):
        """
        Load JSON file, serialize items and their metadata, vectorize,
        and store in both 'main_data' and 'meta_data' collections.
        :param json_file: Path to JSON file; each object must contain a 'metadata' key.
        """
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        ids, full_texts, meta_texts, raw_meta = [], [], [], []
        for item_id, item in data.items():
            meta = item.get('metadata', {})
            ids.append(item_id)
            full_texts.append(json.dumps(item, ensure_ascii=False))
            meta_texts.append(json.dumps(meta, ensure_ascii=False))
            raw_meta.append(meta)

        data_embeddings = self.embedding_model.encode(full_texts)
        meta_embeddings = self.embedding_model.encode(meta_texts)

        self.main_data.add(
            ids=ids,
            embeddings=data_embeddings,
            metadatas=[{'metadata': json.dumps(m, ensure_ascii=False)} for m in raw_meta],
            documents=full_texts
        )
        self.meta_data.add(
            ids=ids,
            embeddings=meta_embeddings,
            metadatas=[{'metadata': json.dumps(m, ensure_ascii=False)} for m in raw_meta],
            documents=meta_texts
        )
        self.save()
        print(f"Added {len(ids)} items to the long-term database from {json_file}.")
        print(f"Data embeddings shape: {data_embeddings.shape}")
        print(f"Metadata embeddings shape: {meta_embeddings.shape}")

    def receive_data(self, ids, data_embeddings, meta_embeddings):
        """
        Directly ingest precomputed embeddings into both collections.
        :param ids: List of item identifiers.
        :param data_embeddings: List of embeddings for the data channel.
        :param meta_embeddings: List of embeddings for the metadata channel.
        """
        self.main_data.add(
            ids=ids,
            embeddings=data_embeddings,
            metadatas=[{} for _ in ids],
            documents=[''] * len(ids)
        )
        self.meta_data.add(
            ids=ids,
            embeddings=meta_embeddings,
            metadatas=[{} for _ in ids],
            documents=[''] * len(ids)
        )
        self.save()

    def smart_query(self, query_text: str, topk_meta: int = 10, topk_data: int = 5):
        """
        Two-stage retrieval:
        1. Top-k_meta by metadata similarity from 'meta_data'.
        2. From those, topk_data by data similarity from 'main_data'.
        Returns concatenated strings: "<id> | <full-item> | <metadata>".
        """
        q_emb = self.embedding_model.encode([query_text])[0]
        meta_res = self.meta_data.query(
            query_embeddings=[q_emb],
            n_results=topk_meta
        )

        if not meta_res['ids'] or not meta_res['ids'][0]:
            return []

        candidate_ids = meta_res['ids'][0]

        full_res = self.main_data.get(
            ids=candidate_ids,
            include=["documents", "embeddings", "metadatas"]
        )
        docs = full_res['documents']
        embs = full_res['embeddings']
        metas = [m.get('metadata') for m in full_res['metadatas']]

        q_norm = np.linalg.norm(q_emb)
        d_norms = np.linalg.norm(embs, axis=1)
        sims = np.dot(embs, q_emb) / (d_norms * q_norm + 1e-8)
        idx_sorted = np.argsort(-sims)[:topk_data]

        results = []
        for idx in idx_sorted:
            full_text = docs[idx]
            try:
                full_item = json.dumps(json.loads(full_text), ensure_ascii=False)
            except:
                full_item = full_text
            meta_text = json.dumps(metas[idx], ensure_ascii=False)
            results.append(f"{candidate_ids[idx]} | {full_item} | {meta_text}")
        return results

    def save(self):
        """
        Save the current state of the database to disk.
        """
        pass  # Removed self.client.persist() as it is not a valid method

    @classmethod
    def load_database(cls, persist_directory="longterm_db"):
        """
        Load an existing database from disk.
        """
        return cls(persist_directory=persist_directory)

if __name__ == "__main__":
    db = LongTermDatabase(persist_directory="longterm_db")
    json_file = r"C:\Users\dedeep vasireddy\.vscode\RAG-narok\tools\latest_emails.json"
    print(f"Adding data from {json_file} to the long-term database...")
    db.add_data(json_file)
    print("Data added and persisted.")
    db = LongTermDatabase.load_database(persist_directory="longterm_db")
    print("Long-term database loaded successfully.")
    query = input("Enter your query: ")
    print(f"\nSmart query results for: '{query}'\n")
    results = db.smart_query(query_text=query, topk_meta=5, topk_data=3)
    for res in results:
        print(res)
