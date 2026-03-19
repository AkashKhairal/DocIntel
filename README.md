<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/react-18-61dafb?style=flat-square&logo=react&logoColor=white" alt="React" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Qdrant-vector%20db-dc382c?style=flat-square" alt="Qdrant" />
  <img src="https://img.shields.io/badge/Cohere-Re--ranking-white?style=flat-square&logo=cohere&logoColor=black" alt="Cohere" />
  <img src="https://img.shields.io/badge/OpenAI-GPT--4.1--mini-412991?style=flat-square&logo=openai&logoColor=white" alt="OpenAI" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License" />
</p>

<h1 align="center">🧠 DocIntel Enterprise</h1>

<p align="center">
  <strong>The Ultimate Enterprise Document Intelligence System</strong><br/>
  Chat with your company documents stored in Google Drive — powered by Hybrid Search (Dense + Sparse), Cross-Encoder Re-ranking, and Real-time Webhooks.
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

- **🚀 Hybrid Search (V2)** — Combines semantic vector search (BGE-Large) with keyword-based BM25 search for industry-leading accuracy.
- **🎯 Cross-Encoder Re-ranking** — Uses Cohere's Re-rank API to sort the best context chunks before they reach the LLM.
- **🏢 Multi-Tenant SaaS Architecture** — Complete organization, tenant, and user management with secure data isolation.
- **🌍 Superadmin Dashboard** — Dedicated `master-frontend` for platform administrators to manage tenants, API keys, and usage analytics.
- **📂 Enterprise Document Hub** — Dedicated management dashboard to view, re-sync, or delete indexed documents.
- **📡 Real-Time Sync** — Google Drive webhooks automatically index new and updated files — zero latency.
- **📎 Multi-Format Parsing** — PDF, DOCX, Excel, CSV, plain text, and scanned documents (OCR).
- **🛡️ Anti-Hallucination** — Strict context-only responses with mandatory source citations and source preview.
- **⚡ Streaming Responses** — Real-time token streaming supporting OpenAI, Google Gemini, and Ollama.
- **📊 Progress Analytics** — Real-time floating widget tracks background indexing and sync status.

---

## 🏗️ Architecture

