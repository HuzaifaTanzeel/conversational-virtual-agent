/**
 * Validates scene nav: registry IDs vs Gecko tour.xml l_menu links.
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");

const tourRaw = fs.readFileSync(path.join(root, "public/vt/icmaldives/tour.xml"), "utf8");
// Ignore commented-out l_menu entries (e.g. Master Living Room not in registry)
const tour = tourRaw.replace(/<!--[\s\S]*?-->/g, "");
const regSrc = fs.readFileSync(path.join(root, "src/lib/sceneRegistry.js"), "utf8");

const registryIds = new Set(
  [...regSrc.matchAll(/krpanoSceneId:\s*"(scene_[^"]+)"/g)].map((m) => m[1]),
);

const lmenuLinks = [
  ...tour.matchAll(/<layer style="l_menu"[^>]*linkedscene="(scene_[^"]+)"/g),
].map((m) => m[1]);

let errors = 0;
let warnings = 0;

console.log("=== Gecko l_menu links not in sceneRegistry ===");
for (const sceneId of lmenuLinks) {
  if (!registryIds.has(sceneId)) {
    console.error("ERROR:", sceneId, "in tour.xml l_menu but not in registry");
    errors++;
  }
}

console.log("\n=== Registry scenes in multi-scene categories (informational) ===");
// Dynamic import of sceneNavGroups would need built env; parse categories inline
const categories = {};
for (const m of regSrc.matchAll(
  /"([^"]+)":\s*\{\s*krpanoSceneId:\s*"(scene_[^"]+)",\s*label:\s*"([^"]+)",\s*category:\s*"([^"]+)"/g,
)) {
  const [, , krpanoSceneId, , category] = m;
  if (!categories[category]) categories[category] = [];
  categories[category].push(krpanoSceneId);
}

const lmenuSet = new Set(lmenuLinks);
for (const [cat, ids] of Object.entries(categories)) {
  if (ids.length < 2) continue;
  for (const id of ids) {
    if (!lmenuSet.has(id)) {
      console.warn("INFO:", id, `(${cat}) in registry nav group but not in Gecko l_menu`);
      warnings++;
    }
  }
}

console.log(`\nDone: ${errors} error(s), ${warnings} info warning(s)`);
if (errors > 0) process.exit(1);
