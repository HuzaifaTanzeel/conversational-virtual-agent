import { useEffect, useRef } from "react";
import { User, VideoOff } from "lucide-react";
import { cn } from "@/lib/utils";

export function SelfPreview({ stream, enabled, error, label = "You", className }) {
  const videoRef = useRef(null);

  useEffect(() => {
    const el = videoRef.current;
    if (!el) return;
    el.srcObject = stream ?? null;
  }, [stream]);

  return (
    <div
      className={cn(
        "absolute bottom-20 right-4 sm:bottom-24 sm:right-6 z-10",
        "w-[clamp(130px,22vw,220px)] aspect-video overflow-hidden",
        "rounded-xl border border-white/20 bg-[#3c4043] shadow-2xl",
        "transition-all duration-300 hover:scale-[1.03] hover:border-white/40 hover:shadow-blue-500/10",
        !enabled && "opacity-90",
        className,
      )}
    >
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="h-full w-full object-cover"
      />

      {!stream && !error && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#3c4043] text-white/40 gap-1">
          <User className="h-8 w-8" />
        </div>
      )}

      {error && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#3c4043] text-white/50 gap-1.5 p-3">
          <VideoOff className="h-6 w-6" />
          <span className="text-[10px] text-center leading-tight">Camera unavailable</span>
        </div>
      )}

      {!enabled && stream && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/70 text-white/80 gap-1.5">
          <VideoOff className="h-6 w-6" />
          <span className="text-xs font-medium">Camera off</span>
        </div>
      )}

      <span className="absolute bottom-2 left-2.5 text-xs font-medium text-white drop-shadow-lg">
        {label}
      </span>
    </div>
  );
}