```
┌──────────────┐     Webhook      ┌──────────────┐     Parse/Chunk     ┌──────────────┐
│              │ ──────────────▸  │              │ ──────────────────▸ │              │
│ Google Drive │                  │   FastAPI    │                     │   Celery     │
│              │ ◂──────────────  │   Backend    │ ◂────────────────── │   Worker     │
└──────────────┘   Push Notify    └──────┬───────┘     Hybrid Embed    └──────┬───────┘
                                         │             (Dense + BM25)         │
            ┌────────────────────────────┤                                    │
            │                      Query │                             Vectors│
     ┌──────▼───────┐             ┌──────▼───────┐                     ┌──────▼───────┐
     │  PostgreSQL  │             │   Cohere     │ ◂── Hybrid Retrieval ──┤              │
     │ (Tenants/DB) │             │  Re-ranker   │                     │   Qdrant     │
     └──────────────┘             └──────┬───────┘                     │  Vector DB   │
                                         │                             └──────────────┘
                                  ┌──────▼───────┐
                                  │  LLM (Gen)   │
                                  └──────┬───────┘
                                         │
┌────────────────┐                Stream │ Response
│ Superadmin UI  │ ◂──(Admin Api)────────┤
│master-frontend │                ┌──────▼───────┐
└────────────────┘                │   React UI   │
                                  │(Chat + Hub)  │
                                  └──────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|:------|:-----------|:--------|
| **Backend** | Python 3.11, FastAPI | REST API, webhook handling, Multi-tenant logic |
| **Relational DB**| PostgreSQL + Alembic | Organizations, Tenants, Users, Usage Logs, and Auth DB |
| **Hybrid Retrieval**| FastEmbed (BM25) | Sparse vector generation for keyword search |
| **Re-ranking** | Cohere Re-rank v3 | Cross-encoder relevance sorting |
| **Vector Database** | Qdrant | Hybrid (Dense + Sparse) vector storage (Tenant-isolated) |
| **LLM** | OpenAI / Gemini / Ollama | Multi-provider answer generation |
| **Task Queue** | Celery + Redis | Distributed document processing |
| **Frontend** | React 18, TailwindCSS, Vite | High-density enterprise dashboard and Admin panel |
| **Doc Parsing** | Tesseract OCR + PyMuPDF | Complex document extraction |

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- PostgreSQL (or via Docker)
- A Google Cloud service account with Drive API enabled ([setup guide ↓](#google-cloud-setup))
- API Keys: OpenAI, Gemini, or Cohere (for re-ranking)

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

This launches **6 containers**:

| Service | Port | Description |
|:--------|:-----|:------------|
| `backend` | `8000` | FastAPI server + Swagger docs + Alembic Migrations |
| `worker` | — | Celery background processor |
| `frontend` | `3000` | React chat interface (End-user facing) |
| `master-frontend`| `3100` | React Superadmin panel for tenant management |
| `qdrant` | `6333` | Vector database |
| `redis` | `6379` | Message broker |

*(Note: Ensure your PostgreSQL database matches the connection string in your `.env` to run Alembic migrations automatically or manually via `alembic upgrade head`)*

### 3. Setup in the UI

Navigate to **[http://localhost:3000](http://localhost:3000)** (End user):
1.  Open **Settings**
2.  Upload your Google Service Account JSON
3.  Paste your OpenAI/Gemini/Cohere keys
4.  Enter your webhook URL (use `ngrok http 8000` for local dev)

Navigate to **[http://localhost:3100](http://localhost:3100)** (Admin):
- Manage System Tenants, Organizations, Users, and monitor LLM token Usage Logs.

---

## ⚙️ Configuration

All credentials can be configured through the **in-app Settings page** — no manual `.env` editing required.

### In-App Setup (recommended)

1. Click **Settings** in the sidebar
2. **Connect** Google Drive via OAuth (new flow) instead of service account JSON
3. **On connect callback**, your browser is redirected to `/googledrive-callback` in frontend
4. **Enter** your OpenAI or Gemini or Cohere key
5. **Set** the webhook endpoint URL ([see ngrok setup ↓](#webhook-setup-for-local-development))
6. **Set** the Drive folder ID to monitor
7. Click **Setup Watch Channel** to activate real-time sync
8. Click **Full Sync Now** to index existing documents

### Environment Variables (.env)

| Variable | Required | Description |
|:---------|:---------|:------------|
| `DATABASE_URL` | Yes | Postgres DB connection string (e.g. `postgresql://user:pass@localhost/db`) |
| `OPENAI_API_KEY` | Optional* | API key for OpenAI models |
| `GEMINI_API_KEY` | Optional* | API key for Google Gemini models |
| `COHERE_API_KEY` | Optional | API key for high-accuracy re-ranking |
| `GOOGLE_CLIENT_ID` | Yes (OAuth) | Google OAuth client ID (for integrations) |
| `GOOGLE_CLIENT_SECRET` | Yes (OAuth) | Google OAuth client secret |
| `GOOGLE_OAUTH_REDIRECT_URI` | Yes | OAuth callback URL (e.g. https://app.example.com/integrations/google/callback) |
| `GOOGLE_DRIVE_FOLDER_ID` | Yes | Target folder ID to watch |
| `WEBHOOK_URL` | Yes | Public HTTPS URL for webhooks |
| `USE_OLLAMA` | No | Set to `true` for local-only LLM |

*\*At least one LLM provider (OpenAI, Gemini, or Ollama) must be configured.*

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

### Multi-Tenant Admin API

```
GET /admin/tenants            # Manage isolated tenants
GET /admin/organizations      # Manage orgs within the system
GET /admin/users              # Manage users and RBAC
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
│   ├── alembic/               # PostgreSQL DB migrations
│   ├── app/                   # New SaaS Application Logic
│   │   ├── api/               # Multi-tenant API routes (users, orgranizations, admin)
│   │   ├── auth/              # JWT Authenication
│   │   ├── core/              # Global config handlers
│   │   ├── db/                # PostgreSQL Session management
│   │   └── models/            # SQLAlchemy Database models (Tenant, User, etc)
│   ├── api/                   # Legacy/Chat Route handlers
│   │   ├── chat.py            # POST /chat — streaming Q&A
│   │   ├── documents.py       # GET /documents, /sync-status
│   │   └── settings.py        # Runtime settings management
│   ├── rag/                   # RAG Engine
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
│   └── alembic.ini
├── frontend/                  # End-User Chat/Dashboard
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── nginx.conf
│   └── Dockerfile
├── master-frontend/           # Superadmin panel
│   ├── src/
│   │   ├── pages/             # Tenant/User/Organization management pages
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── Dockerfile
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
