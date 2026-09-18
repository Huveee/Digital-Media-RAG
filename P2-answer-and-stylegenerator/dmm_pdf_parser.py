"""
dmm_pdf_parser.py
-----------------
Structure-aware PDF parser with §-based chunking and automatic metadata extraction.
Combines structure parsing + chunking + metadata enrichment in a single module.

Pipeline: PDF → raw text extraction → § structure detection → chunking → metadata enrichment
"""

import pdfplumber
import re
import os
from tabulate import tabulate
from metadata_extractor import extract_document_metadata


def clean_text(text: str) -> str:
    """Cleans up PDF text: removes hard line breaks, double spaces, and hyphenation."""
    if not text:
        return ""
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(\w+)- (\w+)", r"\1\2", text)  # Fix hyphenation
    return text.strip()


def _extract_full_text_with_pages(pdf_path: str) -> list[dict]:
    """
    Extracts text from each page of the PDF.
    Returns a list of {"page": int, "text": str} dicts.
    """
    pages = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    pages.append({"page": page_num, "text": page_text})
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return pages


def _extract_tables(pdf_path: str) -> list[dict]:
    """
    Extracts tables from the PDF and returns them as markdown.
    Each entry: {"page": int, "table_index": int, "text": str}
    """
    tables = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_tables = page.extract_tables()
                for t_idx, table in enumerate(page_tables, start=1):
                    if table and any(table):
                        try:
                            md_table = tabulate(table, headers="firstrow", tablefmt="github")
                        except Exception:
                            md_table = "\n".join([" | ".join(str(c) for c in row) for row in table if row])
                        tables.append({
                            "page": page_num,
                            "table_index": t_idx,
                            "text": md_table
                        })
    except Exception as e:
        print(f"Error extracting tables from {pdf_path}: {e}")
    return tables


def _detect_section_structure(full_text: str) -> bool:
    """Check if the document has § section structure (study regulation style)."""
    section_count = len(re.findall(r"§\s*\d+", full_text))
    return section_count >= 3  # At least 3 sections to be considered structured


def _parse_sections_from_pages(pages: list[dict]) -> list[dict]:
    """
    Parse § sections from page-level text, tracking which page each section starts on.
    
    Returns a list of sections:
    [{"section_symbol": "§7", "section_title": "Bachelor Thesis", 
      "text": "...", "page": 12}, ...]
    """
    # Combine all text with page markers
    full_text = ""
    page_boundaries = []  # (char_position, page_number)
    
    for page_data in pages:
        page_boundaries.append((len(full_text), page_data["page"]))
        full_text += page_data["text"] + "\n"
    
    # Split by § symbols
    # Pattern: capture "§ 7" or "§7a" etc. and what follows until the next §
    section_pattern = r"(§\s*\d+[a-zA-Z]*)"
    parts = re.split(section_pattern, full_text)
    
    sections = []
    
    for i in range(1, len(parts), 2):
        if i + 1 >= len(parts):
            break
            
        section_symbol = parts[i].strip()
        section_content = parts[i + 1].strip()
        
        # Clean section symbol (remove extra spaces)
        clean_symbol = re.sub(r"\s+", "", section_symbol)
        
        # Extract section title: first line or text until first period/newline
        title_match = re.match(r"^[\s]*([^\n.;(]+)", section_content)
        section_title = title_match.group(1).strip() if title_match else ""
        
        # Determine which page this section starts on
        section_start_pos = full_text.find(section_symbol)
        page_num = 1
        for char_pos, pg in page_boundaries:
            if section_start_pos >= char_pos:
                page_num = pg
        
        # Clean the full section text
        cleaned_text = clean_text(f"{section_symbol} {section_content}")
        
        if cleaned_text:
            sections.append({
                "section_symbol": clean_symbol,
                "section_title": section_title,
                "text": cleaned_text,
                "page": page_num
            })
    
    return sections


