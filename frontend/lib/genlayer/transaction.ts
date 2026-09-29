/**
 * Following a write through GenLayer, and saying only what has been seen.
 *
 * TRACE depends on the difference between "submitted", "accepted" and
 * "finalized", so this never collapses them into loading/success/error. A step
 * is marked as reached when a status read showed it, and a step that went past
 * between two reads says that rather than pretending it was watched.
 *
 * Nothing here is a timer dressed as progress: no percentages, and no state
 * that the chain did not report.
 */
import { txLink, type AppConfig } from "@/lib/config/env";
import { refusalSentence, walletFailure, type FailureKind } from "@/lib/genlayer/errors";
import type { Call } from "@/lib/genlayer/contract";
import type { Client } from "@/lib/genlayer/client";

export const STEPS = [
  "WALLET_CONFIRMATION",
  "SUBMITTED",
  "PENDING",
  "LEADER_PROPOSED",
  "VALIDATING",
  "ACCEPTED",
  "APPEAL_WINDOW",
  "FINALIZED",
] as const;

export type Step = (typeof STEPS)[number];
export type StepState = "todo" | "current" | "observed" | "passed" | "failed";

export type TxState = {
  phase: "READY" | "RUNNING" | "DONE" | "FAILED";
  /** How many steps have definitely happened. */
  happened: number;
  /** Which steps a status read actually showed. */
  observed: Step[];
  hash?: string;
  /** Every GenLayer status this console read, in the order it read them. */
  statuses: string[];
  protocolStatus?: string;
  failure?: FailureKind;
  message?: string;
  link?: string;
};

export const initialTx: TxState = { phase: "READY", happened: 0, observed: [], statuses: [] };

/** GenLayer statuses that mean the write took effect. */
const ACCEPTED = new Set(["ACCEPTED", "FINALIZED"]);
/** Statuses that mean this round decided nothing, so nothing was written. */
const UNDECIDED = new Set(["UNDETERMINED", "LEADER_TIMEOUT", "VALIDATORS_TIMEOUT", "CANCELED"]);

const STEP_OF_STATUS: Record<string, Step> = {
  PENDING: "PENDING",
  QUEUED: "PENDING",
  ACTIVATED: "PENDING",
  PROPOSING: "LEADER_PROPOSED",
  COMMITTING: "VALIDATING",
  REVEALING: "VALIDATING",
  ACCEPTED: "ACCEPTED",
  FINALIZED: "FINALIZED",
};

export const isAccepted = (status?: string) => !!status && ACCEPTED.has(status);
export const isUndecided = (status?: string) => !!status && UNDECIDED.has(status);

/** The rungs to draw, and what is known about each one. */
export function rungsFor(state: TxState): { step: Step; state: StepState }[] {
  return STEPS.map((step, index) => {
    if (state.failure && index === state.happened) return { step, state: "failed" as StepState };
    if (index < state.happened) {
      return {
        step,
        state: state.observed.includes(step) ? ("observed" as StepState) : ("passed" as StepState),
      };
    }
    if (index === state.happened && state.phase === "RUNNING") {
      return { step, state: "current" as StepState };
    }
    return { step, state: "todo" as StepState };
  });
}

type Receipt = {
  statusName?: string;
  consensusData?: { leaderReceipt?: Array<{ executionResult?: string; result?: unknown }> };
  consensus_data?: { leader_receipt?: Array<{ execution_result?: string; result?: unknown }> };
};

/**
 * The contract's own refusal, decoded from the leader's receipt.
 *
 * A refusal usually arrives as an ERROR execution. Funding is the exception: it
 * is the only payable write, and GenLayer credits a payable transaction's value
 * before the call runs, so refusing by raising would keep GEN nobody meant to
 * send. It refuses by returning "[REFUNDED] <reason>" instead -- a transaction
 * that succeeded, having sent the value straight back -- and that must be shown
 * as the refusal it is.
 */
export function refusalOf(tx: Receipt): { message: string; kind: FailureKind } | null {
  const leaders = tx.consensus_data?.leader_receipt ?? tx.consensusData?.leaderReceipt ?? [];
  const leader = Array.isArray(leaders) ? leaders[0] : undefined;
  const execution =
    (leader as { execution_result?: string })?.execution_result ??
    (leader as { executionResult?: string })?.executionResult;
  const text = decodePayload((leader as { result?: { payload?: unknown } })?.result?.payload);
  if (!execution || execution === "SUCCESS") {
    const refunded = /\[REFUNDED\]\s*(.*)/.exec(text);
    if (!refunded) return null;
    const reason = refusalSentence(refunded[1].trim()) || "The deposit was not accepted.";
    return { message: `${reason} The GEN was sent back.`, kind: "CONTRACT_REFUSED" };
  }
  return {
    message: refusalSentence(text) || "The contract refused this transaction.",
    kind: "CONTRACT_REFUSED",
  };
}

