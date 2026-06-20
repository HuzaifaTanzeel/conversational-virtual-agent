# Avatar Sales Agent — Architecture Reference

This document describes the architecture of **avatour**: how components fit together, how Docker containers communicate, and the important integration details you need when building a similar project (for example, swapping LiveAvatar for **Tavus**).

---

## 1. What this system does

A **single-tenant AI video sales agent** with two portals:

| Portal | Route | Users | Purpose |
|--------|-------|-------|---------|
| **Public** | `/`, `/call` | Prospects (demo users / meeting invitees) | Marketing page + gated video call with an AI avatar |
| **Admin** | `/admin` | Super admin | Manage avatars, voices, contexts, knowledge base, demo users, meetings, analytics |

The avatar conducts a **live video call**: it hears the prospect (STT), answers using **RAG over sales documents** (LLM + vector search), and speaks with lip-synced video (TTS + avatar rendering). All real-time AV orchestration is delegated to **LiveAvatar FULL Mode**; this backend owns business logic, auth, quotas, and the custom LLM/RAG endpoint.

---

## 2. High-level architecture

```mermaid
flowchart TB
    subgraph Browser["Prospect browser"]
        FE[React frontend<br/>Vite :5173]
        SDK[LiveAvatar Web SDK<br/>WebRTC + mic]
    end

    subgraph Docker["Docker Compose network"]
        NGINX[nginx :80]
        BE[FastAPI backend<br/>avatour-backend :8000]
        PG[(PostgreSQL<br/>avatour-postgres :5432)]
        QD[(Qdrant<br/>avatour-qdrant :6333)]
    end

    subgraph External["External SaaS"]
        LA[LiveAvatar API<br/>api.liveavatar.com]
        OAI[OpenAI<br/>LLM + embeddings]
        UNS[Unstructured API<br/>document parsing]
        SMTP[SMTP<br/>meeting emails]
    end

    FE -->|REST + JWT| BE
    FE --> SDK
    SDK <-->|WebRTC / voice| LA
    LA -->|POST /chat/completions<br/>OpenAI-compatible SSE| BE
    BE --> PG
    BE --> QD
    BE --> LA
    BE --> OAI
    BE --> UNS
    BE --> SMTP
    NGINX --> BE
```

### Layered responsibility

| Layer | Owner in this project | Role |
|-------|-------------------------|------|
| **Transport + AV** | LiveAvatar FULL Mode | WebRTC, mic capture, avatar video stream, session lifecycle |
| **STT** | LiveAvatar (built-in) | User speech → text |
| **TTS** | LiveAvatar (ElevenLabs-backed) | Agent text → spoken audio + lip sync |
| **Avatar video** | LiveAvatar | Lip-synced video stream to browser |
| **LLM + RAG** | This backend (`/llm/chat`) | Retrieve docs from Qdrant, answer via OpenAI |
| **Auth & quotas** | This backend | JWT, demo-user minutes, meeting invites |
| **Knowledge base** | This backend + Qdrant | Ingest PDFs/docs, embed, search |
| **Admin & CMS** | This backend + PostgreSQL | Settings, users, audit, conversations |

> **Historical note:** An older design used LiveKit + Deepgram + separate avatar plugins. The current production path is **LiveAvatar FULL Mode only**. `docker/docker-compose.full.yml` still references LiveKit and is legacy; the active stack is `docker/docker-compose.yml`.

---

## 3. Repository layout

```
avatour/
├── .env                    # Root env (backend + docker read this)
├── backend/                # FastAPI application
│   ├── app/
│   │   ├── main.py         # App factory, router registration, lifespan
│   │   ├── config.py       # Pydantic settings from .env
│   │   ├── models.py       # SQLAlchemy ORM (PostgreSQL)
│   │   ├── db.py           # Async SQLAlchemy engine
│   │   ├── api/            # HTTP routers (public, admin, session, llm, rag)
│   │   ├── auth/           # JWT + password hashing
│   │   ├── providers/      # Swappable LLM + vector store factories
│   │   ├── rag/            # Ingest + retriever
│   │   └── services/       # LiveAvatar client, quota, email, bootstrap
│   ├── alembic/            # DB migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # React + Vite (NOT in default docker-compose)
│   └── src/
│       ├── hooks/useAvatar.js   # LiveAvatar Web SDK integration
│       └── pages/               # Public + admin portals
├── docker/
│   ├── docker-compose.yml       # Primary stack (postgres, qdrant, backend, nginx)
│   ├── docker-compose.full.yml  # Legacy full stack (+ livekit, frontend container)
│   └── nginx/nginx.conf         # Reverse proxy + SSE rewrite for LiveAvatar
└── docs/
    ├── ARCHITECTURE.md     # This file
    └── sales-docs/         # Local PDF drop folder (gitignored content)
```

