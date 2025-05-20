import requests
from bs4 import BeautifulSoup
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS 
from langchain_google_genai import ChatGoogleGenerativeAI  
from langchain.text_splitter import RecursiveCharacterTextSplitter  
from langchain_community.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
import tempfile
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class VectorDatabase:
    def __init__(self):
        self.embeddings = SentenceTransformer('all-MiniLM-L6-v2')
        self.vectorstore = None
        # Set Gemini API key from environment variable
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

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
        documents = [doc["page_content"] for doc in docs]
        metadatas_list = [doc["metadata"] for doc in docs]
        unique = set()
        filtered_docs = []
        filtered_metas = []
        for doc, meta in zip(documents, metadatas_list):
            key = (doc, tuple(sorted(meta.items())) if isinstance(meta, dict) else str(meta))
            if key not in unique:
                unique.add(key)
                filtered_docs.append(doc)
                filtered_metas.append(meta)
        hf_embed = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
        if self.vectorstore is None:
            self.vectorstore = FAISS.from_texts(filtered_docs, hf_embed, metadatas=filtered_metas)
        else:
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

    def update_database(self, website_urls=None, pdf_urls=None):
        """
        Scrape new website and PDF URLs, add their content and metadata to the vectorstore,
        and avoids duplicating content already present in the database.
        Args:
            website_urls (list): List of website URLs to scrape.
            pdf_urls (list): List of PDF URLs to scrape.
        """
        website_urls = website_urls or []
        pdf_urls = pdf_urls or []
        new_texts = []
        new_metas = []
        # Collect all existing sources from metadata to avoid re-scraping
        existing_sources = set()
        if self.vectorstore is not None:
            for doc in self.vectorstore.docstore._dict.values():
                src = doc.metadata.get("source") if isinstance(doc.metadata, dict) else None
                if src:
                    existing_sources.add(src)
        # Scrape websites
        for url in website_urls:
            if url not in existing_sources:
                try:
                    text = self.scrape_web(url)
                    if text.strip():
                        new_texts.append(text)
                        new_metas.append({"source": url, "type": "web"})
                except Exception as e:
                    print(f"Failed to scrape {url}: {e}")
        # Scrape PDFs
        for pdf_url in pdf_urls:
            if pdf_url not in existing_sources:
                try:
                    text = self.scrape_pdf(pdf_url)
                    if text.strip():
                        new_texts.append(text)
                        new_metas.append({"source": pdf_url, "type": "pdf"})
                except Exception as e:
                    print(f"Failed to scrape {pdf_url}: {e}")
        # Add new documents if any
        if new_texts:
            self.add_documents(new_texts, metadatas=new_metas)
        else:
            print("No new URLs to add to the database.")

    def retrieve(self, query, k=5, rerank_with_llm=False, rerank_top_n=10):
        if not self.vectorstore:
            raise ValueError("Vector store is empty. Add documents first.")
        # Step 1: Retrieve top-N candidates using FAISS
        candidates = self.vectorstore.similarity_search(query, k=rerank_top_n if rerank_with_llm else k)
        if not rerank_with_llm:
            return candidates[:k]
        # Step 2: Rerank using Gemini 2.0 Flash (fix system_instruction argument)
        system_instruction = (
            "You are a helpful assistant for reranking search results. "
            "Given a user query and a document, score the relevance of the document to the query "
            "from 1 (not relevant) to 10 (very relevant). Only return the score as a number."
        )
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, model_kwargs={"system_instruction": system_instruction})
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

if __name__ == "__main__":
    # Example inference code for RAGnarok VectorDatabase

    # Initialize the vector database
    db = VectorDatabase()

    # Example: Update database with web and PDF URLs
    web_urls = ["https://www.iitrpr.ac.in/"]
    pdf_urls = ["https://arxiv.org/pdf/1706.03762.pdf"]
    print("Updating database with new URLs...")
    db.update_database(website_urls=web_urls, pdf_urls=pdf_urls)

    # Example query
    query = "What are the research areas at IIT Ropar?"

    print("\nRetrieving with FAISS similarity only:")
    results = db.retrieve(query, k=3)
    for i, doc in enumerate(results, 1):
        print(f"\nResult {i}:\n{doc.page_content[:500]}...")  # Print first 500 chars
        print(f"Metadata: {doc.metadata}")

    print("\nRetrieving with reranking using Gemini 2.0 Flash:")
    results_rerank = db.retrieve(query, k=3, rerank_with_llm=True, rerank_top_n=8)
    for i, doc in enumerate(results_rerank, 1):
        print(f"\nReranked Result {i}:\n{doc.page_content[:500]}...")  # Print first 500 chars
        print(f"Metadata: {doc.metadata}")