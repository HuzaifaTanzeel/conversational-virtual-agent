import { AvatarStage } from "./AvatarStage.jsx";
import { SelfPreview } from "./SelfPreview.jsx";
import { TranscriptPanel } from "./TranscriptPanel.jsx";
import { cn } from "@/lib/utils";

export function ParticipantPanel({
  avatar,
  camera,
  displayName,
  transcriptOpen,
  onCloseTranscript,
  className,
  layout = "sidebar",
}) {
  const isSidebar = layout === "sidebar";
  const userLabel = displayName || "You";

  const cardShell = "relative overflow-hidden rounded-xl border border-white/10 bg-[#3c4043]";

  if (!isSidebar) {
    return (
      <div className={cn("flex gap-2 px-2 pb-2", className)}>
        <div className={cn(cardShell, "aspect-video flex-1 min-w-0")}>
          <AvatarStage
            videoElement={avatar.videoElement}
            isConnected={avatar.isConnected}
            isAvatarSpeaking={avatar.isAvatarSpeaking}
            isUserSpeaking={avatar.isUserSpeaking}
            status={avatar.status}
            variant="tile"
          />
        </div>
        <div className={cn(cardShell, "aspect-video flex-1 min-w-0")}>
          <SelfPreview
            stream={camera.stream}
            enabled={camera.enabled}
            error={camera.error}
            displayName={userLabel}
            layout="tile"
          />
        </div>
      </div>
    );
  }

  const tiles = (
    <>
      <div className="flex w-full flex-col gap-1.5">
        <div className={cn(cardShell, "aspect-video w-full")}>
          <AvatarStage
            videoElement={avatar.videoElement}
            isConnected={avatar.isConnected}
            isAvatarSpeaking={avatar.isAvatarSpeaking}
            isUserSpeaking={avatar.isUserSpeaking}
            status={avatar.status}
            variant="tile"
          />
        </div>
        <span className="pl-1 text-xs font-medium text-white/50">AI Agent</span>
      </div>

      <div className="flex w-full flex-col gap-1.5">
        <div className={cn(cardShell, "aspect-video w-full")}>
          <SelfPreview
            stream={camera.stream}
            enabled={camera.enabled}
            error={camera.error}
            displayName={userLabel}
            layout="tile"
          />
        </div>
        <span className="pl-1 text-xs font-medium text-white/50">You</span>
      </div>
    </>
  );

  return (
    <aside
      className={cn(
        "hidden lg:flex w-[320px] xl:w-[340px] shrink-0 flex-col",
        "border-l border-white/10 bg-[#292a2d]",
        className,
      )}
    >
      <div className="flex flex-1 min-h-0 flex-col items-center justify-center gap-3 px-3 py-4">
        {tiles}
      </div>

      {transcriptOpen && (
        <div className="flex min-h-0 max-h-[45%] flex-col border-t border-white/10">
          <TranscriptPanel
            status={avatar.status}
            messages={avatar.messages}
            liveUserText={avatar.liveUserText}
            liveAgentText={avatar.liveAgentText}
            isUserSpeaking={avatar.isUserSpeaking}
            isAvatarSpeaking={avatar.isAvatarSpeaking}
            sessionWarning={avatar.sessionWarning}
            onClose={onCloseTranscript}
            className="w-full border-l-0 max-h-none flex-1 min-h-0 animate-none"
          />
        </div>
      )}
    </aside>
  );
}
