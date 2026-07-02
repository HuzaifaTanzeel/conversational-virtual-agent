import { useEffect, useRef } from "react";
import { Bot, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const videoStyle = {
  width: "100%",
  height: "100%",
  objectFit: "cover",
};

const STATUS_LABELS = {
  idle: "Ready",
  connecting: "Connecting\u2026",
  listening: "Listening",
  thinking: "Thinking\u2026",
  speaking: "Speaking",
  error: "Connection error",
};

const STATUS_DOT = {
  listening: "bg-emerald-400",
  thinking: "bg-amber-400 animate-pulse",
  speaking: "bg-blue-400 animate-pulse",
  connecting: "bg-amber-400 animate-pulse",
  error: "bg-red-400",
};

export function AvatarStage({
  videoElement,
  isConnected,
  isAvatarSpeaking,
  isUserSpeaking,
  status,
  variant = "full",
}) {
  const isPip = variant === "pip";
  const isTile = variant === "tile";
  const isCompact = isPip || isTile;
  const mountRef = useRef(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    while (mount.firstChild) mount.removeChild(mount.firstChild);
    if (!videoElement) return;

    Object.assign(videoElement.style, videoStyle);
    mount.appendChild(videoElement);

    return () => {
      if (videoElement.parentNode === mount) {
        mount.removeChild(videoElement);
      }
    };
  }, [videoElement]);

  const statusLabel = STATUS_LABELS[status] ?? status;
  const dotClass = STATUS_DOT[status] ?? "bg-white/50";

  return (
    <div className={cn("relative", isTile ? "h-full w-full" : "absolute inset-0")}>
      {/* Placeholder */}
      {!videoElement && (
        <div className="absolute inset-0 z-0 flex flex-col items-center justify-center gap-4">
          <div className="relative">
            <div
              className={cn(
                "rounded-full bg-gradient-to-br from-[#1a73e8]/30 to-[#8ab4f8]/20 flex items-center justify-center",
                isCompact ? "h-12 w-12" : "h-24 w-24",
              )}
            >
              <Bot className={cn("text-white/60", isCompact ? "h-5 w-5" : "h-10 w-10")} />
            </div>
            {isConnected && !isTile && (
              <div className="absolute inset-0 flex items-center justify-center">
                <Loader2 className="text-white/70 animate-spin h-8 w-8" />
              </div>
            )}
          </div>
          {!isCompact && (
            <p className="text-sm text-white/50 font-medium">
              {isConnected ? "Loading avatar stream\u2026" : "Ready to join"}
            </p>
          )}
        </div>
      )}

      {/* Video mount */}
      <div ref={mountRef} className="absolute inset-0 z-[1]" />

      {/* Speaking ring — only on the large stage variant */}
      {isAvatarSpeaking && !isTile && (
        <div
          className="absolute inset-0 z-[2] pointer-events-none animate-speak-glow rounded-2xl"
          aria-hidden
        />
      )}

      {/* User-speaking indicator — only on the large stage variant */}
      {isUserSpeaking && !isTile && (
        <div className="absolute bottom-0 left-0 right-0 z-[3] h-1 bg-gradient-to-r from-transparent via-emerald-400 to-transparent animate-slide-bar" />
      )}

      {/* Participant badge — only on the large stage variant; tiles are labeled beneath the card */}
      {!isTile && (
        <div
          className={cn(
            "absolute z-[4] flex items-center gap-2 pointer-events-none",
            isPip ? "bottom-2 left-2" : "bottom-4 left-4",
          )}
        >
          <span
            className={cn(
              "inline-flex items-center gap-1.5 rounded-lg bg-black/60 font-medium text-white backdrop-blur-sm",
              isPip ? "px-2 py-1 text-[10px]" : "gap-2 px-3 py-1.5 text-sm",
            )}
          >
            <span className={cn("rounded-full shrink-0", dotClass, isPip ? "h-1.5 w-1.5" : "h-2 w-2")} />
            AI Agent
            {isConnected && !isCompact && (
              <span className="text-white/60 text-xs font-normal">&middot; {statusLabel}</span>
            )}
          </span>
        </div>
      )}
    </div>
  );
}
