// Pre-share fix (frontend half): if the backend has TRADE101_ACCESS_TOKEN set,
// /analyze and /ask require an X-Access-Token header or they 401. Rather than
// build a login form, the owner shares a link with ?token=... once; the first
// visit stores it locally and strips it from the visible URL, so every link
// after that (including a shared #TICKER link) keeps working silently.
const KEY = 'tradecraft_access_token'

export function captureTokenFromUrl() {
  try {
    const url = new URL(window.location.href)
    const token = url.searchParams.get('token')
    if (!token) return
    localStorage.setItem(KEY, token)
    url.searchParams.delete('token')
    window.history.replaceState(window.history.state, '', url.pathname + url.search + url.hash)
  } catch {
    // localStorage unavailable (private mode, etc.) — the app still works,
    // just without a saved token; the owner can retry the token link.
  }
}

export function getAccessToken() {
  try {
    return localStorage.getItem(KEY) || ''
  } catch {
    return ''
  }
}
