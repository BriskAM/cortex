# Cortex — RAG-Based Codebase Q&A Companion

Cortex is an AI-powered developer tool that enables you to connect any GitHub repository and chat with it in natural language. Cortex indexes not just the source code, but the full engineering history (pull requests, merge descriptions, and diff summaries), answering both **what** the code does and **why** it was written.

Cortex features a frictionless URL routing system: navigate to `localhost:5173/:owner/:repo` (e.g. `localhost:5173/BriskAM/cortex`), and Cortex will automatically verify, resolve, and index the repository.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Vue 3 Frontend                     │
│  /:owner/:repo  /:owner/:repo/pr/:number  /dashboard    │
└────────────────────┬────────────────────────────────────┘
                     │ Axios (REST) + EventSource (SSE)
┌────────────────────▼────────────────────────────────────┐
│                    Flask API Gateway                    │
│  /auth  /gh/:owner/:repo  /gh/:owner/:repo/pr/:number   │
│  /chat  /status                                          │
└──────┬──────────────┬──────────────────┬────────────────┘
       │              │                  │
┌──────▼──────┐ ┌─────▼──────┐ ┌────────▼───────┐
│  PostgreSQL  │ │   Redis    │ │   ChromaDB     │
│  (or SQLite) │ │Task Queue  │ │ Vector Store   │
│  Users,Repos │ │Job Status  │ │ Code + PR Index│
└─────────────┘ └─────┬──────┘ └────────────────┘
                      │
              ┌───────▼────────┐
              │  Celery Worker  │
              │                │
              │ 1. Fetch Tree  │
              │ 2. Parse Code  │
              │ 3. Fetch PRs   │
              │ 4. Embed All   │
              │ 5. Store Chroma│
              └───────┬────────┘
                      │
          ┌───────────┴───────────┐
          │                       │
   ┌──────▼──────┐       ┌────────▼──────┐
   │  GitHub API  │       │   Google AI   │
   │  File Trees  │       │ gemini-embed  │
   │  PRs + Diffs │       │  gemma-4-26b  │
   └─────────────┘       └───────────────┘
```

---

## Technology Stack

| Component | Choice |
|---|---|
| **Frontend** | Vue 3 + Pinia + Vue Router 4 + Axios |
| **Styling** | Vanilla CSS (Rigid Geometry, Technical Precision Dark Theme) |
| **Markdown** | `marked` (rendered dynamically with styled headers/lists/inline code) |
| **Syntax Highlighting** | `highlight.js` (GitHub Dark Theme for cited code blocks) |
| **Backend** | Flask + Flask-Security-Too (JWT Token Authentication) |
| **Database** | SQLite (Dev) / PostgreSQL (Prod) + SQLAlchemy ORM |
| **Task Queue** | Celery + Redis |
| **Vector DB** | ChromaDB (Persistent client, cosine distance metric) |
| **Code Parser** | `tree-sitter` (AST-aware function/class boundary chunking) |
| **Embeddings** | `gemini-embedding-001` via `google-genai` (1536-dim) |
| **LLM Generator** | `gemma-4-26b-a4b-it` via Gemini API (with thinking config retry fallbacks) |
| **Streaming** | Server-Sent Events (SSE) typewriter-style stream client |

---

## Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Redis Server
- GitHub CLI (`gh`) logged in, or a Personal Access Token

### 1. Configure Environment Variables
Copy the env template in the workspace root and configure your `GOOGLE_API_KEY`:
```bash
cp .env.example .env
```
*(If `GITHUB_TOKEN` is left blank, Cortex will automatically fallback to your active `gh auth token` session).*

To enable **Sign In with GitHub**, register a new OAuth Application in your GitHub Developer Settings with the Authorization Callback URL set to `http://localhost:5173/auth/callback/github` and configure:
```env
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
```

### 2. Start Redis
```bash
redis-server --daemonize yes
```

### 3. Setup Backend
```bash
cd backend
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations / setup tables
# (Dev sqlite database auto-generates on server start)
```

Start the Celery worker and Flask API server in separate shells:
```bash
# Terminal 1: Celery task processor (run from workspace root)
PYTHONPATH=. backend/.venv/bin/celery -A backend.celery_worker.celery worker --loglevel=info

# Terminal 2: Flask web server (run from workspace root)
PORT=5001 PYTHONPATH=. backend/.venv/bin/python backend/run.py
```

### 4. Setup Frontend
```bash
cd frontend
# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
Navigate to `http://localhost:5173/` in your browser. All `/api` requests are proxied automatically to `http://127.0.0.1:5001`.

---

## Production Deployment (Docker Compose)

Cortex is containerized and ready to deploy via Docker Compose. Ensure you have your `GOOGLE_API_KEY` and `GITHUB_TOKEN` exported on your host environment.

Start the multi-container stack (PostgreSQL + Redis + Flask + Celery Worker):
```bash
export GOOGLE_API_KEY="your_api_key_here"
export GITHUB_TOKEN="your_pat_here"

docker compose up --build -d
```

---

## API Documentation

### Auth — `/api/auth/`
- `POST /register`: Registers a new user session.
- `POST /login`: Validates email/password and returns a JWT token.
- `POST /logout`: Invalidates the current user context.
- `GET /me`: Returns details of the logged-in user.

### Dynamic Repo Registry — `/api/gh/`
- `GET /api/gh/:owner/:repo`: Resolves a repo by name. Triggers Celery indexing task if first time seen. Returns indexing job status and `repo_id`.
- `GET /api/gh/:owner/:repo/pr/:number`: Resolves PR details and file changes.

### Repositories — `/api/repos/`
- `GET /`: Lists indexed repositories.
- `DELETE /:id`: Deletes repository metadata, chat history, and both associated ChromaDB vector collections.
- `POST /:id/reindex`: Force re-triggers the full indexing Celery task.

### Conversational Chat — `/api/chat/`
- `GET /sessions?repo_id=N`: Lists previous sessions for a repository.
- `POST /sessions`: Creates a new session (`scope="repo"` or `scope="pr"`).
- `GET /sessions/:id`: Retrieves full message history.
- `POST /sessions/:id/message?q=query`: Sends user message and returns streamed tokens (SSE format: `data: {"token": "..."}\n\n`). Closes with `data: {"done": true, "sources": [...]}\n\n` containing citations.
- `DELETE /sessions/:id`: Deletes a session.

### Job Status
- `GET /api/status/job/:job_id`: Returns progress details (`state`, `stage`, `progress %`, `error`).

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
