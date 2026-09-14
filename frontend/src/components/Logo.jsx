// Trade101 mark — an isometric "data cube": a bar-chart motif on the right face
// (teal, ascending) and a green up-candlestick on the left face, per the brand
// spec. Pure SVG, scales cleanly. `size` sets both dimensions.
export default function Logo({ size = 26 }) {
  const uid = 'lg' // static ids are fine — one mark instance styled per use
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <defs>
        <clipPath id={uid + '-r'}>
          <polygon points="29.5,10.25 16,18 16,31.5 29.5,23.75" />
        </clipPath>
        <clipPath id={uid + '-l'}>
          <polygon points="2.5,10.25 16,18 16,31.5 2.5,23.75" />
        </clipPath>
      </defs>

      {/* three cube faces */}
      <polygon points="16,2.5 29.5,10.25 16,18 2.5,10.25" fill="#4A8CA0" />
      <polygon points="2.5,10.25 16,18 16,31.5 2.5,23.75" fill="#20323d" />
      <polygon points="29.5,10.25 16,18 16,31.5 29.5,23.75" fill="#2b4e5c" />

      {/* right face — ascending bar chart (teal) */}
      <g clipPath={`url(#${uid}-r)`} fill="#34A9BE">
        <rect x="18.5" y="24.5" width="2.2" height="5" />
        <rect x="21.7" y="22.4" width="2.2" height="7.5" />
        <rect x="24.9" y="20.2" width="2.2" height="9.8" />
      </g>

      {/* left face — green up-candlestick */}
      <g clipPath={`url(#${uid}-l)`}>
        <line x1="8.6" y1="14.5" x2="8.6" y2="27" stroke="#00D68F" strokeWidth="1" />
        <rect x="7" y="17.5" width="3.2" height="6.5" fill="#00D68F" />
      </g>

      {/* top-edge highlight */}
      <polygon points="16,2.5 29.5,10.25 16,18 2.5,10.25" fill="none" stroke="#5fd0a8" strokeOpacity=".35" strokeWidth="0.6" />
    </svg>
  )
}
