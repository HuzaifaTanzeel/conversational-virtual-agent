import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Local webcam preview only — never published to Tavus/Daily.
 */
export function useLocalCamera() {
  const streamRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [enabled, setEnabled] = useState(true);
  const [error, setError] = useState(null);

  const stop = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setStream(null);
    setError(null);
  }, []);

  const start = useCallback(async () => {
    stop();
    try {
      const media = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      });
      streamRef.current = media;
      setStream(media);
      setEnabled(true);
      setError(null);
    } catch (err) {
      setError(err?.message || "Camera access denied");
      setStream(null);
    }
  }, [stop]);

  const toggleCamera = useCallback(() => {
    const track = streamRef.current?.getVideoTracks()[0];
    if (!track) return;
    track.enabled = !track.enabled;
    setEnabled(track.enabled);
  }, []);

  useEffect(() => () => stop(), [stop]);

  return { stream, enabled, error, start, stop, toggleCamera };
}