---

## 4. Docker containers and networking

### 4.1 Primary stack (`docker/docker-compose.yml`)

| Container | Image / build | Host port | Internal port | Network name (DNS) |
|-----------|---------------|-----------|---------------|---------------------|
| `avatour-postgres` | `postgres:16` | **5432** | 5432 | `avatour-postgres` |
| `avatour-qdrant` | `qdrant/qdrant:v1.9.2` | **6334** → 6333, **6335** → 6334 (gRPC) | 6333 | `avatour-qdrant` |
| `avatour-backend` | Built from `backend/Dockerfile` | **8000** | 8000 | `avatour-backend` |
| `avatour-nginx` | `nginx:alpine` | **80** | 80 | `avatour-nginx` |

**Frontend is intentionally excluded** from this compose file. Run it locally:

```bash
cd frontend && npm run dev   # http://localhost:5173
```

### 4.2 How containers talk to each other

All services share the default Compose network (`avatour_default`). Containers reach each other by **service name**, not `localhost`.

```
┌─────────────────────────────────────────────────────────────────┐
│  Docker network: avatour_default                                │
│                                                                 │
│  avatour-backend ──DATABASE_URL──► avatour-postgres:5432                 │
│       │                                                         │
│       └──QDRANT_URL──────────► avatour-qdrant:6333                  │
│                                                                 │
│  avatour-nginx ──proxy_pass──────► avatour-backend:8000                 │
└─────────────────────────────────────────────────────────────────┘

From host machine (local dev, not inside Docker):
  PostgreSQL  → localhost:5432
  Qdrant      → localhost:6334   (mapped from container 6333)
  Backend     → localhost:8000
  nginx       → localhost:80
  Frontend    → localhost:5173   (separate npm process)
```

### 4.3 Environment overrides inside Docker

The backend container receives explicit overrides in compose:

```yaml
environment:
  - QDRANT_URL=http://avatour-qdrant:6333      # internal DNS, port 6333
  - DATABASE_URL=postgresql+asyncpg://asa:asa@avatour-postgres:5432/asa
```

When running the backend **on the host** (not in Docker), `.env` defaults apply:

```
QDRANT_URL=http://localhost:6334
DATABASE_URL=postgresql+asyncpg://asa:asa@localhost:5432/asa
```

### 4.4 nginx role

nginx (`avatour-nginx`) sits in front of the backend for production-style deployment. Critical behavior:

| Incoming path | Proxied to | Why |
|---------------|------------|-----|
| `/chat/completions` | `backend/llm/chat` | LiveAvatar registers `base_url` as OpenAI-compatible; it calls `{base_url}/chat/completions` |
| `/llm/` | `backend/llm/` | Direct SSE access |
| `/session/` | `backend/session/` | Session create/end |
| `/rag/` | `backend/rag/` | RAG debug/stats |
| `/health` | `backend/health` | Health check |
| `/api/` | `backend/` | Legacy prefix strip |

SSE settings (`proxy_buffering off`, long `proxy_read_timeout`) are required so LiveAvatar receives streamed LLM tokens in real time.

### 4.5 Backend container startup

