from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# .env lives at repo root; scripts are often run from backend/
_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT / ".env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_name: str = "avatour"
    debug: bool = False
    cors_origins: str = "http://localhost:5173,http://localhost:80"
    backend_public_url: str = "http://localhost:8000"
    # ^ IMPORTANT: Tavus calls this URL to reach /llm/chat (via /chat/completions rewrite).
    frontend_public_url: str = "http://localhost:5173"

    # --- Email (SMTP) ---
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Avatour"
    smtp_use_tls: bool = True

    # --- Meeting invites ---
    meeting_invite_expiry_days: int = 30
    default_meeting_minute_quota: int = 30

    # --- Database (PostgreSQL, async via asyncpg) ---
    database_url: str = "postgresql+asyncpg://asa:asa@localhost:5432/avatour_db"

    # --- Auth ---
    auth_jwt_secret: str = "change-me-in-production"
    auth_jwt_expiry_minutes: int = 720
    call_token_expiry_minutes: int = 60
    secrets_encryption_key: str = ""

    # --- Super admin bootstrap (first boot only) ---
    initial_superadmin_email: str = "admin@company.com"
    initial_superadmin_password: str = ""

    # --- LLM ---
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    openai_api_key: str = ""
    llm_max_tokens: int = 500
    llm_temperature: float = 0.75

    # --- Embeddings ---
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # --- Vector store ---
    vector_store: str = "qdrant"
    qdrant_url: str = "http://localhost:6334"
    qdrant_collection: str = "avatour-docs"
    qdrant_top_k: int = 4

    # --- Unstructured (Serverless API) ---
    unstructured_api_url: str = "https://api.unstructuredapp.io"
    unstructured_api_key: str = ""
    unstructured_chunk_max_chars: int = 500
    unstructured_chunk_overlap: int = 50

    # --- Tavus CVI ---
    tavus_api_key: str = ""
    # NOTE: replica_id / persona_id / tavus_sandbox live in the DB (app_settings),
    # configurable from the admin portal. Env vars below are INITIAL SEED values only.
    tavus_replica_id: str = ""
    tavus_persona_id: str = ""
    tavus_sandbox: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
