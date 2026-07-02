import { useEffect, useRef } from "react";
import { VideoOff } from "lucide-react";
import { cn } from "@/lib/utils";

function getInitials(name) {
  if (!name) return "";
  const parts = name.trim().split(/\s+/).slice(0, 2);
  return parts.map((p) => p[0]?.toUpperCase() ?? "").join("");
}

export function SelfPreview({
  stream,
  enabled,
  error,
  displayName = "You",
  layout = "overlay",
  className,
}) {
  const videoRef = useRef(null);
  const isTile = layout === "tile";
  const initials = getInitials(displayName);
  const showVideo = !!stream && enabled;

  useEffect(() => {
    const el = videoRef.current;
    if (!el) return;
    el.srcObject = stream ?? null;
  }, [stream]);

  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border border-white/10 bg-[#3c4043] shadow-lg",
        isTile
          ? "relative h-full w-full"
          : [
              "absolute bottom-20 right-4 sm:bottom-24 sm:right-6 z-10",
              "w-[clamp(130px,22vw,220px)] aspect-video",
              "transition-all duration-300 hover:scale-[1.03] hover:border-white/40",
            ],
        className,
      )}
    >
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className={cn("h-full w-full object-cover", !showVideo && "invisible")}
      />

      {!showVideo && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-[#3c4043] text-white/60">
          {error ? (
            <>
              <VideoOff className="h-6 w-6" />
              <span className="text-[10px] text-center leading-tight">Camera unavailable</span>
            </>
          ) : initials ? (
            <span className="flex h-12 w-12 items-center justify-center rounded-full bg-white/10 text-base font-semibold text-white/80">
              {initials}
            </span>
          ) : (
            <VideoOff className="h-6 w-6" />
          )}
        </div>
      )}
    </div>
  );
}
