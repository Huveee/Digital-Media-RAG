import fitz  # PyMuPDF
import nltk
import json
import argparse
import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import chromadb

# Ensure nltk punkt is available
nltk.download('punkt')
nltk.download('punkt_tab')


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    paragraphs = []
    last_heading = None

    for page in doc:
        text = page.get_text("text")
        for para in text.split("\n\n"):
            cleaned = para.strip().replace("\n", " ")
            if not cleaned:
                continue
            if cleaned.isupper() and len(cleaned.split()) <= 10:
                last_heading = cleaned
            else:
                if last_heading:
                    paragraphs.append("[HEADING+PARA] " + last_heading + " || " + cleaned)
                    last_heading = None
                else:
                    paragraphs.append(cleaned)
    return paragraphs


def semantic_chunking(paragraphs, model_name="all-MiniLM-L6-v2", sim_threshold=0.6, max_chunk_len=800):
    model = SentenceTransformer(model_name)
    chunks = []

    for para in paragraphs:
        if para.startswith("[HEADING+PARA]"):
            content = para.replace("[HEADING+PARA] ", "")
            chunks.append(content)
            continue

        sentences = nltk.sent_tokenize(para)
        if not sentences:
            continue

        embeddings = model.encode(sentences)
        current_chunk = [sentences[0]]
        current_embedding = embeddings[0].reshape(1, -1)

        for i in range(1, len(sentences)):
            similarity = cosine_similarity(current_embedding, embeddings[i].reshape(1, -1))[0][0]
            if similarity > sim_threshold and len(" ".join(current_chunk)) < max_chunk_len:
                current_chunk.append(sentences[i])
                current_embedding = np.mean([current_embedding, embeddings[i].reshape(1, -1)], axis=0)
            else:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentences[i]]
                current_embedding = embeddings[i].reshape(1, -1)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

    return chunks


def upload_to_chroma(chunks, pdf_name, collection_name="pdf_chunks"):
    # New Chroma client initialization (non-deprecated)
    client = chromadb.Client()
    collection = client.get_or_create_collection(name=collection_name)

    ids = [f"{pdf_name}_{i}" for i in range(len(chunks))]
    collection.add(ids=ids, documents=chunks, metadatas=[{"pdf_name": pdf_name}] * len(chunks))
    print(f"💾 Uploaded {len(chunks)} chunks from {pdf_name} to Chroma")


def process_folder(pdf_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")]

    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_folder, pdf_file)
        output_json = os.path.join(output_folder, os.path.splitext(pdf_file)[0] + ".json")

        paragraphs = extract_text_from_pdf(pdf_path)
        chunks = semantic_chunking(paragraphs)

        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)

        upload_to_chroma(chunks, pdf_file)
        print(f"✅ Processed {pdf_file}: {len(chunks)} chunks saved to JSON + Chroma DB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Semantic chunking of PDFs in a folder and upload to Chroma.")
    parser.add_argument("pdf_folder", help="Path to the folder containing PDFs")
    parser.add_argument("output_folder", help="Path to save the JSON outputs")
    args = parser.parse_args()

    process_folder(args.pdf_folder, args.output_folder)
