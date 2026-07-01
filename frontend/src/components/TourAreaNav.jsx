import { useCallback, useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import {
  getLiveSceneId,
  loadSceneDirect,
  subscribeSceneChanges,
} from "@/lib/krpanoController.js";
import { getDisplayLabel } from "@/lib/geckoDisplayLabels.js";
import { getNavGroupForScene } from "@/lib/sceneNavGroups.js";

/**
 * Left-side room/area links for self-explore navigation during a video call.
 * Targets: sceneRegistry krpanoSceneIds. Labels: Gecko tour display names.
 */
export function TourAreaNav({ className }) {
  const [currentSceneId, setCurrentSceneId] = useState(getLiveSceneId);

  useEffect(() => {
    const sync = (sceneId) => {
      setCurrentSceneId(sceneId || getLiveSceneId());
    };
    sync(getLiveSceneId());
    return subscribeSceneChanges(sync);
  }, []);

  // Always derive menu from the live krpano scene — never reuse a previous category.
  const navGroup = getNavGroupForScene(currentSceneId);

  const handleNavigate = useCallback((krpanoSceneId) => {
    loadSceneDirect(krpanoSceneId);
  }, []);

  if (!navGroup) return null;

  return (
    <nav
      aria-label={`${navGroup.categoryName} areas`}
      className={cn(
        "pointer-events-auto absolute left-3 top-1/2 z-30 max-h-[min(70vh,520px)] -translate-y-1/2 overflow-y-auto",
        "rounded-sm bg-black/55 px-4 py-3 shadow-lg backdrop-blur-[2px]",
        className,
      )}
    >
      <ul className="flex flex-col gap-2.5">
        {navGroup.items.map((item) => {
          const isActive = item.krpanoSceneId === currentSceneId;
          const label = getDisplayLabel(item.krpanoSceneId);
          return (
            <li key={item.krpanoSceneId}>
              <button
                type="button"
                onClick={() => handleNavigate(item.krpanoSceneId)}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "block w-full text-left font-sans text-[11px] font-medium uppercase tracking-[0.18em]",
                  "transition-colors duration-150",
                  isActive
                    ? "text-white"
                    : "text-white/75 hover:text-white",
                )}
              >
                {label}
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
