/**
 * TranslationDisplay — Shows real-time English translation output.
 */
import { useRef, useEffect } from "react";

export default function TranslationDisplay({ translation, history = [] }) {
  const endRef = useRef(null);
  const { translated, original } = translation;

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [translated]);

  return (
    <div className="panel translation-panel">
      <div className="panel-header">
        <span className="panel-icon">🌐</span>
        <h2 className="panel-title">Translation</h2>
        <span className="lang-badge lang-badge--en">EN</span>
      </div>
      <div className="panel-body" aria-live="polite" aria-label="English translation">
        <div className="conversation-flow">
          <p className="translation-text text--final">
            {history.map(t => t.translated).join(" ")}
            
            {translated && !history.some(h => h.original === original) && (
              <span className="text--interim"> {translated}</span>
            )}
          </p>

          {!translated && history.length === 0 && (
            <p className="panel-placeholder">English translation will appear here...</p>
          )}
        </div>
        <div ref={endRef} />
      </div>
    </div>
  );
}
