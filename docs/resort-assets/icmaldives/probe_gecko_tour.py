"""Probe Gecko Digital tour page for deep-link parameters."""

import re
from pathlib import Path

import requests

URL = "https://geckodigital.co/vt/IntercontinentalMaldives/"
OUT = Path(__file__).resolve().parent / "tour_360_mapping.md"

resp = requests.get(URL, timeout=20)
text = resp.text

patterns = {
    "startscene": r"startscene[=:\"']+([a-zA-Z0-9_\-]+)",
    "nodeid": r"nodeid[=:\"']+([a-zA-Z0-9_\-]+)",
    "xml": r"([a-zA-Z0-9_\-]+\.xml)",
    "iframe_src": r'src="([^"]+)"',
}

findings: dict[str, list[str]] = {}
for name, pat in patterns.items():
    findings[name] = sorted(set(re.findall(pat, text)))

lines = [
    "# Gecko Digital 360 Tour Mapping",
    "",
    f"Base URL: {URL}",
    "",
    "## Automated probe results",
    "",
    "The tour is JS-rendered (Pano2VR/krpano). Scene deep links require manual browser inspection.",
    "Until scene-specific URLs are confirmed, all tour_360 assets use the base URL as iframe fallback.",
    "",
]
for name, values in findings.items():
    lines.append(f"### {name}")
    if values:
        for v in values[:20]:
            lines.append(f"- `{v}`")
    else:
        lines.append("- (none found in static HTML)")
    lines.append("")

lines.extend(
    [
        "## Manual mapping checklist",
        "",
        "Open the tour in Chrome, click each scene, and note the URL bar hash/query params.",
        "",
        "| room_name | Suggested scene | asset_url |",
        "|---|---|---|",
        "| resort_overview | Main island aerial | https://geckodigital.co/vt/IntercontinentalMaldives/ |",
        "| overwater_pool_villa | Overwater villa interior | TBD — add ?startscene= or hash after browser walk |",
        "| avi_spa | Spa treatment villa | TBD |",
        "| the_lighthouse | Lighthouse terrace | TBD |",
        "| two_bedroom_overwater_pool_residence | Residence deck | TBD |",
        "",
    ]
)

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {OUT}")
