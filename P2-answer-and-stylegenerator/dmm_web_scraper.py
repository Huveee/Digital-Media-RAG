"""
dmm_web_scraper.py
------------------
Structure-aware web scraper with heading-based chunking and automatic metadata extraction.
Splits web pages into chunks based on HTML headings (h1, h2, h3) and enriches
each chunk with LLM-detected metadata.

Pipeline: URL → fetch HTML → heading-based chunking → metadata enrichment
"""

import requests
from bs4 import BeautifulSoup
from metadata_extractor import extract_document_metadata


def _clean_element_text(element) -> str:
    """Extract and clean text from a BeautifulSoup element."""
    text = element.get_text(separator=' ', strip=True)
    # Remove consecutive duplicate words (common in menus)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    deduped = []
    for line in lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)
    return '\n'.join(deduped)


def _extract_heading_chunks(html_content: str) -> list[dict]:
    """
    Splits HTML content into chunks based on heading tags (h1, h2, h3).
    Each chunk = heading + all content until the next heading of same or higher level.
    
    Returns: [{"heading": "...", "heading_level": 2, "text": "..."}, ...]
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove non-content elements
    for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
        tag.extract()
    
    # Find the main content area (try common containers)
    main_content = soup.find("main") or soup.find("article") or soup.find("div", class_="content") or soup.body or soup
    
    # Collect all heading tags and their content
    heading_tags = {"h1", "h2", "h3", "h4"}
    chunks = []
    current_heading = None
    current_heading_level = 0
    current_content = []
    
    for element in main_content.descendants:
        if element.name in heading_tags:
            # Save previous chunk if exists
            if current_heading and current_content:
                combined_text = current_heading + "\n" + "\n".join(current_content)
                chunks.append({
                    "heading": current_heading,
                    "heading_level": current_heading_level,
                    "text": combined_text.strip()
                })
            
            current_heading = element.get_text(strip=True)
            current_heading_level = int(element.name[1])
            current_content = []
            
        elif element.name in {"p", "li", "td", "span", "div"} and element.string:
            text = element.get_text(strip=True)
            if text and len(text) > 5:  # Skip very short fragments
                current_content.append(text)
    
    # Don't forget the last chunk
    if current_heading and current_content:
        combined_text = current_heading + "\n" + "\n".join(current_content)
        chunks.append({
            "heading": current_heading,
            "heading_level": current_heading_level,
            "text": combined_text.strip()
        })
    
    return chunks


def scrape_url(url: str, source_name: str = None) -> dict:
    """
    Downloads a webpage, splits it by headings, and extracts metadata from LLM.
    
    Returns chunks in format: {chunk_id: {"text": "...", "metadata": {...}}}
    """
    # Step 1: Fetch the page
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return {}
    
    html_content = response.text
    
    # Create source name from URL if not provided
    if not source_name:
        source_name = url.split('/')[-1] if not url.endswith('/') else url.split('/')[-2]
    
    # Step 2: Extract page title for metadata hint
    soup = BeautifulSoup(html_content, 'html.parser')
    page_title = soup.title.string.strip() if soup.title and soup.title.string else ""
    
    # Step 3: Get clean text sample for LLM metadata detection
    # Remove non-content elements for sampling
    for tag in soup(["script", "style", "header", "footer", "nav"]):
        tag.extract()
    sample_text = soup.get_text(separator=' ', strip=True)[:2000]
    
    # Add page title to sample for better context
    if page_title:
        sample_text = f"Page title: {page_title}\n\n{sample_text}"
    
    # Step 4: Auto-detect metadata via LLM
    base_metadata = extract_document_metadata(sample_text, url)
    
    print(f"  Detected metadata for {url}: degree={base_metadata['degree']}, "
          f"program={base_metadata['program']}, type={base_metadata['document_type']}")
    
    # Step 5: Heading-based chunking
    heading_chunks = _extract_heading_chunks(html_content)
    
    chunks = {}
    
    if heading_chunks:
        # Use heading-based chunks
        for i, hchunk in enumerate(heading_chunks):
            chunk_id = f"web_{source_name}_h{hchunk['heading_level']}_{i}"
            
            chunk_metadata = {
                **base_metadata,
                "source_url": url,
                "heading": hchunk["heading"],
                "type": "website"
            }
            
            chunks[chunk_id] = {
                "text": hchunk["text"],
                "metadata": chunk_metadata
            }
        
        print(f"  → {len(heading_chunks)} heading-based chunks created")
    else:
        # Fallback: treat entire page as one chunk (like before)
        full_text_soup = BeautifulSoup(html_content, 'html.parser')
        for tag in full_text_soup(["script", "style", "header", "footer", "nav"]):
            tag.extract()
        
        full_text = full_text_soup.get_text(separator=' ', strip=True)
        
        if full_text:
            chunk_id = f"web_{source_name}_full"
            
            chunk_metadata = {
                **base_metadata,
                "source_url": url,
                "heading": page_title or "Full Page",
                "type": "website"
            }
            
            chunks[chunk_id] = {
                "text": full_text,
                "metadata": chunk_metadata
            }
            
            print(f"  → 1 full-page chunk created (no headings detected)")
    
    return chunks


if __name__ == "__main__":
    # Test script
    urls_to_test = [
        "https://www.hfk-bremen.de/en/application/applying-for-the-study-programme-digital-media-m-a/3#portfolio",
        "https://www.uni-bremen.de/en/studies/orientation-application/offered-study-program/dbs/study/22"
    ]
    
    all_web_chunks = {}
    for url in urls_to_test:
        print(f"\nScraping: {url}")
        chunks = scrape_url(url)
        all_web_chunks.update(chunks)
    
    print(f"\n{'='*60}")
    print(f"Total: {len(all_web_chunks)} web chunks")
    
    # Preview first few chunks
    for i, (chunk_id, data) in enumerate(all_web_chunks.items()):
        if i >= 3:
            break
        print(f"\nChunk ID: {chunk_id}")
        print(f"Metadata: {data['metadata']}")
        print(f"Text preview: {data['text'][:200]}...")
