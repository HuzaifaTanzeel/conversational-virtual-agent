/**
 * useTavus — Tavus CVI + Daily.co session hook
 */

import { useCallback, useEffect, useRef, useState } from "react";
import DailyIframe from "@daily-co/daily-js";
import { createSession, endSession, postConversation, resolveToolCall } from "../lib/api";
import { navigateToArea } from "../lib/krpanoController.js";
import { NAVIGATE_TOOL_NAMES } from "../lib/sceneRegistry.js";

/**
 * Build a spoken clarifying question when a room name maps to more than one
 * villa/residence, e.g. "Which one did you mean — the Three Bedroom Lagoon
 * Residence or the Two Bedroom Overwater Pool Villa?".
 */
function buildClarifyingQuestion(options = []) {
  const labels = options.map((o) => `the ${o}`);
  let list;
  if (labels.length <= 1) {
    list = labels.join("");
  } else if (labels.length === 2) {
    list = `${labels[0]} or ${labels[1]}`;
  } else {
    list = `${labels.slice(0, -1).join(", ")}, or ${labels[labels.length - 1]}`;
  }
  return `Which one did you mean — ${list}?`;
}

const BROCHURE_URLS = {
  planet_trekkers:
    "https://issuu.com/icmmg/docs/icm_planet-trekkers-brochure_final?fr=sN2ZlMjUzNDY5NDg",
};

