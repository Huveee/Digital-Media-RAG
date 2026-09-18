"""
metadata_extractor.py
---------------------
LLM-based automatic metadata extraction from document content.
Sends a sample of text to the LLM and asks it to classify the document
into structured metadata fields (degree, program, document_type, etc.).
"""

import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

METADATA_EXTRACTION_PROMPT = """You are a metadata extraction assistant for German and English university documents.
Analyze the following document excerpt and extract metadata.
Return ONLY a valid JSON object with exactly these fields:

- "degree": one of ["bachelor", "master", "unknown"]
- "program": one of ["digital_media", "computer_science", "public_health", "unknown"]  
- "document_type": one of ["study_regulation", "exam_regulation", "website", "flyer", "unknown"]
- "document_name": a short descriptive slug using underscores (e.g. "dm_master_regulation_2025")
- "year": integer year if found in the document, otherwise null

Degree detection rules:
- "Master", "M.A.", "M.Sc.", "Masterstudiengang", "Masterprüfungsordnung", "MPO" → "master"
- "Bachelor", "B.Sc.", "B.A.", "Bachelorstudiengang", "Bachelorprüfungsordnung", "BPO" → "bachelor"
- Check the filename hint too: "MPO" or "Master" in filename → "master", "BPO" or "Bachelor" → "bachelor"

Program detection rules (IMPORTANT - check carefully):
- "Digitale Medien", "Digital Media", "Medieninformatik" → "digital_media"
- "Informatik", "Computer Science" (without "Medien") → "computer_science"
- "Public Health", "Gesundheitswissenschaften" → "public_health"
- If the document mentions a specific university like "Hochschule für Künste Bremen" together with "Universität Bremen", it is very likely "digital_media"
- If the filename contains "AT-MPO" or "AT-BPO" (Allgemeiner Teil), it is the Digital Media program regulation

Document type detection rules:
- If the source is a URL (starts with "http://" or "https://"), the document_type MUST be "website"
- "Prüfungsordnung", "Studienordnung", "§" symbols, "Satzung" → "study_regulation"
- Short promotional documents, brochures without § symbols → "flyer"

IMPORTANT: Return ONLY the JSON object, no other text.

Document source hint: {source_hint}

Document excerpt:
{text_sample}
"""


def extract_document_metadata(text_sample: str, source_hint: str = "") -> dict:
    """
    Sends a text sample to the LLM and extracts structured metadata.
    
    Args:
        text_sample: First ~2000 characters of the document
        source_hint: Filename or URL for additional context
        
    Returns:
        dict with keys: degree, program, document_type, document_name, year
    """
    # Default metadata in case of failure
    default_metadata = {
        "degree": "unknown",
        "program": "unknown",
        "document_type": "unknown",
        "document_name": _generate_fallback_name(source_hint),
        "year": None
    }
    
    try:
        api_key = os.getenv("CHATAI_API_KEY")
        base_url = os.getenv("BASE_URL")
        
        if not api_key or not base_url:
            print("Warning: API credentials not found. Using default metadata.")
            return default_metadata
        
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        # Truncate text sample to ~3000 chars for better context
        truncated_text = text_sample[:3000]
        
        prompt = METADATA_EXTRACTION_PROMPT.format(
            source_hint=source_hint,
            text_sample=truncated_text
        )
        
        response = client.chat.completions.create(
            model="meta-llama-3.1-8b-instruct",
            messages=[
                {"role": "system", "content": "You are a JSON-only metadata extraction assistant. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1  # Low temperature for consistent extraction
        )
        
        raw_response = response.choices[0].message.content.strip()
        
        # Try to extract JSON from the response
        metadata = _parse_llm_response(raw_response)
        
        if metadata:
            # Validate and fill in missing fields
            return _validate_metadata(metadata, source_hint)
        else:
            print(f"Warning: Could not parse LLM response for '{source_hint}'. Using defaults.")
            return default_metadata
            
    except Exception as e:
        print(f"Error extracting metadata for '{source_hint}': {e}")
        return default_metadata


def _parse_llm_response(raw_response: str) -> dict | None:
    """
    Attempts to parse JSON from the LLM response.
    Handles cases where the LLM wraps JSON in markdown code blocks.
    """
    # Try direct JSON parse first
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code block
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw_response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON object pattern in the text
    json_match = re.search(r'\{[^{}]*\}', raw_response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    return None


def _validate_metadata(metadata: dict, source_hint: str) -> dict:
    """Validates and normalizes extracted metadata fields."""
    valid_degrees = {"bachelor", "master", "unknown"}
    valid_programs = {"digital_media", "computer_science", "public_health", "unknown"}
    valid_doc_types = {"study_regulation", "exam_regulation", "website", "flyer", "unknown"}
    
    validated = {
        "degree": metadata.get("degree", "unknown").lower(),
        "program": metadata.get("program", "unknown").lower(),
        "document_type": metadata.get("document_type", "unknown").lower(),
        "document_name": metadata.get("document_name", _generate_fallback_name(source_hint)),
        "year": metadata.get("year")
    }
    
    # Enforce valid values
    if validated["degree"] not in valid_degrees:
        validated["degree"] = "unknown"
    if validated["program"] not in valid_programs:
        validated["program"] = "unknown"
    if validated["document_type"] not in valid_doc_types:
        validated["document_type"] = "unknown"
    
    # Ensure year is int or None
    if validated["year"] is not None:
        try:
            validated["year"] = int(validated["year"])
        except (ValueError, TypeError):
            validated["year"] = None
    
    # Ensure document_name is a valid slug
    if not validated["document_name"]:
        validated["document_name"] = _generate_fallback_name(source_hint)
    
    return validated


def _generate_fallback_name(source_hint: str) -> str:
    """Creates a simple slug from the source hint (filename or URL)."""
    if not source_hint:
        return "unknown_document"
    
    # Remove file extension and path
    name = os.path.basename(source_hint)
    name = os.path.splitext(name)[0]
    
    # Replace non-alphanumeric with underscores 
    name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    name = re.sub(r'_+', '_', name).strip('_').lower()
    
    return name if name else "unknown_document"


if __name__ == "__main__":
    # Quick test with a sample text
    test_text = """
    Allgemeiner Teil der Masterprüfungsordnung (AT-MPO)
    für den Masterstudiengang Digitale Medien
    der Universität Bremen und der Hochschule für Künste Bremen
    vom 25. Juni 2025
    
    § 1 Regelungsgegenstand
    Diese Prüfungsordnung regelt das Studium im Masterstudiengang Digitale Medien...
    """
    
    result = extract_document_metadata(test_text, "AT-MPO-06-25_Lesefassung.pdf")
    print("Extracted metadata:")
    print(json.dumps(result, indent=2))
