// Trade Craft mark — an upward growth spiral (green→teal gradient ribbon) ending
// in an arrowhead, with an ascending bar chart in the loop and small currency
// nodes along the path. Transparent background so it sits on the dark header.
// `size` sets both dimensions.
export default function Logo({ size = 26 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
      <defs>
        <linearGradient id="tc-rib" x1="6" y1="58" x2="56" y2="8" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#2ecc71" />
          <stop offset="0.55" stopColor="#12b7b0" />
          <stop offset="1" stopColor="#00a8ff" />
        </linearGradient>
        <linearGradient id="tc-rib2" x1="6" y1="58" x2="56" y2="8" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#00a8ff" />
          <stop offset="1" stopColor="#2ecc71" />
        </linearGradient>
      </defs>

      {/* spiral ribbon — a back band and a front band for a wrapped-cylinder feel */}
      <path d="M9 53 C 4 36, 24 26, 33 34 C 41 41, 31 52, 22 48"
            fill="none" stroke="url(#tc-rib2)" strokeWidth="4.4" strokeLinecap="round" opacity="0.55" />
      <path d="M14 50 C 12 38, 30 33, 34 25 C 39 15, 47 14, 52 12"
            fill="none" stroke="url(#tc-rib)" strokeWidth="5.4" strokeLinecap="round" />

      {/* arrowhead top-right */}
      <path d="M45 9 L55 8 L52 19 Z" fill="#2ecc71" />

      {/* ascending bar chart nestled in the top loop */}
      <rect x="28" y="26" width="4.2" height="8" rx="1.2" fill="#00c2d6" />
      <rect x="34" y="21" width="4.2" height="13" rx="1.2" fill="#1f8bd6" />
      <rect x="40" y="15" width="4.2" height="19" rx="1.2" fill="#2ecc71" />

      {/* currency nodes along the spiral */}
      <g fontFamily="'Segoe UI',system-ui,sans-serif" fontWeight="700" textAnchor="middle">
        <circle cx="10" cy="52" r="4.4" fill="#2ecc71" /><text x="10" y="54" fontSize="6" fill="#07351f">$</text>
        <circle cx="24" cy="47" r="4" fill="#0fbfae" /><text x="24" y="49" fontSize="5.4" fill="#062f2b">€</text>
        <circle cx="21" cy="30" r="4" fill="#1f8bd6" /><text x="21" y="32" fontSize="5.4" fill="#04263f">¥</text>
      </g>
    </svg>
  )
}