export function useTavus(callToken) {
  const callRef = useRef(null);
  const avatarVideoRef = useRef(null);
  const avatarAudioRef = useRef(null);
  const callSessionIdRef = useRef(null);
  const callTokenRef = useRef(callToken);
  const conversationIdRef = useRef(null);
  const conversationUrlRef = useRef(null);
  const messagesRef = useRef([]);

  const [isConnected, setIsConnected] = useState(false);
  const [isAvatarSpeaking, setIsAvatarSpeaking] = useState(false);
  const [isUserSpeaking, setIsUserSpeaking] = useState(false);
  const [messages, setMessages] = useState([]);
  const [liveUserText, setLiveUserText] = useState("");
  const [liveAgentText, setLiveAgentText] = useState("");
  const liveUserRef = useRef("");
  const liveAgentRef = useRef("");
  const [status, setStatus] = useState("idle");
  const [videoElement, setVideoElement] = useState(null);
  const [sessionWarning, setSessionWarning] = useState("");
  const [isMicMuted, setIsMicMuted] = useState(false);
  const [isSpeakerMuted, setIsSpeakerMuted] = useState(false);
  const [avatarVolume, setAvatarVolumeState] = useState(1);
  const [remoteParticipants, setRemoteParticipants] = useState({});
  const [brochureUrl, setBrochureUrl] = useState(null);

  useEffect(() => {
    callTokenRef.current = callToken;
  }, [callToken]);

  const applySpeakerSettings = useCallback((audioEl, muted, volume) => {
    if (!audioEl) return;
    audioEl.muted = muted;
    audioEl.volume = muted ? 0 : volume;
  }, []);

  const setAvatarVolume = useCallback(
    (value) => {
      const v = Math.min(1, Math.max(0, value));
      setAvatarVolumeState(v);
      if (avatarAudioRef.current) {
        avatarAudioRef.current.volume = isSpeakerMuted ? 0 : v;
      }
    },
    [isSpeakerMuted],
  );

  const appendMessage = useCallback((role, text) => {
    const trimmed = (text || "").trim();
    if (!trimmed) return;
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (last?.role === role && last.text === trimmed) return prev;
      const next = [
        ...prev,
        { id: `${role}-${Date.now()}-${prev.length}`, role, text: trimmed },
      ];
      messagesRef.current = next;
      return next;
    });
  }, []);

  const attachVideoTrack = useCallback((track) => {
    if (!track || track.kind !== "video") return;
    const video = document.createElement("video");
    video.autoplay = true;
    video.playsInline = true;
    video.muted = true;
    video.srcObject = new MediaStream([track]);
    avatarVideoRef.current = video;
    video.play().catch((err) => console.warn("Avatar video play failed:", err));
    setVideoElement(video);
  }, []);

  const attachAudioTrack = useCallback(
    (track) => {
      if (!track || track.kind !== "audio") return;
      const audio = document.createElement("audio");
      audio.autoplay = true;
      audio.playsInline = true;
      audio.srcObject = new MediaStream([track]);
      avatarAudioRef.current = audio;
      applySpeakerSettings(audio, isSpeakerMuted, avatarVolume);
      audio.play().catch((err) => console.warn("Avatar audio play failed:", err));
    },
    [applySpeakerSettings, avatarVolume, isSpeakerMuted],
  );

  const handleToolCall = useCallback(
    async (call, data) => {
      const toolName = data.properties?.name;
      console.log("[tavus] tool_call received:", toolName, data.properties);
      if (!toolName) return;

      const rawArgs = data.properties?.arguments;
      let parameters = {};
      try {
        parameters =
          typeof rawArgs === "string" ? JSON.parse(rawArgs) : rawArgs || {};
      } catch (err) {
        console.warn("[tavus] Failed to parse tool call arguments:", rawArgs, err);
      }
      console.log("[tavus] tool args", {
        tool: toolName,
        raw: rawArgs,
        parsed: parameters,
        area: parameters.area,
        speech: parameters.speech,
      });

      if (toolName === "show_brochure") {
        const brochureId = parameters.brochure_id || "planet_trekkers";
        const url = BROCHURE_URLS[brochureId];
        if (url) {
          setBrochureUrl(url);
          console.log(`[tavus] show_brochure: showing ${brochureId}`);
        }
        const speech = parameters.speech?.trim() || "";
        if (speech && call && data.conversation_id) {
          call.sendAppMessage(
            {
              message_type: "conversation",
              event_type: "conversation.echo",
              conversation_id: data.conversation_id,
              properties: { modality: "text", text: speech, done: true },
            },
            "*",
          );
        }
        return;
      }

      if (toolName === "navigate_to_area" || NAVIGATE_TOOL_NAMES.has(toolName)) {
        // Clear brochure overlay when navigating
        setBrochureUrl(null);

        // Stop any in-flight replica speech so we don't narrate a place we
        // haven't shown yet (Tavus may already be reading the tool speech).
        if (call && data.conversation_id) {
          call.sendAppMessage(
            {
              message_type: "conversation",
              event_type: "conversation.interrupt",
              conversation_id: data.conversation_id,
              properties: {},
            },
            "*",
          );
        }

        // Direct registry lookup: enum value -> krpano scene. No NLP needed.
        const result = navigateToArea(parameters.area || "");
        console.log(
          `[tavus] navigate_to_area: "${parameters.area}" => ${result.status}` +
            (result.krpanoSceneId ? ` (${result.krpanoSceneId} / "${result.label}")` : ""),
          result,
        );

        // Best-effort logging only (no asset resolution anymore).
        const callSessionId = callSessionIdRef.current;
        const callToken = callTokenRef.current;
        if (callSessionId && callToken) {
          resolveToolCall(
            callSessionId,
            { tool_name: toolName, parameters },
            callToken,
          ).catch((err) => {
            console.warn("Failed to log navigate tool call:", err);
          });
        }

        // Decide what the avatar says. On success we use the LLM's speech; for
        // ambiguous/not-found we override so it asks/redirects instead of
        // pretending it showed something.
        let speech = parameters.speech?.trim() || "";
        if (result.status === "notFound") {
          speech = `I'm sorry, I wasn't able to find that area in the tour. Is there another part of the resort I can show you?`;
        }

        if (speech && call && data.conversation_id) {
          call.sendAppMessage(
            {
              message_type: "conversation",
              event_type: "conversation.echo",
              conversation_id: data.conversation_id,
              properties: { modality: "text", text: speech, done: true },
            },
            "*",
          );
        }
      }
    },
    [],
  );

  const setupDailyCall = useCallback(
    (conversationUrl, meetingToken) => {
      if (!conversationUrl) return null;

      if (window.__avatourDailyCall) {
        window.__avatourDailyCall.leave().catch(() => {});
        window.__avatourDailyCall.destroy().catch(() => {});
        window.__avatourDailyCall = null;
      }

      const call = DailyIframe.createCallObject({
        subscribeToTracksAutomatically: true,
      });
      window.__avatourDailyCall = call;
      callRef.current = call;

      const updateParticipants = () => {
        const all = call.participants();
        const remotes = Object.fromEntries(
          Object.entries(all).filter(([id]) => id !== "local"),
        );
        setRemoteParticipants(remotes);

        for (const participant of Object.values(remotes)) {
          const videoTrack = participant?.tracks?.video?.persistentTrack;
          const audioTrack = participant?.tracks?.audio?.persistentTrack;
          if (videoTrack) attachVideoTrack(videoTrack);
          if (audioTrack) attachAudioTrack(audioTrack);
        }
      };

      call.on("joined-meeting", () => {
        setIsConnected(true);
        setStatus("listening");
        updateParticipants();
      });

      call.on("participant-joined", updateParticipants);
      call.on("participant-updated", updateParticipants);
      call.on("participant-left", updateParticipants);

      call.on("track-started", (event) => {
        if (event.participant?.local) return;
        if (event.track?.kind === "video") attachVideoTrack(event.track);
        if (event.track?.kind === "audio") attachAudioTrack(event.track);
      });

      call.on("app-message", (event) => {
        const data = event?.data;
        if (!data) return;

        // Trace every conversation event so tool calls (or their absence) are
        // visible in the console while debugging navigation.
        if (data.event_type && data.event_type !== "conversation.utterance") {
          console.log("[tavus] app-message:", data.event_type, data.properties);
        }

        if (data.conversation_id) {
          conversationIdRef.current = data.conversation_id;
        }

        if (data.event_type === "conversation.tool_call") {
          handleToolCall(call, data);
        }

        if (data.event_type === "conversation.utterance") {
          const role = data.properties?.role === "user" ? "user" : "agent";
          const text = data.properties?.speech || "";
          if (role === "user") {
            liveUserRef.current = text;
            setLiveUserText(text);
            setIsUserSpeaking(true);
            appendMessage("user", text);
          } else {
            liveAgentRef.current = text;
            setLiveAgentText(text);
            appendMessage("agent", text);
          }
        }

        if (
          data.event_type === "conversation.replica.started_speaking" ||
          (data.event_type === "conversation.started_speaking" &&
            data.properties?.role === "replica")
        ) {
          setIsAvatarSpeaking(true);
          setIsUserSpeaking(false);
          setStatus("speaking");
        }
        if (
          data.event_type === "conversation.replica.stopped_speaking" ||
          (data.event_type === "conversation.stopped_speaking" &&
            data.properties?.role === "replica")
        ) {
          setIsAvatarSpeaking(false);
          setStatus("listening");
        }
        if (
          data.event_type === "conversation.started_speaking" &&
          data.properties?.role === "user"
        ) {
          setIsUserSpeaking(true);
        }
        if (
          data.event_type === "conversation.stopped_speaking" &&
          data.properties?.role === "user"
        ) {
          setIsUserSpeaking(false);
        }
      });

      call.on("left-meeting", () => {
        setIsConnected(false);
        setStatus("idle");
      });

      const joinOptions = { url: conversationUrl };
      if (typeof meetingToken === "string" && meetingToken) {
        joinOptions.token = meetingToken;
      }

      call.join(joinOptions).catch((err) => {
        console.error("Daily join failed:", err);
        setSessionWarning(err?.message || "Failed to join the conversation room.");
        setStatus("error");
      });

      return call;
    },
    [appendMessage, attachAudioTrack, attachVideoTrack, handleToolCall],
  );

  const toggleMic = useCallback(async () => {
    const call = callRef.current;
    if (!call) return;
    const next = !isMicMuted;
    call.setLocalAudio(!next);
    setIsMicMuted(next);
  }, [isMicMuted]);

  const toggleSpeaker = useCallback(() => {
    setIsSpeakerMuted((prev) => {
      const next = !prev;
      applySpeakerSettings(avatarAudioRef.current, next, avatarVolume);
      return next;
    });
  }, [applySpeakerSettings, avatarVolume]);

  const start = useCallback(async () => {
    setStatus("connecting");
    try {
      const {
        conversation_url,
        meeting_token,
        warnings,
        call_session_id,
      } = await createSession(callToken);

      callSessionIdRef.current = call_session_id || null;
      conversationUrlRef.current = conversation_url || null;
      setSessionWarning(warnings?.[0] ?? "");

      setupDailyCall(conversation_url, meeting_token);
    } catch (err) {
      const detail =
        err?.response?.data?.detail ||
        err?.message ||
        "Failed to start the call.";
      console.error("Failed to start Tavus session:", detail, err);
      setSessionWarning(detail);
      setStatus("error");
      throw err;
    }
  }, [callToken, setupDailyCall]);

  const persistAndEnd = useCallback(async () => {
    const callSessionId = callSessionIdRef.current;
    if (!callSessionId || !callToken) return;
    try {
      const turns = messagesRef.current.map((m) => ({
        role: m.role === "agent" ? "assistant" : "user",
        content: m.text,
      }));
      if (turns.length) {
        await postConversation(callSessionId, turns, callToken);
      }
    } catch (err) {
      console.warn("Failed to persist conversation:", err);
    }
    try {
      await endSession(callSessionId, callToken);
    } catch (err) {
      console.warn("Failed to end session cleanly:", err);
    }
    callSessionIdRef.current = null;
  }, [callToken]);

  const stop = useCallback(async () => {
    const call = callRef.current;
    if (call) {
      await call.leave().catch(() => {});
      await call.destroy().catch(() => {});
    }
    window.__avatourDailyCall = null;
    callRef.current = null;
    await persistAndEnd();
    avatarVideoRef.current = null;
    avatarAudioRef.current = null;
    setIsConnected(false);
    setStatus("idle");
    setVideoElement(null);
    setSessionWarning("");
    setMessages([]);
    messagesRef.current = [];
    liveUserRef.current = "";
    liveAgentRef.current = "";
    setLiveUserText("");
    setLiveAgentText("");
    setIsMicMuted(false);
    setIsSpeakerMuted(false);
    setRemoteParticipants({});
  }, [persistAndEnd]);

  const interrupt = useCallback(() => {
    // Tavus/Daily interrupt is handled server-side; no-op on client for now.
  }, []);

  useEffect(() => {
    return () => {
      if (callRef.current) {
        callRef.current.leave().catch(() => {});
        callRef.current.destroy().catch(() => {});
      }
      window.__avatourDailyCall = null;
    };
  }, []);

  const closeBrochure = useCallback(() => {
    setBrochureUrl(null);
  }, []);

  return {
    start,
    stop,
    interrupt,
    toggleMic,
    toggleSpeaker,
    setAvatarVolume,
    isConnected,
    isAvatarSpeaking,
    isUserSpeaking,
    isMicMuted,
    isSpeakerMuted,
    avatarVolume,
    messages,
    liveUserText,
    liveAgentText,
    status,
    videoElement,
    sessionWarning,
    remoteParticipants,
    brochureUrl,
    closeBrochure,
  };
}
