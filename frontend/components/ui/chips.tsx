import { LIFECYCLE_WORDS, RESULT_WORDS, STATUS_WORDS, AVAILABILITY_WORDS, words } from
  "@/lib/formatting/present";

/**
 * One state, one chip. The tone says what kind of state it is; the word says
 * which. Nothing here invents a confidence or a percentage.
 */

const RESULT_TONE: Record<string, string> = {
  VERIFIED: "chip-good",
  PARTIALLY_VERIFIED: "chip-open",
  NOT_VERIFIED: "chip-bad",
  INCONCLUSIVE: "chip-open",
  PROTOCOL_DEVIATION: "chip-bad",
};

const STATUS_TONE: Record<string, string> = {
  SATISFIED: "chip-good",
  UNSATISFIED: "chip-bad",
  UNCERTAIN: "chip-open",
};

const LIFECYCLE_TONE: Record<string, string> = {
  FINALIZED: "chip-good",
  ACCEPTED: "chip-good",
  CANCELLED: "chip-bad",
  VERDICT_PROPOSED: "chip-open",
  VERIFICATION_PENDING: "chip-open",
};

export const ResultChip = ({ result }: { result: string }) =>
  result && result !== "NONE" ? (
    <span className={`chip ${RESULT_TONE[result] ?? ""}`}>{words(RESULT_WORDS, result)}</span>
  ) : null;

export const StatusChip = ({ status }: { status: string }) => (
  <span className={`chip ${STATUS_TONE[status] ?? ""}`}>{words(STATUS_WORDS, status)}</span>
);

export const LifecycleChip = ({ state }: { state: string }) => (
  <span className={`chip ${LIFECYCLE_TONE[state] ?? ""}`}>{words(LIFECYCLE_WORDS, state)}</span>
);

export const AvailabilityChip = ({ availability }: { availability: string }) => (
  <span className={`chip ${availability === "READ" ? "chip-good" : "chip-open"}`}>
    {words(AVAILABILITY_WORDS, availability)}
  </span>
);
