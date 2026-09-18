"""
ingest_pipeline.py
------------------
Single entry point that orchestrates the full document → ChromaDB pipeline.
Handles both PDFs and URLs, auto-detects source type, and manages the RAGBot instance.

Usage:
    python ingest_pipeline.py                    # Ingest demo sources
    python ingest_pipeline.py --pdf docs/my.pdf  # Ingest a single PDF
    python ingest_pipeline.py --url https://...  # Ingest a single URL
    python ingest_pipeline.py --rebuild          # Clear DB and re-ingest all
"""

import os
import argparse
from ragbot import RAGBot
from dmm_pdf_parser import parse_pdf_with_metadata
from dmm_web_scraper import scrape_url


def ingest_pdf(pdf_path: str, bot: RAGBot) -> int:
    """
    Parse a PDF → extract metadata → chunk → store in ChromaDB.
    
    Args:
        pdf_path: Path to the PDF file
        bot: RAGBot instance with ChromaDB collection
        
    Returns:
        int: Number of chunks ingested
    """
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return 0
    
    print(f"\n📄 Ingesting PDF: {pdf_path}")
    chunks = parse_pdf_with_metadata(pdf_path)
    
    if chunks:
        bot.add_documents_with_metadata(chunks)
    
    return len(chunks)


def ingest_url(url: str, bot: RAGBot) -> int:
    """
    Scrape a URL → extract metadata → chunk → store in ChromaDB.
    
    Args:
        url: URL to scrape
        bot: RAGBot instance with ChromaDB collection
        
    Returns:
        int: Number of chunks ingested
    """
    print(f"\n🌐 Ingesting URL: {url}")
    chunks = scrape_url(url)
    
    if chunks:
        bot.add_documents_with_metadata(chunks)
    
    return len(chunks)


def ingest_source(source: str, bot: RAGBot) -> int:
    """
    Auto-detect source type (PDF path or URL) and ingest accordingly.
    
    Args:
        source: Either a file path to a PDF or a URL
        bot: RAGBot instance
        
    Returns:
        int: Number of chunks ingested
    """
    if source.startswith("http://") or source.startswith("https://"):
        return ingest_url(source, bot)
    elif source.lower().endswith(".pdf"):
        return ingest_pdf(source, bot)
    else:
        print(f"Warning: Unknown source type for '{source}'. Trying as PDF path...")
        return ingest_pdf(source, bot)


def rebuild_database(sources: list, bot: RAGBot) -> dict:
    """
    Clear ChromaDB and re-ingest all sources from scratch.
    
    Args:
        sources: List of PDF paths and/or URLs
        bot: RAGBot instance
        
    Returns:
        dict: Summary of ingestion results
    """
    print("🔄 Rebuilding database from scratch...")
    bot.clear_collection()
    
    results = {}
    total_chunks = 0
    
    for source in sources:
        count = ingest_source(source, bot)
        results[source] = count
        total_chunks += count
    
    print(f"\n{'='*60}")
    print(f"✅ Database rebuilt: {total_chunks} total chunks from {len(sources)} sources")
    
    return results


# ─── Default Sources ──────────────────────────────────────────────────

# These are the known documents and URLs for the project.
# You can add more sources here or provide them via command line.
DEFAULT_SOURCES = [
    # PDF documents in docs/ folder
    "docs/AT-MPO-06-25_Lesefassung.pdf",
    "docs/AT-MPO-06-25_Lesefassung_automatVerz.pdf",
    "docs/AT-BPO-06-25_Lesefassung_automVerz.pdf",
    "docs/BPO-Informatik-VF.pdf",
    "docs/MPO_Informatik_VF.pdf",
    "docs/Master_Flyer_EN.pdf",
    # Websites
    "https://www.hfk-bremen.de/en/application/applying-for-the-study-programme-digital-media-m-a/3#portfolio",
    "https://www.uni-bremen.de/en/studies/orientation-application/offered-study-program/dbs/study/22",
]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents into the RAG pipeline")
    parser.add_argument("--pdf", type=str, help="Path to a single PDF to ingest")
    parser.add_argument("--url", type=str, help="URL to scrape and ingest")
    parser.add_argument("--rebuild", action="store_true", help="Clear DB and re-ingest all default sources")
    args = parser.parse_args()
    
    # Initialize RAGBot
    bot = RAGBot()
    
    if args.pdf:
        count = ingest_pdf(args.pdf, bot)
        print(f"\n✅ Ingested {count} chunks from PDF")
    elif args.url:
        count = ingest_url(args.url, bot)
        print(f"\n✅ Ingested {count} chunks from URL")
    elif args.rebuild:
        results = rebuild_database(DEFAULT_SOURCES, bot)
        for source, count in results.items():
            print(f"  {source}: {count} chunks")
    else:
        # Default: ingest all sources (additive, won't duplicate due to upsert)
        print("Ingesting all default sources...")
        total = 0
        for source in DEFAULT_SOURCES:
            count = ingest_source(source, bot)
            total += count
        
        print(f"\n{'='*60}")
        print(f"✅ Total: {total} chunks ingested")
        
        # Show collection stats
        stats = bot.get_collection_stats()
        print(f"Collection '{stats['collection_name']}': {stats['total_chunks']} total chunks in DB")
