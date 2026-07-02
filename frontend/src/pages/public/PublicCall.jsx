import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { callJoin, getInvitePreview } from "../../lib/api";
import { useTavus } from "../../hooks/useTavus.js";
import { useLocalCamera } from "../../hooks/useLocalCamera.js";
import { VideoCallRoom } from "../../components/VideoCallRoom.jsx";
import { PreJoinLobby } from "../../components/PreJoinLobby.jsx";
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
    <div className="flex min-h-[100dvh] flex-col bg-[#f8f9fa] text-[#202124]">
      <header className="flex items-center justify-between border-b border-[#dadce0] px-4 py-3 sm:px-8">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm text-[#5f6368] transition-colors hover:text-[#202124]"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to home
        </Link>
        <div className="flex items-center gap-2 text-xs text-[#5f6368]">
          <Shield className="h-3.5 w-3.5" />
          Encrypted session
        </div>
      </header>

      <main className="flex flex-1 items-center justify-center p-4 sm:p-8">
        <div className="grid w-full max-w-4xl gap-8 lg:grid-cols-2 lg:gap-12 items-center">
          <div className="hidden lg:flex flex-col gap-6">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#1a73e8] shadow-md">
              <Video className="h-7 w-7 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-normal tracking-tight leading-tight text-[#202124]">
                Join your property tour
              </h1>
              <p className="mt-3 text-base text-[#5f6368] leading-relaxed max-w-md">
                Enter the Meeting ID and Passcode from your email to connect with our AI sales agent.
              </p>
            </div>
            <ul className="space-y-3">
              {[
                { icon: Sparkles, text: "Talk naturally with a lifelike AI avatar" },
                { icon: Calendar, text: "Your session time starts when you join the call" },
                { icon: Lock, text: "Secure, encrypted one-to-one conversation" },
              ].map(({ icon: Icon, text }) => (
                <li key={text} className="flex items-center gap-3 text-sm text-[#5f6368]">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#e8f0fe]">
                    <Icon className="h-4 w-4 text-[#1a73e8]" />
                  </span>
                  {text}
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-2xl border border-[#dadce0] bg-white p-6 sm:p-8 shadow-sm">
            <div className="mb-6 lg:hidden text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-[#1a73e8]">
                <Video className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-xl font-medium text-[#202124]">Join a Meeting</h1>
              <p className="mt-1.5 text-sm text-[#5f6368]">
                Enter your credentials to continue
              </p>
            </div>

            <div className="mb-6 hidden lg:block">
              <h2 className="text-lg font-medium text-[#202124]">Enter meeting details</h2>
              <p className="mt-1 text-sm text-[#5f6368]">
                Check your email for the Meeting ID and Passcode
              </p>
            </div>

            <form onSubmit={submit} className="space-y-5">
              {error && (
                <div className="flex items-start gap-2.5 rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                  <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="meetingId" className="text-[#5f6368] text-sm">
                  Meeting ID
                </Label>
                <Input
                  id="meetingId"
                  value={meetingId}
                  onChange={(e) => setMeetingId(formatMeetingId(e.target.value))}
                  placeholder="384 291 7405"
                  autoComplete="off"
                  required
                  className="h-12 bg-white border-[#dadce0] text-[#202124] placeholder:text-[#80868b] focus-visible:ring-[#1a73e8] text-base tracking-widest font-mono"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="passcode" className="text-[#5f6368] text-sm">
                  Passcode
                </Label>
                <Input
                  id="passcode"
                  value={passcode}
                  onChange={(e) => setPasscode(e.target.value.toUpperCase())}
                  placeholder="ABC123"
                  autoComplete="off"
                  required
                  className="h-12 bg-white border-[#dadce0] text-[#202124] placeholder:text-[#80868b] focus-visible:ring-[#1a73e8] text-base tracking-widest font-mono uppercase"
                />
              </div>

              <Button
                type="submit"
                disabled={submitting}
                className="w-full h-12 rounded-full text-base font-medium bg-[#1a73e8] hover:bg-[#1765cc]"
              >
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Verifying&hellip;
                  </>
                ) : (
                  "Continue"
                )}
              </Button>

              <p className="text-center text-xs text-[#80868b] pt-1">
                Don&apos;t have a meeting?{" "}
                <Link to="/" className="text-[#1a73e8] hover:underline">
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
  const [inCall, setInCall] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const pendingMicMuted = useRef(false);
  const avatar = useTavus(callToken);
  const camera = useLocalCamera();

  useEffect(() => {
    camera.start();
    return () => camera.stop();
    // Run once on mount; camera.start/stop are stable useCallbacks. Depending on
    // the whole `camera` object would restart the stream on every render because
    // the hook returns a fresh object literal each time.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!inCall || !avatar.isConnected || !pendingMicMuted.current) return;
    if (!avatar.isMicMuted) {
      avatar.toggleMic();
    }
    pendingMicMuted.current = false;
  }, [inCall, avatar.isConnected, avatar.isMicMuted, avatar.toggleMic]);

  const handleJoin = useCallback(
    async ({ micMuted }) => {
      pendingMicMuted.current = micMuted;
      setInCall(true);
      setIsStarting(true);
      try {
        await avatar.start();
      } catch (e) {
        console.error(e);
        setInCall(false);
        pendingMicMuted.current = false;
      } finally {
        setIsStarting(false);
      }
    },
    [avatar],
  );

  const handleLeave = useCallback(async () => {
    setInCall(false);
    pendingMicMuted.current = false;
    await camera.start();
  }, [camera]);

  if (!inCall) {
    return (
      <PreJoinLobby
        camera={camera}
        displayName={displayName}
        minutesRemaining={minutesRemaining}
        isJoining={isStarting}
        onJoin={handleJoin}
      />
    );
  }

  return (
    <VideoCallRoom
      avatar={avatar}
      camera={camera}
      displayName={displayName}
      minutesRemaining={minutesRemaining}
      onLeave={handleLeave}
    />
  );
}

function LoadingScreen() {
  return (
    <div className="flex min-h-[100dvh] flex-col items-center justify-center gap-4 bg-[#f8f9fa] text-[#202124]">
      <div className="relative">
        <div className="h-16 w-16 rounded-full border-2 border-[#dadce0]" />
        <div className="absolute inset-0 h-16 w-16 animate-spin rounded-full border-2 border-transparent border-t-[#1a73e8]" />
      </div>
      <p className="text-sm text-[#5f6368]">Loading meeting&hellip;</p>
    </div>
  );
}

function ErrorScreen({ message }) {
  return (
    <div className="flex min-h-[100dvh] items-center justify-center bg-[#f8f9fa] p-4">
      <div className="w-full max-w-sm rounded-2xl border border-[#dadce0] bg-white p-8 text-center shadow-sm">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-red-50">
          <AlertCircle className="h-7 w-7 text-red-500" />
        </div>
        <h1 className="text-xl font-medium text-[#202124]">Unable to join</h1>
        <p className="mt-2 text-sm text-[#5f6368] leading-relaxed">{message}</p>
        <Button
          asChild
          className="mt-6 w-full h-11 rounded-full bg-[#1a73e8] hover:bg-[#1765cc] text-white"
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
