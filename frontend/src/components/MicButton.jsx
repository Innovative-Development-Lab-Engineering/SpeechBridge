/**
 * MicButton — Animated microphone start/stop button.
 * Shows pulsing ring while recording, idle state when stopped.
 */
export default function MicButton({ isRecording, isConnected, onClick }) {
  return (
    <div className="mic-button-wrapper">
      {isRecording && (
        <>
          <span className="mic-pulse mic-pulse-1" />
          <span className="mic-pulse mic-pulse-2" />
        </>
      )}
      <button
        id="mic-toggle-btn"
        className={`mic-button ${isRecording ? "mic-button--recording" : ""}`}
        onClick={onClick}
        aria-label={isRecording ? "Stop recording" : "Start recording"}
        title={isRecording ? "Stop recording" : "Start recording"}
      >
        {isRecording ? (
          <svg viewBox="0 0 24 24" fill="currentColor" width="32" height="32">
            <rect x="6" y="6" width="12" height="12" rx="2" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="currentColor" width="32" height="32">
            <path d="M12 1a4 4 0 0 1 4 4v6a4 4 0 0 1-8 0V5a4 4 0 0 1 4-4zm0 2a2 2 0 0 0-2 2v6a2 2 0 0 0 4 0V5a2 2 0 0 0-2-2zm7 8a1 1 0 0 1 1 1 8 8 0 0 1-7 7.938V21h2a1 1 0 0 1 0 2H9a1 1 0 0 1 0-2h2v-1.062A8 8 0 0 1 4 12a1 1 0 0 1 2 0 6 6 0 0 0 12 0 1 1 0 0 1 1-1z" />
          </svg>
        )}
      </button>
      <span className="mic-label">
        {isRecording ? "Recording..." : "Tap to speak"}
      </span>
    </div>
  );
}
