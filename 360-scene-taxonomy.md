# InterContinental Maldives Maamunagau Resort — 360° Scene Taxonomy

Source: https://maldives.intercontinental.com/
Purpose: Reference structure for building tools that fetch 360° scenes by category, and for prompting an LLM (Cursor) to pick the correct scene without guessing.

> **Corrections made to your original notes** (verified against the resort's own site):
> - "Cafe Omi" → **Café Umi** (Japanese-inspired restaurant)
> - "Planet Traker / Planet Trackker" → **Planet Trekkers** (kids club, ages 4–12)
> - The Spa's official name is **AVI Spa**
> - A few gaps/inconsistencies are flagged inline with 🚩 — please confirm rather than assume I filled them in correctly.

---

## 1. Resort Overview (General Areas)
| Scene ID | Scene Name |
|---|---|
| `main-pool-area` | Main Pool Area |
| `main-pool-aerial` | Main Pool — Aerial View |
| `sunset-bar` | Sunset Bar |

## 2. Wellness — AVI Spa
| Scene ID | Scene Name | Notes |
|---|---|---|
| `spa-treatment-room` | Treatment Room | **Default scene when user asks generically about "the Spa"** |
| `spa-relaxation-lounge` | Relaxation Lounge | Offer as secondary option |

## 3. Kids & Family
| Scene ID | Scene Name | Notes |
|---|---|---|
| `kids-planet-trekkers` | Planet Trekkers (Kids Club) | **Default scene for "kids area," "kids club," "kids facilities"** — only one scene, no ambiguity |

## 4. Dining
| Scene ID | Scene Name |
|---|---|
| `dining-lighthouse` | The Lighthouse Restaurant |
| `dining-lighthouse-aerial` | The Lighthouse — Aerial View |
| `dining-fish-market` | Fish Market |
| `dining-cafe-umi` | Café Umi |

⚠️ No safe default here — three distinct restaurants exist. See routing rules below.

## 5. Lagoon Area
**Shared facilities:**
| Scene ID | Scene Name |
|---|---|
| `lagoon-aerial` | Lagoon — Aerial View |
| `lagoon-retreat-pool` | The Retreat Pool (Lagoon, adults-only) |

**Villas in this area:**

### One Bedroom Lagoon Pool Villa (`lagoon-villa-1br`)
- `living-room`
- `bedroom`
- `bathroom`

### Two Bedroom Lagoon Pool Villa (`lagoon-villa-2br`)
- `living-room`
- `master-bedroom`
- `second-bedroom`

### Three Bedroom Lagoon Pool Villa Residence (`lagoon-villa-3br-residence`)
- `living-room`
- `dining-area`
- `pool-deck`
- `master-bedroom`
- `master-bathroom`
- `second-bedroom`
- `second-bathroom`
- `third-bedroom`
- `third-bathroom`

## 6. Overwater Pool Villas

### One Bedroom Overwater Pool Villa (`overwater-villa-1br`)
- `bedroom`
- `bathroom`

### Two Bedroom Overwater Pool Villa (`overwater-villa-2br`)
- `master-bedroom`
- `master-bathroom`
- `second-bedroom`
- `second-bathroom`
- `living-room`

### Three Bedroom Overwater Pool Villa (`overwater-villa-3br`)
- `master-bedroom`
- `second-bedroom`
- `second-bathroom`
- `third-bedroom`
- `third-bathroom`
- `living-room`
- `aerial-view`

🚩 No "Master Bathroom" scene was listed for this villa (unlike its 2BR sibling). Kept as-is rather than invented — please confirm whether that scene exists.

## 7. Beach Villas

### Beach Pool Villa (`beach-villa-pool`)
- `bedroom`
- `bathroom`

### Family Beach Pool Villa (`beach-villa-family`)
- `master-bedroom`
- `master-bathroom`
- `family-room`

### One Bedroom Beach Pool Villa (`beach-villa-1br`)
- `bedroom`
- `living-room`

### Two Bedroom Family Beach Pool Villa (`beach-villa-2br-family`)
- `master-bedroom`
- `second-bedroom`
- `living-room`

### Two Bedroom Beachfront Pool Residence (`beach-residence-2br`)
- `master-bedroom`
- `master-bathroom`
- `second-bedroom`
- `pool-deck`
- `living-room`

### Three Bedroom Royal Beachfront Residence (`beach-residence-3br-royal`)
- `master-bedroom`
- `second-bedroom`
- `third-bedroom`
- `pool-deck`
- `living-room`

---

## LLM Routing / Disambiguation Rules

These rules exist so the assistant picks an exact `scene_id` instead of guessing.

| User says... | Action |
|---|---|
| "Spa" (no specifics) | Default → `spa-treatment-room` |
| "Kids area / kids club / kids facilities" | Default → `kids-planet-trekkers` |
| "Restaurant / dining" (no specifics) | **No default.** Ask: Lighthouse, Fish Market, or Café Umi? |
| "Pool" (no specifics) | **No default.** Ask: Main Pool, The Retreat (Lagoon), or a specific villa's private pool? |
| "Villa" (no area / bedroom count) | **No default.** Ask: Lagoon, Overwater, or Beach — and how many bedrooms? |
| "Two bedroom villa" (no area) | **No default.** Lagoon, Overwater, and Beach each have their own distinct 2BR product — ask which. |
| "Residence" (no specifics) | **No default.** Three distinct residences exist (Lagoon 3BR, Beachfront 2BR, Royal Beachfront 3BR) — ask which. |
| Room inside a named villa (e.g. "master bedroom of the two bedroom overwater villa") | Resolve directly to that villa's specific room scene — no need to ask. |

**General principle:** only auto-resolve to a single scene when the table above defines an explicit default, or when the user's request maps unambiguously to exactly one `scene_id`. Otherwise, ask a short clarifying question listing the real options rather than picking one.

---

A matching `360-scene-taxonomy.json` is provided alongside this file as the machine-readable version, structured for direct use when building the fetch tool(s) in Cursor.
