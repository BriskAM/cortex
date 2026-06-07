# Cortex — RAG-Based Codebase Q&A Tool
### Full Technical Plan

---

## 1. Product Vision

A developer tool where you connect any GitHub repo and chat with your codebase in natural language — not just the code, but the full engineering history behind it. Cortex understands *what* the code does and *why* it exists.

**Code questions it answers:**
- "Where is authentication handled?"
- "What does the `process_payment` function do?"
- "Which files touch the user model?"
- "Explain the flow when a new user registers"
- "Find all places where we call the GitHub API"

**History questions it answers:**
- "When was the auth system refactored and why?"
- "Which PR introduced rate limiting?"
- "What was the reasoning behind switching to JWT?"
- "Who worked on the payment module and what did they change?"
- "Show me everything that touched the user model in the last 3 months"

**Who uses this:** Developers onboarding to new codebases, code reviewers, team leads doing audits, anyone trying to understand *why* code is the way it is.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Vue3 Frontend                       │
│  /:owner/:repo  /:owner/:repo/pr/:number  /dashboard    │
└────────────────────┬────────────────────────────────────┘
                     │ Axios (REST)
┌────────────────────▼────────────────────────────────────┐
│                   Flask REST API                         │
│  /auth  /gh/:owner/:repo  /gh/:owner/:repo/pr/:number   │
│  /chat  /status                                          │
└──────┬──────────────┬──────────────────┬────────────────┘
       │              │                  │
┌──────▼──────┐ ┌─────▼──────┐ ┌────────▼───────┐
│  PostgreSQL  │ │   Redis    │ │   ChromaDB     │
│  Users,Repos │ │Task Queue  │ │ Vector Store   │
│  Chat History│ │Job Status  │ │ Code + PR Index│
└─────────────┘ └─────┬──────┘ └────────────────┘
                      │
              ┌───────▼────────┐
              │  Celery Worker  │
              │                │
              │ 1. Clone repo  │
              │ 2. Parse files │
              │ 3. Chunk code  │
              │ 4. Fetch PRs   │
              │ 5. Embed all   │
              │ 6. Store Chroma│
              └───────┬────────┘
                      │
          ┌───────────┴───────────┐
          │                       │
   ┌──────▼──────┐       ┌────────▼──────┐
   │  GitHub API  │       │  Google AI    │
   │  Repo fetch  │       │  gemini-embed │
   │  File trees  │       │  gemma-4-26b  │
   │  PRs + diffs │       └───────────────┘
   └─────────────┘
```

---

## 3. Folder Structure

```
cortex/
├── backend/
│   ├── app/
│   │   ├── __init__.py              # App factory
│   │   ├── config.py                # Config classes (dev/prod)
│   │   ├── extensions.py            # db, security, celery init
│   │   │
│   │   ├── models/
│   │   │   ├── user.py              # User, Role (Flask-Security)
│   │   │   ├── repo.py              # IndexedRepo model
│   │   │   └── chat.py              # ChatSession, Message model
│   │   │
│   │   ├── api/
│   │   │   ├── auth.py              # /api/auth/* routes
│   │   │   ├── repos.py             # /api/repos/* routes
│   │   │   ├── chat.py              # /api/chat/* routes
│   │   │   └── status.py            # /api/status/* routes
│   │   │
│   │   ├── services/
│   │   │   ├── github_service.py    # GitHub API interactions
│   │   │   ├── indexer_service.py   # Chunking + embedding logic
│   │   │   ├── pr_service.py        # PR fetch, filter, chunk logic
│   │   │   ├── chroma_service.py    # ChromaDB read/write
│   │   │   └── rag_service.py       # Query → retrieve → LLM → answer
│   │   │
│   │   └── tasks/
│   │       └── indexing_tasks.py    # Celery tasks for indexing
│   │
│   ├── migrations/                  # Flask-Migrate
│   ├── tests/
│   ├── requirements.txt
│   ├── celery_worker.py
│   └── run.py
│
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── router/index.js
│   │   ├── stores/                  # Pinia stores
│   │   │   ├── auth.js
│   │   │   ├── repos.js
│   │   │   └── chat.js
│   │   ├── views/
│   │   │   ├── LandingView.vue          # cortex.dev/
│   │   │   ├── RepoView.vue             # cortex.dev/:owner/:repo
│   │   │   ├── PrView.vue               # cortex.dev/:owner/:repo/pr/:number
│   │   │   └── DashboardView.vue        # cortex.dev/dashboard (saved repos)
│   │   ├── components/
│   │   │   ├── RepoCard.vue
│   │   │   ├── IndexingProgress.vue
│   │   │   ├── ChatWindow.vue
│   │   │   ├── MessageBubble.vue
│   │   │   ├── SourceDrawer.vue         # Code + PR sources tabs
│   │   │   └── RepoNotFound.vue         # Invalid owner/repo fallback
│   │   └── api/
│   │       └── axios.js             # Axios instance + interceptors
│   └── package.json
│
├── docker-compose.yml
└── README.md
```

---

## 4. Database Models

### User (Flask-Security)
```python
class User(db.Model, UserMixin):
    id, email, password, active
    github_token       # OAuth token (encrypted)
    fs_uniquifier
    roles → Role
