/**
 * LanguageSelector — Source language dropdown.
 * Allows the user to select input language before starting recording.
 */
export const LANGUAGES = [
  { code: "en-US", lang: "en", label: "English", flag: "🇺🇸", native: "English" },
  { code: "hi-IN", lang: "hi", label: "Hindi", flag: "🇮🇳", native: "हिन्दी" },
  { code: "es-ES", lang: "es", label: "Spanish", flag: "🇪🇸", native: "Español" },
  { code: "gu-IN", lang: "gu", label: "Gujarati", flag: "🇮🇳", native: "ગુજરાતી" },
];

export default function LanguageSelector({ value, onChange, disabled }) {
  return (
    <div className="language-selector">
      <label htmlFor="language-select" className="language-label">
        Input Language
      </label>
      <div className="select-wrapper">
        <select
          id="language-select"
          className="language-select"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          aria-label="Select source language"
        >
          {LANGUAGES.map((lang) => (
            <option key={lang.code} value={lang.code}>
              {lang.flag} {lang.label} — {lang.native}
            </option>
          ))}
        </select>
        <span className="select-arrow">▾</span>
      </div>
      <p className="language-hint">Select the language you will speak</p>
    </div>
  );
}
