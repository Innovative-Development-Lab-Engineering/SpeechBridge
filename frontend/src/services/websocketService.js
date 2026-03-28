const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws/translate"

export function createWebSocketConnection() {
  return new WebSocket(WS_URL)
}

export function sendConfig(ws, languageCode, autoDetect = false, targetLanguage = "en") {
  ws.send(JSON.stringify({
    type: "config",
    language_code: languageCode,
    target_language: targetLanguage,
    sample_rate: 16000,
    auto_detect: autoDetect,
  }))
}

export function sendStop(ws) {
  ws.send(JSON.stringify({ type: "stop" }))
}

export function enableTTS(ws) {
  ws.send(JSON.stringify({ type: "enable_tts" }))
}
