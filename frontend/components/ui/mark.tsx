/**
 * The TRACE mark: three requirements, and a line drawn under the one that was
 * checked. No cubes, no glow.
 */
export function Mark({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} role="img" aria-label="TRACE"
         xmlns="http://www.w3.org/2000/svg">
      <rect x="0.75" y="0.75" width="22.5" height="22.5" rx="4.5" fill="#171b18"
            stroke="#29302b" strokeWidth="1.5" />
      <path d="M6 8h12M6 12h9M6 16h6" stroke="#9aa39d" strokeWidth="1.6" strokeLinecap="square" />
      <path d="M13.5 16.5l2.2 2.2 4.3-4.6" stroke="#22c55e" strokeWidth="2" fill="none"
            strokeLinecap="square" />
    </svg>
  );
}
