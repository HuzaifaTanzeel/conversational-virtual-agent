"""CLI: python scripts/ingest_docs.py --dir docs/sales-docs"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.providers.vectorstore import get_vector_store
from app.rag.ingest import ingest_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest sales docs into the vector store")
    parser.add_argument(
        "--dir",
        type=Path,
        required=True,
        help="Directory containing PDFs and other sales documents",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Ingest files recursively under --dir",
    )
    return parser.parse_args()


def expand_dir(directory: Path, recursive: bool) -> list[Path]:
    pattern = "**/*" if recursive else "*"
    return [p for p in directory.glob(pattern) if p.is_file()]


async def main() -> None:
    args = parse_args()
    if not args.dir.is_dir():
        print(f"Not a directory: {args.dir}", file=sys.stderr)
        raise SystemExit(1)

    settings = get_settings()
    vector_store = get_vector_store()
    files = expand_dir(args.dir, args.recursive)
    if not files:
        print("No files found to ingest", file=sys.stderr)
        raise SystemExit(1)

    count = await ingest_paths(files, vector_store, settings=settings)
    print(f"Ingested {count} chunks from {len(files)} file(s)")


if __name__ == "__main__":
    asyncio.run(main())
