"""Generate Avatour technical summary Word document."""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUTPUT = Path(__file__).resolve().parents[2] / "docs" / "Avatour_Technical_Summary.docx"


def set_cell_shading(cell, color: str) -> None:
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), color)
    cell._tc.get_or_add_tcPr().append(shading)


def add_heading(doc: Document, text: str, level: int = 1) -> None:
    doc.add_heading(text, level=level)


def add_para(doc: Document, text: str, bold: bool = False, italic: bool = False) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(11)


def add_bullet(doc: Document, text: str, level: int = 0) -> None:
    p = doc.add_paragraph(text, style="List Bullet")
    if level:
        p.paragraph_format.left_indent = Inches(0.25 * level)


def add_code_block(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = "Consolas"
    run.font.size = Pt(9)
    p.paragraph_format.left_indent = Inches(0.25)
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), "F5F5F5")
    p._p.get_or_add_pPr().append(shading)


def add_table(doc: Document, headers: list[str], rows: list[list[str]]) -> None:
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    hdr_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        hdr_cells[i].text = header
        set_cell_shading(hdr_cells[i], "1A73E8")
        for p in hdr_cells[i].paragraphs:
            for run in p.runs:
                run.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
                run.font.size = Pt(10)
    for row_idx, row in enumerate(rows, start=1):
        for col_idx, value in enumerate(row):
            cell = table.rows[row_idx].cells[col_idx]
            cell.text = value
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(10)
    doc.add_paragraph()


