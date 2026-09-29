"use client";

import Link from "next/link";

import { configResult } from "@/lib/config/env";
import { useActivity, useNow } from "@/lib/genlayer/hooks";
import {
  formatTime,
  humaniseNote,
  LIFECYCLE_WORDS,
  protocolLabel,
  relativeTime,
  words,
} from "@/lib/formatting/present";
import { ConfigProblem } from "@/components/ui/config-problem";

/**
 * Every state change this contract has recorded, newest first.
 *
 * This is the contract's own transition log, not an off-chain index: if it is
 * here, the contract wrote it while something was happening.
 */
export default function Activity() {
  const activity = useActivity();
  const now = useNow();
  if (!configResult.ok) return <ConfigProblem />;

  const rows = [...(activity.data?.items ?? [])].reverse();

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] gap-6">
      <header className="grid gap-2">
        <p className="label">Activity</p>
        <h1 className="text-2xl">Everything this contract has recorded</h1>
        <p className="max-w-2xl text-sm text-[var(--muted)]">
          The contract's own log of state changes. Nothing is indexed elsewhere, and nothing is
          inferred: each line was written by the transaction that caused it.
        </p>
      </header>

      {activity.error ? (
        <p role="alert" className="card border-[var(--error)] p-4 text-sm">
          The contract could not be read: {activity.error}{" "}
          <button type="button" className="underline" onClick={activity.reload}>Try again</button>
        </p>
      ) : rows.length === 0 ? (
        <p className="card p-4 text-sm text-[var(--muted)]">Nothing has happened yet.</p>
      ) : (
        <ol className="card divide-y divide-[var(--border)]">
          {rows.map((row, index) => (
            <li key={`${row.protocol_id}-${row.at}-${index}`} className="grid gap-1 p-4">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <Link href={`/protocols/${row.protocol_id}`}
                      className="mono text-xs text-[var(--muted)] underline decoration-dotted
                                 underline-offset-2">
                  {protocolLabel(row.protocol_id)}
                </Link>
                <span className="text-xs text-[var(--muted)]">
                  {formatTime(row.at)} ({relativeTime(row.at, now)})
                </span>
              </div>
              <p className="text-sm">
                {row.from ? `${words(LIFECYCLE_WORDS, row.from)} to ` : ""}
                {words(LIFECYCLE_WORDS, row.to)}
              </p>
              {row.note ? (
                <p className="text-xs text-[var(--muted)]">{humaniseNote(row.note)}</p>
              ) : null}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