```dockerfile
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

Migrations run automatically on container start. Local dev can run migrations manually: `cd backend && alembic upgrade head`.

### 4.6 Volumes

| Volume | Mount | Purpose |
|--------|-------|---------|
| `avatour-postgres-data` | Postgres data dir | Persistent users, sessions, settings |
| `avatour-qdrant-data` | Qdrant storage | Persistent embeddings |
| `../docs/sales-docs` → `/app/docs/sales-docs:ro` | Backend read-only | Optional local doc folder for scripts |

---

## 5. External service communication

These are **not** Docker containers; the backend and browser call them over the public internet.

| Service | Base URL | Called by | Purpose |
|---------|----------|-----------|---------|
| **LiveAvatar** | `https://api.liveavatar.com` | Backend (`LiveAvatarClient`), Browser (Web SDK / WebRTC) | Session tokens, avatar/voice/context CRUD, stop session, transcript |
| **OpenAI** | `https://api.openai.com` | Backend | Chat completions (RAG answers), embeddings |
| **Unstructured** | `https://api.unstructuredapp.io` | Backend | PDF/DOCX parsing and chunking |
| **SMTP** | Configurable | Backend | Meeting invite emails |

### 5.1 LiveAvatar FULL Mode — the critical integration

LiveAvatar FULL Mode is an **all-in-one realtime stack**. Your backend does **not** run STT/TTS/WebRTC workers.

**Registration (once per deployment):**

1. Backend creates a LiveAvatar **secret** (stores OpenAI API key reference).
2. Backend creates an **LLM configuration** pointing at `BACKEND_PUBLIC_URL` as `base_url`.
3. The `llm_configuration_id` is cached in PostgreSQL (`app_settings` table).

**Per call:**

1. Backend calls `POST /v1/sessions/token` with:
   - `mode: "FULL"`
   - `avatar_id`, `llm_configuration_id`
   - `avatar_persona` (voice_id, context_id, voice_settings)
   - `is_sandbox`, `max_session_duration`
2. Returns `session_token` to frontend.
3. Frontend starts `@heygen/liveavatar-web-sdk` with that token.
4. During the call, **LiveAvatar** POSTs to `{BACKEND_PUBLIC_URL}/chat/completions` with OpenAI message format; backend streams RAG response via SSE.

**`BACKEND_PUBLIC_URL` must be publicly reachable** in dev (use ngrok) because LiveAvatar's servers call your LLM endpoint — not the browser.

```
Prospect speaks
    → LiveAvatar STT
    → LiveAvatar builds messages[]
    → HTTP POST https://YOUR_PUBLIC_URL/chat/completions  (or /llm/chat direct)
    → Your backend: embed query → Qdrant search → OpenAI stream
    → SSE tokens back to LiveAvatar
    → LiveAvatar TTS + avatar video
    → WebRTC to browser
```

---

## 6. Data architecture

### 6.1 PostgreSQL (source of truth for app state)

Async SQLAlchemy via `asyncpg`. Key tables:

| Table | Purpose |
|-------|---------|
| `users` | Super admin accounts |
| `demo_users` | Prospect credentials + minute quota |
| `app_settings` | Singleton row (id=1): avatar_id, voice_id, context_id, llm_configuration_id, sandbox, CMS content |
| `documents` / `document_chunks` | KB metadata; chunks map to Qdrant point IDs |
| `call_sessions` | Per-call record (LiveAvatar session ID, duration, config snapshot) |
| `conversation_messages` | Transcript turns (SDK events + LiveAvatar API sync) |
| `meeting_invites` | Zoom-style meeting ID + passcode, email workflow |
| `usage_events` | Minute metering audit trail |
| `audit_logs` | Admin action log |

Migrations: `backend/alembic/versions/`.

### 6.2 Qdrant (vector search only)

- Collection: `sales-docs` (configurable via `QDRANT_COLLECTION`)
- Dimensions: 1536 (`text-embedding-3-small`)
- Distance: cosine
- Each point payload: `{ text, source_file, document_id, chunk_index, page_number, ... }`

PostgreSQL owns document **metadata and lifecycle**; Qdrant owns **embeddings**. Deleting a document removes Qdrant points by `document_id` filter.

---

## 7. Authentication model

Two JWT audiences (`app/auth/security.py`):

| Audience | Claim `aud` | Used for | Typical expiry |
|----------|-------------|----------|----------------|
| Admin | `admin` | `/admin/*`, `/auth/*` | 12 hours |
| Call | `call` | `/session/*` | 60 minutes |

**Public call access paths:**

