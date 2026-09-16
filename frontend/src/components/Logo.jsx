// Trade Craft mark — a T/C monogram: a bold structural T ("Trade") with a
// teal ribbon wrapping its right side into a C ("Craft"), plus a copper
// accent node where they meet — echoing the brand brief's "information
// streams converging into understanding." Not finance iconography (no
// candlesticks/arrows/$/bulls/bears/coins).
//
// Brand-spec colors are navy/teal/copper on an off-white ground. This app
// keeps its dark-navy theme, so the T is rendered in `--ink` (the theme's
// near-white) rather than navy, which would vanish on a dark background —
// teal and copper are used true to spec. Bold, simplified geometry (thick
// strokes, a pointed ribbon-tail stem) over a literal reproduction, so the
// T reads clearly even at the 26px header size.
export default function Logo({ size = 26 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
      {/* teal ribbon — wraps the T's right side into an open C */}
      <path
        d="M42 9 C 59 11, 61 37, 48 47 C 40 53, 30 54, 23 48"
        fill="none" stroke="var(--teal)" strokeWidth="11" strokeLinecap="round"
      />

      {/* copper accent — a small node marking where the streams meet,
          the third brand color, tucked into the crook of the T/ribbon */}
      <path
        d="M49 13 C 56 15, 57 23, 51 26 C 47 28, 43 25, 43 20 C 43 15, 45 12, 49 13 Z"
        fill="#D3A464"
      />

      {/* the T — bold crossbar + a pointed ribbon-tail stem, solid ink so
          it stays crisp and legible at any size */}
      <rect x="6" y="6" width="34" height="13" rx="5" fill="var(--ink)" />
      <path d="M16 6 L30 6 L30 44 L23 53 L16 44 Z" fill="var(--ink)" />
    </svg>
  )
}
