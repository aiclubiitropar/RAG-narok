import chromadb
from chromadb.config import Settings
from FlagEmbedding import BGEM3FlagModel 
import json
import os
import numpy as np

class LongTermDatabase:
    def __init__(self, persist_directory="longterm_db", model_name='BAAI/bge-m3', use_fp16=True):
        """
        Initialize long-term databases for both full-data and metadata embeddings.
        Creates two ChromaDB collections: 'main_data' and 'meta_data'.
        """
        self.persist_directory = persist_directory
        os.makedirs(self.persist_directory, exist_ok=True)
        # Removed the deprecated chroma_db_impl setting
        settings = Settings(
            persist_directory=self.persist_directory,
            # chroma_db_impl="duckdb+parquet" # This is deprecated
        )
        self.client = chromadb.Client(settings)
        self.main_data = self.client.get_or_create_collection(name="main_data")
        self.meta_data = self.client.get_or_create_collection(name="meta_data")
        self.embedding_model = BGEM3FlagModel(model_name, use_fp16=use_fp16)

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
            metadatas=[{'metadata': m} for m in raw_meta],
            documents=full_texts
        )
        self.meta_data.add(
            ids=ids,
            embeddings=meta_embeddings,
            metadatas=[{'metadata': m} for m in raw_meta],
            documents=meta_texts
        )
        self.save()

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
        Persist both collections.
        """
        self.client.persist()
        
    @classmethod
    def load_database(cls, persist_directory, model_name='BAAI/bge-m3', use_fp16=True):
        """
        Load an existing ChromaDB database from disk.
        :param persist_directory: directory where ChromaDB data is stored
        :param model_name: embedding model to use for queries
        :param use_fp16: whether to run embeddings in FP16
        :return: LongTermDatabase instance connected to existing data
        """
        return cls(persist_directory=persist_directory, model_name=model_name, use_fp16=use_fp16)

if __name__ == "__main__":
    # Example usage for adding data
    db = LongTermDatabase(persist_directory="longterm_db")
    json_file = "C:\\Users\\dedeep vasireddy\\.vscode\\RAG-narok\\tools\\latest_emails.json"  # Path to your JSON file
    print(f"Adding data from {json_file} to the long-term database...")
    db.add_data(json_file)
    print("Data added and persisted.")

    # Example usage for smart query
    query = "overall coordinator"
    print(f"\nSmart query results for: '{query}'\n")
    results = db.smart_query(query_text=query, topk_meta=5, topk_data=3)
    for res in results:
        print(res)

