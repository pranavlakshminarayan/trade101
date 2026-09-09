// Placeholder Trade101 mark (real data-cube logo drops in later).
export default function Logo({ size = 26 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 26 26" aria-hidden="true">
      <polygon points="13,1 24,7 24,19 13,25 2,19 2,7" fill="none" stroke="#34A9BE" strokeWidth="1.5" />
      <path d="M13,1 L13,25 M2,7 L24,19 M24,7 L2,19" stroke="#2e5e4e" strokeWidth="1" opacity=".6" />
      <rect x="7" y="10" width="2" height="6" fill="#dfeff2" />
      <rect x="10" y="8" width="2" height="8" fill="#dfeff2" />
      <rect x="13" y="11" width="2" height="5" fill="#00D68F" />
    </svg>
  )
}
