import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Mic,
  MicOff,
  Video,
  VideoOff,
  PhoneOff,
  HandMetal,
  MessageSquare,
  Maximize2,
  Minimize2,
} from "lucide-react";
import { cn } from "@/lib/utils";

function ControlButton({
  onClick,
  active,
  danger,
  disabled,
  label,
  children,
  className,
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          onClick={onClick}
          disabled={disabled}
          aria-label={label}
          className={cn(
            "flex h-10 w-10 items-center justify-center rounded-full transition-all duration-200",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/50",
            "disabled:pointer-events-none disabled:opacity-40",
            danger
              ? "bg-red-500 text-white hover:bg-red-600 hover:scale-105"
              : active
                ? "bg-white text-[#202124] hover:bg-white/90"
                : "bg-white/10 text-white hover:bg-white/20",
            className
          )}
        >
          {children}
        </button>
      </TooltipTrigger>
      <TooltipContent side="bottom" className="bg-[#3c4043] text-white border-0">
        {label}
      </TooltipContent>
    </Tooltip>
  );
}

export function CallControls({
  isMicMuted,
  isCameraEnabled,
  isAvatarSpeaking,
  onEnd,
  onToggleMic,
  onToggleCamera,
  onInterrupt,
  hasLocalCamera,
  transcriptOpen,
  onToggleTranscript,
  isFullscreen,
  onToggleFullscreen,
}) {
  return (
    <TooltipProvider delayDuration={300}>
      <div className="pointer-events-auto flex items-center gap-1.5 sm:gap-2 rounded-full bg-[#202124]/80 px-2.5 py-1.5 backdrop-blur-md border border-white/10 shadow-2xl">
        <ControlButton
          label={isMicMuted ? "Turn on microphone" : "Turn off microphone"}
          onClick={onToggleMic}
          active={isMicMuted}
        >
          {isMicMuted ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
        </ControlButton>

        <ControlButton
          label={isCameraEnabled ? "Turn off camera" : "Turn on camera"}
          onClick={onToggleCamera}
          active={!isCameraEnabled}
          disabled={!hasLocalCamera}
        >
          {isCameraEnabled ? <Video className="h-5 w-5" /> : <VideoOff className="h-5 w-5" />}
        </ControlButton>

        {isAvatarSpeaking && (
          <ControlButton label="Interrupt agent" onClick={onInterrupt} active>
            <HandMetal className="h-5 w-5" />
          </ControlButton>
        )}

        <ControlButton
          label={transcriptOpen ? "Hide captions" : "Show captions"}
          onClick={onToggleTranscript}
          active={transcriptOpen}
          className="lg:hidden flex"
        >
          <MessageSquare className="h-5 w-5" />
        </ControlButton>

        <ControlButton
          label={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
          onClick={onToggleFullscreen}
          className="hidden sm:flex"
        >
          {isFullscreen ? <Minimize2 className="h-5 w-5" /> : <Maximize2 className="h-5 w-5" />}
        </ControlButton>

        <div className="mx-0.5 h-6 w-px bg-white/15" />

        <ControlButton label="Leave call" onClick={onEnd} danger>
          <PhoneOff className="h-5 w-5" />
        </ControlButton>
      </div>
    </TooltipProvider>
  );
}
