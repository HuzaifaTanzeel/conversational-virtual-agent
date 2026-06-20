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
}) {
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
    <div className="absolute inset-0">
      {/* Placeholder */}
      {!videoElement && (
        <div className="absolute inset-0 z-0 flex flex-col items-center justify-center gap-4">
          <div className="relative">
            <div className="h-24 w-24 rounded-full bg-gradient-to-br from-[#1a73e8]/30 to-[#8ab4f8]/20 flex items-center justify-center">
              <Bot className="h-10 w-10 text-white/60" />
            </div>
            {isConnected && (
              <div className="absolute inset-0 flex items-center justify-center">
                <Loader2 className="h-8 w-8 text-white/70 animate-spin" />
              </div>
            )}
          </div>
          <p className="text-sm text-white/50 font-medium">
            {isConnected ? "Loading avatar stream\u2026" : "Ready to join"}
          </p>
        </div>
      )}

      {/* Video mount */}
      <div ref={mountRef} className="absolute inset-0 z-[1]" />

      {/* Speaking ring */}
      {isAvatarSpeaking && (
        <div
          className="absolute inset-0 z-[2] pointer-events-none animate-speak-glow rounded-2xl"
          aria-hidden
        />
      )}

      {/* User-speaking indicator */}
      {isUserSpeaking && (
        <div className="absolute bottom-0 left-0 right-0 z-[3] h-1 bg-gradient-to-r from-transparent via-emerald-400 to-transparent animate-slide-bar" />
      )}

      {/* Participant badge — bottom left, Meet-style */}
      <div className="absolute bottom-4 left-4 z-[4] flex items-center gap-2 pointer-events-none">
        <span className="inline-flex items-center gap-2 rounded-lg bg-black/60 px-3 py-1.5 text-sm font-medium text-white backdrop-blur-sm">
          <span className={cn("h-2 w-2 rounded-full shrink-0", dotClass)} />
          AI Agent
          {isConnected && (
            <span className="text-white/60 text-xs font-normal">&middot; {statusLabel}</span>
          )}
        </span>
      </div>
    </div>
  );
}