def build_document() -> Document:
    doc = Document()

    # Title
    title = doc.add_heading("Avatour — Technical Implementation Summary", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph(
        "Conversational Virtual Agent (Tavus CVI + RAG + Tool Calling)"
    )
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.runs[0].italic = True
    sub.runs[0].font.size = Pt(12)
    doc.add_paragraph(
        "Use this document as context when discussing Tavus tool calling and system architecture."
    )

    # 1. What the system does
    add_heading(doc, "1. What the System Does", 1)
    add_para(
        doc,
        "Avatour is a single-tenant AI video sales agent for real estate / resort property tours, "
        "with two portals:",
    )
    add_table(
        doc,
        ["Portal", "Routes", "Users", "Purpose"],
        [
            [
                "Public",
                "/, /call, /call/join/:inviteId",
                "Prospects (meeting invitees / demo users)",
                "Marketing page + gated video call with AI avatar",
            ],
            [
                "Admin",
                "/admin/*",
                "Super admin",
                "Manage Tavus replicas/personas, properties/media, KB docs, demo users, meetings, analytics, tool call logs",
            ],
        ],
    )
    add_para(
        doc,
        "During a call, the prospect speaks to a Tavus CVI avatar over Daily.co WebRTC. "
        "The avatar's brain is a custom LLM endpoint on this backend: RAG over sales documents "
        "(Qdrant + OpenAI) plus a show_media tool that displays property photos/videos/tours in a side panel.",
    )

    # 2. High-level architecture
    add_heading(doc, "2. High-Level Architecture", 1)
    add_para(doc, "Architecture Diagram (Mermaid source):", bold=True)
    add_code_block(
        doc,
        """flowchart TB
    subgraph Browser["Prospect browser"]
        FE[React + Vite frontend]
        Daily[Daily.co JS SDK - WebRTC mic + avatar AV]
    end

    subgraph Docker["Docker Compose"]
        NGINX[nginx :80]
        BE[FastAPI backend :8000]
        PG[(PostgreSQL)]
        QD[(Qdrant)]
    end

    subgraph External["External SaaS"]
        Tavus[Tavus API - tavusapi.com]
        OAI[OpenAI - LLM + embeddings]
        UNS[Unstructured API - doc parsing]
        SMTP[SMTP - meeting emails]
    end

    FE -->|REST + JWT| BE
    FE --> Daily
    Daily <-->|WebRTC room| Tavus
    Tavus -->|POST /chat/completions SSE| BE
    BE --> PG
    BE --> QD
    BE --> Tavus
    BE --> OAI
    BE --> UNS
    BE --> SMTP
    NGINX --> BE""",
    )

    add_heading(doc, "Layered Responsibility", 2)
    add_table(
        doc,
        ["Layer", "Owner", "Role"],
        [
            ["Transport + AV", "Tavus CVI + Daily.co", "WebRTC room, mic, avatar video/audio"],
            ["STT / TTS / lip sync", "Tavus (bundled in CVI)", "Speech ↔ text ↔ avatar speech"],
            [
                "LLM + RAG + tools",
                "This backend (POST /llm/chat)",
                "Retrieve docs, decide answers, emit show_media tool calls",
            ],
            [
                "Media display UI",
                "React frontend (MediaPanel)",
                "Renders resolved asset URLs in 40% side panel",
            ],
            ["Auth & quotas", "This backend", "JWT, demo-user minutes, meeting invites"],
            ["Knowledge base", "Backend + Qdrant", "Ingest PDFs/docs, embed, search"],
            [
                "Property media CMS",
                "Backend + PostgreSQL",
                "Properties + media_assets table for tool resolution",
            ],
            [
                "Admin & analytics",
                "Backend + PostgreSQL",
                "Settings, users, audit, conversations, tool call logs",
            ],
        ],
    )

    # 3. Tech stack
    add_heading(doc, "3. Tech Stack", 1)
    add_heading(doc, "Backend", 2)
    for item in [
        "FastAPI + Uvicorn",
        "SQLAlchemy 2.0 async + asyncpg + Alembic migrations",
        "Qdrant vector store (qdrant-client)",
        "OpenAI (gpt-4o chat, text-embedding-3-small embeddings)",
        "Unstructured Serverless API for document chunking",
        "httpx for Tavus REST API",
        "JWT auth (python-jose), bcrypt passwords, Fernet secret encryption",
    ]:
        add_bullet(doc, item)

    add_heading(doc, "Frontend", 2)
    for item in [
        "React 18, Vite, React Router",
        "Tailwind CSS + shadcn/ui (Radix)",
        "@daily-co/daily-js — joins Tavus conversation room",
        "axios for REST (via frontend/src/lib/api)",
    ]:
        add_bullet(doc, item)

    add_heading(doc, "Infrastructure", 2)
    for item in [
        "docker/docker-compose.yml: postgres, qdrant, backend, nginx",
        "Frontend runs separately: cd frontend && npm run dev (port 5173)",
        "nginx rewrites /chat/completions → /llm/chat for Tavus custom LLM convention",
    ]:
        add_bullet(doc, item)

    add_para(
        doc,
        "Note: docs/ARCHITECTURE.md and parts of README.md still describe LiveAvatar and are outdated. "
        "The codebase has migrated to Tavus CVI.",
        italic=True,
    )

    # 4. Repository layout
    add_heading(doc, "4. Repository Layout", 1)
    add_code_block(
        doc,
        """conversational-virtual-agent/
├── .env                          # Root env (backend + docker)
├── backend/
│   ├── app/
│   │   ├── main.py               # App factory, router registration
│   │   ├── config.py             # Pydantic settings
│   │   ├── models.py             # SQLAlchemy ORM
│   │   ├── api/
│   │   │   ├── session.py        # Tavus session create/end + tool-call resolver
│   │   │   ├── llm_chat.py       # Custom LLM + RAG + show_media tool
│   │   │   ├── public.py         # Marketing, booking, call join
│   │   │   ├── rag.py            # RAG debug/stats
│   │   │   └── admin/            # settings, tavus proxy, properties, tool_calls, etc.
│   │   ├── auth/                 # JWT deps + security
│   │   ├── providers/            # Swappable LLM + vector store factories
│   │   ├── rag/                  # ingest.py + retriever.py
│   │   └── services/
│   │       ├── tavus.py          # Tavus REST client
│   │       ├── quota.py          # Minute metering
│   │       └── ...
│   └── alembic/versions/         # 0001 initial, 0002 meetings, 0003 Tavus migration
├── frontend/src/
│   ├── hooks/useTavus.js         # Daily.co + tool call listener
│   ├── components/VideoCallRoom.jsx, MediaPanel.jsx
│   └── pages/public/ + pages/admin/
├── docker/
│   ├── docker-compose.yml
│   └── nginx/nginx.conf          # /chat/completions → /llm/chat rewrite
└── docs/sales-docs/              # Local PDF drop for ingestion""",
    )

    # 5. Data model
    add_heading(doc, "5. Data Model (PostgreSQL)", 1)
    add_table(
        doc,
        ["Table", "Purpose"],
        [
            ["users", "Super admin accounts"],
            ["demo_users", "Prospect credentials + minute quota"],
            ["app_settings", "Singleton (id=1): replica_id, persona_id, tavus_sandbox, CMS content"],
            ["documents / document_chunks", "KB metadata; chunks map to Qdrant point IDs"],
            ["call_sessions", "Per-call record: tavus_conversation_id, tavus_conversation_url, replica/persona snapshot"],
            ["conversation_messages", "Transcript turns (from Daily events)"],
            ["meeting_invites", "Zoom-style meeting ID + passcode, email workflow"],
            ["properties", "Real estate / resort listings"],
            ["media_assets", "Photos, videos, 360 tours, floor plans linked to properties"],
            ["tool_call_logs", "Every show_media tool invocation"],
            ["usage_events", "Minute metering audit"],
            ["audit_logs", "Admin action log"],
        ],
    )
    add_para(
        doc,
        "Migration 0003 replaced LiveAvatar fields (avatar_id, voice_id, context_id, llm_configuration_id) "
        "with Tavus fields (replica_id, persona_id, tavus_conversation_id).",
    )

    # 6. Authentication
    add_heading(doc, "6. Authentication", 1)
    add_para(doc, "Two JWT audiences (backend/app/auth/security.py):")
    add_table(
        doc,
        ["Audience", "Claim aud", "Used for", "Expiry"],
        [
            ["admin", "Admin portal", "/admin/*, /auth/*", "12 hours (720 min)"],
            ["call", "Call session", "/session/*", "60 minutes"],
        ],
    )
    add_para(doc, "Public call access:", bold=True)
    add_bullet(doc, "Primary: POST /public/call/join with meeting ID + passcode → call_token")
    add_bullet(doc, "Legacy: POST /public/call/login with username + password → call_token")
    add_para(doc, "Session endpoints require Authorization: Bearer <call_token>.")

    # 7. End-to-end call flow
    add_heading(doc, "7. End-to-End Call Flow", 1)
    add_para(doc, "Sequence Diagram (Mermaid source):", bold=True)
    add_code_block(
        doc,
        """sequenceDiagram
    participant P as Prospect browser
    participant FE as React frontend
    participant BE as FastAPI backend
    participant PG as PostgreSQL
    participant Tavus as Tavus API
    participant Daily as Daily.co room
    participant QD as Qdrant
    participant OAI as OpenAI

    P->>FE: Join meeting (ID + passcode)
    FE->>BE: POST /public/call/join
    BE->>PG: Redeem invite, issue call_token
    BE-->>FE: call_token

    P->>FE: Start call
    FE->>BE: POST /session/create (Bearer call_token)
    BE->>PG: Check quota, read app_settings
    BE->>Tavus: POST /v2/conversations
    BE->>PG: Insert call_sessions row
    BE-->>FE: conversation_url, call_session_id, meeting_token

    FE->>Daily: DailyIframe.createCallObject().join(conversation_url)
    Note over FE,Daily: WebRTC: mic up, avatar video/audio down

    loop Each user turn
        Tavus->>Tavus: STT user speech
        Tavus->>BE: POST /chat/completions → /llm/chat (SSE)
        BE->>OAI: Embed user message
        BE->>QD: Vector search top_k
        BE->>OAI: Chat completion with tools (show_media)
        alt Tool call (show_media)
            BE-->>Tavus: SSE tool_calls + speech chunks + tool result JSON
            Tavus->>Daily: conversation.tool_call app-message
            FE->>BE: POST /session/{id}/tool-call (resolve asset URL)
            FE->>FE: MediaPanel displays photo/video/tour
        else Normal reply
            BE-->>Tavus: SSE text tokens
        end
        Daily-->>FE: conversation.utterance events (transcript)
    end

    P->>FE: Hang up
    FE->>BE: POST /session/{id}/messages (transcript)
    FE->>BE: DELETE /session/end/{id}
    BE->>Tavus: DELETE /v2/conversations/{id}
    BE->>PG: Meter minutes, store conversation""",
    )

    # 8. Tavus integration
    add_heading(doc, "8. Tavus Integration", 1)
    add_heading(doc, "Backend client (backend/app/services/tavus.py)", 2)
    add_bullet(doc, "Base URL: https://tavusapi.com")
    add_bullet(doc, "Auth: x-api-key header")
    add_bullet(doc, "POST /v2/conversations — create conversation")
    add_bullet(doc, "DELETE /v2/conversations/{id} — end conversation")
    add_bullet(doc, "GET /v2/replicas, /v2/personas — list/get for admin UI")

    add_heading(doc, "Session creation (backend/app/api/session.py)", 2)
    for item in [
        "Reads replica_id + persona_id from singleton app_settings",
        "Creates Tavus conversation, stores CallSession",
        "Enforces demo-user minute quota before starting",
    ]:
        add_bullet(doc, item)

    add_heading(doc, "Frontend (frontend/src/hooks/useTavus.js)", 2)
    for item in [
        "Uses @daily-co/daily-js to join conversation_url",
        "Listens to Daily app-message events: conversation.utterance, conversation.tool_call, speaking events",
        "Attaches remote participant video/audio tracks for avatar display",
    ]:
        add_bullet(doc, item)

    add_heading(doc, "Custom LLM configuration (manual, outside codebase)", 2)
    add_para(
        doc,
        "Unlike the old LiveAvatar flow, Tavus persona must be configured in the Tavus dashboard to point "
        "its custom LLM at: {BACKEND_PUBLIC_URL}/chat/completions",
    )
    add_para(
        doc,
        "nginx rewrites this to POST /llm/chat. BACKEND_PUBLIC_URL must be publicly reachable (ngrok in dev) "
        "because Tavus servers call the LLM endpoint, not the browser.",
    )

    # 9. RAG pipeline
    add_heading(doc, "9. RAG Pipeline", 1)
    add_heading(doc, "Ingestion", 2)
    add_code_block(
        doc,
        """File (PDF/DOCX/PPT/TXT/MD/HTML)
  → Unstructured Serverless API (by_title chunking)
  → OpenAI embeddings (text-embedding-3-small, 1536 dims)
  → Qdrant upsert + PostgreSQL documents/document_chunks rows

CLI: python backend/scripts/ingest_docs.py --dir ../docs/sales-docs --recursive""",
    )
    add_heading(doc, "Query-time", 2)
    for item in [
        "Embed latest user message",
        "Qdrant search (QDRANT_TOP_K, default 4)",
        "Build system prompt (conversational, no markdown — spoken delivery)",
        "System prompt instructs: When customers ask to SEE something, ALWAYS call the show_media tool",
        "OpenAI chat completion with tools=TOOLS, tool_choice=auto",
    ]:
        add_bullet(doc, item)
    add_para(doc, "Collection: avatour-docs (configurable via QDRANT_COLLECTION).")

    # 10. Tool calling
    add_heading(doc, "10. Tool Calling — Current Implementation", 1)

    add_heading(doc, "10.1 Tool definition (backend/app/api/llm_chat.py)", 2)
    add_para(doc, "Single tool: show_media")
    add_code_block(
        doc,
        """{
  "name": "show_media",
  "parameters": {
    "asset_type": enum ["photo", "video", "tour_360", "floor_plan", "matterport"],
    "room_name": string,
    "speech": string
  },
  "required": ["asset_type", "room_name", "speech"]
}""",
    )

    add_heading(doc, "10.2 LLM-side flow (Tavus → backend)", 2)
    for item in [
        "Resolve media asset from DB (media_assets) by asset_type + room_name",
        "Normalize room names: lowercase, spaces/hyphens → underscores",
        "Match by room_name column, then tags, then fallback to first asset of that type",
        "Log to tool_call_logs (links to call_session_id via x-conversation-id header if present)",
        "Stream OpenAI-compatible SSE: tool_calls delta → speech chunks → JSON tool result with finish_reason: tool_calls",
    ]:
        add_bullet(doc, item)
    add_para(
        doc,
        "Note: The LLM call is non-streaming; SSE is synthesized manually afterward.",
        italic=True,
    )

    add_heading(doc, "10.3 Client-side flow (Daily app-message → frontend → backend)", 2)
    add_code_block(
        doc,
        '{ event_type: "conversation.tool_call", properties: { name, arguments }, conversation_id }',
    )
    for item in [
        "useTavus.js parses tool name + arguments from app-message",
        "If show_media: POST /session/{call_session_id}/tool-call",
        "Backend resolves asset URL and logs to tool_call_logs",
        "Frontend updates MediaPanel via onMediaEvent callback",
        "Optionally sends conversation.echo app-message with speech text",
    ]:
        add_bullet(doc, item)

    add_heading(doc, "10.4 Media display (MediaPanel.jsx)", 2)
    add_table(
        doc,
        ["asset_type", "Rendering"],
        [
            ["photo", "<img>"],
            ["video", "<video>"],
            ["tour_360 / matterport", "<iframe>"],
            ["floor_plan", "<iframe>"],
        ],
    )

    add_heading(doc, "10.5 Known design characteristics / gaps", 2)
    add_table(
        doc,
        ["Topic", "Current state"],
        [
            ["Dual resolution", "Asset resolved in both /llm/chat and /session/{id}/tool-call — may log twice"],
            ["Session linking in LLM", "Depends on Tavus sending x-conversation-id header"],
            ["Tool registration with Tavus", "Tool defined only in backend OpenAI call; no Tavus persona API sync"],
            ["Persona LLM setup", "Manual in Tavus dashboard, not programmatic"],
            ["Docs drift", "ARCHITECTURE.md still describes LiveAvatar"],
        ],
    )

    # 11. API surface
    add_heading(doc, "11. Backend API Surface", 1)
    add_heading(doc, "Public", 2)
    add_table(
        doc,
        ["Method", "Path", "Description"],
        [
            ["GET", "/public/content", "Marketing CMS content"],
            ["POST", "/public/book", "Self-service meeting booking + email"],
            ["GET", "/public/call/invite/{id}", "Invite preview"],
            ["POST", "/public/call/join", "Meeting ID + passcode → call_token"],
            ["POST", "/public/call/login", "Legacy demo user login"],
        ],
    )
    add_heading(doc, "Call session (call_token)", 2)
    add_table(
        doc,
        ["Method", "Path", "Description"],
        [
            ["POST", "/session/create", "Create Tavus conversation"],
            ["POST", "/session/{id}/tool-call", "Resolve show_media → asset URLs"],
            ["POST", "/session/{id}/messages", "Persist transcript from Daily events"],
            ["DELETE", "/session/end/{id}", "End conversation, meter quota"],
        ],
    )
    add_heading(doc, "LLM (called by Tavus servers)", 2)
    add_table(
        doc,
        ["Method", "Path", "Description"],
        [
            ["POST", "/llm/chat", "OpenAI-compatible RAG + tools (SSE)"],
        ],
    )
    add_heading(doc, "Admin (admin token)", 2)
    add_table(
        doc,
        ["Prefix", "Features"],
        [
            ["/auth", "Login, me, change password"],
            ["/admin/settings", "replica_id, persona_id, sandbox, CMS"],
            ["/admin/tavus", "Proxy list/get replicas & personas"],
            ["/admin/properties", "Properties + media assets CRUD"],
            ["/admin/documents", "Upload/delete KB documents"],
            ["/admin/tool-calls", "Tool call log viewer"],
            ["/admin/demo-users", "Prospect accounts + quotas"],
            ["/admin/meetings", "Invites, cancel, resend email"],
            ["/admin/analytics", "Sessions, messages, audit"],
            ["/rag", "Stats and debug query"],
        ],
    )

    # 12. Provider abstraction
    add_heading(doc, "12. Provider Abstraction", 1)
    add_table(
        doc,
        ["Env var", "Options", "Used for"],
        [
            ["LLM_PROVIDER", "openai, anthropic (stub)", "Non-streaming RAG answers"],
            ["VECTOR_STORE", "qdrant, pinecone (stub)", "Document search"],
        ],
    )
    add_para(doc, "Not abstracted: Tavus avatar transport (hard-wired in session + useTavus.js).")

    # 13. Environment variables
    add_heading(doc, "13. Key Environment Variables", 1)
    add_table(
        doc,
        ["Variable", "Purpose"],
        [
            ["BACKEND_PUBLIC_URL", "Critical. Public URL Tavus uses for custom LLM (/chat/completions)"],
            ["TAVUS_API_KEY", "Tavus REST API"],
            ["TAVUS_REPLICA_ID / TAVUS_PERSONA_ID", "Seed-only; then managed in admin + DB"],
            ["OPENAI_API_KEY", "LLM + embeddings"],
            ["UNSTRUCTURED_API_KEY", "Document parsing"],
            ["DATABASE_URL", "PostgreSQL (asyncpg)"],
            ["QDRANT_URL", "Qdrant HTTP API (host:6334, docker:6333)"],
            ["AUTH_JWT_SECRET", "JWT signing"],
            ["VITE_API_URL", "Frontend → backend base URL"],
        ],
    )

    # 14. Frontend routes
    add_heading(doc, "14. Frontend Routes", 1)
    add_table(
        doc,
        ["Route", "Component", "Purpose"],
        [
            ["/", "PublicHome", "Marketing + book call"],
            ["/call", "PublicCall", "Join gate + video room"],
            ["/call/join/:inviteId", "PublicCall", "Email link with optional passcode"],
            ["/admin", "Dashboard", "Admin home"],
            ["/admin/replicas", "ReplicasPage", "Pick Tavus replica"],
            ["/admin/personas", "PersonasPage", "Pick Tavus persona"],
            ["/admin/properties", "PropertiesPage", "Manage property media for tools"],
            ["/admin/tool-calls", "ToolCallsPage", "Tool call analytics"],
            ["/admin/documents", "DocumentsPage", "Knowledge base"],
            ["/admin/call-settings", "CallSettingsPage", "Sandbox + CMS"],
            ["/admin/demo-users", "DemoUsersPage", "Prospect accounts"],
            ["/admin/conversations", "ConversationsPage", "Session replay"],
            ["/admin/meetings", "MeetingsPage", "Meeting invites"],
        ],
    )

    # 15. Files to read first
    add_heading(doc, "15. Files to Read First (for Tool Calling Discussion)", 1)
    add_table(
        doc,
        ["File", "Why"],
        [
            ["backend/app/api/llm_chat.py", "Tool definition, RAG + OpenAI tools, SSE format to Tavus"],
            ["backend/app/api/session.py", "Session lifecycle + /tool-call resolver"],
            ["frontend/src/hooks/useTavus.js", "Daily app-message listener for conversation.tool_call"],
            ["frontend/src/components/MediaPanel.jsx", "How resolved media is rendered"],
            ["backend/app/api/admin/properties.py", "Media asset CMS backing the tool"],
            ["backend/app/models.py", "ToolCallLog, MediaAsset, Property schemas"],
            ["backend/app/rag/retriever.py", "System prompt that instructs tool use"],
            ["backend/app/services/tavus.py", "Tavus conversation API"],
            ["docker/nginx/nginx.conf", "/chat/completions → /llm/chat rewrite"],
        ],
    )

    # 16. Discussion topics
    add_heading(doc, "16. Suggested Discussion Topics for Tavus Tool Calling", 1)
    topics = [
        "Correct Tavus tool calling contract — Does Tavus expect tools registered on the persona, returned via custom LLM SSE, or both?",
        "SSE response format — Is the current pattern (tool_calls delta → speech chunks → JSON result with finish_reason: tool_calls) correct for Tavus CVI?",
        "conversation.tool_call app-message — When does Tavus emit this vs. relying on the LLM stream alone?",
        "Avoiding duplicate resolution/logging — Should asset resolution happen only server-side in /llm/chat, only client-side, or is the dual path intentional?",
        "Persona configuration — Should tool schemas be synced to Tavus persona via API?",
        "Conversation ID header — How does Tavus pass conversation_id to the custom LLM endpoint for session-scoped logging?",
    ]
    for i, topic in enumerate(topics, 1):
        add_bullet(doc, f"{i}. {topic}")

    doc.add_paragraph()
    footer = doc.add_paragraph("Generated from the Avatour codebase.")
    footer.runs[0].italic = True
    footer.runs[0].font.size = Pt(9)

    return doc


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = build_document()
    doc.save(str(OUTPUT))
    print(f"Written: {OUTPUT}")


if __name__ == "__main__":
    main()
