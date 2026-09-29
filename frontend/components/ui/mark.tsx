/**
 * The TRACE mark: three requirements set as rules, and a seal on the one the
 * evidence settled. Blush ground, sienna ink -- the same warm pair the console
 * rations everywhere else, so the mark belongs to the system rather than
 * sitting on top of it.
 */
export function Mark({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} role="img" aria-label="TRACE"
         xmlns="http://www.w3.org/2000/svg">
      <rect width="24" height="24" rx="7" fill="#fbe1d1" />
      <g stroke="#5d2a1a" strokeWidth="1.7" strokeLinecap="round">
        <path d="M5.5 8h13" />
        <path d="M5.5 12h8.5" />
        <path d="M5.5 16h5" />
      </g>
      <circle cx="17" cy="12" r="2.6" fill="#5d2a1a" />
    </svg>
  );
}
