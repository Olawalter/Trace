/**
 * Every word and number the console shows, in one place.
 *
 * The contract speaks in constants and atto; a person reads sentences and GEN.
 * Nothing renders a raw protocol constant, and no screen shows an amount in
 * atto -- identifiers and digests appear only where somebody is checking the
 * record against the chain.
 */

export const LIFECYCLE_WORDS: Record<string, string> = {
  DRAFT: "Draft",
  REGISTERED: "Ready to freeze",
  ACTIVE: "Open for evidence",
  EVIDENCE_SUBMITTED: "Evidence registered",
  VERIFICATION_PENDING: "Verifying",
  VERDICT_PROPOSED: "Result proposed",
  ACCEPTED: "Result accepted",
  FINALIZED: "Finalized",
  CANCELLED: "Withdrawn",
};

export const RESULT_WORDS: Record<string, string> = {
  VERIFIED: "Verified",
  PARTIALLY_VERIFIED: "Partially verified",
  NOT_VERIFIED: "Not verified",
  INCONCLUSIVE: "Inconclusive",
  PROTOCOL_DEVIATION: "Protocol deviation",
  NONE: "Not verified yet",
};

export const STATUS_WORDS: Record<string, string> = {
  SATISFIED: "Satisfied",
  UNSATISFIED: "Unsatisfied",
  UNCERTAIN: "Uncertain",
};

export const AVAILABILITY_WORDS: Record<string, string> = {
  READ: "Read by the panel",
  MISSING: "Not there",
  UNREADABLE: "Could not be read",
};

export const SOURCE_TYPE_WORDS: Record<string, string> = {
  PUBLICATION: "Publication",
  REGISTRY: "Registry",
  REPOSITORY: "Repository",
  REPORT: "Report",
  STATEMENT: "Statement",
  OTHER: "Other",
};

export const ACTION_WORDS: Record<string, string> = {
  REFUND: "everything returns to where it came from",
  RELEASE: "the reward goes to the submitter",
  SPLIT: "the reward is split evenly",
};

export const STEP_WORDS: Record<string, string> = {
  WALLET_CONFIRMATION: "Wallet confirmation",
  SUBMITTED: "Transaction submitted",
  PENDING: "Queued on GenLayer",
  LEADER_PROPOSED: "Leader execution",
  VALIDATING: "Independent validation",
  ACCEPTED: "Decision accepted",
  APPEAL_WINDOW: "Appeal window",
  FINALIZED: "Finalized",
};

export const words = (table: Record<string, string>, key: string) =>
  table[key] ?? key.toLowerCase().replace(/_/g, " ");

export const protocolLabel = (id: string) => `Protocol ${id.replace(/^P/, "#")}`;

/** GEN, written the way a person would: never atto, never scientific notation. */
export function formatGen(atto: string | bigint): string {
  const value = typeof atto === "bigint" ? atto : BigInt(atto || "0");
  if (value === 0n) return "0 GEN";
  const whole = value / 10n ** 18n;
  const fraction = (value % 10n ** 18n).toString().padStart(18, "0").replace(/0+$/, "");
  return `${whole}${fraction ? `.${fraction.slice(0, 6)}` : ""} GEN`;
}

export const toAtto = (gen: string): bigint | null => {
  const text = gen.trim();
  if (!/^\d+(\.\d{1,18})?$/.test(text)) return null;
  const [whole, fraction = ""] = text.split(".");
  return BigInt(whole) * 10n ** 18n + BigInt(fraction.padEnd(18, "0"));
};

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
                "September", "October", "November", "December"];

export function formatTime(seconds: number): string {
  if (!seconds) return "not set";
  const at = new Date(seconds * 1000);
  const hours = String(at.getUTCHours()).padStart(2, "0");
  const minutes = String(at.getUTCMinutes()).padStart(2, "0");
  return `${at.getUTCDate()} ${MONTHS[at.getUTCMonth()]} ${at.getUTCFullYear()}, ${hours}:${minutes} UTC`;
}

export function relativeTime(seconds: number, now: number): string {
  if (!seconds) return "not set";
  const delta = seconds - now;
  const ahead = delta > 0;
  const size = Math.abs(delta);
  const [count, unit] =
    size < 90 ? [Math.max(1, Math.round(size)), "second"] :
    size < 5400 ? [Math.round(size / 60), "minute"] :
    size < 172800 ? [Math.round(size / 3600), "hour"] :
    [Math.round(size / 86400), "day"];
  const plural = count === 1 ? "" : "s";
  return ahead ? `in ${count} ${unit}${plural}` : `${count} ${unit}${plural} ago`;
}

export const shortAddress = (address: string) =>
  address && address.length > 12 ? `${address.slice(0, 6)}…${address.slice(-4)}` : address;

export const shortDigest = (digest: string) =>
  digest && digest.length > 20 ? `${digest.slice(0, 16)}…` : digest;

/**
 * A note the contract wrote, put into words. It records amounts in atto because
 * that is what it holds, so a settlement line reads "5000000000000000 to the
 * submitter" unless somebody translates it.
 */
export const humaniseNote = (note: string): string =>
  (note || "").replace(/\b\d{12,}\b/g, (digits) => formatGen(digits));

/** What a protocol's custody says, in a sentence. */
export function custodyWords(p: {
  economic: boolean;
  reward_deposited: string;
  bond_deposited: string;
  reward_required: string;
  bond_required: string;
  paid_creator: string;
  paid_submitter: string;
  settled_at: number;
}): string {
  if (!p.economic) return "No economic consequence is attached to this protocol.";
  const held = BigInt(p.reward_deposited) + BigInt(p.bond_deposited);
  const wanted = BigInt(p.reward_required) + BigInt(p.bond_required);
  // a settled protocol holds nothing BECAUSE it paid out, which is the opposite
  // of a protocol nobody has funded yet, and the two must never read alike
  if (p.settled_at > 0) {
    const paid = BigInt(p.paid_creator) + BigInt(p.paid_submitter);
    return paid === 0n
      ? "This protocol is settled. Nothing was held against it, so nothing moved."
      : `${formatGen(paid.toString())} has been paid out, and the protocol now holds nothing.`;
  }
  if (held === 0n) return `Nothing has been deposited yet, of ${formatGen(wanted.toString())}.`;
  if (held < wanted) {
    return `${formatGen(held.toString())} of ${formatGen(wanted.toString())} has been deposited.`;
  }
  return `${formatGen(held.toString())} is held by the contract.`;
}

/** The headline of a result, without inventing a number. */
export function resultHeadline(
  result: string,
  findings: { requirement_id: string; effective_status: string }[],
  requirements: { requirement_id: string; mandatory: boolean }[],
): string {
  const mandatory = requirements.filter((r) => r.mandatory).map((r) => r.requirement_id);
  const met = findings.filter(
    (f) => mandatory.includes(f.requirement_id) && f.effective_status === "SATISFIED",
  ).length;
  const requirement = mandatory.length === 1 ? "requirement" : "requirements";
  return `${met} of ${mandatory.length} mandatory ${requirement} satisfied`;
}
