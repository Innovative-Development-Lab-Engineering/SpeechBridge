/**
 * TranscriptDisplay — Shows live original-language transcription.
 * Interim text appears muted; final text appears solid.
 */
import { useRef, useEffect } from "react";

export default function TranscriptDisplay({ transcript, history = [] }) {
  const endRef = useRef(null);
  const { text, isFinal, language } = transcript;

  // Auto-scroll on new content
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [text]);

  const langLabel = language
    ? language.split("-")[0].toUpperCase()
    : "";

  return (
    <div className="panel transcript-panel">
      <div className="panel-header">
        <span className="panel-icon">🎙️</span>
        <h2 className="panel-title">Original</h2>
        {langLabel && <span className="lang-badge">{langLabel}</span>}
      </div>
      <div className="panel-body" aria-live="polite" aria-label="Live transcription">
        <div className="conversation-flow">
          {history.map((t, index) => (
            <p key={`hist-${index}`} className="transcript-text text--final">
              {t.text}
            </p>
          ))}
          
          {text && !isFinal && (
            <p className="transcript-text text--interim">
              {text}
              <span className="cursor-blink">|</span>
            </p>
          )}

          {!text && history.length === 0 && (
            <p className="panel-placeholder">Transcription will appear here as you speak...</p>
          )}
        </div>
        <div ref={endRef} />
      </div>
    </div>
  );
}
