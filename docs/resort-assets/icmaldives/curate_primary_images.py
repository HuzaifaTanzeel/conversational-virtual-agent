"""Pick one primary photo per room_name from manifest.csv and update media_assets_seed.csv."""

import csv
import shutil
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
MANIFEST = SCRIPT_DIR / "manifest.csv"
SEED = SCRIPT_DIR / "media_assets_seed.csv"
PUBLIC_ROOT = SCRIPT_DIR.parents[2] / "frontend" / "public" / "resort-media" / "icmaldives"

SKIP_PATTERNS = (
    "ic_logo",
    "ihgor-brand",
    "unnamed-1",
    "AVI-SPA_Black",
    "Web.png",
)


def is_logo(path: str) -> bool:
    name = Path(path).name.lower()
    return any(s.lower() in name for s in SKIP_PATTERNS)


def score_row(row: dict) -> tuple:
    url = row["source_url"]
    res_bonus = 1 if any(x in url for x in ("1920", "1080", "1603")) else 0
    return (res_bonus, len(url))


def main() -> None:
    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8")))
    by_room: dict[str, list] = defaultdict(list)
    for row in rows:
        if is_logo(row["local_path"]):
            continue
        by_room[row["room_name"]].append(row)

    primary: dict[str, dict] = {}
    for room, items in by_room.items():
        primary[room] = max(items, key=score_row)

    PUBLIC_ROOT.mkdir(parents=True, exist_ok=True)
    seed_rows = list(csv.DictReader(SEED.open(encoding="utf-8")))

    for seed in seed_rows:
        if seed["asset_type"] != "photo":
            continue
        room = seed["room_name"]
        if room not in primary:
            continue
        src_path = Path(primary[room]["local_path"])
        category = src_path.parent.name
        dest_dir = PUBLIC_ROOT / category
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_name = f"{room}{src_path.suffix.lower()}"
        dest_path = dest_dir / dest_name
        shutil.copy2(src_path, dest_path)
        seed["source_url"] = f"/resort-media/icmaldives/{category}/{dest_name}"

    with SEED.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=seed_rows[0].keys())
        writer.writeheader()
        writer.writerows(seed_rows)

    curated = SCRIPT_DIR / "primary_images.csv"
    with curated.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["room_name", "source_url", "local_path", "public_path"],
        )
        writer.writeheader()
        for room, row in sorted(primary.items()):
            category = Path(row["local_path"]).parent.name
            dest_name = f"{room}{Path(row['local_path']).suffix.lower()}"
            writer.writerow(
                {
                    "room_name": room,
                    "source_url": row["source_url"],
                    "local_path": row["local_path"],
                    "public_path": f"/resort-media/icmaldives/{category}/{dest_name}",
                }
            )

    print(f"Updated {SEED} with {sum(1 for s in seed_rows if s['source_url'])} photo URLs")
    print(f"Copied images to {PUBLIC_ROOT}")
    print(f"Wrote {curated}")


if __name__ == "__main__":
    main()
