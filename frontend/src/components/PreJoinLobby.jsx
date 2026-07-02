import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Clock,
  Loader2,
  Mic,
  MicOff,
  Shield,
  User,
  Video,
  VideoOff,
} from "lucide-react";
import { cn } from "@/lib/utils";

function LobbyControlButton({ active, label, onClick, disabled, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      className={cn(
        "flex h-11 w-11 items-center justify-center rounded-full transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1a73e8]",
        "disabled:pointer-events-none disabled:opacity-40",
        active
          ? "bg-white text-[#202124] hover:bg-white/90"
          : "bg-[#3c4043] text-white hover:bg-[#5f6368]",
      )}
    >
      {children}
    </button>
  );
}

export function PreJoinLobby({
  camera,
  displayName,
  minutesRemaining,
  isJoining,
  onJoin,
}) {
  const videoRef = useRef(null);
  const [micMuted, setMicMuted] = useState(false);

  useEffect(() => {
    const el = videoRef.current;
    if (!el) return;
    el.srcObject = camera.stream ?? null;
  }, [camera.stream]);

  const handleJoin = () => {
    onJoin({ micMuted });
  };

  const name = displayName || "Guest";

  return (
    <div className="flex min-h-[100dvh] flex-col bg-[#f8f9fa] text-[#202124]">
      <header className="flex items-center justify-between border-b border-[#dadce0] px-4 py-3 sm:px-8">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#1a73e8]">
            <Video className="h-4 w-4 text-white" />
          </div>
          <span className="text-sm font-medium text-[#5f6368]">Avatour Property Tour</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-[#5f6368]">
          <Shield className="h-3.5 w-3.5" />
          Encrypted session
        </div>
      </header>

      <main className="flex flex-1 items-center justify-center p-4 sm:p-8">
        <div className="grid w-full max-w-5xl gap-8 lg:grid-cols-2 lg:gap-16 items-center">
          {/* Left — camera preview */}
          <div className="relative mx-auto w-full max-w-xl">
            <div className="relative aspect-video overflow-hidden rounded-2xl bg-[#202124] shadow-lg">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className={cn(
                  "h-full w-full object-cover",
                  (!camera.enabled || !camera.stream) && "invisible",
                )}
              />

              {!camera.stream && !camera.error && (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 text-white/60">
                  <User className="h-12 w-12" />
                  <p className="text-sm">Starting camera&hellip;</p>
                </div>
              )}

              {camera.error && (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 px-6 text-center text-white/70">
                  <VideoOff className="h-10 w-10" />
                  <p className="text-sm font-medium">Camera unavailable</p>
                  <p className="text-xs text-white/50">{camera.error}</p>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => camera.start()}
                    className="mt-1 border-white/20 bg-transparent text-white hover:bg-white/10"
                  >
                    Try again
                  </Button>
                </div>
              )}

              {!camera.enabled && camera.stream && (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-[#3c4043] text-white/80">
                  <VideoOff className="h-10 w-10" />
                  <span className="text-sm font-medium">Camera is off</span>
                </div>
              )}

              <span className="absolute left-4 top-4 text-sm font-medium text-white drop-shadow-md">
                {name}
              </span>

              <div className="absolute bottom-4 left-1/2 flex -translate-x-1/2 items-center gap-3">
                <LobbyControlButton
                  label={micMuted ? "Turn on microphone" : "Turn off microphone"}
                  active={micMuted}
                  onClick={() => setMicMuted((v) => !v)}
                >
                  {micMuted ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
                </LobbyControlButton>
                <LobbyControlButton
                  label={camera.enabled ? "Turn off camera" : "Turn on camera"}
                  active={!camera.enabled}
                  onClick={camera.toggleCamera}
                  disabled={!camera.stream}
                >
                  {camera.enabled ? <Video className="h-5 w-5" /> : <VideoOff className="h-5 w-5" />}
                </LobbyControlButton>
              </div>
            </div>
          </div>

          {/* Right — join panel */}
          <div className="flex flex-col items-center lg:items-start text-center lg:text-left">
            <h1 className="text-3xl sm:text-4xl font-normal tracking-tight text-[#202124]">
              Ready to join?
            </h1>
            <p className="mt-3 text-base text-[#5f6368] max-w-sm">
              You&apos;re about to start your AI-guided property tour with{" "}
              <span className="font-medium text-[#202124]">{name}</span>.
            </p>

            <div className="mt-5 inline-flex items-center gap-2 rounded-full bg-[#e8f0fe] px-4 py-2 text-sm text-[#1a73e8]">
              <Clock className="h-4 w-4" />
              <span className="tabular-nums">{Math.floor(minutesRemaining)} min session time</span>
            </div>

            <Button
              type="button"
              onClick={handleJoin}
              disabled={isJoining}
              className="mt-8 h-12 min-w-[200px] rounded-full px-10 text-base font-medium bg-[#1a73e8] hover:bg-[#1765cc] shadow-sm"
            >
              {isJoining ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Connecting&hellip;
                </>
              ) : (
                "Join now"
              )}
            </Button>

            <p className="mt-6 text-xs text-[#80868b]">
              Your session time starts when you join.{" "}
              <Link to="/" className="text-[#1a73e8] hover:underline">
                Back to home
              </Link>
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
