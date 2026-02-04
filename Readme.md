# SupportAI

A powerful Retrieval-Augmented Generation (RAG) system for automated customer support. Ingest knowledge from websites or PDF documents, store it in a vector database, and answer user questions with context-aware AI responses.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [How It Works](#how-it-works)

---

## Overview

SupportAI is an intelligent question-answering system designed to automate customer support workflows. It allows you to:

1. **Ingest knowledge** from websites (via web scraping) or PDF documents
2. **Store and index** content using vector embeddings for semantic search
3. **Answer questions** using a local LLM with retrieved context
4. **Notify support teams** via email when questions cannot be answered

The system uses a strict retrieval-based approach, ensuring answers are grounded in the provided knowledge base without hallucination.

---

## Features

- **Multi-source Ingestion**: Scrape websites using Firecrawl or upload PDF documents
- **Intelligent Chunking**: Smart text splitting with overlap for better context preservation
- **Vector Storage**: Qdrant vector database for fast semantic search
- **Query Rewriting**: Optimizes user queries for better retrieval
- **Re-ranking**: LLM-powered chunk re-ranking for improved relevance
- **Conversation History**: Maintains context across multi-turn conversations
- **Email Notifications**: Alerts support team when answers cannot be found
- **REST API**: Clean FastAPI-based API for easy integration
- **Local LLM**: Uses Ollama for privacy-focused, local inference

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SupportAI Architecture                         │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │   Client     │
                              │  (API Call)  │
                              └──────┬───────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │   FastAPI    │
                              │   Server     │
                              └──────┬───────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
           ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
           │ /ingest/url  │  │ /ingest/pdf  │  │    /ask      │
           └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
                  │                 │                 │
                  ▼                 ▼                 ▼
    ┌─────────────────────────────────────┐   ┌─────────────────┐
    │        Ingestion Pipeline           │   │   QA Pipeline   │
    │         (LangGraph)                 │   │                 │
    │  ┌─────────┐    ┌─────────────┐     │   │ ┌─────────────┐ │
    │  │ Scraper │    │ PDF Loader  │     │   │ │Query Rewrite│ │
    │  │(Firecrawl)   │  (PyMuPDF)  │     │   │ └──────┬──────┘ │
    │  └────┬────┘    └──────┬──────┘     │   │        │        │
    │       │                │            │   │        ▼        │
    │       ▼                │            │   │ ┌─────────────┐ │
    │  ┌─────────┐    ┌──────             │   │ │  Retriever  │ │
    │  │Analyzer │    │                   │   │ │  (Qdrant)   │ │
    │  │ (LLM)   │    │                   │   │ └──────┬──────┘ │
    │  └────┬────┘    │                   │   │        │        │
    │       │         │                   │   │        ▼        │
    │       ▼         ▼                   │   │ ┌─────────────┐ │
    │  ┌─────────────────────┐            │   │ │  Re-ranker  │ │
    │  │      Chunker        │            │   │ │   (LLM)     │ │
    │  │(RecursiveTextSplit) │            │   │ └──────┬──────┘ │
    │  └──────────┬──────────┘            │   │        │        │
    │             │                       │   │        ▼        │
    │             ▼                       │   │ ┌─────────────┐ │
    │  ┌─────────────────────┐            │   │ │   Answer    │ │
    │  │   Vector Storage    │◄─────-─────┼───│ │Generation   │ │
    │  │     (Qdrant)        │            │   │ │   (LLM)     │ │
    │  └─────────────────────┘            │   │ └──────┬──────┘ │
    └─────────────────────────────────────┘   │        │        │
                                              │        ▼        │
                                              │ ┌─────────────┐ │
                                              │ │   Email     │ │
                                              │ │ Notifier    │ │
                                              │ │(if no answer) │
                                              │ └─────────────┘ │
                                              └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            External Services                                │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│   Firecrawl     │     Qdrant      │     Ollama      │    SMTP Server        │
│  (Web Scraping) │ (Vector Store)  │  (Local LLM)    │   (Email Alerts)      │
└─────────────────┴─────────────────┴─────────────────┴───────────────────────┘
```

### Data Flow

1. **Ingestion Flow**: URL/PDF → Scrape/Load → Analyze → Chunk → Embed → Store in Qdrant
2. **Query Flow**: Question → Rewrite → Retrieve → Re-rank → Generate Answer → (Notify if no answer)

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Framework** | FastAPI |
| **Workflow Orchestration** | LangGraph |
| **LLM Framework** | LangChain |
| **Local LLM** | Ollama (llama3.1:8b) |
| **Embeddings** | HuggingFace (all-MiniLM-L6-v2) |
| **Vector Database** | Qdrant |
| **Web Scraping** | Firecrawl |
| **PDF Processing** | PyMuPDF |
| **Notifications** | SMTP (Email) |

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+**
- **Ollama** - For running local LLM
- **Qdrant** - Vector database (can run via Docker)
- **Firecrawl API Key** - For web scraping (get from [firecrawl.dev](https://firecrawl.dev))

### Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Pull the required model
ollama pull model_name
```

### Start Qdrant (Docker)

```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

Or install Qdrant locally following [official docs](https://qdrant.tech/documentation/quick-start/).

---

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/Psanjay-15/SupportAi.git
cd SupportAi
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration (see [Configuration](#configuration)).

---

## Configuration

Create a `.env` file in the project root with the following variables:

```env
# Firecrawl (Web Scraping)
FIRE_CRAWL_API_KEY=your_firecrawl_api_key

# Qdrant (Vector Database)
QDRANT_HOST=localhost
QDRANT_PORT=6333

# LLM Settings
LLM_MODEL=llama3.1:8b
LLM_TEMPERATURE=0

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Email Notifications (for unanswered questions)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENT=support_team@example.com
EMAIL_SENDER_NAME=SupportAI
```

### Configuration Details

| Variable | Description | Default |
|----------|-------------|---------|
| `FIRE_CRAWL_API_KEY` | API key for Firecrawl web scraping service | Required |
| `QDRANT_HOST` | Qdrant server hostname | `localhost` |
| `QDRANT_PORT` | Qdrant server port | `6333` |
| `LLM_MODEL` | Ollama model name |
| `LLM_TEMPERATURE` | LLM temperature (0 = deterministic) | `0` |
| `EMBEDDING_MODEL` | HuggingFace embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| `EMAIL_*` | SMTP settings for email notifications | Optional |

### Gmail App Password Setup

If using Gmail for notifications:
1. Enable 2-Factor Authentication on your Google account
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Generate a new app password for "Mail"
4. Use this password as `EMAIL_PASSWORD`

---

## Running the Application

1. **Ensure Qdrant is running**

```bash
docker run -p 6333:6333 qdrant/qdrant
```

2. **Ensure Ollama is running with the model**

```bash
ollama serve
# In another terminal:
ollama run model_name
```

3. **Start the FastAPI server**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## How It Works

### 1. Ingestion Pipeline (LangGraph)

The ingestion pipeline is built using LangGraph for orchestrating the workflow:

```
START → Router → [URL Path OR PDF Path] → Chunker → Vector Storage → END
              │
              ├─► URL: Scraper → Analyzer → Chunk Web → Store
              │
              └─► PDF: PDF Loader → Chunk PDF → Store
```

- **Scraper**: Uses Firecrawl to crawl websites 
- **Analyzer**: LLM analyzes scraped content to extract metadata
- **PDF Loader**: Extracts text from PDF using PyMuPDF
- **Chunker**: Splits content into 400-char chunks with 200-char overlap
- **Storage**: Embeds chunks and stores in Qdrant

### 2. Question Answering Pipeline

```
Question → Query Rewrite → Vector Search → Re-rank → Generate Answer
                                                          │
                                                          ├─► Answer Found → Return
                                                          │
                                                          └─► No Answer → Email Notification
```

- **Query Rewrite**: Optimizes the question for better retrieval
- **Vector Search**: Finds top-K relevant chunks from Qdrant
- **Re-ranking**: LLM re-orders chunks by relevance
- **Answer Generation**: Strict RAG with only context-based answers
- **Fallback**: Sends email notification when no answer is found

### 3. Strict RAG Approach

The system follows a strict retrieval-based approach:
- Answers ONLY from provided context
- No external knowledge or assumptions
- Returns "No answer found, our team will reach out to you" when information is unavailable
- Triggers email notification for human follow-up

---

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn app.main:app --reload
```

## Acknowledgments

- [LangChain](https://langchain.com/) - LLM application framework
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Workflow orchestration
- [Ollama](https://ollama.ai/) - Local LLM inference
- [Qdrant](https://qdrant.tech/) - Vector database
- [Firecrawl](https://firecrawl.dev/) - Web scraping API
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
