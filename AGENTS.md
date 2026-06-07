# Cortex — AGENTS.md

AI-powered codebase Q&A tool. Users navigate to `cortex.dev/:owner/:repo`, Cortex auto-indexes the GitHub repo (code + last 100 PRs), and they can chat with it in natural language. Answers cite exact file+line for code and PR number+title for history.

---

## Project Structure

```
cortex/
├── backend/
│   ├── app/
│   │   ├── __init__.py              # App factory (create_app)
│   │   ├── config.py                # Config classes: DevConfig, ProdConfig
│   │   ├── extensions.py            # db, security, celery — initialized here, bound in create_app
│   │   ├── models/
│   │   │   ├── user.py              # User, Role (Flask-Security)
│   │   │   ├── repo.py              # IndexedRepo
│   │   │   └── chat.py              # ChatSession, Message
│   │   ├── api/
│   │   │   ├── auth.py              # /api/auth/*
│   │   │   ├── gh.py                # /api/gh/:owner/:repo and /api/gh/:owner/:repo/pr/:num
│   │   │   ├── repos.py             # /api/repos/*
│   │   │   ├── chat.py              # /api/chat/*
│   │   │   └── status.py            # /api/status/*
│   │   ├── services/
│   │   │   ├── github_service.py    # GitHub API: file tree, contents, PRs, diffs
│   │   │   ├── indexer_service.py   # File filtering, tree-sitter chunking
│   │   │   ├── pr_service.py        # PR fetching, bot filtering, chunk building
│   │   │   ├── chroma_service.py    # ChromaDB read/write for both collections
│   │   │   └── rag_service.py       # Embed query → dual search → rerank → prompt → stream
│   │   └── tasks/
│   │       └── indexing_tasks.py    # Celery task: index_repository(repo_id)
│   ├── migrations/
│   ├── tests/
│   ├── celery_worker.py
│   ├── run.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── router/index.js          # Dynamic routes (see Routing section)
│   │   ├── stores/
│   │   │   ├── auth.js              # Pinia: user, token, login/logout
│   │   │   ├── repos.js             # Pinia: repo state, indexing status
│   │   │   └── chat.js              # Pinia: sessions, messages, streaming
│   │   ├── views/
│   │   │   ├── LandingView.vue      # /
│   │   │   ├── RepoView.vue         # /:owner/:repo — three-state (indexing/ready/404)
│   │   │   ├── PrView.vue           # /:owner/:repo/pr/:number
│   │   │   └── DashboardView.vue    # /dashboard
│   │   ├── components/
│   │   │   ├── ChatWindow.vue
│   │   │   ├── MessageBubble.vue
│   │   │   ├── SourceDrawer.vue     # Two tabs: Code + PRs
│   │   │   ├── IndexingProgress.vue # Two-stage bar
│   │   │   ├── RepoCard.vue
│   │   │   └── RepoNotFound.vue
│   │   └── api/axios.js             # Axios instance with JWT interceptor
│   └── package.json
├── docker-compose.yml
└── .env.example
```

---

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | Flask + Flask-Security-Too |
| ORM | SQLAlchemy + Flask-Migrate |
| Database | PostgreSQL |
| Task queue | Celery + Redis |
| Vector store | ChromaDB (local persist) |
| Embeddings | `gemini-embedding-001` via `google-genai` |
| LLM | `gemma-4-26b-a4b-it` via Gemini API |
| Code parsing | `tree-sitter` (AST-aware chunking) |
| GitHub | `PyGithub` |
| Frontend | Vue 3 + Pinia + Vue Router 4 |
| HTTP | Axios |
| Streaming | Server-Sent Events (SSE) |
| Container | Docker + docker-compose |

Single `GOOGLE_API_KEY` covers both embeddings and LLM.

---

## Environment Variables

```env
# Flask
FLASK_SECRET_KEY=
DATABASE_URL=postgresql://user:pass@localhost:5432/cortex
SECURITY_PASSWORD_SALT=

# Redis + Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Google AI (embeddings + LLM)
GOOGLE_API_KEY=

# GitHub
GITHUB_TOKEN=                    # PAT with read:repo scope

# Embedding
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=1536        # MRL truncated from 3072

# LLM
LLM_MODEL=gemma-4-26b-a4b-it    # or gemma-4-31b-it

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_data
```

---

## Database Models

### User
```python
class User(db.Model, UserMixin):
    id: int
    email: str
    password: str
    active: bool
    github_token: str        # encrypted OAuth token
    fs_uniquifier: str
    roles: relationship(Role)
```

### IndexedRepo
```python
class IndexedRepo(db.Model):
    id: int
    user_id: int             # FK → User, nullable (public repos have no owner)
    github_url: str          # https://github.com/BriskAM/resume
    owner: str               # BriskAM
    repo_name: str           # resume
    branch: str              # default: main
    status: str              # pending | indexing | ready | failed
    is_public: bool          # True = auto-indexed via URL, no login needed
    chroma_collection: str   # collection name prefix in ChromaDB
    file_count: int
    chunk_count: int
    pr_count: int
    last_indexed_at: datetime
    created_at: datetime
```

