// The kit's mark: a search lens over a vector point, with two neighbouring points.
// Line style, coloured by CSS (.logo-lens / .logo-dot), so it follows light and dark mode.

export default function Logo({ size = 32, className = '' }: { size?: number; className?: string }) {
  return (
    <svg
      className={`logo-mark ${className}`}
      width={size}
      height={size}
      viewBox="0 0 32 32"
      aria-hidden="true"
      focusable="false"
    >
      <circle className="logo-lens" cx="13.5" cy="13.5" r="8" strokeWidth="2.75" />
      <path className="logo-lens" d="M19.5 19.5 27 27" strokeWidth="3.25" strokeLinecap="round" />
      <circle className="logo-dot" cx="13.5" cy="13.5" r="2.5" />
      <path className="logo-spark" d="M26 2.5l1 2.5 2.5 1-2.5 1-1 2.5-1-2.5-2.5-1 2.5-1z" />
    </svg>
  )
}
