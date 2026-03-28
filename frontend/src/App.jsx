/**
 * App.jsx — Root application component.
 * Wires all hooks to all components.
 */
import { useState, useCallback, useEffect } from "react";
import MicButton from "./components/MicButton";
import LanguageSelector, { LANGUAGES } from "./components/LanguageSelector";
import TranscriptDisplay from "./components/TranscriptDisplay";
import TranslationDisplay from "./components/TranslationDisplay";
import StatusBar from "./components/StatusBar";
import { useWebSocket } from "./hooks/useWebSocket";
import { useAudioStream } from "./hooks/useAudioStream";

export default function App() {
  const [transcriptHistory, setTranscriptHistory] = useState([]);
  const [translationHistory, setTranslationHistory] = useState([]);
  const [language, setLanguage] = useState("hi-IN");
  const [targetLanguage, setTargetLanguage] = useState("en");

  const {
    isConnected, transcript, translation,
    status, wsError, connect, disconnect, getWebSocket,
  } = useWebSocket();

  const {
    isRecording, error: audioError,
    startRecording, stopRecording,
  } = useAudioStream();

  // Update history when a final result arrives
  useEffect(() => {
    if (transcript.isFinal && transcript.text.trim()) {
      setTranscriptHistory((prev) => [...prev, transcript]);
    }
  }, [transcript.isFinal, transcript.text]);

  useEffect(() => {
    if (translation.isFinal && translation.translated.trim()) {
      setTranslationHistory((prev) => [...prev, translation]);

      // Speak the translated text aloud using the browser's TTS
      if ("speechSynthesis" in window) {
        const utterance = new SpeechSynthesisUtterance(translation.translated);
        utterance.lang = translation.targetLanguage || targetLanguage;
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        window.speechSynthesis.cancel(); // cancel any queued speech first
        window.speechSynthesis.speak(utterance);
      }
    }
  }, [translation.isFinal, translation.translated]);

  const handleMicToggle = useCallback(async () => {
    if (isRecording) {
      stopRecording();
      disconnect();
    } else {
      // Clear history for a fresh session
      setTranscriptHistory([]);
      setTranslationHistory([]);
      
      connect(language, false, targetLanguage);
      // Small delay to let WS handshake complete
      await new Promise((r) => setTimeout(r, 400));
      const ws = getWebSocket();
      if (ws) await startRecording(ws);
    }
  }, [isRecording, language, connect, disconnect, startRecording, stopRecording, getWebSocket]);

  const displayError = wsError || audioError;

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <span className="logo-icon">⚡</span>
            <span className="logo-text">SpeechBridge</span>
          </div>
          <p className="logo-tagline">Real-time multilingual speech translation</p>
        </div>
      </header>

      <main className="app-main">
        {/* Controls */}
        <section className="controls-section" aria-label="Recording controls">
          <div className="language-pair-controls">
            <div className="control-group">
              <label>Input Language</label>
              <LanguageSelector
                value={language}
                onChange={setLanguage}
                disabled={isRecording}
              />
            </div>
            <div className="control-arrow">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12"></line>
                <polyline points="12 5 19 12 12 19"></polyline>
              </svg>
            </div>
            <div className="control-group">
              <label>Output Language</label>
              <select 
                className="target-language-select"
                value={targetLanguage}
                onChange={(e) => setTargetLanguage(e.target.value)}
                disabled={isRecording}
              >
                {LANGUAGES.map(l => (
                  <option key={`out-${l.lang}`} value={l.lang}>
                    {l.flag} {l.label} ({l.native})
                  </option>
                ))}
              </select>
            </div>
          </div>
          
          <MicButton
            isRecording={isRecording}
            isConnected={isConnected}
            onClick={handleMicToggle}
          />
          <StatusBar status={status} error={displayError} />
        </section>

        {/* Panels */}
        <section className="panels-section" aria-label="Translation output">
          <TranscriptDisplay transcript={transcript} history={transcriptHistory} />
          <TranslationDisplay translation={translation} history={translationHistory} />
        </section>

        {/* Agent Skills badge */}
        <div className="agent-badge" title="Powered by Google ADK Agent Skills">
          <span>🤖</span>
          <span>Powered by Google ADK · STT · Translate · TTS Skills</span>
        </div>
      </main>

      <footer className="app-footer">
        <p>Built with Google Cloud Speech-to-Text · Translation API · ADK Agent Skills</p>
      </footer>
    </div>
  );
}