function decodePayload(payload: unknown): string {
  let text = typeof payload === "string" ? payload : "";
  try {
    if (text && /^[A-Za-z0-9+/=]+$/.test(text)) text = atob(text);
  } catch {
    /* the payload was not base64; use it as it came */
  }
  return text.replace(/[^\x20-\x7e]+/g, " ").trim();
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export type RunOptions = {
  config: AppConfig;
  client: Client;
  call: Call;
  /** Resolves true once the contract's own views show the write. */
  reconciled: () => Promise<boolean>;
  /** Called the moment the contract shows it, before finality is waited for. */
  onRecorded?: () => void;
  onUpdate: (state: TxState) => void;
  poller?: Client;
  pollMs?: number;
};

/**
 * Send one write and follow it. The returned state is whatever was true when
 * this stopped watching -- it never claims more.
 */
export async function runWrite(options: RunOptions): Promise<TxState> {
  const { config, client, call, onUpdate } = options;
  const poller = options.poller ?? client;
  const pollMs = options.pollMs ?? 4000;

  let state: TxState = { ...initialTx, phase: "RUNNING" };
  const set = (patch: Partial<TxState>) => {
    state = { ...state, ...patch };
    onUpdate(state);
    return state;
  };
  const fail = (message: string, failure: FailureKind) =>
    set({ phase: "FAILED", message, failure });

  const see = (status?: string) => {
    if (!status) return;
    if (state.statuses[state.statuses.length - 1] !== status) {
      state.statuses = [...state.statuses, status];
    }
    state.protocolStatus = status;
    const step = STEP_OF_STATUS[status];
    if (step && !state.observed.includes(step)) {
      state.observed = [...state.observed, step];
      const index = STEPS.indexOf(step);
      if (index + 1 > state.happened) state.happened = index + 1;
    }
    onUpdate({ ...state });
  };

  set({ happened: 0 });
  let hash: string;
  try {
    hash = (await client.writeContract({
      address: config.contractAddress,
      functionName: call.functionName,
      args: call.args,
      value: call.value,
    } as never)) as unknown as string;
  } catch (err) {
    const failure = walletFailure(err);
    return fail(failure.message, failure.kind);
  }

  set({
    happened: 1,
    observed: ["WALLET_CONFIRMATION"],
    hash,
    link: txLink(config, hash),
  });

  let tx: Receipt & { statusName?: string };
  try {
    tx = (await poller.getTransaction({ hash: hash as never })) as Receipt;
  } catch {
    return fail(
      "The wallet returned a hash, but GenLayer has no record of the transaction.",
      "TRANSACTION_FAILED",
    );
  }
  set({ happened: 2, observed: [...state.observed, "SUBMITTED"] });
  see(tx.statusName);

  const started = Date.now();
  while (!isAccepted(tx.statusName)) {
    if (isUndecided(tx.statusName)) {
      return fail(
        "The validators did not reach a decision on this transaction, so it changed nothing. " +
          "It can be sent again.",
        "NO_CONSENSUS",
      );
    }
    if (Date.now() - started > 20 * 60_000) {
      return fail(
        "This is taking longer than twenty minutes. The transaction may still complete; " +
          "reload the page later.",
        "TIMEOUT",
      );
    }
    await sleep(pollMs + 2000);
    try {
      tx = (await poller.getTransaction({ hash: hash as never })) as Receipt;
      see(tx.statusName);
    } catch {
      /* a transient read failure: keep polling */
    }
  }

  const refusal = refusalOf(tx);
  if (refusal) return fail(refusal.message, refusal.kind);

  let updated = false;
  for (let i = 0; i < 40 && !updated; i++) {
    try {
      updated = await options.reconciled();
    } catch {
      updated = false;
    }
    if (!updated) await sleep(pollMs);
  }
  if (!updated) {
    return fail(
      "The transaction was accepted, but the contract's state has not caught up yet. " +
        "Reload in a minute.",
      "STATE_NOT_CAUGHT_UP",
    );
  }
  set({ happened: 6, observed: [...state.observed, "ACCEPTED"] });
  options.onRecorded?.();

  for (let i = 0; i < 90 && state.protocolStatus !== "FINALIZED"; i++) {
    await sleep(10_000);
    try {
      const again = (await poller.getTransaction({ hash: hash as never })) as Receipt;
      see(again.statusName);
    } catch {
      /* keep the last status seen */
    }
  }
  if (state.protocolStatus === "FINALIZED") {
    return set({ phase: "DONE", happened: 8, observed: [...state.observed, "FINALIZED"] });
  }
  return set({ phase: "DONE" });
}
