/**
 * What went wrong, in words somebody can act on.
 *
 * The contract refuses in its own sentence; this keeps that sentence and only
 * removes the protocol tag it carries for the validators. "Something went
 * wrong" appears nowhere.
 */

export type FailureKind =
  | "WALLET_REJECTED"
  | "WALLET_MISSING"
  | "WRONG_NETWORK"
  | "INSUFFICIENT_FUNDS"
  | "CONTRACT_REFUSED"
  | "NO_CONSENSUS"
  | "TRANSACTION_FAILED"
  | "STATE_NOT_CAUGHT_UP"
  | "TIMEOUT"
  | "READ_FAILED";

const TAGS = ["[EXPECTED]", "[EXTERNAL]", "[TRANSIENT]", "[LLM_ERROR]", "[REFUNDED]"];

export function refusalSentence(text: string): string {
  let out = (text ?? "").trim();
  for (const tag of TAGS) {
    if (out.startsWith(tag)) out = out.slice(tag.length).trim();
  }
  out = readableTimes(out);
  return out.charAt(0).toUpperCase() + out.slice(1);
}

/**
 * The contract measures its windows in seconds since the epoch, because that is
 * what a transaction carries. Nobody reads 1791450000.
 */
function readableTimes(text: string): string {
  return text.replace(/\b\d{10}\b/g, (digits) => {
    const value = Number(digits);
    if (value < 1_600_000_000 || value > 4_000_000_000) return digits;
    return new Date(value * 1000).toISOString().replace("T", " ").replace(/:\d\d\.\d+Z$/, " UTC");
  });
}

export function walletFailure(err: unknown): { message: string; kind: FailureKind } {
  const code = (err as { code?: number })?.code;
  const raw = String((err as { message?: string })?.message ?? err ?? "");
  if (code === 4001 || /user rejected|denied/i.test(raw)) {
    return { message: "You rejected the transaction in your wallet.", kind: "WALLET_REJECTED" };
  }
  if (/insufficient/i.test(raw)) {
    return {
      message: "That account does not have enough GEN for this transaction.",
      kind: "INSUFFICIENT_FUNDS",
    };
  }
  if (/chain|network/i.test(raw)) {
    return {
      message: "Your wallet is on a different network. Switch it to GenLayer StudioNet.",
      kind: "WRONG_NETWORK",
    };
  }
  if (/no provider|not found/i.test(raw)) {
    return { message: "No wallet answered. Connect one and try again.", kind: "WALLET_MISSING" };
  }
  return { message: raw || "The wallet did not complete the request.", kind: "TRANSACTION_FAILED" };
}

/** A read that failed because the thing does not exist, rather than because the endpoint did. */
export function isMissing(err: unknown): boolean {
  const raw = String((err as { message?: string })?.message ?? err ?? "");
  return /there is no protocol|has no evidence|has no round/i.test(raw);
}

export function readFailure(err: unknown): string {
  const raw = String((err as { message?: string })?.message ?? err ?? "");
  if (isMissing(err)) return refusalSentence(raw);
  if (/fetch|network|timeout|econn/i.test(raw)) {
    return "The GenLayer endpoint could not be reached.";
  }
  return refusalSentence(raw) || "The contract could not be read.";
}
