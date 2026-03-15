<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/react-18-61dafb?style=flat-square&logo=react&logoColor=white" alt="React" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Qdrant-vector%20db-dc382c?style=flat-square" alt="Qdrant" />
  <img src="https://img.shields.io/badge/OpenAI-GPT--4.1--mini-412991?style=flat-square&logo=openai&logoColor=white" alt="OpenAI" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License" />
</p>

<h1 align="center">🧠 DocIntel</h1>

<p align="center">
  <strong>Enterprise Document Intelligence System</strong><br/>
  Chat with your company documents stored in Google Drive — powered by RAG, real-time webhooks, and AI.
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#%EF%B8%8F-architecture">Architecture</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#%EF%B8%8F-configuration">Configuration</a> •
  <a href="#-api-reference">API Reference</a> •
  <a href="#-project-structure">Project Structure</a>
</p>

---

## ✨ Features

- **🔍 Intelligent Q&A** — Ask natural language questions about your company documents and get grounded, cited answers
- **📡 Real-Time Sync** — Google Drive webhooks automatically index new and updated files — no polling
- **📎 Multi-Format Parsing** — PDF, DOCX, Excel, CSV, plain text, and scanned documents (OCR)
- **🛡️ Anti-Hallucination** — Strict context-only responses with mandatory source citations
- **⚡ Streaming Responses** — Real-time token streaming for a ChatGPT-like experience
- **🔧 In-App Settings** — Configure Google credentials, API keys, and webhooks through the UI
- **🐳 One-Command Deploy** — Full Docker Compose setup with 5 services
- **📊 Live Dashboard** — Monitor sync status, indexed documents, and vector store health

---

## 🏗️ Architecture

```
┌──────────────┐     Webhook      ┌──────────────┐     Parse/Chunk     ┌──────────────┐
│              │ ──────────────▸  │              │ ──────────────────▸ │              │
│ Google Drive │                  │   FastAPI    │                     │   Celery     │
│              │ ◂──────────────  │   Backend    │ ◂────────────────── │   Worker     │
└──────────────┘   Push Notify    └──────┬───────┘     Embed & Store   └──────┬───────┘
                                         │                                     │
                                    Query│                              Vectors │
                                         │                                     │
                                  ┌──────▼───────┐                     ┌───────▼──────┐
                                  │              │ ◂──── Retrieve ──── │              │
                                  │  LLM (GPT)   │                     │   Qdrant     │
                                  │              │                     │  Vector DB   │
                                  └──────┬───────┘                     └──────────────┘
                                         │
                                  Stream │ Response
                                         │
                                  ┌──────▼───────┐
                                  │   React UI   │
                                  │   (Chat)     │
                                  └──────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|:------|:-----------|:--------|
| **Backend** | Python 3.11, FastAPI | REST API, webhook handling |
| **RAG Framework** | LlamaIndex | Chunking, retrieval orchestration |
| **Vector Database** | Qdrant (self-hosted) | Semantic search over embeddings |
| **Embeddings** | BAAI/bge-large-en-v1.5 | Document & query embedding |
| **LLM** | OpenAI GPT-4.1-mini | Answer generation with streaming |
| **Task Queue** | Celery + Redis | Async document processing |
| **Frontend** | React 18, Vite, TailwindCSS | Chat UI with live streaming |
| **Doc Parsing** | PyMuPDF, python-docx, pandas, Tesseract | Multi-format text extraction |

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- A Google Cloud service account with Drive API enabled ([setup guide ↓](#google-cloud-setup))
- An OpenAI API key (or a local [Ollama](https://ollama.ai) instance)

### 1. Clone & configure

```bash
git clone <your-repo-url>
cd docintel

cp .env.example .env
```

### 2. Start all services

```bash
docker compose up --build
```

This launches **5 containers**:

| Service | Port | Description |
|:--------|:-----|:------------|
| `backend` | `8000` | FastAPI server + Swagger docs |
| `worker` | — | Celery background processor |
| `frontend` | `3000` | React chat interface |
| `qdrant` | `6333` | Vector database |
| `redis` | `6379` | Message broker |

### 3. Open the app

Navigate to **[http://localhost:3000](http://localhost:3000)** and click **Settings** in the sidebar to configure your credentials.

---

## ⚙️ Configuration

All credentials can be configured through the **in-app Settings page** — no manual `.env` editing required.

### In-App Setup (recommended)

1. Click **Settings** in the sidebar
2. **Upload** your Google service account JSON file
3. **Enter** your OpenAI API key
4. **Set** the webhook endpoint URL ([see ngrok setup ↓](#webhook-setup-for-local-development))
5. **Set** the Drive folder ID to monitor
6. Click **Setup Watch Channel** to activate real-time sync
7. Click **Full Sync Now** to index existing documents

### Environment Variables

Alternatively, configure via `.env`:

```bash
# Required
OPENAI_API_KEY=sk-...
GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'
GOOGLE_DRIVE_FOLDER_ID=1a2b3c4d5e6f
WEBHOOK_URL=https://your-domain.ngrok-free.app

