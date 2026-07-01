"""
collect_resort_images.py

Run on your local machine to pull sample images from the resort's public marketing site
for LOCAL DEV / TESTING of the show_media tool resolution logic only.

Before running:
  - Check the site's Terms of Use / robots.txt and only use this for internal prototyping.
    These images belong to the resort / IHG - do NOT ship them in a production app without
    a proper licensing agreement.
  - pip install requests beautifulsoup4

Usage:
  cd docs/resort-assets/icmaldives
  python collect_resort_images.py
"""

import csv
import os
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://maldives.intercontinental.com"

# page -> (category, room_name, tags) used to label images found on that page
PAGES = {
    "/": ("overview", "resort_aerial", "resort overview, island aerial, whole resort"),
    "/villas-residences/villas/": ("villas", "villas_overview", "villa, villas overview"),
    "/villas-residences/villas/overwater-pool-villas/": (
        "villas",
        "overwater_pool_villa",
        "overwater villa, water villa, pool villa",
    ),
    "/villas-residences/villas/sunset-overwater-pool-villas/": (
        "villas",
        "sunset_overwater_pool_villa",
        "sunset villa, sunset overwater",
    ),
    "/villas-residences/villas/1-bedroom-lagoon-pool-villas/": (
        "villas",
        "one_bedroom_lagoon_pool_villa",
        "lagoon villa, one bedroom lagoon",
    ),
    "/villas-residences/villas/1-bedroom-sunset-lagoon-pool-villas/": (
        "villas",
        "one_bedroom_sunset_lagoon_pool_villa",
        "sunset lagoon villa, lagoon sunset villa",
    ),
    "/villas-residences/villas/1-bedroom-beach-pool-villas/": (
        "villas",
        "one_bedroom_sunset_beach_pool_villa",
        "beach villa, sunset beach villa",
    ),
    "/villas-residences/villas/beach-pool-villas/": (
        "villas",
        "beach_pool_villa",
        "beach villa, beachfront villa",
    ),
    "/villas-residences/villas/family-beach-pool-villas/": (
        "villas",
        "family_beach_pool_villa",
        "family villa, kids villa, family beach villa",
    ),
    "/villas-residences/villas/2-bedroom-family-lagoon-pool-villas/": (
        "villas",
        "two_bedroom_family_lagoon_pool_villa",
        "two bedroom family villa, family lagoon villa",
    ),
    "/villas-residences/villas/2-bedroom-family-beach-pool-villas/": (
        "villas",
        "two_bedroom_family_beach_pool_villa",
        "two bedroom family beach villa, family beach villa two bedroom",
    ),
    "/villas-residences/residence/": (
        "residences",
        "residences_overview",
        "residence overview, residence collection",
    ),
    "/villas-residences/residence/2-bedroom-overwater-pool-villas/": (
        "residences",
        "two_bedroom_overwater_pool_residence",
        "overwater residence, two bedroom residence",
    ),
    "/villas-residences/residence/2-bedroom-beachfront-pool-residence/": (
        "residences",
        "two_bedroom_beachfront_pool_residence",
        "beachfront residence, family residence",
    ),
    "/villas-residences/residence/3-bedroom-overwater-residence/": (
        "residences",
        "three_bedroom_overwater_pool_residence",
        "three bedroom residence, 3br residence",
    ),
    "/villas-residences/residence/3-bedroom-lagoon-residence/": (
        "residences",
        "three_bedroom_lagoon_pool_residence",
        "three bedroom lagoon residence, lagoon residence",
    ),
    "/villas-residences/residence/3-bedroom-royal-beachfront-residence/": (
        "residences",
        "three_bedroom_royal_beachfront_pool_residence",
        "royal residence, most exclusive residence",
    ),
    "/restaurantsandbars/": (
        "dining",
        "dining_overview",
        "restaurants and bars, dining overview",
    ),
    "/restaurantsandbars/the-lighthouse/": (
        "dining",
        "the_lighthouse",
        "lighthouse restaurant, mediterranean restaurant, fine dining",
    ),
    "/restaurantsandbars/fish-market/": (
        "dining",
        "fish_market",
        "fish market restaurant, seafood restaurant",
    ),
    "/restaurantsandbars/cafe-umi/": (
        "dining",
        "cafe_umi",
        "cafe umi, breakfast restaurant, all day dining",
    ),
    "/restaurantsandbars/the-collective/": (
        "dining",
        "the_collective",
        "the collective, pool lounge, pizzeria",
    ),
    "/restaurantsandbars/the-retreat/": (
        "dining",
        "the_retreat",
        "the retreat, adults only bar, overwater lounge",
    ),
    "/spawellness/": ("spa", "avi_spa", "spa, avi spa, wellness, massage"),
    "/leisure/": ("activities", "water_sports", "water sports, recreation, snorkeling"),
    "/family/": ("family", "planet_trekkers", "kids club, planet trekkers, children activities"),
    "/gallery/": ("gallery", "gallery_misc", "gallery, resort photos"),
}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; internal-dev-asset-collector/1.0)"}


def safe_name(url: str) -> str:
    name = url.split("/")[-1].split("?")[0]
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return name or "image.jpg"


def collect() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    images_root = os.path.join(script_dir, "images")
    os.makedirs(images_root, exist_ok=True)
    manifest_rows: list[dict] = []

    for path, (category, room_name, tags) in PAGES.items():
        url = urljoin(BASE, path)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[skip] {url} -> {e}")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        image_urls: set[str] = set()

        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            image_urls.add(og_image["content"])

        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src and "wp-content/uploads" in src:
                image_urls.add(urljoin(BASE, src))

        out_dir = os.path.join(images_root, category)
        os.makedirs(out_dir, exist_ok=True)

        for img_url in sorted(image_urls):
            fname = safe_name(img_url)
            out_path = os.path.join(out_dir, fname)
            if not os.path.exists(out_path):
                try:
                    img_resp = requests.get(img_url, headers=HEADERS, timeout=15)
                    img_resp.raise_for_status()
                    with open(out_path, "wb") as f:
                        f.write(img_resp.content)
                    print(f"[ok] {out_path}")
                except requests.RequestException as e:
                    print(f"[fail] {img_url} -> {e}")
                    continue

            manifest_rows.append(
                {
                    "property_slug": "icmaldives",
                    "asset_type": "photo",
                    "room_name": room_name,
                    "tags": tags,
                    "caption": "",
                    "source_url": img_url,
                    "local_path": out_path,
                    "page": url,
                }
            )

        time.sleep(0.5)

    manifest_path = os.path.join(script_dir, "manifest.csv")
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "property_slug",
                "asset_type",
                "room_name",
                "tags",
                "caption",
                "source_url",
                "local_path",
                "page",
            ],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(f"\nDone. {len(manifest_rows)} images indexed in {manifest_path}")
    print(
        "Review manifest.csv, fill in captions, then merge into media_assets_seed.csv "
        "or import directly into your media_assets table via Admin CMS."
    )


if __name__ == "__main__":
    collect()
