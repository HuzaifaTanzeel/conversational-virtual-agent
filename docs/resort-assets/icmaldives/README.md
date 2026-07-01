# InterContinental Maldives — Resort Assets

Sample media and knowledge-base content for testing `show_media` with the ICM resort.

## Quick start

```powershell
cd docs/resort-assets/icmaldives
pip install requests beautifulsoup4
python collect_resort_images.py
python curate_primary_images.py
python patch_seed_dining.py
```

```powershell
# Seed DB (requires Docker backend + postgres)
docker cp docs/resort-assets/icmaldives/media_assets_seed.csv avatour-backend:/tmp/media_assets_seed.csv
docker exec -e SEED_CSV=/tmp/media_assets_seed.csv avatour-backend python scripts/seed_icmaldives_property.py
docker exec avatour-backend python scripts/smoke_test_icmaldives_media.py
```

## Deliverables

| File | Purpose |
|------|---------|
| `media_assets_seed.csv` | Canonical room_name + tags catalog (comma-separated tags) |
| `manifest.csv` | Raw scraper output (gitignored) |
| `primary_images.csv` | One primary image per room_name |
| `tour_360_mapping.md` | Gecko Digital tour notes and deep-link checklist |
| `tavus_document_id.txt` | Tavus KB document ID attached to persona |
| `../InterContinental_Maldives_Maamunagau_KB.docx` | Curated KB for manual Tavus upload |
| `../ICM_Resort_Next_Actions.docx` | Follow-up engineering checklist |

## Media URLs

Curated photos live under `frontend/public/resort-media/icmaldives/` and are referenced as `/resort-media/...` in the seed CSV. Vite serves these at `http://localhost:5173/resort-media/...` during dev.

360 tours use `https://geckodigital.co/vt/IntercontinentalMaldives/` until scene deep links are mapped.

## Tavus Knowledge Base

- **Website crawl (automated):** document ID in `tavus_document_id.txt`, attached to persona `p5d4d7d09196`
- **Curated docx (manual):** upload `docs/InterContinental_Maldives_Maamunagau_KB.docx` at [platform.tavus.io/documents](https://platform.tavus.io/documents) for the structured agent instructions version

## Copyright

Scraped resort images are for local dev/testing only. Do not ship without a media license from the property.
