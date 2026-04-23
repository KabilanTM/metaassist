"""
rag_pipeline.py
================
Core RAG pipeline for MetaAssist.
Handles document ingestion, embedding, vector storage, and answer generation.

Author      : Kabilan TM
Internship  : Metaplore Solutions Pvt. Ltd.
"""

import os
from typing import List, Dict, Tuple, Any
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
load_dotenv()


SYSTEM_PROMPT = """You are MetaAssist, an intelligent enterprise document assistant \
built during an internship at Metaplore Solutions Pvt. Ltd.

Your job is to answer questions ONLY using the context extracted from the uploaded documents.

Rules:
- Answer clearly and professionally.
- If the answer exists in the context, provide it confidently.
- If the answer is NOT in the context, say exactly:
  "This information is not available in the uploaded documents."
- Never make up facts. Never go beyond the provided context.
- When possible, mention which document or section the answer came from.

Context from documents:
{context}

Conversation so far:
{chat_history}

User's Question: {question}

Your Answer:"""


class RAGPipeline:
    """
    End-to-end Retrieval-Augmented Generation pipeline.

    Flow:
        PDF files
          → load pages (PyPDFLoader)
          → split into chunks (RecursiveCharacterTextSplitter)
          → embed chunks (GoogleGenerativeAIEmbeddings)
          → index in FAISS vector store
          → on query: embed question → similarity search → top-K chunks
          → pass chunks + history + question to Gemini LLM
          → return grounded answer + source documents
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        top_k: int = 4,
        model_name: str = "llama-3.3-70b-versatile",
    ):
        self.chunk_size    = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k         = top_k
        self.total_chunks  = 0
        self.vector_store  = None
        self.retriever     = None

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found. "
                "Please add it to your .env file."
            )

        # Embedding model — converts text to 768-dim vectors
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=api_key
        )

        # Generation model — produces answers
        # Generation model — Groq (free tier, works globally)
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise ValueError(
                "GROQ_API_KEY not found. "
                "Please add it to your .env file."
            )
        self.llm = ChatGroq(
            model=model_name,
            temperature=0.3,
            groq_api_key=groq_key
        )

        # Prompt template
        self.prompt = PromptTemplate(
            input_variables=["context", "chat_history", "question"],
            template=SYSTEM_PROMPT
        )

    # ──────────────────────────────────────────
    # STAGE 1 & 2 : Load PDFs → Split into chunks
    # ──────────────────────────────────────────
    def _load_and_split(self, pdf_paths: List[str]):
        """
        Load all PDFs page by page, then split into overlapping chunks.

        Why overlap?
            A 64-token overlap ensures that sentences split across a chunk
            boundary still have enough context to be retrieved correctly.
        """
        all_docs = []
        for path in pdf_paths:
            loader = PyPDFLoader(path)
            pages  = loader.load()
            all_docs.extend(pages)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size      = self.chunk_size,
            chunk_overlap   = self.chunk_overlap,
            # Tries to split on paragraph → sentence → word → character
            separators      = ["\n\n", "\n", ". ", " ", ""],
            length_function = len,
        )
        chunks = splitter.split_documents(all_docs)
        self.total_chunks = len(chunks)
        return chunks

    # ──────────────────────────────────────────
    # STAGE 3 & 4 : Embed chunks → Build FAISS index
    # ──────────────────────────────────────────
    def _build_vector_store(self, chunks):
        """
        Embed all chunks and store in a FAISS index.

        FAISS (Facebook AI Similarity Search):
            Stores dense vectors and supports fast cosine/L2 similarity
            search across millions of entries in milliseconds.
        """
        self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        self.retriever    = self.vector_store.as_retriever(
            search_type   = "similarity",
            search_kwargs = {"k": self.top_k}
        )

    # ──────────────────────────────────────────
    # Public : Load documents (full pipeline)
    # ──────────────────────────────────────────
    def load_documents(self, pdf_paths: List[str]) -> int:
        """
        Run the full ingestion pipeline on a list of PDF paths.
        Returns the total number of indexed chunks.
        """
        print(f"[MetaAssist] Loading {len(pdf_paths)} document(s)...")
        chunks = self._load_and_split(pdf_paths)

        print(f"[MetaAssist] Embedding {len(chunks)} chunks — this may take a moment...")
        self._build_vector_store(chunks)

        print(f"[MetaAssist] ✅ Done. {self.total_chunks} chunks indexed.")
        return self.total_chunks

    # ──────────────────────────────────────────
    # Public : Query the knowledge base
    # ──────────────────────────────────────────
    def query(
        self,
        question: str,
        chat_history: List[Tuple[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Answer a natural language question using the indexed documents.

        Args:
            question     : The user's question.
            chat_history : List of (user_message, assistant_message) tuples
                           representing prior conversation turns.

        Returns:
            dict with:
              - "answer"           : str — the LLM's grounded answer
              - "source_documents" : List[Document] — retrieved chunks used
        """
        if not self.retriever:
            raise RuntimeError(
                "No documents loaded. Call load_documents() first."
            )

        # Step 1 — Retrieve relevant chunks via semantic similarity
        source_docs = self.retriever.invoke(question)

        # Step 2 — Format retrieved chunks into a single context string
        context = "\n\n---\n\n".join([
            f"[Source: {os.path.basename(doc.metadata.get('source', 'Unknown'))}, "
            f"Page {doc.metadata.get('page', 'N/A')}]\n{doc.page_content}"
            for doc in source_docs
        ])

        # Step 3 — Format conversation history (last 5 turns max)
        history = chat_history or []
        history_text = ""
        for human_msg, ai_msg in history[-5:]:
            history_text += f"User: {human_msg}\nAssistant: {ai_msg}\n\n"

        # Step 4 — Build the prompt
        final_prompt = self.prompt.format(
            context      = context,
            chat_history = history_text if history_text else "No prior conversation.",
            question     = question
        )

        # Step 5 — Generate answer with Gemini
        response = self.llm.invoke(final_prompt)

        return {
            "answer"           : response.content,
            "source_documents" : source_docs,
        }

    # ──────────────────────────────────────────
    # Utility : Save / Load FAISS index
    # ──────────────────────────────────────────
    def save_index(self, path: str = "faiss_index"):
        """
        Persist the FAISS index + metadata to disk.
        Saves both the vector index and a JSON file with doc names and chunk count.
        """
        if self.vector_store:
            import json
            os.makedirs(path, exist_ok=True)
            self.vector_store.save_local(path)
            meta = {
                "total_chunks": self.total_chunks,
                "chunk_size":   self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "top_k":        self.top_k,
            }
            with open(os.path.join(path, "meta.json"), "w") as f:
                json.dump(meta, f)
            print(f"[MetaAssist] Index saved → '{path}/'")

    def load_index(self, path: str = "faiss_index"):
        """
        Load a previously saved FAISS index + metadata from disk.
        Returns the metadata dict so the caller can restore session state.
        """
        import json
        self.vector_store = FAISS.load_local(
            path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        self.retriever = self.vector_store.as_retriever(
            search_type   = "similarity",
            search_kwargs = {"k": self.top_k}
        )
        meta_path = os.path.join(path, "meta.json")
        meta = {}
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                meta = json.load(f)
            self.total_chunks = meta.get("total_chunks", 0)
        print(f"[MetaAssist] Index loaded ← '{path}/'")
        return meta

    @staticmethod
    def index_exists(path: str = "faiss_index") -> bool:
        """Check if a saved FAISS index exists on disk."""
        return os.path.exists(os.path.join(path, "index.faiss"))