```

### IndexedRepo
```python
class IndexedRepo(db.Model):
    id
    user_id            # FK → User (nullable — public repos auto-indexed)
    github_url         # https://github.com/BriskAM/resume
    owner              # BriskAM
    repo_name          # resume
    branch             # default: main
    status             # pending | indexing | ready | failed
    is_public          # True if auto-indexed via URL, no user login needed
    chroma_collection  # collection name in ChromaDB
    file_count
    chunk_count
    pr_count
    last_indexed_at
    created_at
```

### ChatSession
```python
class ChatSession(db.Model):
    id
    user_id            # FK → User
    repo_id            # FK → IndexedRepo
    title              # Auto-generated from first message
    created_at
```

### Message
```python
class Message(db.Model):
    id
    session_id         # FK → ChatSession
    role               # user | assistant
    content
    sources            # JSON array of:
                       #   code: {type, file, start_line, end_line, snippet}
                       #   pr:   {type, pr_number, pr_title, pr_url, pr_author, merged_at}
    created_at
```

---

## 5. API Endpoints

### Auth
```
POST   /api/auth/register
POST   /api/auth/login               → returns JWT token
POST   /api/auth/logout
GET    /api/auth/me
```

### Dynamic Repo Resolution (core of the URL feature)
```
GET    /api/gh/:owner/:repo          → resolve repo by owner+name
                                       • NOT SEEN: trigger index, return {status: "indexing", job_id}
                                       • INDEXING:  return {status: "indexing", progress: 42}
                                       • READY:     return {status: "ready", repo_id, stats}
                                       • NOT FOUND: GitHub 404, return {status: "not_found"}

GET    /api/gh/:owner/:repo/pr/:num  → resolve specific PR
                                       • Returns PR metadata + index status
                                       • Triggers PR-scoped indexing if needed
```

### Repos (dashboard / saved repos)
```
GET    /api/repos                    → list user's indexed repos
DELETE /api/repos/:id                → remove repo + chroma collection
POST   /api/repos/:id/reindex        → re-trigger full indexing
```

### Chat
```
GET    /api/chat/sessions                  → list sessions for a repo
POST   /api/chat/sessions                  → create new session
                                             body: {repo_id, scope?: "pr", pr_number?}
GET    /api/chat/sessions/:id              → session + all messages
POST   /api/chat/sessions/:id/message      → send message → get answer (SSE stream)
DELETE /api/chat/sessions/:id              → delete session
```

### Status
```
GET    /api/status/job/:job_id       → Celery job status + progress %
```

---

## 6. Celery Indexing Pipeline

This is the core of the application. Triggered when user connects a repo.

```
Task: index_repository(repo_id)

Step 1: CLONE
  → Use GitHub API token to clone repo to /tmp/{repo_id}/
  → Or use GitHub API to fetch file tree + contents (no clone needed)
  → Update repo.status = "indexing"

Step 2: FILTER FILES
  → Skip: node_modules, .git, dist, build, __pycache__
  → Skip binary files, images, lock files
  → Keep: .py .js .ts .vue .jsx .tsx .java .go .rs .md .sql

Step 3: PARSE & CHUNK CODE
  For each file:
    → Read content
    → Apply chunking strategy:
        - Code files: chunk by function/class boundaries
          (use regex or tree-sitter for AST-aware chunking)
        - Large files: sliding window (512 tokens, 50 token overlap)
        - Small files (<200 tokens): keep as single chunk
    → Each chunk stores: {content, file_path, start_line, end_line, language}

