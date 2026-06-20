import { useCallback, useEffect, useRef, useState } from "react";
import { AvatarStage } from "./AvatarStage.jsx";
import { SelfPreview } from "./SelfPreview.jsx";
import { CallControls } from "./CallControls.jsx";
import { TranscriptPanel } from "./TranscriptPanel.jsx";
import { MediaPanel } from "./MediaPanel.jsx";
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
  isStarting,
  onStart,
  displayName,
  minutesRemaining,
  currentMedia,
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

  const handleStart = useCallback(async () => {
    await onStart();
  }, [onStart]);

  const handleEnd = useCallback(async () => {
    await avatar.stop();
    camera.stop();
    if (document.fullscreenElement) {
      document.exitFullscreen?.();
    }
    setIsFullscreen(false);
  }, [avatar, camera]);

  const toggleFullscreen = useCallback(() => {
    const el = stageRef.current;
    if (!el) return;
    if (!document.fullscreenElement) {
      el.requestFullscreen?.().then(() => setIsFullscreen(true));
    } else {
      document.exitFullscreen?.().then(() => setIsFullscreen(false));
    }
  }, []);

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
              className="sm:hidden flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-white/80 hover:bg-white/20 transition-colors"
              aria-label="Show captions"
            >
              <MessageSquare className="h-4 w-4" />
            </button>
          )}
        </div>
      </header>

      <div className="flex flex-1 min-h-0 pt-14">
        {/* Avatar panel — 60% */}
        <div className="relative flex flex-[0_0_60%] flex-col min-h-0 min-w-0">
          <div
            ref={stageRef}
            className={cn(
              "relative flex-1 min-h-0 m-2 sm:m-3 mb-0 overflow-hidden bg-[#3c4043]",
              transcriptOpen ? "rounded-t-2xl sm:rounded-2xl sm:mr-0" : "rounded-2xl",
              isFullscreen && "rounded-none m-0",
            )}
          >
            <AvatarStage
              videoElement={avatar.videoElement}
              isConnected={avatar.isConnected}
              isAvatarSpeaking={avatar.isAvatarSpeaking}
              isUserSpeaking={avatar.isUserSpeaking}
              status={avatar.status}
            />
            <SelfPreview
              stream={camera.stream}
              enabled={camera.enabled}
              error={camera.error}
              label={displayName || "You"}
            />

            <CallControls
              isConnected={avatar.isConnected}
              isStarting={isStarting}
              isMicMuted={avatar.isMicMuted}
              isSpeakerMuted={avatar.isSpeakerMuted}
              isCameraEnabled={camera.enabled}
              isAvatarSpeaking={avatar.isAvatarSpeaking}
              avatarVolume={avatar.avatarVolume}
              hasLocalCamera={!!camera.stream}
              onStart={handleStart}
              onEnd={handleEnd}
              onToggleMic={avatar.toggleMic}
              onToggleSpeaker={avatar.toggleSpeaker}
              onToggleCamera={camera.toggleCamera}
              onInterrupt={avatar.interrupt}
              onVolumeChange={avatar.setAvatarVolume}
              transcriptOpen={transcriptOpen}
              onToggleTranscript={() => setTranscriptOpen((v) => !v)}
              isFullscreen={isFullscreen}
              onToggleFullscreen={toggleFullscreen}
            />
          </div>
        </div>

        {/* Media panel — 40% (hidden on small screens when no media) */}
        <div
          className={cn(
            "hidden sm:flex flex-[0_0_40%] min-h-0 m-2 sm:m-3 ml-0 overflow-hidden rounded-2xl border border-white/10",
            !currentMedia && "opacity-90",
          )}
        >
          <MediaPanel media={currentMedia} />
        </div>

        {transcriptOpen && (
          <TranscriptPanel
            status={avatar.status}
            messages={avatar.messages}
            liveUserText={avatar.liveUserText}
            liveAgentText={avatar.liveAgentText}
            isUserSpeaking={avatar.isUserSpeaking}
            isAvatarSpeaking={avatar.isAvatarSpeaking}
            sessionWarning={avatar.sessionWarning}
            onClose={() => setTranscriptOpen(false)}
            className="hidden lg:flex max-h-[100dvh]"
          />
        )}
      </div>

      {currentMedia && (
        <div className="sm:hidden flex flex-col max-h-[35vh] border-t border-white/10 bg-[#292a2d]">
          <MediaPanel media={currentMedia} />
        </div>
      )}

      {transcriptOpen && (
        <div className="lg:hidden sm:flex hidden flex-col max-h-[40vh] border-t border-white/10 bg-[#292a2d] animate-in slide-in-from-bottom-4 duration-300">
          <TranscriptPanel
            status={avatar.status}
            messages={avatar.messages}
            liveUserText={avatar.liveUserText}
            liveAgentText={avatar.liveAgentText}
            isUserSpeaking={avatar.isUserSpeaking}
            isAvatarSpeaking={avatar.isAvatarSpeaking}
            sessionWarning={avatar.sessionWarning}
            onClose={() => setTranscriptOpen(false)}
            className="border-l-0 w-full max-h-[40vh]"
          />
        </div>
      )}
    </div>
  );
}