1. **Meeting invite (primary):** `POST /public/call/join` with meeting ID + passcode → `call_token`
2. **Legacy demo login:** `POST /public/call/login` with username + password → `call_token`

Session endpoints require `Authorization: Bearer <call_token>`.

Admin endpoints require `Authorization: Bearer <admin_token>` from `POST /auth/login`.

---

## 8. End-to-end call flow

```mermaid
sequenceDiagram
    participant P as Prospect browser
    participant FE as React frontend
    participant BE as FastAPI backend
    participant PG as PostgreSQL
    participant LA as LiveAvatar
    participant QD as Qdrant
    participant OAI as OpenAI

    P->>FE: Join meeting (ID + passcode)
    FE->>BE: POST /public/call/join
    BE->>PG: Redeem invite, issue call_token
    BE-->>FE: call_token

    P->>FE: Start call
    FE->>BE: POST /session/create (Bearer call_token)
    BE->>PG: Check quota, read app_settings
    BE->>LA: Register LLM config (if needed)
    BE->>LA: POST /v1/sessions/token
    BE->>PG: Insert call_sessions row
    BE-->>FE: session_token, call_session_id

    FE->>LA: LiveAvatarSession.start() via Web SDK
    Note over FE,LA: WebRTC: mic up, avatar video down

    loop Each user turn
        LA->>LA: STT user speech
        LA->>BE: POST /chat/completions (SSE)
        BE->>OAI: Embed user message
        BE->>QD: Vector search top_k
        BE->>OAI: Stream completion with RAG context
        BE-->>LA: SSE token stream
        LA->>LA: TTS + avatar render
        LA-->>FE: Avatar video + transcriptions
    end

    P->>FE: Hang up
    FE->>BE: POST /session/{id}/messages (SDK transcript)
    FE->>BE: DELETE /session/end/{id}
    BE->>LA: Stop session + fetch transcript
    BE->>PG: Meter minutes, store conversation
```

---

## 9. RAG pipeline

### 9.1 Ingestion (admin uploads or CLI script)

```
File (PDF/DOCX/...)
  → Unstructured Serverless API (by_title chunking)
  → OpenAI embeddings (text-embedding-3-small)
  → Qdrant upsert + PostgreSQL documents/document_chunks rows
```

Supported extensions: `.pdf`, `.docx`, `.doc`, `.pptx`, `.ppt`, `.txt`, `.md`, `.html`.

CLI: `python backend/scripts/ingest_docs.py --dir ../docs/sales-docs --recursive`

### 9.2 Query-time (during live call)

Implemented in `backend/app/rag/retriever.py`:

1. Embed latest user message
2. Qdrant search (`QDRANT_TOP_K`, default 4)
3. Build spoken-delivery system prompt (conversational, no markdown)
4. Stream LLM completion (conversation history preserved)

The `/llm/chat` endpoint wraps this in **OpenAI SSE chunk format** for LiveAvatar compatibility.

---

## 10. Backend API surface

### Public (no admin token)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/public/content` | Marketing CMS content |
| POST | `/public/book` | Self-service meeting booking + email |
| GET | `/public/call/invite/{id}` | Invite preview |
| POST | `/public/call/join` | Meeting ID + passcode → call_token |
| POST | `/public/call/login` | Legacy demo user login |

### Call session (call_token required)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/session/create` | Create LiveAvatar session |
| POST | `/session/{id}/messages` | Persist SDK transcript |
| DELETE | `/session/end/{id}` | Stop session, meter quota, sync transcript |

### LLM (called by LiveAvatar, not browser)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/llm/chat` | OpenAI-compatible RAG endpoint (SSE) |

### Admin (admin token required)

| Prefix | Features |
|--------|----------|
| `/auth` | Login, me, change password |
| `/admin/settings` | Avatar/voice/context IDs, sandbox, CMS |
| `/admin/liveavatar` | Proxy CRUD to LiveAvatar API |
| `/admin/documents` | Upload/delete KB documents |
| `/admin/demo-users` | Prospect account management |
| `/admin/meetings` | Invite list, cancel, resend email |
| `/admin/analytics` | Sessions, messages, audit log |
| `/rag` | Stats and debug query |

---

