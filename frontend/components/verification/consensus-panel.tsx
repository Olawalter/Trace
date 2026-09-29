"use client";

import type { Verification } from "@/lib/genlayer/contract";
import { formatTime, shortDigest } from "@/lib/formatting/present";

/**
 * How this result was reached, using only what GenLayer actually provides.
 *
 * There are no validator names here, no vote counts and no percentages: the
 * protocol decides consensus, and a console that drew a pie chart of it would
 * be drawing a fiction. What can honestly be shown is the shape of the process
 * and the things the round itself recorded.
 */
export function ConsensusPanel({ verification }: { verification: Verification }) {
  const readable = verification.evidence.filter((e) => e.availability === "READ").length;

  const stages = [
    {
      title: "Leader proposal",
      detail:
        `A leader fetched ${verification.evidence.length} source` +
        `${verification.evidence.length === 1 ? "" : "s"} and answered ` +
        `${verification.findings.length} requirement` +
        `${verification.findings.length === 1 ? "" : "s"} against them.`,
    },
    {
      title: "Independent validation",
      detail:
        "Every validator fetched the same sources itself and answered the same requirements " +
        "itself. None of them inspected the leader's answer to decide whether to agree.",
    },
    {
      title: "Equivalence principle",
      detail:
        "The answers, the status after the independent-source floor, the derived result and what " +
        "each node found at each address were compared. The reasoning was not: two readers never " +
        "write the same sentence.",
    },
    {
      title: "Optimistic democracy",
      detail:
        "GenLayer decided whether the proposal was accepted. This contract records nothing when " +
        "a round reaches no majority.",
    },
    {
      title: "Recorded",
      detail:
        `Written at ${formatTime(verification.verified_at)} against the protocol frozen as ` +
        `${shortDigest(verification.fingerprint)}, under ${verification.rules}.`,
    },
  ];

  return (
    <div className="grid gap-4">
      <ol className="card divide-y divide-[var(--border)]">
        {stages.map((stage, index) => (
          <li key={stage.title} className="grid grid-cols-[1.75rem_minmax(0,1fr)] gap-3 p-4">
            <span aria-hidden="true"
                  className="mono flex h-6 w-6 items-center justify-center rounded-sm border
                             border-[var(--border)] text-[11px] text-[var(--muted)]">
              {String(index + 1).padStart(2, "0")}
            </span>
            <div>
              <p className="text-sm font-semibold">{stage.title}</p>
              <p className="text-sm text-[var(--muted)]">{stage.detail}</p>
            </div>
          </li>
        ))}
      </ol>

      <div className="card p-4">
        <h3 className="label">What the panel had in front of it</h3>
        <p className="mt-2 text-sm text-[var(--muted)]">
          {readable} of {verification.evidence.length} registered source
          {verification.evidence.length === 1 ? " was" : "s were"} readable when this round ran.
          A source that could not be read is recorded as such and is never evidence that a
          requirement was unmet.
        </p>
        {verification.deviation ? (
          <p className="mt-2 text-sm text-[var(--warning)]">
            The evidence did not meet the frozen evidence policy: {verification.deviation}. That is
            decided in code, and it outranks everything the panel concluded.
          </p>
        ) : null}
      </div>
    </div>
  );
}
