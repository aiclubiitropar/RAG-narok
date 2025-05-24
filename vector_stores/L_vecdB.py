import chromadb
from chromadb.config import Settings
from FlagEmbedding import BGEM3FlagModel
import json
import os
import numpy as np

class LongTermDatabase:
    def __init__(self, persist_directory=".longterm_db", model_name='BAAI/bge-m3', use_fp16=True):
        """
        Initialize long-term databases for both full-data and metadata embeddings.
        Creates two ChromaDB collections: 'main_data' and 'meta_data'.
        """
        self.persist_directory = persist_directory
        os.makedirs(self.persist_directory, exist_ok=True)
        settings = Settings(
            persist_directory=self.persist_directory,
            chroma_db_impl="duckdb+parquet"
        )
        self.client = chromadb.Client(settings)
        # Collections for main and metadata channels
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
        # Ingest
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

    def receive_data(self, ids, data_embeddings, meta_embeddings, documents=None, metadatas=None):
        """
        Directly ingest precomputed embeddings into both collections.
        :param ids: List of item identifiers.
        :param data_embeddings: List of embeddings for the full-data channel.
        :param meta_embeddings: List of embeddings for the metadata channel.
        :param documents: (Optional) List of serialized full items (strings). If None, stored docs remain empty.
        :param metadatas: (Optional) List of metadata dicts. If None, stored metadatas use empty dicts.
        """
        # Prepare defaults
        if documents is None:
            documents = [''] * len(ids)
        if metadatas is None:
            metadatas = [{} for _ in ids]

        # Add to main_data
        self.main_data.add(
            ids=ids,
            embeddings=data_embeddings,
            metadatas=[{'metadata': m} for m in metadatas],
            documents=documents
        )
        # Add to meta_data
        self.meta_data.add(
            ids=ids,
            embeddings=meta_embeddings,
            metadatas=[{'metadata': m} for m in metadatas],
            documents=[json.dumps(m, ensure_ascii=False) for m in metadatas]
        )
        self.save()

    def smart_query(self, query_text: str, topk_meta: int = 10, topk_data: int = 5):
        """
        Two-stage retrieval:
        1. Top-k_meta by metadata similarity from 'meta_data'.
        2. From those, topk_data by data similarity from 'main_data'.
        Returns concatenated strings: "<id> | <full-item> | <metadata>".
        """
        # Stage 1: metadata
        q_emb = self.embedding_model.encode([query_text])[0]
        meta_res = self.meta_data.query(
            query_embeddings=[q_emb],
            n_results=topk_meta
        )
        candidate_ids = meta_res['ids'][0]

        # Stage 2: data
        full_res = self.main_data.get(
            ids=candidate_ids,
            include=["documents", "embeddings", "metadatas"]
        )
        docs = full_res['documents']
        embs = full_res['embeddings']
        metas = [m.get('metadata') for m in full_res['metadatas']]

        # Cosine similarity
        q_norm = np.linalg.norm(q_emb)
        d_norms = np.linalg.norm(embs, axis=1)
        sims = np.dot(embs, q_emb) / (d_norms * q_norm + 1e-8)
        idx_sorted = np.argsort(-sims)[:topk_data]

        results = []
        for idx in idx_sorted:
            # Format text
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
