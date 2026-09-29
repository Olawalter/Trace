import { LIFECYCLE_WORDS, RESULT_WORDS, STATUS_WORDS, AVAILABILITY_WORDS, words } from
  "@/lib/formatting/present";

/**
 * One state, one chip. The tone says what kind of state it is; the word says
 * which. Nothing here invents a confidence or a percentage.
 *
 * The warm tone is spent only where something was DECIDED: a verified protocol,
 * a satisfied requirement. Where a protocol has got to in its life is not a
 * verdict -- a finalized protocol may have been finalized as not verified -- so
 * lifecycle chips stay neutral. Spending the accent on both would make the
 * common case colourful and leave the finding with nothing to say.
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
  CANCELLED: "chip-bad",
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

// a source that could not be read is a fact about the fetch, not a failed
// requirement, so it is flagged rather than condemned
export const AvailabilityChip = ({ availability }: { availability: string }) => (
  <span className={`chip ${availability === "READ" ? "" : "chip-open"}`}>
    {words(AVAILABILITY_WORDS, availability)}
  </span>
);
