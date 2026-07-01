/**
 * DEV ONLY — Scene mapping verification page.
 * Remove this file + its route in App.jsx when mapping QA is complete.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronDown, ChevronRight, Search } from "lucide-react";
import { TourViewer } from "@/components/TourViewer.jsx";
import { TourAreaNav } from "@/components/TourAreaNav.jsx";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  getLiveSceneId,
  getCurrentSceneId,
  loadSceneDirect,
  navigateToArea,
  subscribeSceneChanges,
} from "@/lib/krpanoController.js";
import { SCENE_REGISTRY, KRPANO_TO_ENUM } from "@/lib/sceneRegistry.js";
import { getDisplayLabel } from "@/lib/geckoDisplayLabels.js";
import { getNavGroupForScene } from "@/lib/sceneNavGroups.js";

// ─── Build the category tree from SCENE_REGISTRY ──────────────────────────────

function buildCategoryTree() {
  const categoryMap = {};

  for (const [enumValue, { krpanoSceneId, label, category }] of Object.entries(SCENE_REGISTRY)) {
    if (!categoryMap[category]) {
      categoryMap[category] = { categoryName: category, scenes: [] };
    }
    categoryMap[category].scenes.push({ enumValue, krpanoSceneId, label });
  }

  return Object.values(categoryMap);
}

// ─── Status badge style ───────────────────────────────────────────────────────

function statusClass(status) {
  if (status === "ok") return "bg-emerald-100 text-emerald-800 border-emerald-200";
  if (status === "notFound") return "bg-red-100 text-red-800 border-red-200";
  if (status === "error") return "bg-orange-100 text-orange-800 border-orange-200";
  return "bg-slate-100 text-slate-600 border-slate-200";
}

// ─── Scene row ────────────────────────────────────────────────────────────────

function SceneRow({ scene, activeKey, onAgent, onDirect }) {
  const isActive = activeKey === scene.enumValue;

  return (
    <div
      role="button"
      tabIndex={0}
      className={`cursor-pointer rounded-md border px-3 py-2 transition-colors ${
        isActive
          ? "border-indigo-400 bg-indigo-50"
          : "border-slate-200 hover:border-slate-300 hover:bg-slate-50"
      }`}
      onClick={() => onAgent(scene)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onAgent(scene);
        }
      }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium leading-snug">{scene.label}</p>
          <p className="mt-0.5 break-all font-mono text-[11px] text-indigo-700">
            "{scene.enumValue}"
          </p>
          <p className="break-all text-[11px] text-muted-foreground">
            {scene.krpanoSceneId}
          </p>
        </div>
        <div className="flex shrink-0 flex-col gap-1">
          <Button
            size="sm"
            variant="secondary"
            className="h-7 text-xs"
            title="Send enum value through navigateToArea() — same path as the video agent"
            onClick={(e) => {
              e.stopPropagation();
              onAgent(scene);
            }}
          >
            Agent
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-xs"
            title="Load krpano scene directly by ID — bypasses tool handler"
            onClick={(e) => {
              e.stopPropagation();
              onDirect(scene);
            }}
          >
            Direct
          </Button>
        </div>
      </div>
    </div>
  );
}

// ─── Side menu preview (matches TourAreaNav in calls) ─────────────────────────

function SideMenuPreview({ currentSceneId, onNavigate }) {
  const navGroup = getNavGroupForScene(currentSceneId);
  if (!navGroup) {
    return (
      <p className="text-xs text-muted-foreground">
        No sidemenu for this scene (single-scene category or unmapped).
      </p>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-slate-700">{navGroup.categoryName}</p>
      <ul className="space-y-1">
        {navGroup.items.map((item) => {
          const isActive = item.krpanoSceneId === currentSceneId;
          const label = getDisplayLabel(item.krpanoSceneId);
          return (
            <li key={item.krpanoSceneId}>
              <button
                type="button"
                onClick={() => onNavigate(item.krpanoSceneId, item.enumValue)}
                className={`block w-full rounded px-2 py-1 text-left font-mono text-[11px] uppercase tracking-wide ${
                  isActive
                    ? "bg-indigo-100 font-semibold text-indigo-900"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {label}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function SceneDebugPage() {
  const categories = useMemo(() => buildCategoryTree(), []);
  const totalScenes = Object.keys(SCENE_REGISTRY).length;

  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState(() =>
    Object.fromEntries(categories.map((c) => [c.categoryName, false]))
  );
  const [activeKey, setActiveKey] = useState(null);
  const [lastResult, setLastResult] = useState(null);
  const [currentSceneId, setCurrentSceneId] = useState(getLiveSceneId);

  useEffect(() => {
    const sync = (sceneId) => {
      setCurrentSceneId(sceneId || getLiveSceneId());
    };
    sync(getLiveSceneId());
    return subscribeSceneChanges(sync);
  }, []);

  const needle = search.trim().toLowerCase();

  const filteredCategories = useMemo(() => {
    if (!needle) return categories;
    return categories
      .map((cat) => ({
        ...cat,
        scenes: cat.scenes.filter(
          (s) =>
            s.label.toLowerCase().includes(needle) ||
            s.enumValue.includes(needle) ||
            s.krpanoSceneId.toLowerCase().includes(needle)
        ),
      }))
      .filter((cat) => cat.scenes.length > 0);
  }, [categories, needle]);

  const handleAgent = useCallback((scene) => {
    const result = navigateToArea(scene.enumValue);
    setActiveKey(scene.enumValue);
    setCurrentSceneId(scene.krpanoSceneId);
    setLastResult({ mode: "agent", scene, result, at: new Date().toLocaleTimeString() });
  }, []);

  const handleDirect = useCallback((scene) => {
    const result = loadSceneDirect(scene.krpanoSceneId);
    setActiveKey(scene.enumValue);
    setCurrentSceneId(scene.krpanoSceneId);
    setLastResult({ mode: "direct", scene, result, at: new Date().toLocaleTimeString() });
  }, []);

  const handleSideMenuNav = useCallback((krpanoSceneId, enumValue) => {
    const result = loadSceneDirect(krpanoSceneId);
    setActiveKey(enumValue);
    const scene = { enumValue, krpanoSceneId, label: SCENE_REGISTRY[enumValue]?.label ?? enumValue };
    setLastResult({ mode: "sidemenu", scene, result, at: new Date().toLocaleTimeString() });
  }, []);

  return (
    <div className="flex h-[100dvh] flex-col bg-slate-100">

      {/* Header */}
      <header className="flex shrink-0 items-center justify-between border-b bg-white px-4 py-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Dev only</p>
          <h1 className="text-lg font-semibold">360 Scene Registry Debug</h1>
          <p className="text-sm text-muted-foreground">
            {totalScenes} scenes — each enum value maps directly to a krpano scene
          </p>
        </div>
        <Link to="/" className="text-sm text-indigo-600 hover:underline">
          Back to home
        </Link>
      </header>

      <div className="flex min-h-0 flex-1 overflow-hidden">

        {/* Left panel */}
        <aside className="relative z-20 flex h-full min-h-0 w-[min(100%,440px)] shrink-0 flex-col overflow-hidden border-r bg-white shadow-md">

          {/* Search + expand controls */}
          <div className="shrink-0 space-y-2 border-b p-3">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search label, enum value, or scene ID…"
                className="pl-8"
              />
            </div>
            <div className="flex gap-2">
              <Button
                type="button" size="sm" variant="outline" className="h-7 flex-1 text-xs"
                onClick={() =>
                  setExpanded(Object.fromEntries(categories.map((c) => [c.categoryName, true])))
                }
              >
                Expand all
              </Button>
              <Button
                type="button" size="sm" variant="outline" className="h-7 flex-1 text-xs"
                onClick={() =>
                  setExpanded(Object.fromEntries(categories.map((c) => [c.categoryName, false])))
                }
              >
                Collapse all
              </Button>
            </div>
          </div>

          {/* Scene list */}
          <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
            <div className="space-y-2 p-3 pb-6">
              {filteredCategories.map((cat) => {
                const isOpen = expanded[cat.categoryName] ?? false;
                return (
                  <section key={cat.categoryName} className="rounded-lg border">
                    <button
                      type="button"
                      className="flex w-full items-center gap-2 px-3 py-2 text-left hover:bg-slate-50"
                      onClick={() =>
                        setExpanded((prev) => ({
                          ...prev,
                          [cat.categoryName]: !prev[cat.categoryName],
                        }))
                      }
                    >
                      {isOpen ? (
                        <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
                      ) : (
                        <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
                      )}
                      <span className="flex-1 text-sm font-semibold">{cat.categoryName}</span>
                      <Badge variant="secondary">{cat.scenes.length}</Badge>
                    </button>

                    {isOpen && (
                      <div className="space-y-1 border-t px-2 py-2">
                        {cat.scenes.map((scene) => (
                          <SceneRow
                            key={scene.enumValue}
                            scene={scene}
                            activeKey={activeKey}
                            onAgent={handleAgent}
                            onDirect={handleDirect}
                          />
                        ))}
                      </div>
                    )}
                  </section>
                );
              })}
            </div>
          </div>

          {/* Side menu preview + last result */}
          <div className="max-h-56 shrink-0 overflow-y-auto border-t bg-slate-50 p-3 text-xs">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
              Side menu preview
            </p>
            <SideMenuPreview
              currentSceneId={currentSceneId}
              onNavigate={handleSideMenuNav}
            />
          </div>

          {lastResult && (
            <div className="max-h-40 shrink-0 overflow-y-auto border-t bg-white p-3 text-xs">
              <div className="mb-1 flex items-center gap-2">
                <span
                  className={`rounded border px-1.5 py-0.5 text-xs font-semibold ${statusClass(
                    lastResult.result.status
                  )}`}
                >
                  {lastResult.result.status}
                </span>
                <span className="text-muted-foreground">
                  {lastResult.mode} @ {lastResult.at}
                </span>
              </div>
              <p><span className="font-medium">Scene:</span> {lastResult.scene.label}</p>
              <p>
                <span className="font-medium">Enum value:</span>{" "}
                <span className="font-mono text-indigo-700">"{lastResult.scene.enumValue}"</span>
              </p>
              <p><span className="font-medium">krpano ID:</span> {lastResult.scene.krpanoSceneId}</p>
              {lastResult.result.status !== "ok" && (
                <p className="text-red-700">
                  Error: {lastResult.result.status} — check console for details
                </p>
              )}
              <p className="text-muted-foreground">
                Current scene: {currentSceneId}{" "}
                {KRPANO_TO_ENUM[currentSceneId]
                  ? `("${KRPANO_TO_ENUM[currentSceneId]}")`
                  : ""}
              </p>
            </div>
          )}
        </aside>

        {/* Tour viewer + live sidemenu overlay */}
        <main className="scene-debug-tour relative z-0 min-h-0 min-w-0 flex-1 overflow-hidden">
          <TourViewer className="h-full w-full" />
          <TourAreaNav />
        </main>
      </div>

      {/* Legend */}
      <div className="shrink-0 border-t bg-white px-4 py-2 text-xs text-muted-foreground">
        <span className="font-medium text-foreground">Agent</span> — calls{" "}
        <code>navigateToArea(enumValue)</code>, the exact same path the video agent uses.{" "}
        <span className="font-medium text-foreground">Direct</span> — loads{" "}
        <code>krpanoSceneId</code> immediately, bypassing the tool handler. Both should open the
        same scene. If Agent fails but Direct works, the registry enum value is wrong.
      </div>
    </div>
  );
}
