/**
 * useWebSocket — Custom hook managing the WebSocket lifecycle.
 * Handles connection, reconnection, message routing, and cleanup.
 */
import { useRef, useState, useCallback, useEffect } from "react";
import { createWebSocketConnection, sendConfig, sendStop } from "../services/websocketService";

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [transcript, setTranscript] = useState({ text: "", isFinal: false, language: "" });
  const [translation, setTranslation] = useState({ original: "", translated: "", sourceLanguage: "" });
  const [status, setStatus] = useState("idle"); // idle | connected | listening | disconnected
  const [wsError, setWsError] = useState(null);

  const wsRef = useRef(null);

  const connect = useCallback((languageCode, autoDetect = false, targetLanguage = "en") => {
    // Close any existing connection first
    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = createWebSocketConnection();
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setWsError(null);
      // Send config as first message
      sendConfig(ws, languageCode, autoDetect, targetLanguage);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleMessage(msg);
      } catch (e) {
        console.error("WS message parse error:", e);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      setStatus("disconnected");
    };

    ws.onerror = (e) => {
      setWsError("WebSocket connection failed. Is the backend running?");
      setIsConnected(false);
    };
  }, []);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      sendStop(wsRef.current);
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setStatus("idle");
  }, []);

  const handleMessage = (msg) => {
    switch (msg.type) {
      case "status":
        setStatus(msg.state);
        break;

      case "transcript":
        setTranscript({
          text: msg.text,
          isFinal: msg.is_final,
          language: msg.language,
          confidence: msg.confidence,
        });
        break;

      case "translation":
        setTranslation({
          original: msg.original,
          translated: msg.translated,
          sourceLanguage: msg.source_language,
          targetLanguage: msg.target_language,
          isFinal: msg.is_final,
        });
        break;

      case "tts_audio":
        // Play audio in browser
        playAudio(msg.audio_base64, msg.format);
        break;

      case "error":
        setWsError(msg.message);
        break;

      default:
        break;
    }
  };

  const getWebSocket = useCallback(() => wsRef.current, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return {
    isConnected,
    transcript,
    translation,
    status,
    wsError,
    connect,
    disconnect,
    getWebSocket,
  };
}

function playAudio(base64Audio, format = "mp3") {
  try {
    const byteChars = atob(base64Audio);
    const byteArr = new Uint8Array(byteChars.length);
    for (let i = 0; i < byteChars.length; i++) {
      byteArr[i] = byteChars.charCodeAt(i);
    }
    const blob = new Blob([byteArr], { type: `audio/${format}` });
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.play().catch(console.error);
    audio.onended = () => URL.revokeObjectURL(url);
  } catch (e) {
    console.error("TTS playback error:", e);
  }
}
