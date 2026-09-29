"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { configResult } from "@/lib/config/env";
import { useNow, useProtocols } from "@/lib/genlayer/hooks";
import { custodyWords, formatTime, protocolLabel, relativeTime } from "@/lib/formatting/present";
import { LifecycleChip, ResultChip } from "@/components/ui/chips";
import { ConfigProblem } from "@/components/ui/config-problem";

const FILTERS: Record<string, (lifecycle: string, result: string) => boolean> = {
  All: () => true,
  Open: (lifecycle) => ["ACTIVE", "EVIDENCE_SUBMITTED"].includes(lifecycle),
  Verifying: (lifecycle) => ["VERIFICATION_PENDING", "VERDICT_PROPOSED"].includes(lifecycle),
  Finalized: (lifecycle) => ["ACCEPTED", "FINALIZED"].includes(lifecycle),
  Verified: (_l, result) => result === "VERIFIED",
  "Not verified": (_l, result) => result === "NOT_VERIFIED",
  Inconclusive: (_l, result) => ["INCONCLUSIVE", "PROTOCOL_DEVIATION"].includes(result),
};

export default function Protocols() {
  const protocols = useProtocols();
  const now = useNow();
  const [filter, setFilter] = useState<keyof typeof FILTERS>("All");
  const [query, setQuery] = useState("");

  const rows = useMemo(() => {
    const items = [...(protocols.data?.items ?? [])].reverse();
    const matches = items.filter((p) => FILTERS[filter](p.lifecycle, p.overall_result));
    const needle = query.trim().toLowerCase();
    if (!needle) return matches;
    return matches.filter(
      (p) =>
        p.protocol_id.toLowerCase().includes(needle) ||
        p.title.toLowerCase().includes(needle) ||
        p.subject.toLowerCase().includes(needle) ||
        p.creator.toLowerCase().includes(needle),
    );
  }, [protocols.data, filter, query]);

  if (!configResult.ok) return <ConfigProblem />;

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] gap-6">
      <header className="grid gap-2">
        <p className="label">Protocols</p>
        <h1 className="text-2xl">Protocols on this contract</h1>
        <p className="max-w-2xl text-sm text-[var(--muted)]">
          Read from the deployed contract each time this page loads. Nothing is indexed off-chain,
          so what you see is what the chain holds.
        </p>
      </header>

      <div className="flex flex-wrap items-center gap-2">
        <div className="no-scrollbar flex min-w-0 flex-1 gap-1 overflow-x-auto" role="tablist"
             aria-label="Filter">
          {(Object.keys(FILTERS) as (keyof typeof FILTERS)[]).map((key) => (
            <button key={key} type="button" role="tab" aria-selected={filter === key}
                    onClick={() => setFilter(key)}
                    className={`shrink-0 rounded-sm border px-2.5 py-1 text-[13px] ${
                      filter === key
                        ? "border-[var(--signal)] text-[var(--signal)]"
                        : "border-[var(--border)] text-[var(--muted)] hover:text-[var(--text)]"}`}>
              {key}
            </button>
          ))}
        </div>
        <label className="flex w-full min-w-0 items-center gap-2 text-sm sm:ml-auto sm:w-auto">
          <span className="sr-only">Search by identifier, title, subject or creator</span>
          <input className="control w-full sm:w-64" value={query}
                 placeholder="Protocol id, title, subject or address"
                 onChange={(event) => setQuery(event.target.value)} />
        </label>
      </div>

      {protocols.error ? (
        <p role="alert" className="card border-[var(--error)] p-4 text-sm">
          The contract could not be read: {protocols.error}{" "}
          <button type="button" className="underline" onClick={protocols.reload}>Try again</button>
        </p>
      ) : protocols.loading ? (
        <div className="h-48 animate-pulse rounded-sm bg-[var(--surface)]" aria-busy="true"
             aria-label="Loading" />
      ) : rows.length === 0 ? (
        <div className="card p-6">
          <p className="text-sm">
            {protocols.data?.total
              ? "No protocol matches that filter."
              : "No protocol has been created on this contract yet."}
          </p>
          <Link href="/protocols/new" className="btn btn-primary mt-4 w-fit">
            Create the first one
          </Link>
        </div>
      ) : (
        <ul className="grid gap-3">
          {rows.map((p) => (
            <li key={p.protocol_id}>
              <Link href={`/protocols/${p.protocol_id}`}
                    className="card block p-4 hover:border-[var(--signal)]">
                <div className="flex flex-wrap items-baseline justify-between gap-3">
                  <span className="mono text-xs text-[var(--muted)]">
                    {protocolLabel(p.protocol_id)}
                  </span>
                  <div className="flex flex-wrap items-center gap-2">
                    <LifecycleChip state={p.lifecycle} />
                    <ResultChip result={p.overall_result} />
                  </div>
                </div>
                <h2 className="mt-1.5 text-[17px]">{p.title}</h2>
                <p className="mt-1 text-sm text-[var(--muted)]">{p.subject}</p>
                <p className="mt-1 text-sm text-[var(--muted)]">
                  {p.evidence_count} evidence item{p.evidence_count === 1 ? "" : "s"},{" "}
                  {p.round_count} verification round{p.round_count === 1 ? "" : "s"}.{" "}
                  {custodyWords(p)}
                </p>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  Evidence due {formatTime(p.deadline)} ({relativeTime(p.deadline, now)})
                </p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
