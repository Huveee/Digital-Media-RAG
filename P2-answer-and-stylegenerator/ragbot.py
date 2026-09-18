"""
ragbot.py
---------
RAG Bot with metadata-enriched ChromaDB storage, filtered vector search,
and source citations in LLM responses.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
from query_filter import extract_filters

load_dotenv()


class RAGBot:
    def __init__(self, model="meta-llama-3.1-8b-instruct", collection_name="knowledge_base"):
        # Load API keys
        api_key = os.getenv("CHATAI_API_KEY")
        base_url = os.getenv("BASE_URL")

        # Chat client for answer generation
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

        # Local embeddings (SentenceTransformer)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            # model_name="all-MiniLM-L6-v2"  # English-only, fast but poor cross-language
            model_name="paraphrase-multilingual-MiniLM-L12-v2"  # Multilingual, supports DE+EN
        )

        # Vector DB
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

    # ─── Document Ingestion ───────────────────────────────────────────

    def add_documents(self, docs: dict):
        """
        Legacy method for backward compatibility.
        docs = {"doc1": "Some text", "doc2": "Another passage"}
        """
        for doc_id, text in docs.items():
            self.collection.add(documents=[text], ids=[doc_id])

    def add_documents_with_metadata(self, chunks: dict):
        """
        Add documents with rich metadata to ChromaDB.
        
        Args:
            chunks: {chunk_id: {"text": "...", "metadata": {...}}}
        """
        if not chunks:
            return
        
        # Batch upsert for efficiency
        ids = []
        documents = []
        metadatas = []
        
        for chunk_id, data in chunks.items():
            ids.append(chunk_id)
            documents.append(data["text"])
            
            # ChromaDB requires metadata values to be str, int, float, or bool
            # Convert None values to empty strings
            cleaned_metadata = {}
            for key, value in data["metadata"].items():
                if value is None:
                    cleaned_metadata[key] = ""
                else:
                    cleaned_metadata[key] = value
            metadatas.append(cleaned_metadata)
        
        # Upsert in batches (ChromaDB can handle ~5000 at a time)
        batch_size = 500
        for i in range(0, len(ids), batch_size):
            batch_end = min(i + batch_size, len(ids))
            self.collection.upsert(
                ids=ids[i:batch_end],
                documents=documents[i:batch_end],
                metadatas=metadatas[i:batch_end]
            )
        
        print(f"  Upserted {len(ids)} chunks into ChromaDB collection '{self.collection.name}'")

    # ─── Retrieval ────────────────────────────────────────────────────

    def retrieve(self, query, top_k=3):
        """Legacy retrieval without metadata filtering."""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        documents = results["documents"][0] if results["documents"] else []
        ids = results["ids"][0] if results["ids"] else []
        return documents, ids

    def retrieve_with_filters(self, query: str, filters: dict = None, top_k: int = 5) -> tuple:
        """
        Retrieve documents with optional metadata filtering.
        
        Args:
            query: Search query text
            filters: ChromaDB where-filter dict (e.g. {"degree": "bachelor"})
            top_k: Number of results to return
            
        Returns:
            tuple: (documents, ids, metadatas)
        """
        query_params = {
            "query_texts": [query],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"]
        }
        
        if filters:
            query_params["where"] = filters
        
        try:
            results = self.collection.query(**query_params)
        except Exception as e:
            # If filter fails (e.g. no matching docs), fall back to unfiltered
            print(f"  Filtered query failed ({e}), falling back to unfiltered search")
            query_params.pop("where", None)
            results = self.collection.query(**query_params)
        
        documents = results["documents"][0] if results["documents"] else []
        ids = results["ids"][0] if results["ids"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        
        return documents, ids, metadatas

    # ─── Answer Generation ────────────────────────────────────────────

    def ask(self, query: str, use_filters: bool = True) -> tuple:
        """
        Full RAG pipeline: extract filters → retrieve → generate answer.
        
        Args:
            query: User's question
            use_filters: Whether to auto-extract and apply metadata filters
            
        Returns:
            tuple: (answer, sources, passages, metadatas)
        """
        # Step 1: Extract metadata filters from the query
        filters = extract_filters(query) if use_filters else {}
        
        if filters:
            print(f"  Auto-detected filters: {filters}")
        
        # Step 2: Retrieve relevant passages with filters
        passages, ids, metadatas = self.retrieve_with_filters(query, filters if filters else None)
        
        if not passages:
            return (
                "Sorry, I could not find relevant information.",
                [],
                [],
                []
            )
        
        # Step 3: Build context with source citations
        context_parts = []
        for doc, meta in zip(passages, metadatas):
            source_info = f"[Source: {meta.get('document_name', meta.get('source', 'unknown'))}"
            
            if meta.get('section_symbol'):
                source_info += f", {meta['section_symbol']}"
            if meta.get('section_title'):
                source_info += f" - {meta['section_title']}"
            if meta.get('page'):
                source_info += f", Page {meta['page']}"
            if meta.get('heading'):
                source_info += f", Section: {meta['heading']}"
            
            source_info += "]"
            context_parts.append(f"{source_info}\n{doc}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Step 4: Generate answer with LLM
        system_prompt = (
            "You are a helpful university RAG assistant. Use the following context to answer the question.\n"
            "Each context chunk has a [Source: ...] tag — cite these sources in your answer.\n"
            "If the answer is not in the context, say you don't know.\n\n"
            f"{context}"
        )
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
        )
        answer = response.choices[0].message.content
        
        return answer, ids, passages, metadatas

    # ─── Utility ──────────────────────────────────────────────────────

    def get_collection_stats(self) -> dict:
        """Returns basic statistics about the ChromaDB collection."""
        count = self.collection.count()
        return {
            "collection_name": self.collection.name,
            "total_chunks": count
        }

    def clear_collection(self):
        """Deletes and recreates the collection."""
        self.chroma_client.delete_collection(name=self.collection.name)
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection.name,
            embedding_function=self.embedding_fn
        )
        print(f"  Collection '{self.collection.name}' cleared.")
