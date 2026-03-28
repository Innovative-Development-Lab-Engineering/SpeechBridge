/**
 * StatusBar — Connection and session state indicator.
 */
const STATE_CONFIG = {
  idle: { label: "Ready", color: "status--idle", dot: "●" },
  connected: { label: "Connected", color: "status--connected", dot: "●" },
  listening: { label: "Listening", color: "status--listening", dot: "◉" },
  disconnected: { label: "Disconnected", color: "status--disconnected", dot: "○" },
};

export default function StatusBar({ status, error }) {
  const config = STATE_CONFIG[status] || STATE_CONFIG.idle;

  return (
    <div className={`status-bar ${config.color}`} role="status" aria-live="polite">
      <span className="status-dot">{config.dot}</span>
      <span className="status-label">{config.label}</span>
      {error && <span className="status-error">— {error}</span>}
    </div>
  );
}
