// Shared icon set — SVG replacements for the emoji glyphs the app used to
// render directly (🔍 📎 ⚖️ ★ 🕘 ✚ ✦ ▲ ▼ ■ ✕ 🧪). Same meanings, same
// placement — emoji just render inconsistently across OS/fonts and can't be
// recolored to match the accent system, so every glyph below is a 1:1 swap
// for what was already there, not a new icon language.
//
// All icons: 16x16 viewBox, stroke/fill via currentColor so they inherit
// whatever text color the surrounding button/span already sets.

const base = { width: 16, height: 16, viewBox: '0 0 16 16', 'aria-hidden': 'true' }

export function SearchIcon(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="7" cy="7" r="5" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <line x1="11" y1="11" x2="15" y2="15" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  )
}

export function PaperclipIcon(props) {
  return (
    <svg {...base} {...props}>
      <path d="M10.5 4.5 5.8 9.2a2 2 0 0 0 2.83 2.83l4.6-4.6a3.2 3.2 0 0 0-4.53-4.53L4.1 7.6a4.4 4.4 0 0 0 6.22 6.22"
            fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function ScaleIcon(props) {
  return (
    <svg {...base} {...props}>
      <line x1="8" y1="2" x2="8" y2="13" stroke="currentColor" strokeWidth="1.3" />
      <line x1="2.5" y1="4" x2="13.5" y2="4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <path d="M2.5 4 0.8 8a2 2 0 0 0 3.4 0z" fill="none" stroke="currentColor" strokeWidth="1.1" strokeLinejoin="round" />
      <path d="M13.5 4 11.8 8a2 2 0 0 0 3.4 0z" fill="none" stroke="currentColor" strokeWidth="1.1" strokeLinejoin="round" />
      <line x1="5.5" y1="14" x2="10.5" y2="14" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  )
}

export function StarIcon({ filled, ...props }) {
  const pts = '8,1.3 9.8,5.4 14.2,5.9 10.9,8.9 11.8,13.3 8,11 4.2,13.3 5.1,8.9 1.8,5.9 6.2,5.4'
  return (
    <svg {...base} {...props}>
      <polygon points={pts} fill={filled ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />
    </svg>
  )
}

export function ClockIcon(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="8" cy="8.5" r="5.7" fill="none" stroke="currentColor" strokeWidth="1.3" />
      <path d="M8 5.3v3.4l2.4 1.4" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
      <line x1="6" y1="1.3" x2="10" y2="1.3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  )
}

export function PlusIcon(props) {
  return (
    <svg {...base} {...props}>
      <line x1="8" y1="3" x2="8" y2="13" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <line x1="3" y1="8" x2="13" y2="8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  )
}

export function FlaskIcon(props) {
  return (
    <svg {...base} {...props}>
      <path d="M6.3 1.8h3.4M6.8 2v3.8L3.6 12a1.4 1.4 0 0 0 1.25 2h6.3a1.4 1.4 0 0 0 1.25-2L9.2 5.8V2"
            fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
      <line x1="4.8" y1="9.3" x2="11.2" y2="9.3" stroke="currentColor" strokeWidth="1.1" />
    </svg>
  )
}

// The "AI-generated" sparkle — used to flag inference/interpretive content
// (distinct from the deterministic-feed icons above).
export function SparkleIcon(props) {
  return (
    <svg {...base} {...props}>
      <path d="M8 1.5c.4 2.6 1.1 4.1 2.2 5.3 1.2 1.1 2.7 1.8 5.3 2.2-2.6.4-4.1 1.1-5.3 2.2-1.1 1.2-1.8 2.7-2.2 5.3-.4-2.6-1.1-4.1-2.2-5.3C4.6 10 3.1 9.3.5 8.9c2.6-.4 4.1-1.1 5.3-2.2C6.9 5.6 7.6 4.1 8 1.5"
            fill="currentColor" />
    </svg>
  )
}

export function ArrowIcon({ direction = 'flat', ...props }) {
  if (direction === 'flat') {
    return (
      <svg {...base} {...props}>
        <line x1="3" y1="8" x2="13" y2="8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    )
  }
  const up = direction === 'up'
  return (
    <svg {...base} {...props}>
      <path d={up ? 'M8 3 12.5 11 3.5 11 Z' : 'M8 13 3.5 5 12.5 5 Z'} fill="currentColor" strokeLinejoin="round" />
    </svg>
  )
}

export function CloseIcon(props) {
  return (
    <svg {...base} {...props}>
      <line x1="4" y1="4" x2="12" y2="12" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <line x1="12" y1="4" x2="4" y2="12" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  )
}

export function BookIcon(props) {
  return (
    <svg {...base} {...props}>
      <path d="M2 3.2c0-.66.54-1.2 1.2-1.2H8v11.6H3.2c-.66 0-1.2.54-1.2 1.2z"
            fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />
      <path d="M14 3.2c0-.66-.54-1.2-1.2-1.2H8v11.6h4.8c.66 0 1.2.54 1.2 1.2z"
            fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />
    </svg>
  )
}

export function ChevronIcon({ open, ...props }) {
  return (
    <svg {...base} {...props} style={{ transform: open ? 'rotate(90deg)' : 'none', transition: 'transform .12s ease', ...props.style }}>
      <path d="M6 3.5 10.5 8 6 12.5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
