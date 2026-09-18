# 🤖 AI Chatbots with RAG & Adaptive Style

This project provides a collection of **LLM-powered chatbots** built with Python and Gradio.  
It includes:

- 📚 **RAGBot**: A Retrieval-Augmented Generation chatbot with PDF ingestion, local embeddings, and source citation.  
- 🎭 **Style Bots**: Answer rewriting based on **style & tone detection** or via an **adaptive style engine**.  
- 🖥 **Gradio UIs**: Easy-to-use web interfaces to run and test different bots.

---

## 📂 Project Structure
```bash
P2-Answer-and-Stylegenerator/
│── chrome_db/           # Chrome Vectordatabase
│── docs/                # Example PDFs (study regulations, etc.)
│── .env                 # API keys + model configs
│── .gitignore
│── adaptive_style.py           # AdaptiveResponder class
│── flexible_style_detection.py # Detects style & tone with LLM
│── main.py         # currently not used
│── pdf_chuncker.py # Splits PDF into chunks 
│── ragbot.py       # Logic behind RAG Parsing
│── simplechatbot.py  # not used currently
│── sytlebot.py       # not used currently
│── UI_dualbot.py     # UI for dualbot and answer rewriter
│── UI_ragbot.py      # UI for RAGbot
│── UI_styleandtonebot.py   # UI for Style and Tone detection and use to answer
│── requirements.txt  
│── README.md
│
│── # ── New: Document Ingestion Pipeline (feature/digital-media-master-rag)
│── ingest_pipeline.py              # Single entry point for document ingestion
│── dmm_pdf_parser.py               # Structure-aware PDF parser (§-based chunking)
│── dmm_web_scraper.py              # Heading-based web scraper with chunking
│── metadata_extractor.py           # LLM-based automatic metadata extraction
│── query_filter.py                 # Keyword-based query filter for ChromaDB
│── cli_demo.py                     # Terminal-based RAGBot demo
│── cleanupdb.py                    # Clears ChromaDB collection
```
---

## ⚡ Features

### 📚 RAGBot
- Local embeddings with **sentence-transformers**
- Vector search via **ChromaDB**
- Custom PDF chunking:      # Working on an updated chunking method
  - Split by `§` paragraphs  
  - Split by `Anlage X` sections  
  - Extract tables as Markdown
- Returns **answers with sources and used text passages**

### 🎭 Style Bots
- **AdaptiveResponder**:    # not used right now
  - Learns style from user’s question (casual, formal, list, emoji use, etc.)
  - Shapes chatbot responses accordingly
- **Flexible Style Detection**:
  - Uses an LLM to explicitly classify *style* + *tone*
  - Rewrites responses in matching style/tone
- **Dual Bot Pipeline**:
  - Bot1: friendly assistant  
  - Bot2: Shakespearean rewriter  

### 🖥 Gradio UIs
- **RAG App** → Ask document-based questions, get answers with sources
- **Dual Bot App** → User input → Bot1 answers → Bot2 rewrites in new style
- **Style Bot App** → User input analyzed → Answer in same style & tone

---

## 🔧 Installation

1. Clone repo:
   ```bash
   git clone https://gitlab.informatik.uni-bremen.de/comai/p2/P2-answer-and-stylegenerator.git
   cd P2-answer-and-stylegenerator

2. Open code editor
3. Install dependencies:
    ```bash
    pip install -r requirements.txt

## ⚙️ Configuration

Create a .env file in the project root:
```bash
CHATAI_API_KEY=your_api_key_here
BASE_URL="https://chat-ai.academiccloud.de/v1"
MODELS=meta-llama-3.1-8b-instruct,openai-gpt-oss-120b,llama-3.1-sauerkrautlm-70b-instruct
```

## 🚀 Usage
1. Run the RAGBot 
    ```bash
    python UI_ragbot.py

- Preload PDFs (docs/…)
- Ask Questions about "Prüfungsordnung FB3"
- Get answer with Sources

2. Run the Dual Bot (Bot1 → Bot2 rewrite)
    ```bash
    python UI_dualbot.py

- Ask Bot1 → Bot2 rewrites in Shakespearean style

3. Run the Style Detection Bot
    ```bash
    python UI_styleandtonebot.py

- Ask anything, bot analyzes your input style/tone and replies in same manner.

## 🛠 Tech Stack
```bash
Gradio - Web UI
ChromaDB - Vector database
SentenceTransformers - Local embeddings
PyPDF2 + pdfplumber - PDF parsing
BeautifulSoup4 + Requests - Web scraping
Tabulate - Pretty Markdown tables
OpenAI API - Model completions
```

---

## 🆕 Digital Media Master RAG Pipeline (`feature/digital-media-master-rag`)

This branch adds a complete **document ingestion and retrieval pipeline** for the Digital Media Master program.

### New Modules

| Module | Description |
|--------|-------------|
| `ingest_pipeline.py` | Single entry point for ingesting PDFs and URLs into ChromaDB |
| `dmm_pdf_parser.py` | Structure-aware PDF parser: §-based chunking for study regulations, page-based fallback for flyers |
| `dmm_web_scraper.py` | Heading-based web scraper: splits pages by h1–h4 tags with metadata enrichment |
| `metadata_extractor.py` | LLM-based automatic metadata extraction (degree, program, document type, year) |
| `query_filter.py` | Extracts ChromaDB where-filters from user queries via keyword matching |
| `cli_demo.py` | Interactive terminal demo for RAGBot with full metadata display |

### Key Changes to Existing Files

- **`ragbot.py`**: Added `add_documents_with_metadata()`, filtered vector search via `query_filter`, metadata return in `ask()`, switched to multilingual embedding model (`paraphrase-multilingual-MiniLM-L12-v2`)
- **`requirements.txt`**: Added `beautifulsoup4` and `requests`

### Ingestion Pipeline Usage
```bash
# Ingest all default sources (PDFs + URLs)
python ingest_pipeline.py

# Ingest a single PDF
python ingest_pipeline.py --pdf docs/AT-MPO-06-25_Lesefassung.pdf

# Ingest a single URL
python ingest_pipeline.py --url https://www.uni-bremen.de/en/studies/...

# Clear DB and re-ingest everything
python ingest_pipeline.py --rebuild
```

### CLI Demo
```bash
python cli_demo.py
```
- Interactive terminal Q&A
- Displays source document, page, section, program, degree, and document type tags