"""
query_filter.py
---------------
Extracts metadata filters from user queries using keyword matching.
Returns ChromaDB-compatible where-filter dicts for filtered vector search.
"""

import re


# Keyword maps for filter extraction
DEGREE_KEYWORDS = {
    "bachelor": "bachelor",
    "bachelors": "bachelor",
    "bachelor's": "bachelor",
    "bsc": "bachelor",
    "b.sc": "bachelor",
    "b.a": "bachelor",
    "ba": "bachelor",
    "undergraduate": "bachelor",
    "master": "master",
    "masters": "master",
    "master's": "master",
    "msc": "master",
    "m.sc": "master",
    "m.a": "master",
    "ma": "master",
    "graduate": "master",
}

PROGRAM_KEYWORDS = {
    "digital media": "digital_media",
    "digital medien": "digital_media",
    "digitale medien": "digital_media",
    "dm": "digital_media",
    "computer science": "computer_science",
    "informatik": "computer_science",
    "cs": "computer_science",
    "public health": "public_health",
    "gesundheitswissenschaften": "public_health",
}

DOCTYPE_KEYWORDS = {
    "regulation": "study_regulation",
    "regulations": "study_regulation",
    "ordnung": "study_regulation",
    "prüfungsordnung": "study_regulation",
    "studienordnung": "study_regulation",
    "satzung": "study_regulation",
    "website": "website",
    "web page": "website",
    "webpage": "website",
    "online": "website",
    "flyer": "flyer",
    "brochure": "flyer",
    "broschüre": "flyer",
}


def extract_filters(query: str) -> dict:
    """
    Analyzes a query string and returns a ChromaDB-compatible where-filter dict.
    
    Examples:
        "bachelor thesis requirements" 
            → {"degree": "bachelor"}
        "master digital media admission" 
            → {"$and": [{"degree": "master"}, {"program": "digital_media"}]}
        "computer science study regulation" 
            → {"$and": [{"program": "computer_science"}, {"document_type": "study_regulation"}]}
        "what is the weather?" 
            → {}  (no filters detected)
    
    Args:
        query: The user's question string
        
    Returns:
        dict: ChromaDB where-filter, or empty dict if no filters detected
    """
    query_lower = query.lower()
    detected_filters = {}
    
    # Check for degree keywords
    for keyword, value in DEGREE_KEYWORDS.items():
        # Use word boundary matching to avoid partial matches
        # (e.g. "master" shouldn't match in "webmaster")
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, query_lower):
            detected_filters["degree"] = value
            break  # Take the first match
    
    # Check for program keywords (check longer phrases first)
    sorted_program_keywords = sorted(PROGRAM_KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True)
    for keyword, value in sorted_program_keywords:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, query_lower):
            detected_filters["program"] = value
            break
    
    # Check for document type keywords
    sorted_doctype_keywords = sorted(DOCTYPE_KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True)
    for keyword, value in sorted_doctype_keywords:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, query_lower):
            detected_filters["document_type"] = value
            break
    
    # Build ChromaDB where clause
    if len(detected_filters) == 0:
        return {}
    elif len(detected_filters) == 1:
        return detected_filters
    else:
        # Multiple filters → use $and
        return {"$and": [{k: v} for k, v in detected_filters.items()]}


if __name__ == "__main__":
    # Test cases
    test_queries = [
        "What are the requirements for the bachelor thesis?",
        "Master digital media admission requirements",
        "Computer science study regulation",
        "How do I apply for the master's program in digital media?",
        "Prüfungsordnung Informatik Bachelor",
        "What is the weather today?",
        "Tell me about the digital media program",
        "Bachelor thesis Digitale Medien",
    ]
    
    print("Query Filter Test Results:")
    print("=" * 60)
    for q in test_queries:
        filters = extract_filters(q)
        print(f"\nQuery: \"{q}\"")
        print(f"Filters: {filters}")
