import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AlertTriangle, Bot, MessageSquare, User, X } from "lucide-react";
import { cn } from "@/lib/utils";

export function TranscriptPanel({
  status,
  messages,
  liveUserText,
  liveAgentText,
  isUserSpeaking,
  isAvatarSpeaking,
  sessionWarning,
  onClose,
  className,
}) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, liveUserText, liveAgentText, status]);

  const hasHistory = messages.length > 0;
  const showLiveUser = Boolean(liveUserText.trim() && isUserSpeaking);
  const showLiveAgent = Boolean(liveAgentText.trim() && isAvatarSpeaking);
  const isLive = status !== "idle";

  return (
    <aside
      className={cn(
        "flex w-full sm:w-[340px] lg:w-[380px] shrink-0 flex-col",
        "border-l border-white/10 bg-[#292a2d]",
        "animate-in slide-in-from-right-4 duration-300",
        className
      )}
    >
      <header className="flex items-center justify-between border-b border-white/10 px-4 py-3.5">
        <div className="flex items-center gap-2.5">
          <MessageSquare className="h-4 w-4 text-white/70" />
          <h2 className="text-sm font-semibold text-white">Live captions</h2>
          <span
            className={cn(
              "rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
              isLive
                ? "bg-emerald-500/20 text-emerald-400"
                : "bg-white/10 text-white/50"
            )}
          >
            {isLive ? "Live" : "Offline"}
          </span>
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-1.5 text-white/60 transition-colors hover:bg-white/10 hover:text-white"
            aria-label="Close captions"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </header>

      {sessionWarning && (
        <div
          className="mx-4 mt-3 flex items-start gap-2 rounded-lg bg-amber-500/15 border border-amber-500/30 px-3 py-2.5 text-xs text-amber-200"
          role="status"
        >
          <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
          <span>{sessionWarning}</span>
        </div>
      )}

      <ScrollArea className="flex-1 px-4 py-4">
        <div className="flex flex-col gap-3">
          {!hasHistory && !showLiveUser && !showLiveAgent && status === "idle" && (
            <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white/5">
                <MessageSquare className="h-5 w-5 text-white/30" />
              </div>
              <p className="text-sm text-white/40 max-w-[220px] leading-relaxed">
                Captions will appear here once you join and start talking.
              </p>
            </div>
          )}

          {status === "connecting" && (
            <div className="self-center flex items-center gap-2 rounded-full bg-white/5 px-4 py-2 text-xs text-white/50 animate-fade-in">
              <span className="inline-flex gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-white/40 animate-bounce-dot" />
                <span className="h-1.5 w-1.5 rounded-full bg-white/40 animate-bounce-dot [animation-delay:150ms]" />
                <span className="h-1.5 w-1.5 rounded-full bg-white/40 animate-bounce-dot [animation-delay:300ms]" />
              </span>
              Connecting&hellip;
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={cn(
                "flex gap-2.5 animate-fade-in",
                msg.role === "user" && "flex-row-reverse"
              )}
            >
              <div
                className={cn(
                  "flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
                  msg.role === "user" ? "bg-[#1a73e8]/30" : "bg-white/10"
                )}
              >
                {msg.role === "user" ? (
                  <User className="h-3.5 w-3.5 text-[#8ab4f8]" />
                ) : (
                  <Bot className="h-3.5 w-3.5 text-white/70" />
                )}
              </div>
              <div
                className={cn(
                  "max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed",
                  msg.role === "user"
                    ? "bg-[#1a73e8]/20 text-white rounded-tr-sm"
                    : "bg-white/10 text-white/90 rounded-tl-sm"
                )}
              >
                <span className="block text-[10px] font-semibold uppercase tracking-wider text-white/40 mb-1">
                  {msg.role === "user" ? "You" : "Agent"}
                </span>
                {msg.text}
              </div>
            </div>
          ))}

          {showLiveUser && (
            <div className="flex gap-2.5 flex-row-reverse animate-fade-in">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#1a73e8]/30">
                <User className="h-3.5 w-3.5 text-[#8ab4f8]" />
              </div>
              <div
                className={cn(
                  "max-w-[85%] rounded-2xl rounded-tr-sm px-3.5 py-2.5 text-sm leading-relaxed bg-[#1a73e8]/20 text-white",
                  isUserSpeaking && "ring-1 ring-[#1a73e8]/50"
                )}
              >
                <span className="block text-[10px] font-semibold uppercase tracking-wider text-white/40 mb-1">
                  You
                </span>
                {liveUserText}
              </div>
            </div>
          )}

          {status === "thinking" && !showLiveAgent && (
            <div className="self-start flex items-center gap-2.5 animate-fade-in ml-9">
              <div className="flex items-center gap-2 rounded-full bg-white/5 px-4 py-2 text-xs text-white/50">
                <span className="inline-flex gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-bounce-dot" />
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-bounce-dot [animation-delay:150ms]" />
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-bounce-dot [animation-delay:300ms]" />
                </span>
                Agent is thinking&hellip;
              </div>
            </div>
          )}

          {showLiveAgent && (
            <div className="flex gap-2.5 animate-fade-in">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white/10">
                <Bot className="h-3.5 w-3.5 text-white/70" />
              </div>
              <div
                className={cn(
                  "max-w-[85%] rounded-2xl rounded-tl-sm px-3.5 py-2.5 text-sm leading-relaxed bg-white/10 text-white/90",
                  isAvatarSpeaking && "ring-1 ring-blue-400/40"
                )}
              >
                <span className="block text-[10px] font-semibold uppercase tracking-wider text-white/40 mb-1">
                  Agent
                </span>
                {liveAgentText}
              </div>
            </div>
          )}

          <div ref={endRef} />
        </div>
      </ScrollArea>
    </aside>
  );
}
