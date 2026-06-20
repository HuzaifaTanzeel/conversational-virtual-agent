"""
Smoke test — run this after `docker compose up qdrant -d`
to verify infrastructure is reachable before building RAG logic.

Usage:
    cd backend
    python scripts/smoke_test.py
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from app.config import get_settings
from app.providers.vectorstore.qdrant import QdrantVectorStore


async def check_qdrant(settings):
    print("\n[1] Checking Qdrant...")
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{settings.qdrant_url}/healthz", timeout=5)
            r.raise_for_status()
        print(f"    [ok] Qdrant reachable at {settings.qdrant_url}")
    except Exception as e:
        print(f"    [fail] Qdrant not reachable: {e}")
        print(f"      Make sure it's running: docker compose -f docker/docker-compose.yml up qdrant -d")
        return False

    try:
        store = QdrantVectorStore()
        await store.ensure_collection()
        count = await store.count()
        print(f"    [ok] Collection '{settings.qdrant_collection}' ready ({count} vectors)")
    except Exception as e:
        print(f"    [fail] Qdrant collection error: {e}")
        return False

    return True


async def check_unstructured(settings):
    print("\n[2] Checking Unstructured Serverless API config...")
    if not settings.unstructured_api_key:
        print("    [fail] UNSTRUCTURED_API_KEY is not set in .env")
        return False

    print(f"    [ok] UNSTRUCTURED_API_KEY is set")
    print(f"    [ok] API URL: {settings.unstructured_api_url}")
    return True


async def check_openai(settings):
    print("\n[3] Checking OpenAI API key (embeddings)...")
    if not settings.openai_api_key:
        print("    [fail] OPENAI_API_KEY is not set in .env")
        return False
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.embeddings.create(
            input="test",
            model=settings.embedding_model,
        )
        dims = len(resp.data[0].embedding)
        print(f"    [ok] Embeddings working - model: {settings.embedding_model}, dims: {dims}")
        return True
    except Exception as e:
        print(f"    [fail] OpenAI embeddings failed: {e}")
        return False


async def main():
    print("=" * 50)
    print("  avatour — infrastructure smoke test")
    print("=" * 50)

    settings = get_settings()
    print(f"\nConfig loaded:")
    print(f"  QDRANT_URL:              {settings.qdrant_url}")
    print(f"  QDRANT_COLLECTION:       {settings.qdrant_collection}")
    print(f"  UNSTRUCTURED_API_URL:    {settings.unstructured_api_url}")
    print(f"  EMBEDDING_MODEL:         {settings.embedding_model}")

    results = await asyncio.gather(
        check_qdrant(settings),
        check_unstructured(settings),
        check_openai(settings),
    )

    passed = sum(results)
    total = len(results)

    print(f"\n{'=' * 50}")
    print(f"  Results: {passed}/{total} checks passed")
    print(f"{'=' * 50}")

    if passed == total:
        print("\n  All checks passed. Ready to build RAG layer.\n")
        sys.exit(0)
    else:
        print("\n  Fix the failing checks above before proceeding.\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