### ChatSession
```python
class ChatSession(db.Model):
    id: int
    user_id: int             # FK → User
    repo_id: int             # FK → IndexedRepo
    scope: str               # "repo" | "pr"
    pr_number: int           # set if scope == "pr"
    title: str               # auto-generated from first message
    created_at: datetime
```

### Message
```python
class Message(db.Model):
    id: int
    session_id: int          # FK → ChatSession
    role: str                # "user" | "assistant"
    content: str
    sources: JSON            # list of source objects (see Sources section)
    created_at: datetime
```

**Sources JSON shape:**
```json
[
  {"type": "code", "file": "auth/jwt.py", "start_line": 42, "end_line": 67, "snippet": "..."},
  {"type": "pr",   "pr_number": 341, "pr_title": "feat: switch to JWT", "pr_url": "...", "pr_author": "rishi-dev", "merged_at": "2024-11-12"}
]
```

---

## API Endpoints

### Auth — `/api/auth/`
```
POST   /register
POST   /login                → { token, user }
POST   /logout
GET    /me
```

### Dynamic Repo Resolution — `/api/gh/` (core feature)
```
GET    /api/gh/:owner/:repo
  → NOT SEEN:  { status: "indexing", job_id }   (triggers Celery)
  → INDEXING:  { status: "indexing", progress: 42, job_id }
  → READY:     { status: "ready", repo_id, file_count, chunk_count, pr_count }
  → NOT FOUND: { status: "not_found" }

GET    /api/gh/:owner/:repo/pr/:number
  → { status, pr_number, pr_title, pr_body, pr_author, merged_at, files_changed[] }
```

### Repos — `/api/repos/`
```
GET    /                     → list user's saved repos
DELETE /:id                  → delete repo + both chroma collections
POST   /:id/reindex          → re-trigger index_repository Celery task
```

### Chat — `/api/chat/`
```
GET    /sessions                        → list sessions (query param: repo_id)
POST   /sessions                        → create session { repo_id, scope?, pr_number? }
GET    /sessions/:id                    → session + all messages
POST   /sessions/:id/message            → SSE stream: send message, get streamed answer
DELETE /sessions/:id
```

### Status
```
GET    /api/status/job/:job_id          → { status, progress, stage, error? }
```

---

## Celery Indexing Pipeline

**Task:** `index_repository(repo_id)`

```
1. FETCH FILES
   → Use GitHub API (PyGithub) to get file tree
   → No git clone needed — use contents API
   → Filter: skip node_modules, .git, dist, __pycache__, lock files, binaries
   → Keep: .py .js .ts .vue .jsx .tsx .java .go .rs .md .sql

2. CHUNK CODE (tree-sitter)
   → Chunk by function/class boundaries for supported languages
   → Sliding window (512 tokens, 50 overlap) for large files
   → Single chunk for files < 200 tokens
   → Metadata per chunk: { file_path, start_line, end_line, language }

3. FETCH PRs
   → Get last 100 merged PRs via GitHub API (sorted merged_at desc)
   → Skip bots: filter where pr.user.login contains "bot", "dependabot", "renovate"
   → Per PR, build one text chunk:
       "PR #N: {title}\nAuthor: {login}\nMerged: {date}\nFiles: {files}\n\n{body[:1000]}\n\nChanges:\n{diff_summary}"
   → diff_summary = first 5 files changed, 200 chars of diff each
   → Metadata: { pr_number, pr_title, pr_url, pr_author, merged_at, files_changed[] }

4. EMBED
   → Code chunks: task_type="CODE_RETRIEVAL_DOCUMENT"
   → PR chunks:   task_type="RETRIEVAL_DOCUMENT"
   → Model: gemini-embedding-001, output_dimensionality=1536
   → Batch 20 chunks per API call

5. STORE IN CHROMADB
   → Two collections:
       f"repo_{repo_id}_code"  → code chunks
       f"repo_{repo_id}_prs"   → PR chunks
   → repo.status = "ready"

6. CLEANUP
   → Update repo.chunk_count, pr_count, last_indexed_at
   → Publish completion to Redis channel for frontend polling
```

**Progress stages to emit:**
- `{ stage: "fetching_files", progress: 5 }`
- `{ stage: "chunking_code", progress: 20 }`
- `{ stage: "fetching_prs", progress: 50 }`
- `{ stage: "embedding", progress: 70 }`
- `{ stage: "storing", progress: 90 }`
- `{ stage: "done", progress: 100 }`

---

## RAG Query Pipeline

**Called by:** `POST /api/chat/sessions/:id/message`

