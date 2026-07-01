# InterContinental Maldives — vendored krpano tour

These files are a same-origin mirror of Gecko Digital's live krpano tour
(`https://geckodigital.co/vt/IntercontinentalMaldives/`). They are vendored
here because `geckodigital.co` does not send CORS headers, so the tour XML and
skin must be served from our own origin for `embedpano()` to load them.

Layout:

```
tour.xml            # krpano root (includes skin + layout + scenes)
scenes.xml          # 66 scenes; tiles reference cdn_url (Gecko CDN)
template/
  tour.js           # krpano library (provides embedpano)
  layout.xml        # UNENCRYPTED menu styles (local replacement — see below)
  layout.gecko-encrypted.xml.bak       # original Gecko file (encrypted, unusable here)
  skin/
    vtourskin.xml   # UNENCRYPTED skin_settings + hotspot style (local replacement)
    vtourskin.gecko-encrypted.xml.bak  # original Gecko file (encrypted, unusable here)
    vtourskin.png   # skin sprite atlas
    rotate_device.png
```

## Why `vtourskin.xml` / `layout.xml` are hand-written (not mirrored)

Gecko ships these two files krpano-**encrypted** and license/domain-locked to
`geckodigital.co`. The krpano engine cannot decrypt them when the tour is served
from any other origin, so it aborts at startup with
`vtourskin.xml - XML parsing failed` and nothing renders.

We therefore replaced them with local, unencrypted equivalents that define just
what the tour references: `skin_settings` (view defaults), `skin_hotspotstyle`
(clickable scene-to-scene hotspots), and the menu styles. The originals are kept
as `*.gecko-encrypted.xml.bak` for reference.

Trade-off: Gecko's *designed* nav menu (the AERIAL / ACCOMMODATION / DINING bar
+ per-villa room menus) is hidden, because its show/hide interaction logic also
lived inside the encrypted file. Navigation still works via the in-pano hotspots
and the AI agent. To restore the designed menu, obtain **unencrypted** menu/skin
sources from Gecko and drop them in (see "What to request from Gecko" below).

## What to request from Gecko

Ask Gecko (our partner) for **unencrypted / plain-text source** of:

- `vtourskin.xml` (skin + control bar + hotspot styles)
- `layout.xml` (the menu styles + show/hide interaction logic)

i.e. the tour exported **without krpano XML protection/encryption**, OR licensed
for our domain so we can re-export it unprotected. With those, restore the full
designed UI by replacing the two local files. Everything else (`tour.xml`,
`scenes.xml`, pano tiles) already works as-is.

Runtime wiring (see `src/components/TourViewer.jsx`):

- `embedpano({ xml: '/vt/icmaldives/tour.xml', initvars: { path: '/vt/icmaldives/template/', cdn_url: 'https://vt-cdn.geckodigital.app/' } })`
- `path` makes `tour.xml`'s `calc:path + 'skin/...'` / `calc:path + 'layout.xml'` resolve into `template/`.
- `cdn_url` makes `scenes.xml`'s `calc:cdn_url + 'IntercontinentalMaldives/panos/...'` stream pano tiles from the Gecko CDN (it serves them with CORS in-browser).

## Regenerating

```
node scripts/fetch-krpano-assets.mjs
```

Re-run after Gecko ships an updated tour, and regenerate
`src/lib/tourNavigation.js` from the new `scenes.xml` / `layout.xml`.

Pano tiles are intentionally NOT mirrored (gigabytes); they load from the CDN.
If the CDN ever stops allowing cross-origin texture loads, proxy it same-origin
and point `cdn_url` at the proxy.
