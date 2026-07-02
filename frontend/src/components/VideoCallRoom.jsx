import { useCallback, useEffect, useRef, useState } from "react";
import { CallControls } from "./CallControls.jsx";
import { TranscriptPanel } from "./TranscriptPanel.jsx";
import { TourViewer } from "./TourViewer.jsx";
import { TourAreaNav } from "./TourAreaNav.jsx";
import { ParticipantPanel } from "./ParticipantPanel.jsx";
import { Clock, MessageSquare, Shield } from "lucide-react";
import { cn } from "@/lib/utils";

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function VideoCallRoom({
  avatar,
  camera,
  displayName,
  minutesRemaining,
  onLeave,
}) {
  const stageRef = useRef(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [transcriptOpen, setTranscriptOpen] = useState(true);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!avatar.isConnected) return;
    const start = Date.now();
    const id = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 1000));
    }, 1000);
    return () => clearInterval(id);
  }, [avatar.isConnected]);

  useEffect(() => {
    const onFsChange = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", onFsChange);
    return () => document.removeEventListener("fullscreenchange", onFsChange);
  }, []);

  const handleEnd = useCallback(async () => {
    await avatar.stop();
    camera.stop();
    if (document.fullscreenElement) {
      document.exitFullscreen?.();
    }
    setIsFullscreen(false);
    onLeave?.();
  }, [avatar, camera, onLeave]);

  const toggleFullscreen = useCallback(() => {
    const el = stageRef.current;
    if (!el) return;
    if (!document.fullscreenElement) {
      el.requestFullscreen?.().then(() => setIsFullscreen(true));
    } else {
      document.exitFullscreen?.().then(() => setIsFullscreen(false));
    }
  }, []);

  const tourActive = avatar.isConnected;

  return (
    <div className="relative flex h-[100dvh] flex-col overflow-hidden bg-[#202124] text-white">
      <header className="absolute top-0 left-0 right-0 z-20 flex items-center justify-between px-4 py-3 sm:px-6 bg-gradient-to-b from-black/50 to-transparent">
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#1a73e8] shadow-lg shadow-blue-500/20">
            <Shield className="h-4 w-4 text-white" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold truncate">Avatour Property Tour</p>
            <p className="text-xs text-white/50 truncate">
              {displayName ? `Signed in as ${displayName}` : "AI sales session"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          {avatar.isConnected && (
            <span className="hidden sm:inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-white/80 tabular-nums">
              {formatDuration(elapsed)}
            </span>
          )}
          <span className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-white/80">
            <Clock className="h-3.5 w-3.5 text-[#8ab4f8]" />
            <span className="tabular-nums">{Math.floor(minutesRemaining)} min left</span>
          </span>
          {!transcriptOpen && (
            <button
              type="button"
              onClick={() => setTranscriptOpen(true)}
              className="lg:hidden flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-white/80 hover:bg-white/20 transition-colors"
              aria-label="Show captions"
            >
              <MessageSquare className="h-4 w-4" />
            </button>
          )}
        </div>
      </header>

      <div className="flex flex-1 min-h-0 pt-14">
        <div className="relative flex flex-1 flex-col min-h-0 min-w-0">
          <div
            ref={stageRef}
            className={cn(
              "relative flex flex-1 min-h-0 flex-col overflow-hidden",
              "m-2 sm:m-3 mb-0",
              tourActive ? "bg-black" : "bg-[#3c4043]",
              "rounded-t-2xl sm:rounded-2xl",
              isFullscreen && "rounded-none m-0",
            )}
          >
            <div className="relative flex-1 min-h-0 overflow-hidden rounded-t-2xl sm:rounded-2xl">
              {tourActive && (
                <div className="absolute inset-0 z-0">
                  <TourViewer />
                </div>
              )}

              {!tourActive && (
                <div className="absolute inset-0 flex items-center justify-center text-white/40 text-sm">
                  Connecting to your tour&hellip;
                </div>
              )}

              {tourActive && !avatar.brochureUrl && <TourAreaNav />}

              {tourActive && avatar.brochureUrl && (
                <div className="absolute inset-0 z-[5] bg-white flex flex-col">
                  <div className="flex items-center justify-between px-4 py-2 bg-[#1e293b]">
                    <span className="text-sm font-medium text-white/90">Brochure View</span>
                    <button
                      type="button"
                      onClick={avatar.closeBrochure}
                      className="rounded-md bg-white/10 px-3 py-1 text-xs font-medium text-white hover:bg-white/20 transition-colors"
                    >
                      Back to Tour
                    </button>
                  </div>
                  <iframe
                    src={avatar.brochureUrl}
                    title="Brochure"
                    className="flex-1 w-full border-0"
                    allow="fullscreen"
                  />
                </div>
              )}

              {/* Floating toolbar — sits above the scene, not below it */}
              <div className="absolute top-3 left-1/2 z-30 -translate-x-1/2">
                <CallControls
                  isMicMuted={avatar.isMicMuted}
                  isCameraEnabled={camera.enabled}
                  isAvatarSpeaking={avatar.isAvatarSpeaking}
                  hasLocalCamera={!!camera.stream}
                  onEnd={handleEnd}
                  onToggleMic={avatar.toggleMic}
                  onToggleCamera={camera.toggleCamera}
                  onInterrupt={avatar.interrupt}
                  transcriptOpen={transcriptOpen}
                  onToggleTranscript={() => setTranscriptOpen((v) => !v)}
                  isFullscreen={isFullscreen}
                  onToggleFullscreen={toggleFullscreen}
                />
              </div>
            </div>

            <ParticipantPanel
              avatar={avatar}
              camera={camera}
              displayName={displayName}
              layout="strip"
              className="lg:hidden shrink-0 max-h-[28vh]"
            />
          </div>
        </div>

        <ParticipantPanel
          avatar={avatar}
          camera={camera}
          displayName={displayName}
          transcriptOpen={transcriptOpen}
          onCloseTranscript={() => setTranscriptOpen(false)}
          layout="sidebar"
        />
      </div>

      {transcriptOpen && (
        <div className="lg:hidden flex flex-col max-h-[35vh] border-t border-white/10 bg-[#292a2d] animate-in slide-in-from-bottom-4 duration-300">
          <TranscriptPanel
            status={avatar.status}
            messages={avatar.messages}
            liveUserText={avatar.liveUserText}
            liveAgentText={avatar.liveAgentText}
            isUserSpeaking={avatar.isUserSpeaking}
            isAvatarSpeaking={avatar.isAvatarSpeaking}
            sessionWarning={avatar.sessionWarning}
            onClose={() => setTranscriptOpen(false)}
            className="border-l-0 w-full max-h-[35vh]"
          />
        </div>
      )}
    </div>
  );
}
