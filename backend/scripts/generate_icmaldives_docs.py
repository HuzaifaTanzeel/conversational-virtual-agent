"""Generate InterContinental Maldives KB and Next Actions Word documents."""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"
KB_OUTPUT = DOCS_DIR / "InterContinental_Maldives_Maamunagau_KB.docx"
NEXT_OUTPUT = DOCS_DIR / "ICM_Resort_Next_Actions.docx"
KB_MD_OUTPUT = DOCS_DIR / "InterContinental_Maldives_Maamunagau_KB.md"


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


def add_bullet(doc: Document, text: str) -> None:
    doc.add_paragraph(text, style="List Bullet")


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


def build_kb_document() -> Document:
    doc = Document()
    title = doc.add_heading(
        "InterContinental Maldives Maamunagau Resort — Knowledge Base", 0
    )
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph(
        "Source: maldives.intercontinental.com (public marketing content, June 2026). "
        "Concise virtual-tour reference for the immersive video agent."
    )
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.runs[0].italic = True
    sub.runs[0].font.size = Pt(10)

    # ── Overview ────────────────────────────────────────────────────────────
    add_heading(doc, "Resort Overview", 1)
    add_para(
        doc,
        "InterContinental Maldives Maamunagau Resort is a luxury private-island resort in Raa "
        "Atoll, set on a vast lagoon that is a protected manta ray sanctuary beside a UNESCO "
        "Biosphere Reserve. It is a barefoot-luxury island with 81 villas and residences, six "
        "dining venues, an overwater spa, and a kids' and teens' club.",
    )
    add_bullet(doc, "Style: contemporary Maldivian design, private pools with every stay, barefoot luxury.")
    add_bullet(doc, "Setting: private island, house-reef snorkeling, year-round manta rays in the lagoon.")
    add_bullet(doc, "Getting there: scenic seaplane or domestic flight plus speedboat from Malé.")
    add_bullet(doc, "Every villa and residence includes complimentary Club InterContinental benefits.")
    add_para(
        doc,
        "Contact: WhatsApp +960 730 9300 · Resort phone +960 6580 500 · Reservations 1-888-IC-HOTELS.",
    )

    # ── How to think about the stay ─────────────────────────────────────────
    add_heading(doc, "Choosing a Stay (Quick Guide)", 1)
    add_bullet(doc, "Couples / honeymooners: overwater pool villas and sunset villas — romantic, private, ocean from the bed.")
    add_bullet(doc, "Small families (1 child): beach pool villas and lagoon pool villas — easy beach and lagoon access.")
    add_bullet(doc, "Larger families (2 kids): two-bedroom family villas — two-storey, more space, close to the kids' club.")
    add_bullet(doc, "Multi-generational families or groups: two- and three-bedroom residences — separate bedrooms, big living space, full privacy.")
    add_para(
        doc,
        "Villas are one-bedroom retreats for couples and small families. Residences are larger two- "
        "or three-bedroom homes with multiple bathrooms, expansive living and dining space, and the "
        "most personalised service — built for families and groups travelling together.",
    )

    # ── Overwater villas ────────────────────────────────────────────────────
    add_heading(doc, "Overwater Villas", 1)
    add_para(
        doc,
        "Overwater Pool Villa — one bedroom, one bathroom, perched on stilts above the lagoon with a "
        "private infinity pool and a sundeck with steps straight into the sea. Around 100 sqm. "
        "Best for couples; sleeps 2 adults.",
    )
    add_para(
        doc,
        "Sunset Overwater Pool Villa — the same overwater layout with the resort's best sunset-facing "
        "deck and infinity pool. One bedroom, one bathroom, around 100 sqm. Best for couples and "
        "honeymooners who want sunset views; sleeps 2 adults.",
    )

    # ── Beach villas ────────────────────────────────────────────────────────
    add_heading(doc, "Beach Villas", 1)
    add_para(
        doc,
        "Beach Pool Villa — one bedroom, one bathroom, a private garden and pool steps from the sand. "
        "Around 145 sqm. Best for couples or a couple with a young child; sleeps 2 adults and 1 child.",
    )
    add_para(
        doc,
        "One Bedroom Sunset Beach Pool Villa — a larger beachfront villa with lush tropical gardens, a "
        "private pool, and sunset views. Around 210 sqm. Best for couples wanting extra space and "
        "sunsets on the sand.",
    )
    add_para(
        doc,
        "Family Beach Pool Villa — one bedroom plus extra family sleeping space, a private pool, and "
        "direct beach access close to the Planet Trekkers kids' club. Around 180 sqm. Best for small "
        "families with children.",
    )
    add_para(
        doc,
        "Two Bedroom Family Beach Pool Villa — a two-storey beachfront villa with two bedrooms, multiple "
        "bathrooms, a private pool, and sunset orientation. Around 275 sqm. Best for families of four "
        "to five who want room to spread out by the beach.",
    )

    # ── Lagoon villas ───────────────────────────────────────────────────────
    add_heading(doc, "Lagoon Villas", 1)
    add_para(
        doc,
        "One Bedroom Lagoon Pool Villa — one bedroom, one bathroom, a sundeck and infinity plunge pool "
        "overlooking the calm lagoon. Around 150 sqm. Best for couples or a couple with a child.",
    )
    add_para(
        doc,
        "One Bedroom Sunset Lagoon Pool Villa — the lagoon villa oriented for sunset views, one bedroom "
        "with private pool. Around 150 sqm. Best for couples who love a sunset over the water.",
    )
    add_para(
        doc,
        "Two Bedroom Family Lagoon Pool Villa — a two-storey villa with two bedrooms, multiple bathrooms, "
        "a private pool, and gentle lagoon access. Around 175 sqm. Best for families with children who "
        "want safe, shallow water nearby.",
    )

    # ── Residences ──────────────────────────────────────────────────────────
    add_heading(doc, "Residences", 1)
    add_para(
        doc,
        "Two Bedroom Overwater Pool Residence — two bedrooms (one king, two twins), two en-suite "
        "bathrooms, a powder room, spacious living and dining, and a large overwater deck with a "
        "private infinity pool and steps into the sea. Around 295 sqm. Best for two couples or a family; "
        "sleeps up to 4 adults and 2 children.",
    )
    add_para(
        doc,
        "Two Bedroom Beachfront Pool Residence — a beachfront home with two bedrooms, multiple bathrooms, "
        "a large pool and lounge deck, and generous indoor-outdoor living. Around 535 sqm. Best for "
        "families wanting space right on the sand.",
    )
    add_para(
        doc,
        "Three Bedroom Overwater Pool Residence — the signature overwater stay with three bedrooms, "
        "multiple bathrooms, expansive living areas, and a wraparound deck with a private pool above the "
        "ocean. Around 460 sqm. Best for larger families or groups; sleeps up to 6 adults and 3 children.",
    )
    add_para(
        doc,
        "Three Bedroom Lagoon Pool Residence — an intimate lagoon-facing residence with three bedrooms, "
        "multiple bathrooms, a private pool deck, and sunset views. Around 610 sqm. Best for families "
        "and groups who prefer calm lagoon surroundings.",
    )
    add_para(
        doc,
        "Three Bedroom Royal Beachfront Pool Residence — the resort's most exclusive residence: three "
        "bedrooms, multiple bathrooms, vast living space, an oversized pool deck, and the most "
        "personalised service tier. Around 1,120 sqm. Best for VIP families and groups; sleeps up to 6 "
        "adults and 3 children.",
    )

    # ── Dining ──────────────────────────────────────────────────────────────
    add_heading(doc, "Dining", 1)
    add_para(
        doc,
        "Six restaurants and bars span fine dining, all-day casual, and relaxed sunset venues. "
        "A relaxed Island Chic dress code applies at the signature venues in the evening.",
    )
    add_para(
        doc,
        "The Lighthouse — the signature fine-dining restaurant serving a Mediterranean menu from the top "
        "of a lighthouse with 360-degree ocean and resort views. The romantic, special-occasion venue.",
    )
    add_para(
        doc,
        "Fish Market — a relaxed sea-to-table experience where guests pick their own fresh seafood, "
        "cooked with Southeast Asian flavours. Fun, social, and ocean-fresh.",
    )
    add_para(
        doc,
        "Café Umi — the all-day dining hub for breakfast, lunch and dinner, with international buffets, "
        "à la carte choices, and a live teppanyaki counter. The everyday, family-friendly venue with "
        "something for every taste.",
    )
    add_para(
        doc,
        "The Collective — a pool- and beach-view lounge for afternoon tea, aperitif hour and a casual "
        "pizzeria, with an island boutique alongside. Easy daytime grazing and drinks.",
    )
    add_para(
        doc,
        "The Retreat — an adults-only (18+) overwater enclave for cocktails, afternoon tea and "
        "sundowners; an intimate, grown-ups-only escape.",
    )
    add_para(
        doc,
        "Bars and special dining: the Pool Bar swim-up counter, the dhoni-shaped Sunset Bar for "
        "champagne at golden hour, a curated Wine Cellar, plus private Dining by Design on a beach, "
        "sandbank or in-villa, and hands-on cooking classes.",
    )

    # ── Spa & wellness ──────────────────────────────────────────────────────
    add_heading(doc, "AVI Spa and Wellness", 1)
    add_para(
        doc,
        "AVI Spa is an award-winning overwater spa with treatment villas suspended above the lagoon, "
        "using premium natural brands. Couples treatments, facials, massages and holistic therapies are "
        "available, alongside daily yoga on the beach or in the pavilion and an ocean-view fitness centre.",
    )

    # ── Activities ──────────────────────────────────────────────────────────
    add_heading(doc, "Activities and Experiences", 1)
    add_bullet(doc, "Water sports: complimentary non-motorised water sports, house-reef snorkeling, kayaks and paddleboards; diving and excursions available.")
    add_bullet(doc, "Manta rays: the lagoon is a protected manta sanctuary, with a seasonal Manta Ray Experience and an annual Manta Retreat in partnership with the Manta Trust.")
    add_bullet(doc, "Marine life: Raa Atoll has one of the world's largest, most diverse reef systems, ideal for snorkeling and dolphin and reef excursions.")
    add_bullet(doc, "Celebrations: weddings, honeymoons, special occasions, and exclusive full-island buyouts.")

    # ── Family ──────────────────────────────────────────────────────────────
    add_heading(doc, "Family and Kids", 1)
    add_bullet(doc, "Planet Trekkers kids' club (ages 4–12): supervised games, arts and crafts, and mini marine adventures.")
    add_bullet(doc, "Teen Escapades: a dedicated teens-only space with activities and group outings.")
    add_bullet(doc, "Family-friendly throughout: connecting family villas, lifeguarded pools and beaches, and cultural and nature workshops.")

    # ── Club InterContinental ───────────────────────────────────────────────
    add_heading(doc, "Club InterContinental", 1)
    add_para(
        doc,
        "Included with every villa and residence: private lounge access, daily breakfast, and evening "
        "cocktails and canapés, with enhanced personalised service for an elevated, all-day experience.",
    )

    # ── Practical / booking ─────────────────────────────────────────────────
    add_heading(doc, "Good to Know", 1)
    add_bullet(doc, "All villas and residences have a private pool and complimentary Club InterContinental benefits.")
    add_bullet(doc, "Prices, live availability and exact seasonal dates change frequently — these are handled by the reservations team, not quoted here.")
    add_bullet(doc, "To book or check dates: WhatsApp +960 730 9300 or reservations 1-888-IC-HOTELS.")

    return doc


