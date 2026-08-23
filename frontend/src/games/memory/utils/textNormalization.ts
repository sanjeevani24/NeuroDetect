/**
 * Deterministic text normalization. Mirrors the backend's normalization in
 * app/games/memory/features.py::_normalize_text so that any client-side
 * preview/validation matches what the server will ultimately score.
 * Not used for scoring — the backend is the source of truth for feature
 * calculation — but useful for immediate UI feedback (e.g. "already typed
 * that item").
 *
 * Steps: lowercase -> trim -> collapse whitespace -> strip harmless
 * punctuation. No LLM, no fuzzy matching.
 */
export function normalizeText(raw: string): string {
  return raw
    .trim()
    .toLowerCase()
    .replace(/[!.,;:'"?]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}
