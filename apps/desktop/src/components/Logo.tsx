/** UnionPDF mark: two overlapping sheets joined by a "U" — original artwork for this project. */
export function Logo({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
      <defs>
        <linearGradient id="upg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#0f766e" />
          <stop offset="1" stopColor="#14b8a6" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="60" height="60" rx="14" fill="url(#upg)" />
      <path d="M18 14h18l10 10v26a4 4 0 0 1-4 4H18a4 4 0 0 1-4-4V18a4 4 0 0 1 4-4z" fill="#ffffff" opacity="0.95" />
      <path d="M36 14v8a2 2 0 0 0 2 2h8" fill="#99f6e4" />
      <path d="M23 28v10a7 7 0 0 0 14 0V28" fill="none" stroke="#0f766e" strokeWidth="5" strokeLinecap="round" />
    </svg>
  );
}