# Optional
API_KEY=my-secret-key        # Protect /chat endpoint
USE_OLLAMA=false             # Use local LLM instead of OpenAI
OLLAMA_MODEL=llama3          # Ollama model name
```

### Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable **Google Drive API**
3. Navigate to **IAM & Admin → Service Accounts**
4. Create a service account → Generate a JSON key
5. **Share your target Drive folder** with the service account email address

### Webhook Setup (for Local Development)

Google Drive webhooks require a publicly accessible HTTPS endpoint. Use [ngrok](https://ngrok.com/):

```bash
ngrok http 8000
```

Copy the HTTPS forwarding URL and paste it into the **Webhook URL** field in Settings.

> **Note:** Webhook channels expire after ~1 week. Re-run "Setup Watch Channel" to renew.

---

## 📋 API Reference

### Chat

```
POST /chat
```

Send a question and receive a streamed NDJSON response with source citations.

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"question": "What work did Rahul do in February?"}'
```

**Response** (streamed NDJSON):
```json
{"type": "text", "content": "Rahul prepared a marketing report"}
{"type": "text", "content": " for HDFC in February..."}
{"type": "sources", "content": [{"file_name": "report_feb.pdf", "drive_link": "..."}]}
```

### Documents

```
GET /documents          # List all indexed documents
GET /sync-status        # Indexing statistics
```

### Webhook

```
POST /drive/webhook     # Google Drive push notifications (automatic)
```

### Settings

```
GET  /settings                     # View config status (secrets masked)
POST /settings                     # Update config at runtime
POST /settings/upload-credentials  # Upload Google service account JSON
POST /settings/setup-webhook       # Create Drive watch channel
POST /settings/trigger-sync        # Full re-index all files
```

Full interactive docs available at **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 📁 Project Structure

```
docintel/
├── backend/
│   ├── api/                   # Route handlers
│   │   ├── chat.py            # POST /chat — streaming Q&A
│   │   ├── documents.py       # GET /documents, /sync-status
│   │   └── settings.py        # Runtime settings management
│   ├── config/
│   │   └── settings.py        # Pydantic settings + runtime config
│   ├── drive/
│   │   ├── client.py          # Google Drive API v3 client
│   │   └── webhook.py         # Push notification handler
│   ├── rag/
│   │   ├── retriever.py       # Qdrant vector operations
│   │   └── chat.py            # RAG pipeline + anti-hallucination
│   ├── services/
│   │   ├── parser.py          # Multi-format document parser
│   │   ├── chunker.py         # Token-based text chunking
│   │   └── embeddings.py      # BGE embedding generation
│   ├── workers/
│   │   ├── celery_app.py      # Celery configuration
│   │   └── tasks.py           # Background ingestion tasks
│   ├── main.py                # FastAPI application
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatArea.jsx       # Chat with streaming & suggestions
│   │   │   ├── Sidebar.jsx        # Status, documents, settings
│   │   │   ├── SettingsModal.jsx   # Credential management UI
│   │   │   ├── MessageBubble.jsx   # Message with markdown
│   │   │   └── SourceCard.jsx      # Clickable source citation
│   │   ├── services/
│   │   │   └── api.js             # Backend API client
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── nginx.conf
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔒 Security

- **API Key Auth** — Optional key-based authentication on the `/chat` endpoint
- **Secret Masking** — Settings API never exposes raw credentials, only status flags
- **No Local Storage** — Documents are never persisted locally; only embeddings are stored in Qdrant
- **Temp File Cleanup** — Downloaded files are deleted immediately after processing
- **Environment Isolation** — All secrets stored as env vars or encrypted runtime config

---

## 🧩 Local Development

Run individual services for development:

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Worker
cd backend
celery -A workers.celery_app worker --loglevel=info

# Frontend
cd frontend && npm install
npm run dev

# Qdrant (standalone)
docker run -p 6333:6333 qdrant/qdrant

# Redis (standalone)
docker run -p 6379:6379 redis:7-alpine
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
