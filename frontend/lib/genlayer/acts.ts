/**
 * What can be done to a protocol right now, and why not, for everything else.
 *
 * This mirrors the contract's own guards, field for field, so the console can
 * offer an act before spending a transaction on it -- and, more usefully, can
 * say in words why an act is unavailable instead of hiding it. Every reason
 * here is the contract's reason.
 */
import type { Protocol } from "@/lib/genlayer/contract";
import { formatGen, formatTime } from "@/lib/formatting/present";

export type ActId =
  | "set_draft"
  | "activate"
  | "fund_reward"
  | "fund_bond"
  | "submit_evidence"
  | "request_verification"
  | "accept"
  | "finalize"
  | "recover"
  | "cancel";

export type Act = {
  id: ActId;
  label: string;
  detail: string;
  /** Empty when the act is available; otherwise the contract's reason. */
  blocked: string;
  /** Who may send it, in words. */
  who: string;
};

const ACCEPTANCE_DELAY = 300;

export function actsFor(
  protocol: Protocol,
  latestVerifiedAt: number | undefined,
  now: number,
  account: string | undefined,
): Act[] {
  const mine = Boolean(account) && account?.toLowerCase() === protocol.creator.toLowerCase();
  const life = protocol.lifecycle;
  const open = life === "ACTIVE" || life === "EVIDENCE_SUBMITTED";
  const economic = protocol.economic;
  const rewardOwing = BigInt(protocol.reward_required) - BigInt(protocol.reward_deposited);
  const bondOwing = BigInt(protocol.bond_required) - BigInt(protocol.bond_deposited);
  const acceptableAt = (latestVerifiedAt ?? 0) + ACCEPTANCE_DELAY;
  const recoverableAt = protocol.deadline + protocol.recovery_window;

  const act = (id: ActId, label: string, detail: string, who: string, blocked: string): Act => ({
    id, label, detail, who, blocked,
  });

  return [
    act("set_draft", "Write the requirements", "Requirements, policies and the deadline. Only " +
        "before the protocol is frozen.", "the creator",
        !mine ? "Only the creator can write the draft."
          : life === "DRAFT" || life === "REGISTERED" ? ""
          : `The protocol is frozen; its requirements cannot change. It is ${label(life)}.`),

    act("activate", "Freeze the protocol", "After this, the requirements, the policies and the " +
        "deadline cannot change -- by anyone.", "the creator",
        !mine ? "Only the creator can freeze the protocol."
          : life === "DRAFT" ? "Write the requirements and the policies first."
          : life === "REGISTERED" ? ""
          : "This protocol is already frozen."),

    act("fund_reward", `Deposit the reward${economic ? ` (${formatGen(rewardOwing.toString())})` : ""}`,
        "The deposit is the transaction's own value, held by the contract until the protocol ends.",
        "the creator",
        !economic ? "This protocol carries no economic consequence."
          : !mine ? "The reward is deposited by the creator."
          : !open ? `Funding happens while the protocol is open for evidence; it is ${label(life)}.`
          : rewardOwing <= 0n ? "The reward is already deposited."
          : ""),

    act("fund_bond", `Post the bond${economic ? ` (${formatGen(bondOwing.toString())})` : ""}`,
        "A bond from whoever answers the protocol. It answers for a protocol the evidence shows " +
        "was not met, and comes back on every other ending.", "whoever submits evidence",
        !economic ? "This protocol carries no economic consequence."
          : mine ? "The bond is posted by the other side, not by the creator."
          : !open ? `Funding happens while the protocol is open for evidence; it is ${label(life)}.`
          : bondOwing <= 0n ? "The bond is already deposited."
          : ""),

    act("submit_evidence", "Register evidence", "An address every validator will fetch for itself " +
        "when the protocol is verified.", "anyone",
        !open ? `Evidence is registered while the protocol is open; it is ${label(life)}.`
          : now > protocol.deadline ? "The deadline for submitting evidence has passed."
          : protocol.evidence_count >= 20 ? "This protocol already holds twenty evidence items."
          : ""),

    act("request_verification", "Verify the protocol", "Ask GenLayer to decide every requirement " +
        "against the registered evidence. Each validator fetches the sources and reads them " +
        "independently.", "anyone",
        life === "ACTIVE" ? "No evidence has been registered yet."
          : life !== "EVIDENCE_SUBMITTED" ? `Verification needs a protocol with evidence; it is ${label(life)}.`
          : protocol.round_count >= 3 ? "This protocol has been verified three times."
          : protocol.last_round_at && now < protocol.last_round_at + 600
            ? `The next verification is possible at ${formatTime(protocol.last_round_at + 600)}.`
          : ""),

    act("accept", "Accept the result", "Make the proposed result the protocol's standing answer, " +
        "once it has stood for the acceptance delay.", "anyone",
        life !== "VERDICT_PROPOSED" ? `There is no proposed result waiting; the protocol is ${label(life)}.`
          : now < acceptableAt ? `This result can be accepted at ${formatTime(acceptableAt)}.`
          : ""),

    act("finalize", "Finalize", "End the protocol and pay what the frozen policy says about the " +
        "result that was accepted.", "anyone",
        life !== "ACCEPTED" ? `A protocol is finalized after its result is accepted; it is ${label(life)}.`
          : ""),

    act("recover", "Recover", "When the deadline and the recovery window have both passed with no " +
        "accepted result, the rule frozen at the start ends the protocol.", "anyone",
        !["ACTIVE", "EVIDENCE_SUBMITTED", "VERDICT_PROPOSED"].includes(life)
          ? `Recovery applies to a protocol that was never finished; it is ${label(life)}.`
          : now < recoverableAt ? `Recovery is possible from ${formatTime(recoverableAt)}.`
          : ""),

    act("cancel", "Withdraw", "Withdraw a protocol nobody has answered. Every deposit goes back.",
        "the creator",
        !mine ? "Only the creator can withdraw a protocol."
          : protocol.evidence_count > 0
            ? "Evidence has been registered; this protocol must be verified or recovered."
          : !["DRAFT", "REGISTERED", "ACTIVE"].includes(life)
            ? `A protocol in ${label(life)} cannot be withdrawn.`
          : ""),
  ];
}

function label(lifecycle: string): string {
  const words: Record<string, string> = {
    DRAFT: "a draft",
    REGISTERED: "ready to freeze",
    ACTIVE: "open for evidence",
    EVIDENCE_SUBMITTED: "carrying evidence",
    VERIFICATION_PENDING: "being verified",
    VERDICT_PROPOSED: "waiting on a proposed result",
    ACCEPTED: "accepted",
    FINALIZED: "finalized",
    CANCELLED: "withdrawn",
  };
  return words[lifecycle] ?? lifecycle.toLowerCase().replace(/_/g, " ");
}