Step 4: FETCH & CHUNK PULL REQUESTS
  → Fetch last 100 merged PRs via GitHub API (sorted by merged_at desc)
  → Skip bot PRs (author login contains "bot" or "dependabot" or "renovate")
  → For each PR, build a single text chunk:
      chunk = f"""
      PR #{pr.number}: {pr.title}
      Author: {pr.user.login}
      Merged: {pr.merged_at}
      Files changed: {', '.join(pr_files)}

      Description:
      {pr.body[:1000]}  ← cap at 1000 chars

      Key changes:
      {format_diff_summary(pr.files[:5])}  ← first 5 files, 200 chars of diff each
      """
  → Metadata: {pr_number, pr_title, pr_url, pr_author, merged_at, files_changed[]}

Step 5: EMBED ALL CHUNKS
  → Embed code chunks: task="code_retrieval_document"
  → Embed PR chunks: task="retrieval_document"
  → Batch 20 at a time, gemini-embedding-001, 1536-dim

Step 6: STORE IN CHROMADB
  → Two collections per repo:
      "repo_{repo_id}_code"  → code chunks
      "repo_{repo_id}_prs"   → PR chunks
  → Update repo.status = "ready", chunk_count = N, pr_count = M

Step 7: CLEANUP
  → Delete cloned /tmp/{repo_id}/ folder
  → Emit completion via Redis pub/sub (frontend polls /status)
```

---

## 7. RAG Query Pipeline

Triggered on every chat message.

```
User question: "When was JWT authentication introduced and why?"

Step 1: EMBED QUESTION
  → Call gemini-embedding-001 with task="code_retrieval_query"
  → Get 1536-dim query vector (matches document embedding dimensions)

Step 2: RETRIEVE FROM BOTH COLLECTIONS
  → Query "repo_{id}_code" → top 6 code chunks
  → Query "repo_{id}_prs"  → top 4 PR chunks
  → Filter out low-similarity results (threshold: 0.3)
  → Total: up to 10 context chunks, mixed code + PR history

Step 3: RERANK
  → Sort all 10 chunks by relevance score
  → Deduplicate chunks from the same file/PR
  → Keep top 8 overall

Step 4: BUILD PROMPT
  system_prompt = """
  You are an expert code assistant with access to both the codebase and its
  full PR history. Answer questions using the provided code snippets and PR
  context. Always cite your sources — file + line number for code, PR number
  + title for history. If a code change was introduced in a specific PR,
  mention it. If you cannot answer from the context provided, say so.
  """

  user_prompt = f"""
  Code snippets:
  {format_code_chunks(code_chunks)}

  PR history:
  {format_pr_chunks(pr_chunks)}

  Question: {user_question}

  Previous conversation:
  {last_3_messages}
  """

Step 5: LLM CALL
  → Call gemma-4-26b-a4b-it via Gemini API (or gemma-4-31b-it for max quality)
  → Use thinking mode for complex architectural questions
  → Stream response back to frontend via SSE

Step 6: SAVE & RETURN
  → Save Message to DB with sources[] array (mixed code + PR sources)
  → Return {
      answer,
      sources: [
        {type: "code", file, start_line, end_line, snippet},
        {type: "pr", pr_number, pr_title, pr_url, pr_author, merged_at}
      ]
    }
```

---

## 8. Frontend Views & Routing

### Vue Router Config
```javascript
routes: [
  { path: '/',                          component: LandingView },
  { path: '/dashboard',                 component: DashboardView },  // saved repos
  { path: '/:owner/:repo',              component: RepoView },        // auto-index
  { path: '/:owner/:repo/pr/:number',   component: PrView },          // PR-scoped chat
]
```

### Landing Page (`/`)
- Hero: "Chat with any GitHub repo. Just change the URL."
- Input bar: `cortex.dev/ [owner/repo]` → navigates to `/:owner/:repo`
- Recent/popular repos indexed (optional)

### Repo View (`/:owner/:repo`)
On mount, calls `GET /api/gh/:owner/:repo` and handles three states:

**State 1 — Not indexed yet:**
- Shows repo info pulled from GitHub API (name, description, stars, language)
- Full-screen progress UI: "Indexing BriskAM/resume..." with two-stage bar
- Polls `/api/status/job/:id` every 2s, transitions to chat when ready

**State 2 — Already indexed:**
- Opens chat immediately, no waiting
- Left sidebar: previous chat sessions for this repo
- Chat window ready to use

**State 3 — Repo not found:**
- Clean 404 state: "We couldn't find BriskAM/resume on GitHub"
- Suggest checking the URL

### PR View (`/:owner/:repo/pr/:number`)
- Chat scoped to a single PR's changes
- System context preloaded: PR title, description, diff summary
- Starter questions suggested: "Explain this PR", "What could break?", "Is this a breaking change?"
- Link back to full repo chat

### Dashboard (`/dashboard`)
- Lists all repos the logged-in user has previously chatted with
- Quick-jump links (`cortex.dev/owner/repo`)
- Last chatted, index status, re-index button

---

## 9. Tech Stack Summary

| Layer | Technology |
|---|---|
| Backend Framework | Flask + Flask-Security |
| Database | PostgreSQL + SQLAlchemy |
| Vector Store | ChromaDB (local) |
| Task Queue | Celery + Redis |
| Embeddings | gemini-embedding-001 (1536-dim, MRL) |
| LLM | gemma-4-26b-a4b-it (or gemma-4-31b-it) |
| AI SDK | google-genai (single key for both) |
| GitHub Integration | PyGithub (GitHub REST API) |
| Code Parsing | tree-sitter (AST-aware chunking) |
| Frontend | Vue3 + Pinia + Vue Router |
| HTTP Client | Axios |
| Streaming | Server-Sent Events (SSE) |
| Containerization | Docker + docker-compose |

---

## 10. Environment Variables

```env
# Flask
FLASK_SECRET_KEY=
DATABASE_URL=postgresql://...
SECURITY_PASSWORD_SALT=