```
1. EMBED QUESTION
   → gemini-embedding-001, task_type="CODE_RETRIEVAL_QUERY", output_dimensionality=1536

2. DUAL COLLECTION SEARCH
   → Query repo_{id}_code → top 6 results
   → Query repo_{id}_prs  → top 4 results
   → Filter similarity < 0.3
   → For PR-scoped sessions: also filter PR chunks by pr_number in metadata

3. RERANK
   → Sort all results by similarity score descending
   → Deduplicate (same file+lines or same PR number)
   → Keep top 8

4. BUILD PROMPT
   System:
     "You are an expert code assistant with access to both the codebase and its
     PR history. Answer using the provided snippets. Always cite sources —
     file+line for code, PR number+title for history. If a change was
     introduced in a specific PR, mention it. If you cannot answer from the
     context, say so."

   User:
     "Code snippets:\n{code_chunks}\n\nPR history:\n{pr_chunks}\n\nQuestion: {question}\n\nPrevious:\n{last_3_messages}"

5. STREAM
   → gemma-4-26b-a4b-it via Gemini API
   → Enable thinking mode for questions containing "why", "explain", "architecture", "design"
   → Stream tokens via SSE: data: {"token": "..."}\n\n
   → Final event:  data: {"done": true, "sources": [...]}\n\n

6. PERSIST
   → Save user Message + assistant Message to DB
   → sources[] populated from the retrieved chunks metadata
```

---

## Frontend Routing

```javascript
// router/index.js
const routes = [
  { path: '/',                        component: LandingView },
  { path: '/dashboard',               component: DashboardView, meta: { requiresAuth: true } },
  { path: '/:owner/:repo',            component: RepoView },
  { path: '/:owner/:repo/pr/:number', component: PrView },
]
```

### RepoView state machine
```
On mount → GET /api/gh/:owner/:repo

"not_found" → show RepoNotFound component
"indexing"  → show IndexingProgress, poll /api/status/job/:id every 2s
              → when done, transition to "ready" state
"ready"     → show ChatWindow immediately
              → load previous sessions in sidebar
```

### SSE streaming in chat
```javascript
// Use EventSource for streaming
const es = new EventSource(`/api/chat/sessions/${id}/message?q=...`)
es.onmessage = (e) => {
  const data = JSON.parse(e.data)
  if (data.token) appendToken(data.token)
  if (data.done)  { setSources(data.sources); es.close() }
}
```

---

## ChromaDB Collections

Two collections per repo:

| Collection | Content | Metadata fields |
|---|---|---|
| `repo_{id}_code` | Function/class chunks | file_path, start_line, end_line, language |
| `repo_{id}_prs` | PR title+desc+diff summary | pr_number, pr_title, pr_url, pr_author, merged_at, files_changed |

When a repo is deleted, **both collections must be deleted**.

---

## Key Conventions

**Backend:**
- All routes return JSON. Errors: `{ error: "message" }` with appropriate HTTP status.
- JWT token expected in `Authorization: Bearer <token>` header.
- SSE endpoint streams `data: {...}\n\n` format. Final message always has `"done": true`.
- Celery task always updates `repo.status` on start, completion, and failure.
- Never store raw GitHub tokens in plain text — encrypt with `SECURITY_PASSWORD_SALT`.

**Embeddings:**
- Code chunks use `task_type="CODE_RETRIEVAL_DOCUMENT"` at index time, `"CODE_RETRIEVAL_QUERY"` at query time.
- PR chunks use `task_type="RETRIEVAL_DOCUMENT"` at index time.
- Always normalize embeddings when using `output_dimensionality < 3072` (ChromaDB handles this with cosine distance).

**ChromaDB:**
- Collection names: `repo_{repo_id}_code` and `repo_{repo_id}_prs`.
- Use cosine distance metric (default).
- `chroma_service.py` is the only file that touches ChromaDB directly.

**Frontend:**
- All API calls go through `api/axios.js` — never use fetch directly.
- Auth token stored in Pinia `auth` store, injected by Axios interceptor.
- `RepoView` must handle all three states (not_found / indexing / ready) — never assume ready.
- `SourceDrawer` receives `sources[]` array and renders Code tab and PRs tab separately.

---

## What NOT to do

- Don't clone repos to disk — use GitHub Contents API to fetch files.
- Don't index everything — skip node_modules, lock files, binaries. See filter list above.
- Don't index all PRs — last 100 merged only, skip bots.
- Don't put business logic in routes — routes call services, services do the work.
- Don't query both chroma collections in the route handler — that lives in `rag_service.py`.
- Don't block the Flask request thread with embedding calls — those run inside Celery.
- Don't hardcode model names — read from env vars `EMBEDDING_MODEL` and `LLM_MODEL`.

## Design System

All frontend code MUST follow `DESIGN.md` in the project root. Read it
before writing any UI code, component, or style.

Rules:
- Never hardcode colors, fonts, spacing, or border radius — use only the
  tokens defined in DESIGN.md
- Never introduce a new visual style not present in DESIGN.md
- If DESIGN.md and your instinct conflict, DESIGN.md wins
- Every new component must be checked against DESIGN.md before completion
- Do not use Tailwind arbitrary values (e.g. w-[437px]) — if a value
  isn't in the design system, it doesn't belong in the code