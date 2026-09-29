"use client";

import { configResult } from "@/lib/config/env";
import { STEP_WORDS, words } from "@/lib/formatting/present";
import { rungsFor, type TxState } from "@/lib/genlayer/transaction";

/**
 * What has happened to one transaction, and nothing more.
 *
 * Each rung is drawn from a status this console actually read. A step that went
 * past between two reads says so rather than pretending to have been watched,
 * and a step still running never describes a decision that has not been taken.
 */

const WAITING: Record<string, string> = {
  WALLET_CONFIRMATION: "Confirm the transaction in your wallet.",
  SUBMITTED: "Waiting for GenLayer to acknowledge the transaction.",
  PENDING: "Queued for a leader.",
  LEADER_PROPOSED: "A leader is executing it and proposing a result.",
  VALIDATING: "Validators are fetching the evidence and deciding for themselves.",
  ACCEPTED: "Waiting for a decision, then for the contract's own state to show it.",
  APPEAL_WINDOW: "Accepted. GenLayer's appeal window is open.",
  FINALIZED: "Recorded and final.",
};

export function TxPanel({ state, done, leaderNote }: {
  state: TxState;
  done?: string;
  /** What the leader is actually doing, when the act says more than the default. */
  leaderNote?: string;
}) {
  if (state.phase === "READY") return null;
  const explorer = configResult.ok ? configResult.config.explorer : "";

  return (
    <div className="card p-4" aria-live="polite">
      <ol className="grid gap-1.5 text-sm">
        {rungsFor(state).map(({ step, state: rung }) => (
          <li key={step} className="flex items-baseline gap-2.5">
            <span aria-hidden="true"
                  className={`mono w-4 text-center text-xs ${
                    rung === "failed" ? "text-[var(--error)]"
                    : rung === "observed" ? "text-[var(--signal)]"
                    : rung === "passed" ? "text-[var(--muted)]"
                    : rung === "current" ? "text-[var(--signal)]"
                    : "text-[var(--border)]"}`}>
              {rung === "failed" ? "x" : rung === "observed" || rung === "passed" ? "+"
                : rung === "current" ? ">" : "."}
            </span>
            <span className={rung === "todo" ? "text-[var(--muted)]"
                             : rung === "failed" ? "text-[var(--error)]" : ""}>
              {words(STEP_WORDS, step)}
              <span className="sr-only">
                {rung === "observed" ? ", done"
                  : rung === "passed" ? ", passed between two status reads"
                  : rung === "current" ? ", in progress"
                  : rung === "failed" ? ", failed" : ", not yet"}
              </span>
              {rung === "passed" ? (
                <span className="ml-2 text-xs text-[var(--muted)]" aria-hidden="true">
                  passed between reads
                </span>
              ) : null}
              {rung === "current" ? (
                <span className="ml-2 text-xs text-[var(--muted)]">
                  {step === "VALIDATING" && leaderNote ? leaderNote : WAITING[step]}
                </span>
              ) : null}
            </span>
          </li>
        ))}
      </ol>

      {state.phase === "FAILED" ? (
        <p role="alert" className="mt-3 text-sm text-[var(--error)]">{state.message}</p>
      ) : null}
      {state.phase === "DONE" ? (
        <p className="mt-3 text-sm text-[var(--signal)]">{done ?? "Recorded in the contract."}</p>
      ) : null}

      {state.hash ? (
        <p className="mono mt-3 break-all text-xs text-[var(--muted)]">
          Transaction{" "}
          <a className="underline decoration-dotted underline-offset-2"
             href={`${explorer}/tx/${state.hash}`} target="_blank" rel="noreferrer">
            {state.hash.slice(0, 10)}…{state.hash.slice(-6)}
          </a>
          {state.statuses.length > 0 ? (
            <span className="ml-2">
              GenLayer statuses read: {state.statuses.map((s) => s.toLowerCase()).join(" -> ")}
            </span>
          ) : null}
        </p>
      ) : null}
    </div>
  );
}
