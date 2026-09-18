import re
import os
from openai import OpenAI
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv, dotenv_values
# loading variables from .env file
load_dotenv()

# Vieles habe ich jetzt hierher
# https://blog.futuresmart.ai/building-rag-applications-without-langchain-or-llamaindex


# Training of the Rag
class RAGTrainer():
    def __init__(self, path=None, api2use='chatai'):
        # Initialize ChromaDB client with persistence
        if path is not None:
            self.path = path
        else:
            self.path = '.'
        self.client = chromadb.PersistentClient(path=os.path.join(self.path, 'chroma_db'))

        if api2use == 'openai':
            # Configure sentence transformer embeddings
            sentence_transformer_ef = OpenAIEmbeddingFunction(
                model_name="text-embedding-3-small"
            )
        elif api2use == 'chatai':
            sentence_transformer_ef = OpenAIEmbeddingFunction(
                api_base="https://chat-ai.academiccloud.de/v1",
                api_key = os.environ.get("CHATAI_API_KEY"),
                model_name="e5-mistral-7b-instruct"
            )
        # Create or get existing collection
        self.collection = self.client.get_or_create_collection(
            name="documents_collection",
            embedding_function=sentence_transformer_ef
        )

    def read_document(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    def print_search_results(results):
        for i in range(len(results['documents'][0])):
            doc = results['documents'][0][i]
            meta = results['metadatas'][0][i]
            distance = results['distances'][0][i]

            print(f"\nResult {i + 1}")
            print(f"Source: {meta['source']}, Chunk {meta['chunk']}")
            print(f"Distance: {distance}")
            print(f"Content: {doc}\n")

    def split_text(self, text: str, chunk_size: int = 500):
        """Split text into chunks while preserving sentence boundaries"""
        sentences = text.replace('\n', ' ').split('. ')
        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Ensure proper sentence ending
            if not sentence.endswith('.'):
                sentence += '.'

            sentence_size = len(sentence)

            # Check if adding this sentence would exceed chunk size
            if current_size + sentence_size > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size

        # Add the last chunk if it exists
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def process_document(self, file_path: str):
        """Process a single document and prepare it for ChromaDB"""
        try:
            # Read the document
            content = self.read_document(file_path)

            # Split into chunks
            chunks = self.split_text(content)

            # Prepare metadata
            file_name = os.path.basename(file_path)
            metadatas = [{"source": file_name, "chunk": i} for i in range(len(chunks))]
            ids = [f"{file_name}_chunk_{i}" for i in range(len(chunks))]

            return ids, chunks, metadatas
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            return [], [], []

    def add_to_collection(self, ids, texts, metadatas):
        """Add documents to collection in batches"""
        if not texts:
            return

        batch_size = 100
        for i in range(0, len(texts), batch_size):
            end_idx = min(i + batch_size, len(texts))
            self.collection.add(
                documents=texts[i:end_idx],
                metadatas=metadatas[i:end_idx],
                ids=ids[i:end_idx]
            )

    def train(self):
        # markdown_path
        folder_path = os.path.join(self.path, 'parsed_mds')
        """Process all documents in a folder and add to collection"""
        files = [os.path.join(folder_path, file)
                 for file in os.listdir(folder_path)
                 if os.path.isfile(os.path.join(folder_path, file))]

        for file_path in files:
            print(f"Processing {os.path.basename(file_path)}...")
            ids, texts, metadatas = self.process_document(file_path)
            self.add_to_collection(ids, texts, metadatas)
            print(f"Added {len(texts)} chunks to collection")

if __name__ == "__main__":
    rag_trainer = RAGTrainer(os.path.join('data', 'fb11_data'))
    rag_trainer.train()
