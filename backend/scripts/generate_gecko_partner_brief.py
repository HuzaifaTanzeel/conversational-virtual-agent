"""Generate Gecko Digital partner integration brief (DOCX + PDF if possible)."""

from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DOCX = REPO_ROOT / "docs" / "Gecko_Partner_Integration_Brief.docx"
OUTPUT_PDF = REPO_ROOT / "docs" / "Gecko_Partner_Integration_Brief.pdf"


def set_cell_shading(cell, color: str) -> None:
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), color)
    cell._tc.get_or_add_tcPr().append(shading)


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


def build_document() -> Document:
    doc = Document()

    title = doc.add_heading(
        "Gecko Digital — AI-Guided 360° Tour Integration Brief", 0
    )
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sub = doc.add_paragraph(
        "Partner requirements & current workaround (InterContinental Maldives Maamunagau)"
    )
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in sub.runs:
        run.italic = True
        run.font.size = Pt(11)

    meta = doc.add_paragraph(f"Prepared: {date.today().strftime('%d %B %Y')}")
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()

    # --- Executive summary ---
    doc.add_heading("1. Purpose of this document", level=1)
    add_para(
        doc,
        "We are building an AI-guided property tour for the InterContinental Maldives "
        "Maamunagau resort website. A guest joins a live video call with an AI agent, "
        "speaks naturally (e.g. “Show me the main pool”), and the 360° virtual tour "
        "moves to that location while the agent explains the resort.",
    )
    add_para(
        doc,
        "This product is intended to deliver the same look and feel as the existing "
        "Gecko Digital tour on geckodigital.co — not a separate or simplified "
        "third-party experience. This document explains:",
        bold=True,
    )
    add_bullet(doc, "How the solution works today (without special Gecko access)")
    add_bullet(doc, "What gaps remain compared to the live Gecko website")
    add_bullet(doc, "The minimum deliverables we need from Gecko to close those gaps")
    add_bullet(doc, "Plain-language reasons for each request (for non-technical stakeholders)")

    # --- Current operation ---
    doc.add_heading("2. How we operate today (without Gecko special access)", level=1)
    add_para(
        doc,
        "Important: We have NOT received any special API, license, unencrypted skin "
        "files, or embed permission from Gecko yet. What works today is built from "
        "publicly available tour configuration and our own engineering workarounds.",
        bold=True,
    )

    doc.add_heading("2.1 End-to-end flow (guest experience)", level=2)
    flow_steps = [
        ("Guest joins call", "Opens the resort’s AI tour page and starts a video session with a Tavus AI avatar."),
        ("Guest speaks", "Says e.g. “Show me the overwater pool villa” or “Take me to the spa.”"),
        ("AI understands", "Tavus (hosted LLM + resort knowledge base uploaded in Tavus) decides to navigate and calls the navigate_to_area tool."),
        ("Frontend receives tool call", "Our app listens on the Daily.co video channel for a conversation.tool_call event from Tavus."),
        ("Area is resolved", "Our code maps the area name (e.g. “main pool”) to an internal krpano scene id (e.g. scene_MainPool) using a list we built from Gecko’s scenes.xml."),
        ("Tour moves", "We call krpano’s loadscene() to jump directly to that 360° scene with a short crossfade."),
        ("Agent speaks", "The avatar describes the location while the guest looks around freely."),
    ]
    for step, detail in flow_steps:
        add_para(doc, f"{step}: ", bold=True)
        add_para(doc, detail)

    doc.add_heading("2.2 Technical components (what runs where)", level=2)
    add_table(
        doc,
        ["Component", "Source", "Role"],
        [
            [
                "AI voice + conversation",
                "Tavus (cloud)",
                "Speech-to-text, LLM, text-to-speech, avatar video; knowledge base hosted in Tavus UI",
            ],
            [
                "Tour engine",
                "krpano (Gecko’s tour.js, vendored locally)",
                "Renders the 360° viewer in the browser",
            ],
            [
                "Tour structure",
                "tour.xml, scenes.xml (copied from Gecko tour)",
                "Defines 66 scenes, links between rooms, hotspot positions",
            ],
            [
                "Panorama images",
                "Gecko CDN (vt-cdn.geckodigital.app)",
                "High-resolution tile images for each scene",
            ],
            [
                "Skin & menus",
                "Our minimal replacement files",
                "Gecko’s original vtourskin.xml and layout.xml are encrypted for geckodigital.co only — we use simplified substitutes",
            ],
            [
                "Agent navigation",
                "krpanoController.js + tourNavigation.js",
                "Maps spoken area names to scene ids and calls loadscene()",
            ],
            [
                "Image proxy (dev)",
                "Our Vite server (/resort-cdn/)",
                "Workaround because CDN tiles lack CORS headers for cross-origin WebGL loading",
            ],
        ],
    )

    doc.add_heading("2.3 What works today", level=2)
    add_bullet(doc, "Guest can see the 360° tour (panorama tiles load via same-origin proxy)")
    add_bullet(doc, "AI agent can navigate to the correct scene when the guest asks for a known area")
    add_bullet(doc, "108 canonical area names registered on the Tavus persona (enum) to reduce wrong locations")
    add_bullet(doc, "Disambiguation when a room name exists in multiple villas (e.g. “master bedroom”)")
    add_bullet(doc, "In-pano navigation hotspots exist (minimal white-dot style)")

    doc.add_heading("2.4 What does NOT match the Gecko website today", level=2)
    add_bullet(doc, "Bottom navigation bar (AERIAL / ACCOMMODATION / DINING / FACILITIES) — hidden")
    add_bullet(doc, "Per-villa room sub-menus (e.g. MASTER BEDROOM, POOL DECK) — hidden")
    add_bullet(doc, "Gecko’s branded hotspot icons and hover effects — replaced with simple dots")
    add_bullet(doc, "Loading spinner while tiles stream — not present")
    add_bullet(doc, "Smooth zoom-in / zoom-out transition when moving between rooms — we teleport with a basic crossfade")
    add_bullet(doc, "Walking through linked scenes along a path — we jump directly to the destination")
    add_bullet(doc, "Official CDN loading without proxy — requires workaround today")

    add_para(
        doc,
        "Bottom line: Navigation to the correct place works, but the experience does not "
        "feel like geckodigital.co because the polished UI and transitions live inside "
        "Gecko’s protected skin files.",
        bold=True,
    )

    # --- Why not direct from gecko ---
    doc.add_heading("3. Why we cannot simply embed geckodigital.co as-is", level=1)

    doc.add_heading("3.1 Iframe of the live Gecko tour", level=2)
    add_para(
        doc,
        "We could show geckodigital.co/.../IntercontinentalMaldives/ in an iframe and "
        "guests would see the full Gecko experience. However, our JavaScript cannot "
        "control the tour inside a cross-origin iframe (browser security). The AI agent "
        "would not be able to move the tour when the guest speaks.",
    )

    doc.add_heading("3.2 Loading tour files directly from geckodigital.co", level=2)
    add_para(doc, "Two blockers:")
    add_bullet(doc, "CORS: geckodigital.co does not allow our domain to fetch tour XML/JS cross-origin.")
    add_bullet(
        doc,
        "Encrypted skin: vtourskin.xml and layout.xml are krpano-encrypted and domain-locked "
        "to geckodigital.co. Off that domain, krpano fails with “XML parsing failed.”",
    )

    doc.add_heading("3.3 CDN tiles without proxy", level=2)
    add_para(
        doc,
        "Panorama tiles on vt-cdn.geckodigital.app return HTTP 200 but without "
        "Access-Control-Allow-Origin headers. Browsers block them as WebGL textures "
        "when the tour runs on our domain — resulting in a black screen. The proxy is "
        "a workaround, not the desired production architecture.",
    )

    # --- Requirements ---
    doc.add_heading("4. Minimum requirements to ask Gecko (recommended)", level=1)
    add_para(
        doc,
        "These five items are the smallest set that removes almost all current pain "
        "and lets us deliver the same feel as the Gecko website on the client’s domain.",
    )

    requirements = [
        (
            "Requirement 1 — Unencrypted skin & menu files",
            "Deliver plain-text (unencrypted) versions of vtourskin.xml and layout.xml, "
            "licensed for our deployment domain(s).",
            "On your live site, guests see the familiar menu bar, smooth room transitions, "
            "branded hotspot icons, and loading indicators. Those live in protected files "
            "we cannot use off geckodigital.co. We currently run a stripped-down substitute. "
            "Without your unencrypted files, we cannot match your website’s look and behavior — "
            "no matter how good the AI is.",
        ),
        (
            "Requirement 2 — Embed license for our domain",
            "Official permission (and any krpano license/key needed) to run the full tour "
            "on the client/resort domain, not only on geckodigital.co.",
            "Your tour is built to run on your domain. When we run it on the resort’s site, "
            "protected parts fail or we must use simplified replacements. We need the same "
            "tour package you would provide for a white-label or embedded partner deployment.",
        ),
        (
            "Requirement 3 — CDN access from our domain",
            "Either: (A) add CORS headers on vt-cdn.geckodigital.app for our domain(s), "
            "OR (B) written approval for a stable same-origin proxy path to your CDN.",
            "360° photos live on your CDN. Browsers block them from another site unless you "
            "explicitly allow it. We currently proxy images so the tour works — that is fragile "
            "and not ideal for production. A clear CDN policy from Gecko makes loading reliable "
            "and official, like on your site.",
        ),
        (
            "Requirement 4 — Official scene / area name list",
            "A reference document or export: human-readable labels (e.g. “Main Pool”, "
            "“Beach Pool Villa – Bedroom”) mapped to internal scene ids, plus notes on "
            "ambiguous names (e.g. “master bedroom” in multiple villas).",
            "The AI must use the same names your tour uses. We built our list from public "
            "tour files, but if you update the tour, our list can drift. A single source of "
            "truth from Gecko avoids wrong rooms and extra back-and-forth when content changes.",
        ),
        (
            "Requirement 5 — Tour update process",
            "Agree who notifies us when scenes are added/removed/renamed, how we receive "
            "updated tour.xml / scenes.xml / skin files, and whether a staging URL exists "
            "for testing before go-live.",
            "Resorts change villas, photos, and labels over time. Without a simple update "
            "process, the AI might say “I’ll show you X” while the tour still points to old "
            "content. A light “tour updated → send files → we verify” workflow keeps AI and "
            "your site in sync.",
        ),
    ]

    for title_text, ask, reason in requirements:
        doc.add_heading(title_text, level=2)
        add_para(doc, "What to ask:", bold=True)
        add_para(doc, ask)
        add_para(doc, "Why (plain language):", bold=True)
        add_para(doc, reason)
        doc.add_paragraph()

    # --- Optional ---
    doc.add_heading("5. Optional (nice to have — not required for v1)", level=1)
    add_table(
        doc,
        ["Optional ask", "Why"],
        [
            [
                "iframe + postMessage API",
                "Embed your exact live page and still move the tour when the guest speaks — only if Gecko prefers hosting everything on geckodigital.co",
            ],
            ["Staging tour URL", "Test changes without affecting the live resort site"],
            ["Brand assets", "Logo, hotspot icons, loading graphic for pixel-perfect match"],
        ],
    )

    # --- What we don't need ---
    doc.add_heading("6. What we do NOT need from Gecko for v1", level=1)
    add_bullet(doc, "A custom Gecko backend or new product — we use Tavus for AI and our stack for integration")
    add_bullet(doc, "Gecko to build the AI — voice, LLM, and knowledge base are handled by Tavus")
    add_bullet(
        doc,
        "We DO need the same tour files and permissions you would give any serious embed partner",
    )

    # --- Comparison table ---
    doc.add_heading("7. Side-by-side: today vs. with Gecko deliverables", level=1)
    add_table(
        doc,
        ["Capability", "Today (workaround)", "With Gecko minimum package"],
        [
            ["Show correct 360° location when guest asks", "Yes", "Yes"],
            ["Match Gecko site menus (AERIAL, ACCOMMODATION, etc.)", "No — hidden", "Yes"],
            ["Branded hotspot icons", "No — simple dots", "Yes"],
            ["Loading indicator while tiles load", "No", "Yes"],
            ["Zoom-in/out transition between rooms", "No — basic crossfade teleport", "Yes"],
            ["Official CDN loading (no proxy)", "No — proxy workaround", "Yes"],
            ["Stay in sync when tour is updated", "Manual / fragile", "Yes — with agreed process"],
        ],
    )

    # --- Email template ---
    doc.add_heading("8. One-paragraph summary (for email)", level=1)
    email = (
        "Minimum from Gecko to match your site experience: (1) Unencrypted vtourskin.xml "
        "and layout.xml licensed for our deployment domain, (2) Right to run the full krpano "
        "tour off geckodigital.co, (3) CDN access from our domain (CORS or approved proxy), "
        "(4) Official scene/area name list aligned with the tour, and (5) A simple process "
        "when the tour is updated. Today we already move the tour by voice using a workaround "
        "(copied config + direct scene jumps + image proxy), but guests don’t get your menus, "
        "loading animation, zoom transitions, or branded hotspots. Those come from your "
        "protected skin files — which is why we need your help to deliver the same feel as "
        "your website for this partnership."
    )
    add_para(doc, email, italic=True)

    # --- Domains to fill in ---
    doc.add_heading("9. Information to provide Gecko when requesting", level=1)
    add_para(doc, "Fill in before sending:", bold=True)
    add_bullet(doc, "Production domain(s): e.g. https://resort-client.com/tour")
    add_bullet(doc, "Staging domain(s): e.g. https://staging.resort-client.com")
    add_bullet(doc, "Contact person on our side for tour updates")
    add_bullet(doc, "Contact person on Gecko side for file delivery")
    add_bullet(doc, "Target go-live date (if known)")

    doc.add_heading("10. Reference — key file paths in our project", level=1)
    add_para(doc, "For internal technical follow-up (optional to share with Gecko engineering):")
    refs = [
        "frontend/public/vt/icmaldives/ — vendored tour (tour.xml, scenes.xml, template/)",
        "frontend/public/vt/icmaldives/README.md — documents encryption/CORS constraints",
        "frontend/src/lib/krpanoController.js — agent navigation (loadscene)",
        "frontend/src/lib/tourNavigation.js — area name → scene id mapping (108 areas)",
        "frontend/src/hooks/useTavus.js — receives Tavus tool_call events",
        "backend/scripts/register_navigate_to_area_tool.py — registers tool on Tavus persona",
    ]
    for ref in refs:
        add_bullet(doc, ref)

    footer = doc.add_paragraph()
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run("— End of document —")
    run.italic = True
    run.font.size = Pt(10)

    return doc


def try_docx_to_pdf(docx_path: Path, pdf_path: Path) -> bool:
    """Convert DOCX to PDF via Microsoft Word COM (Windows only)."""
    try:
        import win32com.client  # type: ignore

        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(str(docx_path.resolve()))
        doc.SaveAs(str(pdf_path.resolve()), FileFormat=17)  # wdFormatPDF
        doc.Close()
        word.Quit()
        return pdf_path.exists()
    except Exception as exc:
        print(f"PDF via Word COM failed: {exc}")
        return False


def main() -> None:
    doc = build_document()
    OUTPUT_DOCX.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT_DOCX)
    print(f"Wrote {OUTPUT_DOCX}")

    if try_docx_to_pdf(OUTPUT_DOCX, OUTPUT_PDF):
        print(f"Wrote {OUTPUT_PDF}")
    else:
        print(
            "PDF not generated automatically. Open the DOCX in Microsoft Word and "
            "use File → Save As → PDF, or install pywin32 for automatic conversion."
        )


if __name__ == "__main__":
    main()
