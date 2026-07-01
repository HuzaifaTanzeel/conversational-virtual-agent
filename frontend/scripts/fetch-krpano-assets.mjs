/**
 * Reproducibly mirror the InterContinental Maldives krpano tour into
 * frontend/public/vt/icmaldives/ so the viewer is served same-origin
 * (geckodigital.co does not send CORS headers, so the XML/skin must be
 * local). Pano tiles are NOT mirrored — they stream at runtime from the
 * Gecko CDN (cdn_url), which serves them cross-origin in the browser.
 *
 * Usage:  node frontend/scripts/fetch-krpano-assets.mjs
 *
 * Re-run this if Gecko ships an updated tour (also regenerate
 * src/lib/tourNavigation.js from the new scenes.xml/layout.xml).
 */
import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const TOUR_BASE = "https://geckodigital.co/vt/IntercontinentalMaldives/";
const TEMPLATE_BASE = "https://geckodigital.co/vt/!template/";

// destPath is relative to frontend/public/vt/icmaldives/
//
// NOTE: layout.xml and skin/vtourskin.xml are intentionally NOT mirrored here.
// Gecko ships them krpano-"encrypted" and license/domain-locked to
// geckodigital.co, so the krpano engine cannot decrypt them off our own origin
// ("XML parsing failed"). They are replaced by local, unencrypted hand-written
// equivalents (see template/skin/vtourskin.xml + template/layout.xml). Do not
// re-add them here or you will re-break the tour. If Gecko provides UNENCRYPTED
// menu/skin sources, drop them in directly instead.
const ASSETS = [
  { url: TOUR_BASE + "tour.xml", dest: "tour.xml" },
  { url: TOUR_BASE + "scenes.xml", dest: "scenes.xml" },
  { url: TEMPLATE_BASE + "tour.js", dest: "template/tour.js" },
  { url: TEMPLATE_BASE + "skin/vtourskin.png", dest: "template/skin/vtourskin.png" },
  { url: TEMPLATE_BASE + "skin/rotate_device.png", dest: "template/skin/rotate_device.png" },
];

const here = dirname(fileURLToPath(import.meta.url));
const outRoot = join(here, "..", "public", "vt", "icmaldives");

async function run() {
  for (const { url, dest } of ASSETS) {
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`Failed ${res.status} for ${url}`);
    }
    const buf = Buffer.from(await res.arrayBuffer());
    const outPath = join(outRoot, dest);
    await mkdir(dirname(outPath), { recursive: true });
    await writeFile(outPath, buf);
    console.log(`ok  ${dest}  (${buf.length} bytes)`);
  }
  console.log("\nDone. Tiles stream from the Gecko CDN at runtime (cdn_url).");
}

run().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
