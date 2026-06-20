"""Test Unstructured Serverless API with a sample file.

Usage (from backend/, with venv active):
    python scripts/test_unstructured.py
    python scripts/test_unstructured.py --file ../docs/sales-docs/sample-product.md
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from unstructured_client import UnstructuredClient

from app.config import get_settings
from app.rag.ingest import UnstructuredApiError, _partition_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test Unstructured Serverless API")
    parser.add_argument(
        "--file",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "docs" / "sales-docs" / "sample-product.md",
        help="File to send to the Unstructured API",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()

    if not settings.unstructured_api_key:
        print("[fail] UNSTRUCTURED_API_KEY is not set in .env")
        raise SystemExit(1)

    path = args.file.resolve()
    if not path.is_file():
        print(f"[fail] File not found: {path}")
        raise SystemExit(1)

    print("=" * 60)
    print("  Unstructured Serverless API — live test")
    print("=" * 60)
    print(f"API URL : {settings.unstructured_api_url}")
    print(f"File    : {path.name} ({path.stat().st_size} bytes)")
    print()

    client = UnstructuredClient(
        api_key_auth=settings.unstructured_api_key,
        server_url=settings.unstructured_api_url.rstrip("/"),
    )

    try:
        elements = _partition_file(client, path, settings)
    except UnstructuredApiError as exc:
        print(f"[fail] {exc}")
        raise SystemExit(1) from exc

    print(f"[ok] Unstructured returned {len(elements)} element(s)\n")

    for i, element in enumerate(elements):
        text = (element.get("text") or "").strip()
        el_type = element.get("type", "unknown")
        metadata = element.get("metadata") or {}
        page = metadata.get("page_number")

        print(f"--- Element {i + 1} ---")
        print(f"Type : {el_type}")
        if page is not None:
            print(f"Page : {page}")
        print(f"Text :\n{text}\n")

    print("=" * 60)
    print("Raw JSON (first element):")
    print("=" * 60)
    if elements:
        print(json.dumps(elements[0], indent=2, default=str))


if __name__ == "__main__":
    main()
