import re
import pdfplumber
from tabulate import tabulate


def clean_text(text: str) -> str:
    """Bereinigt PDF-Text: entfernt harte Umbrüche, doppelte Leerzeichen, Silbentrennungen"""
    if not text:
        return ""

    # Zeilenumbrüche durch Leerzeichen ersetzen
    text = re.sub(r"\n+", " ", text)

    # Mehrfache Leerzeichen reduzieren
    text = re.sub(r"\s+", " ", text)

    # Silbentrennungen (z. B. "In-formatik") zusammenführen
    text = re.sub(r"(\w+)- (\w+)", r"\1\2", text)

    return text.strip()


def chunk_by_paragraphs(text: str, source_name: str = "document") -> dict:
    """
    Teilt den Text anhand von §§ und Anlagen auf.
    Gibt ein Dict {chunk_id: chunk_text} zurück.
    """
    chunks = {}

    # 1) Split nach Paragraphen (§ ...)
    paragraph_splits = re.split(r"(§\s*\d+[a-zA-Z]*)", text)

    current_section = None
    for part in paragraph_splits:
        part = part.strip()
        if not part:
            continue
        if part.startswith("§"):
            current_section = part
        else:
            if current_section:
                chunk_id = f"{source_name}_{current_section}"
                chunks[chunk_id] = clean_text(f"{current_section}\n{part}")
                current_section = None

    # 2) Split nach Anlagen (Anlage X ...)
    anlage_splits = re.split(r"(Anlage\s+\d+)", text)
    for i in range(1, len(anlage_splits), 2):
        header = anlage_splits[i].strip()
        content = anlage_splits[i + 1].strip()
        chunk_id = f"{source_name}_{header}"
        chunks[chunk_id] = clean_text(f"{header}\n{content}")

    return chunks


def extract_tables(pdf_path: str, source_name: str = "document") -> dict:
    """
    Extrahiert Tabellen und gibt sie als Markdown zurück.
    """
    tables_dict = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for t_idx, table in enumerate(tables, start=1):
                if table and any(table):
                    try:
                        md_table = tabulate(table, headers="firstrow", tablefmt="github")
                    except Exception:
                        # Fallback: rohe Zeilen mit Pipes
                        md_table = "\n".join([" | ".join(row) for row in table if row])
                    chunk_id = f"{source_name}_page{page_num}_table{t_idx}"
                    tables_dict[chunk_id] = md_table
    return tables_dict


def parse_pdf_into_chunks(pdf_path: str) -> dict:
    """
    Hauptfunktion: PDF einlesen, nach Paragraphen/Anlagen splitten und Tabellen hinzufügen.
    Gibt ein Dict {chunk_id: chunk_text} zurück.
    """
    chunks = {}
    source_name = pdf_path.split("/")[-1].replace(".pdf", "")

    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"

    # Paragraphen & Anlagen
    text_chunks = chunk_by_paragraphs(full_text, source_name)

    # Tabellen
    table_chunks = extract_tables(pdf_path, source_name)

    # Alles zusammenführen
    chunks.update(text_chunks)
    chunks.update(table_chunks)

    return chunks
