import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
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
  Volume2,
  VolumeX,
  PhoneOff,
  HandMetal,
  Loader2,
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
            "flex h-12 w-12 items-center justify-center rounded-full transition-all duration-200",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/50",
            "disabled:pointer-events-none disabled:opacity-40",
            danger
              ? "bg-red-500 text-white hover:bg-red-600 hover:scale-105"
              : active
                ? "bg-white text-[#202124] hover:bg-white/90"
                : "bg-[#3c4043] text-white hover:bg-[#5f6368]",
            className
          )}
        >
          {children}
        </button>
      </TooltipTrigger>
      <TooltipContent side="top" className="bg-[#3c4043] text-white border-0">
        {label}
      </TooltipContent>
    </Tooltip>
  );
}

export function CallControls({
  isConnected,
  isStarting,
  isMicMuted,
  isSpeakerMuted,
  isCameraEnabled,
  isAvatarSpeaking,
  avatarVolume,
  onStart,
  onEnd,
  onToggleMic,
  onToggleSpeaker,
  onToggleCamera,
  onInterrupt,
  onVolumeChange,
  hasLocalCamera,
  transcriptOpen,
  onToggleTranscript,
  isFullscreen,
  onToggleFullscreen,
}) {
  if (!isConnected) {
    return (
      <TooltipProvider delayDuration={300}>
        <div className="absolute inset-x-0 bottom-0 z-30 flex flex-col items-center gap-4 pb-8 pt-16 bg-gradient-to-t from-black/80 via-black/40 to-transparent pointer-events-none">
          <div className="pointer-events-auto">
            <Button
              size="lg"
              onClick={onStart}
              disabled={isStarting}
              className="h-14 rounded-full px-10 text-base font-semibold bg-[#1a73e8] hover:bg-[#1765cc] shadow-lg shadow-blue-500/25 transition-transform hover:scale-[1.02]"
            >
              {isStarting ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Connecting&hellip;
                </>
              ) : (
                "Join now"
              )}
            </Button>
          </div>
        </div>
      </TooltipProvider>
    );
  }

  return (
    <TooltipProvider delayDuration={300}>
      <div className="absolute inset-x-0 bottom-0 z-30 flex flex-col items-center gap-3 pb-6 pt-20 bg-gradient-to-t from-black/70 via-black/30 to-transparent pointer-events-none">
        {/* Volume slider — subtle row above controls */}
        <div className="pointer-events-auto flex items-center gap-3 rounded-full bg-[#3c4043]/90 px-4 py-2 backdrop-blur-sm">
          <Volume2 className="h-4 w-4 text-white/70 shrink-0" />
          <Slider
            value={[Math.round(avatarVolume * 100)]}
            max={100}
            step={1}
            onValueChange={([val]) => onVolumeChange(val / 100)}
            aria-label="Agent volume"
            className="w-28 sm:w-36 [&_[role=slider]]:bg-white [&_[role=slider]]:border-0 [&_.bg-primary]:bg-white/80"
          />
        </div>

        {/* Main control bar */}
        <div className="pointer-events-auto flex items-center gap-2 sm:gap-3 rounded-full bg-[#202124]/90 px-3 py-2.5 sm:px-4 backdrop-blur-md border border-white/10 shadow-2xl">
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

          <ControlButton
            label={isSpeakerMuted ? "Unmute agent" : "Mute agent"}
            onClick={onToggleSpeaker}
            active={isSpeakerMuted}
          >
            {isSpeakerMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
          </ControlButton>

          {isAvatarSpeaking && (
            <ControlButton label="Interrupt agent" onClick={onInterrupt} active>
              <HandMetal className="h-5 w-5" />
            </ControlButton>
          )}

          <div className="mx-1 h-8 w-px bg-white/15 hidden sm:block" />

          <ControlButton
            label={transcriptOpen ? "Hide captions" : "Show captions"}
            onClick={onToggleTranscript}
            active={transcriptOpen}
            className="hidden sm:flex"
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

          <div className="mx-1 h-8 w-px bg-white/15" />

          <ControlButton label="Leave call" onClick={onEnd} danger>
            <PhoneOff className="h-5 w-5" />
          </ControlButton>
        </div>
      </div>
    </TooltipProvider>
  );
}
