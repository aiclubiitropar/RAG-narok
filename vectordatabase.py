import requests
from bs4 import BeautifulSoup
from langchain_community.document_loaders import PyPDFLoader # type: ignore
from langchain_community.vectorstores import FAISS # type: ignore
from langchain_openai import OpenAIEmbeddings # type: ignore
from langchain_community.text_splitter import RecursiveCharacterTextSplitter # type: ignore
import tempfile
import os

class VectorDatabase:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = None

    def scrape_web(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        return text

    def scrape_pdf(self, pdf_url):
        response = requests.get(pdf_url)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(response.content)
            tmp_file_path = tmp_file.name
        loader = PyPDFLoader(tmp_file_path)
        docs = loader.load()
        os.remove(tmp_file_path)
        return " ".join([doc.page_content for doc in docs])

    def add_documents(self, texts, metadatas=None):
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = []
        for i, text in enumerate(texts):
            meta = metadatas[i] if metadatas else {}
            for chunk in splitter.split_text(text):
                docs.append({"page_content": chunk, "metadata": meta})
        # Prepare documents and metadatas for FAISS
        documents = [doc["page_content"] for doc in docs]
        metadatas_list = [doc["metadata"] for doc in docs]
        # Remove duplicates based on content and metadata
        unique = set()
        filtered_docs = []
        filtered_metas = []
        for doc, meta in zip(documents, metadatas_list):
            key = (doc, tuple(sorted(meta.items())) if isinstance(meta, dict) else str(meta))
            if key not in unique:
                unique.add(key)
                filtered_docs.append(doc)
                filtered_metas.append(meta)
        if self.vectorstore is None:
            self.vectorstore = FAISS.from_texts(filtered_docs, self.embeddings, metadatas=filtered_metas)
        else:
            # Check for duplicates in the existing vectorstore
            # FAISS does not natively support duplicate checking, so we do a simple check here
            # For a more robust solution, consider using a persistent DB for metadata
            existing = set()
            for doc in self.vectorstore.docstore._dict.values():
                key = (doc.page_content, tuple(sorted(doc.metadata.items())) if isinstance(doc.metadata, dict) else str(doc.metadata))
                existing.add(key)
            new_docs = []
            new_metas = []
            for doc, meta in zip(filtered_docs, filtered_metas):
                key = (doc, tuple(sorted(meta.items())) if isinstance(meta, dict) else str(meta))
                if key not in existing:
                    new_docs.append(doc)
                    new_metas.append(meta)
            if new_docs:
                self.vectorstore.add_texts(new_docs, metadatas=new_metas)

    def retrieve(self, query, k=5, rerank_with_llm=False, rerank_top_n=10):
        if not self.vectorstore:
            raise ValueError("Vector store is empty. Add documents first.")
        # Step 1: Retrieve top-N candidates using FAISS
        candidates = self.vectorstore.similarity_search(query, k=rerank_top_n if rerank_with_llm else k)
        if not rerank_with_llm:
            return candidates[:k]
        # Step 2: Rerank using LLM (OpenAI)
        from langchain_openai import ChatOpenAI # type: ignore
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        scored = []
        for doc in candidates:
            prompt = f"Query: {query}\nDocument: {doc.page_content}\nScore the relevance of the document to the query from 1 (not relevant) to 10 (very relevant). Only return the score as a number."
            try:
                score = int(llm.invoke(prompt).content.strip())
            except Exception:
                score = 1  # fallback if LLM fails
            scored.append((score, doc))
        scored.sort(reverse=True, key=lambda x: x[0])
        return [doc for score, doc in scored[:k]]