# Redis + Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# External APIs
GOOGLE_API_KEY=                # Covers both gemini-embedding-001 + gemma-4
GITHUB_TOKEN=                  # Personal Access Token (read:repo scope)

# Embedding config
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=1536

# LLM config
LLM_MODEL=gemma-4-26b-a4b-it  # or gemma-4-31b-it

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_data
```

---

## 11. Build Order (1 Week Sprint)

### Day 1 — Foundation
- [ ] Flask app factory, config, extensions
- [ ] User + Repo + Chat models (owner + repo_name fields)
- [ ] Flask-Security auth (register/login/JWT)
- [ ] Basic Vue3 setup, router with dynamic `/:owner/:repo` routes, Pinia, Axios
- [ ] Landing page + Login/Register pages

### Day 2 — GitHub + Indexing Pipeline
- [ ] GitHub service (fetch file tree + contents via API)
- [ ] File filtering + chunking logic
- [ ] PR service (fetch last 100 merged PRs, filter bots, build chunks)
- [ ] gemini-embedding-001 calls (google-genai SDK)
- [ ] ChromaDB setup + store both collections (code + prs)
- [ ] Celery task wiring all of the above

### Day 3 — RAG Query Engine
- [ ] Query embedding (gemini-embedding-001, task="code_retrieval_query")
- [ ] Dual collection search (code + prs), merge + rerank results
- [ ] Prompt builder (handles mixed code + PR context)
- [ ] gemma-4-26b-a4b-it call via Gemini API
- [ ] /chat API endpoint working end-to-end

### Day 4 — Streaming + Frontend Core
- [ ] SSE streaming from Flask → Vue3
- [ ] RepoView — three-state logic (not indexed / indexing / ready)
- [ ] Indexing progress UI (two-stage bar)
- [ ] Chat window with streaming typewriter
- [ ] PrView — PR-scoped chat with starter questions

### Day 5 — Sources + Polish
- [ ] Sources drawer — Code tab (file + lines + syntax highlight)
- [ ] Sources drawer — PRs tab (number, title, author, date, GitHub link)
- [ ] Chat session history sidebar
- [ ] Error states, loading states
- [ ] Re-index functionality

### Day 6 — Docker + README
- [ ] docker-compose (flask + postgres + redis + chroma + celery)
- [ ] Full README with architecture diagram, setup steps, API docs
- [ ] .env.example

### Day 7 — Buffer
- [ ] Bug fixes
- [ ] Test with 3-4 real repos
- [ ] Deploy to Render (optional)

---

## 12. What Makes This Stand Out

1. **GitHub-mirror URL structure** — `cortex.dev/vercel/next.js` just works. Zero friction, instantly shareable links.
2. **Code + PR history in one index** — answers both *what* the code does and *why* it exists. No other tool does this.
3. **PR-scoped chat** — `cortex.dev/owner/repo/pr/1234` opens a focused chat on a single PR. Instant code review assistant.
4. **AST-aware chunking** using tree-sitter — chunks by function boundaries, not arbitrary token windows.
5. **Dual collection RAG** — searches code and PR collections simultaneously, merges and reranks before prompting.
6. **Streaming responses** with SSE — feels like a real product.
7. **Source citations with two types** — exact file + line for code, PR number + title + author for history.
8. **Multi-repo, multi-session** — proper data model, not a single-use script.

---

*Start with Day 1. The foundation determines everything else.*