## 11. Frontend architecture

- **Stack:** React 18, Vite, React Router, Tailwind, shadcn/ui components
- **Avatar integration:** `@heygen/liveavatar-web-sdk` in `useAvatar.js`
- **API base:** `VITE_API_URL` (default `http://localhost:8000`); Vite dev proxy rewrites `/api/*` → backend
- **Routes:**
  - `/` — PublicHome (marketing)
  - `/call`, `/call/join/:inviteId` — PublicCall (join gate + VideoCallRoom)
  - `/admin/*` — Admin portal (protected)

The frontend never talks to Qdrant or LiveAvatar REST directly for calls — only to your backend (auth, session token) and to LiveAvatar via the Web SDK (WebRTC).

---

## 12. Provider abstraction pattern

Swappable via env vars and factory functions in `backend/app/providers/`:

| Env var | Options | Factory |
|---------|---------|---------|
| `LLM_PROVIDER` | `openai`, `anthropic` (stub) | `get_llm_provider()` |
| `VECTOR_STORE` | `qdrant`, `pinecone` (stub) | `get_vector_store()` |

Avatar/transport providers are **not** abstracted yet — LiveAvatar is hard-wired in session flow and frontend SDK. README lists **Tavus** as a planned avatar provider.

To add Tavus, you would likely need:

1. A `TavusClient` service (parallel to `LiveAvatarClient`)
2. A Tavus Web SDK or iframe/embed integration in the frontend
3. A Tavus-compatible custom LLM / webhook pattern (if Tavus supports external LLM like LiveAvatar FULL Mode)
4. DB fields or settings for Tavus persona/replica IDs instead of `avatar_id` / `context_id`

---

## 13. Deployment modes

### Local development (typical)

```bash
# Terminal 1 — infra
docker compose -f docker/docker-compose.yml up -d postgres qdrant

# Terminal 2 — backend
cd backend && alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3 — frontend
cd frontend && npm run dev

# Terminal 4 — expose LLM to LiveAvatar
ngrok http 8000
# Set BACKEND_PUBLIC_URL=https://xxxx.ngrok.io in .env, restart backend
```

### Docker backend + infra

```bash
docker compose -f docker/docker-compose.yml up -d
# Backend on :8000, nginx on :80, still run frontend separately
```

### Production checklist

- [ ] `BACKEND_PUBLIC_URL` = public HTTPS API URL (LiveAvatar must reach `/chat/completions`)
- [ ] `AUTH_JWT_SECRET` and `SECRETS_ENCRYPTION_KEY` set to strong random values
- [ ] `LIVEAVATAR_SANDBOX=false` when billing real sessions (via admin Call Settings)
- [ ] SMTP configured for meeting invites
- [ ] CORS origins include your frontend URL
- [ ] nginx or cloud load balancer with SSE-friendly proxy settings

---

## 14. Key environment variables

| Variable | Purpose |
|----------|---------|
| `BACKEND_PUBLIC_URL` | **Critical.** Public URL LiveAvatar uses for custom LLM |
| `FRONTEND_PUBLIC_URL` | Join links in meeting emails |
| `DATABASE_URL` | PostgreSQL (asyncpg driver) |
| `QDRANT_URL` | Qdrant HTTP API |
| `OPENAI_API_KEY` | LLM + embeddings |
| `UNSTRUCTURED_API_KEY` | Document parsing |
| `LIVEAVATAR_API_KEY` | LiveAvatar REST + sessions |
| `AUTH_JWT_SECRET` | JWT signing |
| `INITIAL_SUPERADMIN_EMAIL` | First-boot admin email |
| `VITE_API_URL` | Frontend → backend base URL |

Seed-only (first `app_settings` row, then admin portal): `LIVEAVATAR_AVATAR_ID`, `LIVEAVATAR_VOICE_ID`, `LIVEAVATAR_CONTEXT_ID`, `LIVEAVATAR_SANDBOX`.

---

## 15. Mapping to a Tavus-based project

Use this project as a **reference architecture**, not a drop-in SDK swap.

### What transfers directly

