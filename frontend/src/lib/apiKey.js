// BYOK (bring-your-own-key), added 2026-09-17 — replaces the old shared
// TRADE101_ACCESS_TOKEN link model (lib/access.js, now removed). Each visitor
// pastes their OWN Anthropic API key once; it's stored ONLY in their own
// browser (localStorage — persists permanently across visits/restarts, never
// sent anywhere except as the X-Anthropic-Key header on /analyze and /ask,
// and never logged or echoed back by the backend). This means an open,
// shared link carries zero cost risk to the app owner — every visitor's AI
// usage is billed to their own Anthropic account, never Pranav's.
//
// The key IS the credential — there's no separate password. Also stores an
// optional display name, purely cosmetic (personalizes the Welcome greeting).
const KEY_STORAGE = 'tradecraft_anthropic_key'
const NAME_STORAGE = 'tradecraft_user_name'

export function getApiKey() {
  try {
    return localStorage.getItem(KEY_STORAGE) || ''
  } catch {
    return ''
  }
}

export function setApiKey(key) {
  try {
    localStorage.setItem(KEY_STORAGE, (key || '').trim())
  } catch {
    // localStorage unavailable (private mode, etc.) — the key just won't
    // persist across reloads; the gate will ask again next time.
  }
}

export function clearApiKey() {
  try {
    localStorage.removeItem(KEY_STORAGE)
  } catch { /* ignore */ }
}

export function getUserName() {
  try {
    return localStorage.getItem(NAME_STORAGE) || ''
  } catch {
    return ''
  }
}

export function setUserName(name) {
  try {
    localStorage.setItem(NAME_STORAGE, (name || '').trim())
  } catch { /* ignore */ }
}
