# 🎓 Digital Media RAG

> **ComAI Project** — University of Bremen & Hochschule für Künste Bremen

An AI-powered **Retrieval-Augmented Generation (RAG)** platform designed for university study regulations, featuring adaptive style engines, multilingual support (German & English), and a production-ready FastAPI backend.

---

## 📋 Overview

Digital Media RAG brings together two complementary systems:

| Module | Description |
|--------|-------------|
| **P2-answer-and-stylegenerator** | RAG engine with structure-aware document parsing, vector retrieval, adaptive style/tone adaptation, and interactive Gradio UIs |
| **p2-backend-server** | Production FastAPI server with OpenAI-compatible streaming API, multimodal support, session management, and stylistic persona rewriting |

---

## ✨ Key Features

- 📄 **Structure-aware PDF parsing** — Automatically detects legal paragraph structures (`§` sections, `Anlage` appendices) and extracts tables as Markdown
- 🌐 **Web scraping** — Heading-based HTML chunking (h1–h4) for clean content ingestion
- 🔍 **Smart retrieval** — ChromaDB vector search with automatic metadata filtering (degree, program, document type)
- 🤖 **Adaptive style engine** — Mirrors user's communication style using statistical EWMA analysis (tone, brevity, structure, emoji)
- 🎭 **Persona-based rewriting** — Multiple styles: board, joyful, detailed, casual, professional
- ✏️ **Stylistic variators** — Synonym replacement, hedging, metaphor, and style rewriting
- 🖼️ **Multimodal support** — Base64 image processing via vision models
- 🔐 **Security** — Frontend key authentication and Origin header verification
- 📡 **OpenAI-compatible API** — Full SSE streaming, compatible with Vercel AI SDK

---

## 🛠️ Tech Stack

| Domain | Technology |
|--------|-----------|
| Backend API | FastAPI, Uvicorn |
| Vector Database | ChromaDB |
| Embeddings | Sentence-Transformers (`paraphrase-multilingual-MiniLM-L12-v2`) |
| LLM Inference | OpenAI SDK → AcademicCloud ChatAI |
| PDF Processing | pdfplumber, PyPDF2, tabulate |
| Web Scraping | BeautifulSoup4, Requests |
| Database | SQLAlchemy, SQLite |
| Frontend UIs | Gradio |
| Deployment | Dokku, GitLab CI |

**Supported Models:** LLaMA 3.1/3.3, Mistral Large (Vision), DeepSeek R1, Gemma 3, Qwen 3

---

## 📁 Project Structure

```
Digital-Media-RAG/
├── P2-answer-and-stylegenerator/       # RAG Pipeline & Style Engine
│   ├── docs/                           # Study regulation PDFs
│   ├── ingest_pipeline.py              # Document & URL ingestion CLI
│   ├── dmm_pdf_parser.py              # Structure-aware PDF parser
│   ├── dmm_web_scraper.py             # Web scraper with heading-based chunking
│   ├── metadata_extractor.py          # LLM-based metadata extraction
│   ├── ragbot.py                      # RAG core (retrieval + citation)
│   ├── query_filter.py                # Metadata filter extraction
│   ├── adaptive_style.py              # EWMA-based style mirroring
│   ├── flexible_style_detection.py    # LLM style/tone classifier
│   ├── stylebot.py                    # Persona-based rewriter
│   ├── cli_demo.py                    # Terminal demo
│   ├── UI_ragbot.py                   # Gradio RAG chatbot UI
│   ├── UI_dualbot.py                  # Gradio dual-bot UI
│   └── UI_styleandtonebot.py          # Gradio style detection UI
│
└── p2-backend-server/                  # FastAPI Production Server
    ├── Chatbots/                       # LLM generators & variators
    ├── Core/                           # Bot selection, config, chat history
    ├── Security/                       # Auth, ORM models, database
    └── main.py                         # FastAPI app with SSE streaming
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- AcademicCloud ChatAI API key (or compatible OpenAI API)

### Installation

```bash
# Clone the repository
git clone https://github.com/Huveee/Digital-Media-RAG.git
cd Digital-Media-RAG

# Create & activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1      # Windows
# source venv/bin/activate       # Linux/macOS

# Install dependencies
pip install -r P2-answer-and-stylegenerator/requirements.txt
pip install -r p2-backend-server/requirements.txt
```

### Configuration

Create `.env` files in each module:

**`P2-answer-and-stylegenerator/.env`**
```env
CHATAI_API_KEY=your_api_key
BASE_URL=https://chat-ai.academiccloud.de/v1
MODEL=meta-llama-3.1-8b-instruct
```

**`p2-backend-server/.env`** (see `.env.example` for full template)
```env
CHATAI_API_KEY=your_api_key
BASE_URL=https://chat-ai.academiccloud.de/v1
DEFAULT_CHATAI_MODEL=meta-llama-3.1-8b-rag
FRONTEND_SECRET_KEY=your_secret_key
```

---

## 💻 Usage

### RAG Pipeline

```bash
cd P2-answer-and-stylegenerator

# Ingest documents into ChromaDB
python ingest_pipeline.py              # All default sources
python ingest_pipeline.py --rebuild    # Rebuild from scratch
python ingest_pipeline.py --pdf docs/AT-MPO-06-25_Lesefassung.pdf  # Single PDF

# Run interactive demos
python cli_demo.py                     # Terminal demo
python UI_ragbot.py                    # Gradio RAG chatbot
python UI_dualbot.py                   # Dual-bot rewriting
python UI_styleandtonebot.py           # Style detection & mirroring
```

### Backend Server

```bash
cd p2-backend-server

# Start with auto-reload
uvicorn main:app --reload --port 8000
```

- 📖 API Docs: `http://localhost:8000/docs`
- 💬 Chat Endpoint: `POST /v1/chat/completions` (requires `X-Frontend-Key` header)

---

## 🏫 About

This project is part of the **ComAI Research Project** investigating the design and socio-material constitution of conversational AI interfaces in educational domains.

- **University of Bremen** — Faculty 3: Computer Science
- **Hochschule für Künste Bremen** — Digital Media Program

---

## 📄 License

This project is developed for academic research purposes at the University of Bremen.
