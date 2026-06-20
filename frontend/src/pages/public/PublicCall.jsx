import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { callJoin, getInvitePreview } from "../../lib/api";
import { useTavus } from "../../hooks/useTavus.js";
import { useLocalCamera } from "../../hooks/useLocalCamera.js";
import { VideoCallRoom } from "../../components/VideoCallRoom.jsx";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  ArrowLeft,
  Calendar,
  Loader2,
  Lock,
  Shield,
  Sparkles,
  Video,
  AlertCircle,
} from "lucide-react";
function formatMeetingId(value) {
  const digits = value.replace(/\D/g, "").slice(0, 10);
  return digits.replace(/(\d{3})(?=\d)/g, "$1 ").trim();
}

function CallJoinGate({ onAuthed, initialMeetingId = "", initialPasscode = "", autoJoin = false }) {
  const [meetingId, setMeetingId] = useState(formatMeetingId(initialMeetingId));
  const [passcode, setPasscode] = useState(initialPasscode);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const autoJoinAttempted = useRef(false);

  const submit = useCallback(async (e) => {
    if (e) e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const data = await callJoin(meetingId.replace(/\s/g, ""), passcode.trim());
      onAuthed(data);
    } catch (err) {
      setError(err?.response?.data?.detail || "Could not join the meeting. Check your details.");
    } finally {
      setSubmitting(false);
    }
  }, [meetingId, passcode, onAuthed]);

  useEffect(() => {
    if (initialMeetingId) {
      setMeetingId(formatMeetingId(initialMeetingId));
    }
  }, [initialMeetingId]);

  useEffect(() => {
    if (autoJoin && initialMeetingId && initialPasscode && !autoJoinAttempted.current) {
      autoJoinAttempted.current = true;
      submit();
    }
  }, [autoJoin, initialMeetingId, initialPasscode, submit]);

  return (
    <div className="relative flex min-h-[100dvh] flex-col bg-[#202124] text-white overflow-hidden">
      {/* Ambient background */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-32 -left-32 h-96 w-96 rounded-full bg-[#1a73e8]/20 blur-3xl" />
        <div className="absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-[#8ab4f8]/10 blur-3xl" />
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRhZHRzIGZpbGw9IiNmZmYiIGZpbGwtcnVsZT0iZXZlbm9kZCIgb3BhY2l0eT0iMC4wMiI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiLz48L2RhZHRzPjwvc3ZnPg==')] opacity-40" />
      </div>

      {/* Header */}
      <header className="relative z-10 flex items-center justify-between px-4 py-4 sm:px-8">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm text-white/60 transition-colors hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to home
        </Link>
        <div className="flex items-center gap-2 text-sm text-white/50">
          <Shield className="h-4 w-4" />
          Encrypted session
        </div>
      </header>

      {/* Content */}
      <main className="relative z-10 flex flex-1 items-center justify-center p-4 sm:p-8">
        <div className="grid w-full max-w-4xl gap-8 lg:grid-cols-2 lg:gap-12 items-center">
          {/* Left — hero */}
          <div className="hidden lg:flex flex-col gap-6">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#1a73e8] shadow-lg shadow-blue-500/30">
              <Video className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight leading-tight">
                Ready to join your meeting?
              </h1>
              <p className="mt-3 text-base text-white/50 leading-relaxed max-w-md">
                Enter the Meeting ID and Passcode from your email to connect with our AI sales agent.
              </p>
            </div>
            <ul className="space-y-3">
              {[
                { icon: Sparkles, text: "Talk naturally with a lifelike AI avatar" },
                { icon: Calendar, text: "Your session time starts when you join" },
                { icon: Lock, text: "Secure, encrypted one-to-one conversation" },
              ].map(({ icon: Icon, text }) => (
                <li key={text} className="flex items-center gap-3 text-sm text-white/60">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/5">
                    <Icon className="h-4 w-4 text-[#8ab4f8]" />
                  </span>
                  {text}
                </li>
              ))}
            </ul>
          </div>

          {/* Right — form card */}
          <div className="rounded-2xl border border-white/10 bg-white/5 p-6 sm:p-8 backdrop-blur-xl shadow-2xl">
            <div className="mb-6 lg:hidden text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#1a73e8] shadow-lg shadow-blue-500/30">
                <Video className="h-7 w-7 text-white" />
              </div>
              <h1 className="text-xl font-bold">Join a Meeting</h1>
              <p className="mt-1.5 text-sm text-white/50">
                Enter your credentials to get started
              </p>
            </div>

            <div className="mb-6 hidden lg:block">
              <h2 className="text-lg font-semibold">Enter meeting details</h2>
              <p className="mt-1 text-sm text-white/50">
                Check your email for the Meeting ID and Passcode
              </p>
            </div>

            <form onSubmit={submit} className="space-y-5">
              {error && (
                <div className="flex items-start gap-2.5 rounded-xl bg-red-500/15 border border-red-500/30 px-4 py-3 text-sm text-red-300">
                  <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="meetingId" className="text-white/70 text-sm">
                  Meeting ID
                </Label>
                <Input
                  id="meetingId"
                  value={meetingId}
                  onChange={(e) => setMeetingId(formatMeetingId(e.target.value))}
                  placeholder="384 291 7405"
                  autoComplete="off"
                  required
                  className="h-12 bg-white/5 border-white/10 text-white placeholder:text-white/30 focus-visible:ring-[#1a73e8] text-base tracking-widest font-mono"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="passcode" className="text-white/70 text-sm">
                  Passcode
                </Label>
                <Input
                  id="passcode"
                  value={passcode}
                  onChange={(e) => setPasscode(e.target.value.toUpperCase())}
                  placeholder="ABC123"
                  autoComplete="off"
                  required
                  className="h-12 bg-white/5 border-white/10 text-white placeholder:text-white/30 focus-visible:ring-[#1a73e8] text-base tracking-widest font-mono uppercase"
                />
              </div>

              <Button
                type="submit"
                disabled={submitting}
                className="w-full h-12 rounded-xl text-base font-semibold bg-[#1a73e8] hover:bg-[#1765cc] shadow-lg shadow-blue-500/20 transition-transform hover:scale-[1.01]"
              >
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Joining&hellip;
                  </>
                ) : (
                  "Join meeting"
                )}
              </Button>

              <p className="text-center text-xs text-white/40 pt-1">
                Don&apos;t have a meeting?{" "}
                <Link to="/" className="text-[#8ab4f8] hover:text-white transition-colors">
                  Book a call
                </Link>
              </p>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}

function CallStage({ callToken, displayName, minutesRemaining }) {
  const [isStarting, setIsStarting] = useState(false);
  const [currentMedia, setCurrentMedia] = useState(null);
  const avatar = useTavus(callToken, { onMediaEvent: setCurrentMedia });
  const camera = useLocalCamera();

  useEffect(() => {
    camera.start();
    return () => camera.stop();
  }, [camera]);

  const handleStart = useCallback(async () => {
    setIsStarting(true);
    try {
      await avatar.start();
    } catch (e) {
      console.error(e);
    } finally {
      setIsStarting(false);
    }
  }, [avatar]);

  useEffect(() => {
    if (avatar.isConnected) {
      setIsStarting(false);
    }
  }, [avatar.isConnected]);

  return (
    <VideoCallRoom
      avatar={avatar}
      camera={camera}
      isStarting={isStarting}
      onStart={handleStart}
      displayName={displayName}
      minutesRemaining={minutesRemaining}
      currentMedia={currentMedia}
    />
  );
}

function LoadingScreen() {
  return (
    <div className="flex min-h-[100dvh] flex-col items-center justify-center gap-4 bg-[#202124] text-white">
      <div className="relative">
        <div className="h-16 w-16 rounded-full border-2 border-white/10" />
        <div className="absolute inset-0 h-16 w-16 animate-spin rounded-full border-2 border-transparent border-t-[#1a73e8]" />
      </div>
      <p className="text-sm text-white/50">Loading meeting&hellip;</p>
    </div>
  );
}

function ErrorScreen({ message }) {
  return (
    <div className="relative flex min-h-[100dvh] items-center justify-center bg-[#202124] p-4 overflow-hidden">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-32 left-1/2 -translate-x-1/2 h-64 w-64 rounded-full bg-red-500/10 blur-3xl" />
      </div>
      <div className="relative w-full max-w-sm rounded-2xl border border-white/10 bg-white/5 p-8 text-center backdrop-blur-xl">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-red-500/15">
          <AlertCircle className="h-7 w-7 text-red-400" />
        </div>
        <h1 className="text-xl font-bold text-white">Unable to join</h1>
        <p className="mt-2 text-sm text-white/50 leading-relaxed">{message}</p>
        <Button
          asChild
          className="mt-6 w-full h-11 rounded-xl bg-white/10 hover:bg-white/15 text-white border-0"
        >
          <Link to="/">Book a new call</Link>
        </Button>
      </div>
    </div>
  );
}

export function PublicCall() {
  const [session, setSession] = useState(null);
  const { inviteId } = useParams();
  const [searchParams] = useSearchParams();
  const passcodeFromUrl = searchParams.get("p") || "";

  const [inviteLoading, setInviteLoading] = useState(!!inviteId);
  const [inviteError, setInviteError] = useState("");
  const [initialMeetingId, setInitialMeetingId] = useState("");
  const [initialPasscode, setInitialPasscode] = useState(passcodeFromUrl);
  const [autoJoin, setAutoJoin] = useState(false);

  useEffect(() => {
    if (!inviteId) return;
    setInviteLoading(true);
    getInvitePreview(inviteId)
      .then((invite) => {
        if (invite.status !== "pending") {
          setInviteError(
            invite.status === "cancelled"
              ? "This meeting has been cancelled."
              : "This meeting link has already been used."
          );
          return;
        }
        setInitialMeetingId(invite.meeting_id);
        if (passcodeFromUrl) {
          setInitialPasscode(passcodeFromUrl);
          setAutoJoin(true);
        }
      })
      .catch(() => setInviteError("Meeting not found or no longer available."))
      .finally(() => setInviteLoading(false));
  }, [inviteId, passcodeFromUrl]);

  if (session) {
    return (
      <CallStage
        callToken={session.call_token}
        displayName={session.display_name}
        minutesRemaining={session.minutes_remaining}
      />
    );
  }

  if (inviteLoading) return <LoadingScreen />;
  if (inviteError) return <ErrorScreen message={inviteError} />;

  return (
    <CallJoinGate
      onAuthed={setSession}
      initialMeetingId={initialMeetingId}
      initialPasscode={initialPasscode}
      autoJoin={autoJoin}
    />
  );
}
