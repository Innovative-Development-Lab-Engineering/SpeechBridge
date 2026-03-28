/**
 * useAudioStream — Custom hook for capturing microphone audio.
 *
 * Captures browser microphone as 16kHz LINEAR16 PCM and sends
 * binary chunks to the provided WebSocket. This matches the exact
 * format required by Google Cloud STT.
 *
 * Uses ScriptProcessorNode for broad browser compatibility.
 */
import { useRef, useCallback, useState } from "react";

const TARGET_SAMPLE_RATE = 16000;
const CHUNK_SIZE = 4096; // samples per ScriptProcessorNode callback

export function useAudioStream() {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState(null);

  const audioContextRef = useRef(null);
  const streamRef = useRef(null);
  const processorRef = useRef(null);
  const sourceRef = useRef(null);

  const startRecording = useCallback(async (websocket) => {
    try {
      setError(null);

      // Request mic access
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: TARGET_SAMPLE_RATE,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      streamRef.current = mediaStream;

      // Create audio context at target sample rate
      const audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: TARGET_SAMPLE_RATE,
      });
      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(mediaStream);
      sourceRef.current = source;

      // ScriptProcessorNode: converts Float32 samples → Int16 PCM → send via WS
      const processor = audioContext.createScriptProcessor(CHUNK_SIZE, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (event) => {
        if (!websocket || websocket.readyState !== WebSocket.OPEN) return;

        const float32 = event.inputBuffer.getChannelData(0);
        const int16 = float32ToInt16(float32);
        websocket.send(int16.buffer);
      };

      source.connect(processor);
      processor.connect(audioContext.destination);

      setIsRecording(true);
    } catch (err) {
      const msg =
        err.name === "NotAllowedError"
          ? "Microphone access denied. Please allow microphone permissions."
          : `Microphone error: ${err.message}`;
      setError(msg);
      console.error("useAudioStream error:", err);
    }
  }, []);

  const stopRecording = useCallback(() => {
    // Disconnect audio graph
    if (sourceRef.current) sourceRef.current.disconnect();
    if (processorRef.current) processorRef.current.disconnect();

    // Stop both browser mic tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }

    // Close AudioContext
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }

    setIsRecording(false);
  }, []);

  return { isRecording, error, startRecording, stopRecording };
}

/**
 * Convert Float32Array (Web Audio format) to Int16Array (LINEAR16 PCM).
 * Google STT expects LINEAR16 — 16-bit signed integers.
 */
function float32ToInt16(float32Array) {
  const int16 = new Int16Array(float32Array.length);
  for (let i = 0; i < float32Array.length; i++) {
    // Clamp to [-1, 1] then scale to Int16 range
    const clamped = Math.max(-1, Math.min(1, float32Array[i]));
    int16[i] = clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff;
  }
  return int16;
}
