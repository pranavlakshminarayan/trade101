// Theme handling.
//
// Three states, not two: 'dark', 'light', and 'system' — which follows the OS
// and is the default. A two-state toggle silently overrides someone's OS
// preference the first time they click it, which is the wrong default for an
// app people leave open all day.

const KEY = 'trade101.theme'
export const THEMES = ['system', 'light', 'dark']

export function getTheme() {
  try {
    const v = localStorage.getItem(KEY)
    return THEMES.includes(v) ? v : 'system'
  } catch {
    return 'system' // private mode / blocked storage — follow the OS
  }
}

export function applyTheme(theme) {
  const root = document.documentElement
  if (theme === 'system') root.removeAttribute('data-theme')
  else root.setAttribute('data-theme', theme)
  try {
    localStorage.setItem(KEY, theme)
  } catch {
    /* the theme still applies for this session */
  }
}

export function cycleTheme(current) {
  return THEMES[(THEMES.indexOf(current) + 1) % THEMES.length]
}

export const THEME_LABEL = { system: '◐ System', light: '☀ Light', dark: '☾ Dark' }