def build_next_actions_document() -> Document:
    doc = Document()
    title = doc.add_heading("InterContinental Maldives — Next Action Items", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_para(doc, "Follow-up checklist after content and media collection phase. June 2026.")

    add_heading(doc, "Phase A — Content Phase (this delivery)", 1)
    items_a = [
        "Run collect_resort_images.py locally; review manifest.csv and primary_images.csv.",
        "Curated images copied to frontend/public/resort-media/icmaldives/ — use /resort-media/... URLs in Admin CMS.",
        "Seed property via: python backend/scripts/seed_icmaldives_property.py",
        "Upload InterContinental_Maldives_Maamunagau_KB.docx to Tavus Documents; attach document_id to persona.",
        "Map Gecko Digital 360 tour deep links (browser walk-through) for tour_360 rows in media_assets_seed.csv.",
    ]
    for item in items_a:
        add_bullet(doc, item)

    add_heading(doc, "Phase B — Tavus Tool Registration", 1)
    items_b = [
        "Register show_media on persona layers.llm.tools via platform.tavus.io or PATCH /v2/personas/{persona_id}.",
        "Mirror tool schema from backend/app/api/llm_chat.py TOOLS array.",
        "Add enum of canonical room_name values to tool schema (biggest win for match precision).",
        "Confirm conversation.tool_call fires on Daily data channel; verify useTavus.js resolves and MediaPanel renders.",
    ]
    for item in items_b:
        add_bullet(doc, item)

    add_heading(doc, "Phase C — Testing Matrix", 1)
    add_para(doc, "Sample guest utterances and expected room_name:")
    add_table(
        doc,
        ["Guest utterance", "Expected asset_type", "Expected room_name"],
        [
            ["What does the overwater pool villa look like?", "photo", "overwater_pool_villa"],
            ["Can I see a 360 tour of the spa?", "tour_360", "avi_spa"],
            ["Where would we have dinner?", "photo", "the_lighthouse"],
            ["Show me the kids club", "photo", "planet_trekkers"],
            ["Tell me about the sunset bar", "photo", "sunset_bar"],
            ["Show me the royal residence", "photo", "three_bedroom_royal_beachfront_pool_residence"],
            ["Can I see the whole resort?", "tour_360", "resort_overview"],
            ["What water sports do you offer?", "photo", "water_sports"],
        ],
    )
    add_bullet(doc, "Run smoke_test_icmaldives_media.py to verify resolver without a live call.")
    add_bullet(doc, "Log room_name extracted → resolved asset → intended asset in tool_call_logs.")
    add_bullet(doc, "Iterate tags synonyms and tool enum on misses, not the matching algorithm.")

    add_heading(doc, "Phase D — Engineering Follow-ups", 1)
    items_d = [
        "Add document_ids to conversation create in backend/app/api/session.py.",
        "Scope media resolution by property_id (today resolver ignores property).",
        "Use conversation.append_llm_context after frontend resolves asset so avatar speech matches what's on screen.",
        "Reduce or disable Qdrant in /llm/chat once Tavus KB is verified with custom LLM.",
        "Add static media upload endpoint or S3/CDN for production (replace hotlinks).",
        "Deduplicate double resolution/logging (LLM path + frontend tool-call path).",
        "Request official resort media kit for production licensing.",
        "Open question: confirm whether Tavus injects persona document_ids into custom LLM requests before /llm/chat is called.",
    ]
    for item in items_d:
        add_bullet(doc, item)

    add_heading(doc, "360 Tour Mapping Notes", 1)
    add_para(
        doc,
        "Gecko Digital tour base URL: https://geckodigital.co/vt/IntercontinentalMaldives/ "
        "Deep-link scene parameters require manual browser inspection (JS-rendered Pano2VR/krpano). "
        "Until deep links are mapped, all tour_360 rows use the full tour homepage as fallback iframe.",
    )

    add_heading(doc, "Copyright Notice", 1)
    add_para(
        doc,
        "Scraped IHG/resort marketing images are for local dev/testing of the show_media pipeline only. "
        "Do not ship in a customer-facing product without a media license from the property.",
    )

    return doc


def write_kb_markdown() -> None:
    content = """# InterContinental Maldives Maamunagau Resort — Knowledge Base

Source: maldives.intercontinental.com (public marketing content, June 2026).
Concise virtual-tour reference for the immersive video agent.

## Resort Overview

InterContinental Maldives Maamunagau Resort is a luxury private-island resort in Raa Atoll,
set on a vast lagoon that is a protected manta ray sanctuary beside a UNESCO Biosphere
Reserve. It is a barefoot-luxury island with 81 villas and residences, six dining venues,
an overwater spa, and a kids' and teens' club. Every villa and residence has a private pool
and complimentary Club InterContinental benefits.

Contact: WhatsApp +960 730 9300 · Resort phone +960 6580 500 · Reservations 1-888-IC-HOTELS.

## Choosing a Stay

- Couples / honeymooners: overwater pool villas and sunset villas.
- Small families (1 child): beach pool villas and lagoon pool villas.
- Larger families (2 kids): two-bedroom family villas (two-storey, near the kids' club).
- Groups / multi-generational: two- and three-bedroom residences.

## Overwater Villas

- Overwater Pool Villa — 1 bed, 1 bath, private pool over the lagoon, ~100 sqm. Couples (2 adults).
- Sunset Overwater Pool Villa — same layout with the best sunset deck, ~100 sqm. Couples (2 adults).

## Beach Villas

- Beach Pool Villa — 1 bed, 1 bath, garden + pool by the sand, ~145 sqm. 2 adults + 1 child.
- One Bedroom Sunset Beach Pool Villa — larger beachfront villa with sunset views, ~210 sqm. Couples.
- Family Beach Pool Villa — 1 bed plus family sleeping space, near the kids' club, ~180 sqm. Small families.
- Two Bedroom Family Beach Pool Villa — two-storey, 2 beds, multiple baths, ~275 sqm. Families of 4–5.

## Lagoon Villas

- One Bedroom Lagoon Pool Villa — 1 bed, 1 bath, plunge pool over the lagoon, ~150 sqm. Couples.
- One Bedroom Sunset Lagoon Pool Villa — sunset-facing lagoon villa, ~150 sqm. Couples.
- Two Bedroom Family Lagoon Pool Villa — two-storey, 2 beds, multiple baths, ~175 sqm. Families.

## Residences

- Two Bedroom Overwater Pool Residence — 2 beds, 2 baths, big overwater deck + pool, ~295 sqm. Up to 4 adults + 2 children.
- Two Bedroom Beachfront Pool Residence — 2 beds, multiple baths, large pool deck, ~535 sqm. Families on the sand.
- Three Bedroom Overwater Pool Residence — signature overwater stay, 3 beds, ~460 sqm. Up to 6 adults + 3 children.
- Three Bedroom Lagoon Pool Residence — 3 beds, lagoon-facing with sunset views, ~610 sqm. Families and groups.
- Three Bedroom Royal Beachfront Pool Residence — most exclusive, 3 beds, ~1,120 sqm. Up to 6 adults + 3 children.

## Dining

- The Lighthouse — Mediterranean fine dining atop a lighthouse with 360° views; special-occasion venue.
- Fish Market — sea-to-table, pick-your-own seafood with Southeast Asian flavours; relaxed and social.
- Café Umi — all-day dining for breakfast, lunch and dinner with a live teppanyaki counter; family-friendly.
- The Collective — pool/beach-view lounge, afternoon tea, aperitifs and pizzeria, plus an island boutique.
- The Retreat — adults-only (18+) overwater lounge for cocktails and sundowners.
- Bars & special dining — Pool Bar, dhoni-shaped Sunset Bar, Wine Cellar, private Dining by Design, cooking classes.

## AVI Spa and Wellness

Award-winning overwater spa with treatment villas above the lagoon, premium natural brands,
couples treatments, daily yoga, and an ocean-view fitness centre.

## Activities

- Complimentary non-motorised water sports, house-reef snorkeling, kayaks and paddleboards.
- Protected manta sanctuary with a seasonal Manta Ray Experience and annual Manta Retreat.
- Diving, marine excursions, weddings, honeymoons, and exclusive island buyouts.

## Family and Kids

- Planet Trekkers kids' club (ages 4–12) and Teen Escapades for teens.
- Connecting family villas, lifeguarded pools and beaches, cultural and nature workshops.

## Club InterContinental

Included with every stay: private lounge, daily breakfast, evening cocktails and canapés,
and enhanced personalised service.

## Good to Know

- Every villa and residence has a private pool and Club InterContinental benefits.
- Prices and live availability are handled by reservations (WhatsApp +960 730 9300).
"""
    KB_MD_OUTPUT.write_text(content, encoding="utf-8")


def main() -> None:
    kb_doc = build_kb_document()
    kb_doc.save(KB_OUTPUT)
    next_doc = build_next_actions_document()
    next_doc.save(NEXT_OUTPUT)
    write_kb_markdown()
    print(f"Wrote {KB_OUTPUT}")
    print(f"Wrote {NEXT_OUTPUT}")
    print(f"Wrote {KB_MD_OUTPUT}")


if __name__ == "__main__":
    main()