- **Two-portal pattern** (public call + admin)
- **PostgreSQL** for users, quotas, sessions, transcripts, settings
- **Qdrant + RAG pipeline** (ingest, embed, retrieve, stream)
- **Custom LLM endpoint** pattern (OpenAI-compatible SSE from your backend)
- **JWT auth** with separate admin vs call audiences
- **Minute quota** metering on session end
- **nginx SSE proxy** pattern if the avatar platform calls your backend over HTTP

### What changes for Tavus

| Concern | This project (LiveAvatar) | Likely Tavus approach |
|---------|---------------------------|------------------------|
| Browser AV | `@heygen/liveavatar-web-sdk`, WebRTC | Tavus CVI / Conversational Video Interface or embed |
| Session creation | `POST /v1/sessions/token` FULL mode | Tavus conversation or replica session API |
| STT/TTS/avatar | Bundled in FULL mode | Depends on Tavus product tier (may split components) |
| Custom knowledge | External LLM at `base_url/chat/completions` | Tavus may use different webhook/LLM injection — verify Tavus docs |
| Persona/config | avatar_id, voice_id, context_id in DB | Tavus replica_id, persona, knowledge base config |
| Transcript sync | `GET /v1/sessions/{id}/transcript` | Tavus conversation history API |

### Recommended reuse strategy

1. **Keep** backend structure: `api/`, `auth/`, `rag/`, `services/`, `models.py`
2. **Replace** `services/liveavatar.py` with `services/tavus.py`
3. **Replace** `useAvatar.js` with Tavus client hook
4. **Keep** `/llm/chat` (or adapt to Tavus's expected LLM interface)
5. **Keep** Docker postgres + qdrant; backend container unchanged
6. **Re-evaluate** whether nginx `/chat/completions` rewrite matches Tavus's LLM callback URL convention

---

## 16. Communication summary matrix

| From | To | Protocol | Port / URL | Data |
|------|-----|----------|------------|------|
| Frontend | Backend | HTTP REST | `:8000` or `/api` proxy | JSON, JWT in `Authorization` |
| Frontend | LiveAvatar | WebRTC + SDK | LiveAvatar cloud | Audio up, video down, session_token |
| Backend | PostgreSQL | TCP (asyncpg) | `avatour-postgres:5432` | SQL |
| Backend | Qdrant | HTTP | `avatour-qdrant:6333` | Vectors |
| Backend | LiveAvatar API | HTTPS | `api.liveavatar.com` | Session, CRUD, transcript |
| LiveAvatar cloud | Backend | HTTPS SSE | `BACKEND_PUBLIC_URL/chat/completions` | OpenAI chat format |
| Backend | OpenAI | HTTPS | `api.openai.com` | Chat + embeddings |
| Backend | Unstructured | HTTPS | `api.unstructuredapp.io` | Document bytes |
| Backend | SMTP | TCP/TLS | configurable | Meeting emails |
| nginx | Backend | HTTP | `avatour-backend:8000` | Reverse proxy |
| Host dev tools | Qdrant | HTTP | `localhost:6334` | Direct Qdrant access |
| Host dev tools | Postgres | TCP | `localhost:5432` | Direct DB access |

---

## 17. Health and observability

- **Health:** `GET /health` → `{"status": "ok"}`
- **First boot:** Super admin password printed once to backend logs
- **Audit:** Admin actions logged to `audit_logs`
- **Session analytics:** `/admin/analytics/summary`, `/admin/analytics/sessions`

---

## 18. Files to read first (for onboarding)

| File | Why |
|------|-----|
| `backend/app/main.py` | Router wiring, app lifespan |
| `backend/app/api/session.py` | LiveAvatar session + LLM config registration |
| `backend/app/api/llm_chat.py` | Custom LLM / RAG entry point |
| `backend/app/services/liveavatar.py` | LiveAvatar REST client |
| `frontend/src/hooks/useAvatar.js` | Browser-side session lifecycle |
| `docker/docker-compose.yml` | Container topology |
| `docker/nginx/nginx.conf` | `/chat/completions` rewrite |
| `backend/app/rag/retriever.py` | RAG answer streaming |
| `backend/app/models.py` | Full data model |

---

*Generated from the avatour codebase. Update this document when swapping avatar providers or changing the Docker topology.*
