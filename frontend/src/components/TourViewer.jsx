import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { registerInterface, clearInterface } from "../lib/krpanoController.js";

const TOUR_BASE = "/vt/icmaldives";
const KRPANO_TARGET_ID = "krpano-pano";
// Pano tiles are streamed from Gecko's CDN, which does NOT send CORS headers.
// krpano loads tiles as crossorigin WebGL textures, so the browser blocks them
// unless they are same-origin. We therefore serve them through a same-origin
// proxy (Vite `/resort-cdn` in dev; configurable via VITE_RESORT_CDN_URL in
// prod, where it should point at an equivalent reverse-proxy).
const RESORT_CDN_URL = import.meta.env.VITE_RESORT_CDN_URL || "/resort-cdn/";

// krpano's tour.js registers global embedpano()/removepano(). Load it once.
let krpanoScriptPromise = null;
function loadKrpanoScript() {
  if (typeof window !== "undefined" && window.embedpano) return Promise.resolve();
  if (krpanoScriptPromise) return krpanoScriptPromise;
  krpanoScriptPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = `${TOUR_BASE}/template/tour.js`;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => {
      krpanoScriptPromise = null;
      reject(new Error("Failed to load the 360 tour engine."));
    };
    document.head.appendChild(script);
  });
  return krpanoScriptPromise;
}

/**
 * Embeds the InterContinental Maldives krpano tour and registers its interface
 * with krpanoController so the agent's tool handler can drive navigation. The
 * native krpano UI (menus + controls) is kept so the guest can also explore
 * freely, exactly like the standalone tour.
 */
export function TourViewer({ className }) {
  const containerRef = useRef(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    loadKrpanoScript()
      .then(() => {
        if (cancelled || !containerRef.current) return;
        if (!window.embedpano) {
          setError("The 360 tour engine is unavailable.");
          return;
        }
        // Stub until registerInterface replaces it — vtourskin.xml jscall fires on hotspot nav.
        window.__krpanoNavSync = () => {};
        window.embedpano({
          swf: `${TOUR_BASE}/template/tour.swf`,
          xml: `${TOUR_BASE}/tour.xml`,
          target: KRPANO_TARGET_ID,
          html5: "auto",
          bgcolor: "#000000",
          mobilescale: 1,
          consolelog: false,
          logkey: false,
          // `path` -> resolves tour.xml's `calc:path + 'skin/...'` / layout.xml
          // `cdn_url` -> streams pano tiles from the Gecko CDN at runtime.
          initvars: {
            path: `${TOUR_BASE}/template/`,
            cdn_url: RESORT_CDN_URL,
            showerrors: false,
          },
          onready: (kr) => {
            if (cancelled) return;
            kr.set("showerrors", false);
            // Close the krpano log overlay if it was opened by a prior error.
            try {
              kr.call("showlog(false)");
            } catch {
              /* older krpano builds may not expose showlog */
            }
            registerInterface(kr);
          },
        });
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || "Failed to load the 360 tour.");
      });

    return () => {
      cancelled = true;
      clearInterface();
      if (typeof window !== "undefined" && window.removepano) {
        try {
          window.removepano(KRPANO_TARGET_ID);
        } catch {
          /* viewer may not have finished initializing */
        }
      }
    };
  }, []);

  return (
    <div className={cn("relative h-full w-full bg-black", className)}>
      <div id={KRPANO_TARGET_ID} ref={containerRef} className="h-full w-full" />
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900 p-6 text-center">
          <p className="text-sm text-white/60">{error}</p>
        </div>
      )}
    </div>
  );
}