def parse_pdf_with_metadata(pdf_path: str) -> dict:
    """
    Main function: Parse a PDF with structure-aware chunking and automatic metadata.
    
    Pipeline:
    1. Extract raw text page by page
    2. Send first pages to LLM for metadata detection (degree, program, type)
    3. Detect document structure (§-based or unstructured)
    4. Chunk accordingly (§-based or page-based fallback)
    5. Attach metadata to every chunk
    
    Returns: {chunk_id: {"text": "...", "metadata": {...}}}
    """
    chunks = {}
    filename = os.path.basename(pdf_path)
    
    # Step 1: Extract all pages
    pages = _extract_full_text_with_pages(pdf_path)
    if not pages:
        print(f"No text extracted from {filename}")
        return chunks
    
    # Step 2: Auto-detect metadata using LLM
    # Send first 2 pages for classification
    sample_text = " ".join([p["text"] for p in pages[:2]])
    base_metadata = extract_document_metadata(sample_text, filename)
    
    print(f"  Detected metadata for {filename}: degree={base_metadata['degree']}, "
          f"program={base_metadata['program']}, type={base_metadata['document_type']}")
    
    # Step 3: Detect if document has § structure
    full_text = "\n".join([p["text"] for p in pages])
    has_sections = _detect_section_structure(full_text)
    
    if has_sections:
        # Step 4a: §-based chunking for study regulations
        sections = _parse_sections_from_pages(pages)
        
        for section in sections:
            chunk_id = f"pdf_{filename}_{section['section_symbol']}"
            
            # Build per-chunk metadata
            chunk_metadata = {
                **base_metadata,                          # LLM-detected fields
                "section_symbol": section["section_symbol"],
                "section_title": section["section_title"],
                "page": section["page"],
                "source": filename,
                "type": "pdf"
            }
            
            chunks[chunk_id] = {
                "text": section["text"],
                "metadata": chunk_metadata
            }
        
        print(f"  → {len(sections)} §-based chunks created")
    else:
        # Step 4b: Page-based fallback for unstructured PDFs (flyers, etc.)
        for page_data in pages:
            cleaned_text = clean_text(page_data["text"])
            if not cleaned_text:
                continue
                
            chunk_id = f"pdf_{filename}_page{page_data['page']}"
            
            chunk_metadata = {
                **base_metadata,
                "page": page_data["page"],
                "source": filename,
                "type": "pdf"
            }
            
            chunks[chunk_id] = {
                "text": cleaned_text,
                "metadata": chunk_metadata
            }
        
        print(f"  → {len(chunks)} page-based chunks created (no § structure detected)")
    
    # Step 5: Extract and add table chunks
    tables = _extract_tables(pdf_path)
    for table_data in tables:
        chunk_id = f"pdf_{filename}_page{table_data['page']}_table{table_data['table_index']}"
        
        table_metadata = {
            **base_metadata,
            "page": table_data["page"],
            "source": filename,
            "type": "pdf",
            "content_type": "table"
        }
        
        chunks[chunk_id] = {
            "text": table_data["text"],
            "metadata": table_metadata
        }
    
    if tables:
        print(f"  → {len(tables)} table chunks added")
    
    return chunks


if __name__ == "__main__":
    # Test with existing documents
    pdf_files = [
        "docs/AT-MPO-06-25_Lesefassung.pdf",
        "docs/Master_Flyer_EN.pdf"
    ]
    
    all_chunks = {}
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            print(f"\nProcessing PDF: {pdf_file}")
            page_chunks = parse_pdf_with_metadata(pdf_file)
            all_chunks.update(page_chunks)
            print(f"  Total chunks: {len(page_chunks)}")
        else:
            print(f"File not found: {pdf_file}")
    
    print(f"\n{'='*60}")
    print(f"Grand total: {len(all_chunks)} chunks")
    
    # Show a few sample chunks
    if all_chunks:
        print(f"\n--- Sample Chunks ---")
        for i, (chunk_id, data) in enumerate(all_chunks.items()):
            if i >= 3:
                break
            print(f"\nChunk ID: {chunk_id}")
            print(f"Metadata: {data['metadata']}")
            print(f"Text preview: {data['text'][:150]}...")
