"""Copy dining/spa images to public paths and patch media_assets_seed.csv URLs and tags."""

import csv
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SEED = SCRIPT_DIR / "media_assets_seed.csv"
PUBLIC = SCRIPT_DIR.parents[2] / "frontend" / "public" / "resort-media" / "icmaldives"
IMAGES = SCRIPT_DIR / "images"

DINING_COPIES = {
    "the_lighthouse": IMAGES / "dining" / "InterContinental-Maldives_-The-Light-House-5.jpg",
    "sunset_bar": IMAGES / "dining" / "InterContinental-Maldives_Sunset-Bar-3-1876x1080.jpg",
    "fish_market": IMAGES / "dining" / "InterContinental-Maldives_-The-Light-House-5.jpg",
    "cafe_umi": IMAGES / "dining" / "InterContinental-Maldives_Sunset-Bar-3-1876x1080.jpg",
    "the_collective": IMAGES / "dining" / "InterContinental-Maldives_Sunset-Bar-3-1876x1080.jpg",
    "the_retreat": IMAGES / "spa" / "InterContinental-Maldives_-Spa-Experience-8-1598x1080.jpg",
    "pool_bar": IMAGES / "dining" / "InterContinental-Maldives_Sunset-Bar-3-1876x1080.jpg",
    "wine_cellar": IMAGES / "dining" / "InterContinental-Maldives_-The-Light-House-5.jpg",
    "fitness_centre": IMAGES / "spa" / "InterContinental-Maldives-Hero-37.jpg",
    "manta_ray_experience": IMAGES / "activities" / "InterContinental-Maldives_-Dolphin-Cruise-1-1920x1080.jpg",
    "teen_escapades": IMAGES / "family" / "InterContinental-Maldives_-Water-Sports-19-1920x1080.jpg",
}

TAG_SYNONYMS = {
    "overwater_pool_villa": "overwater_villa",
    "beach_pool_villa": "beach_villa",
    "planet_trekkers": "kids_club",
    "sunset_bar": "sunset_bar",
    "water_sports": "water_sports",
    "three_bedroom_royal_beachfront_pool_residence": "royal_residence",
}


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    dining_public = PUBLIC / "dining"
    dining_public.mkdir(exist_ok=True)

    rows = list(csv.DictReader(SEED.open(encoding="utf-8")))
    for row in rows:
        room = row["room_name"]
        if room in TAG_SYNONYMS and TAG_SYNONYMS[room] not in row["tags"]:
            row["tags"] = f"{row['tags']}, {TAG_SYNONYMS[room]}"

        if room in DINING_COPIES and DINING_COPIES[room].exists():
            ext = DINING_COPIES[room].suffix.lower()
            dest = dining_public / f"{room}{ext}"
            shutil.copy2(DINING_COPIES[room], dest)
            row["source_url"] = f"/resort-media/icmaldives/dining/{room}{ext}"

    with SEED.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Patched {SEED}")


if __name__ == "__main__":
    main()
