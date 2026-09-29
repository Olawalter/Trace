"use client";

import Link from "next/link";

import { configResult } from "@/lib/config/env";
import { useProtocols } from "@/lib/genlayer/hooks";
import { formatTime, protocolLabel } from "@/lib/formatting/present";
import { LifecycleChip, ResultChip } from "@/components/ui/chips";
import { ConfigProblem } from "@/components/ui/config-problem";

/**
 * Every protocol that has been verified, and every one still waiting.
 *
 * The result shown is the one the contract holds. Nothing here is computed from
 * the requirements a second time: a console that re-derived results would be a
 * second opinion, and there is only supposed to be one.
 */
export default function Verifications() {
  const protocols = useProtocols();
  if (!configResult.ok) return <ConfigProblem />;

  const all = protocols.data?.items ?? [];
  const decided = all.filter((p) => p.round_count > 0).reverse();
  const waiting = all.filter((p) => p.round_count === 0 && p.evidence_count > 0).reverse();

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] gap-6">
      <header className="grid gap-2">
        <p className="label">Verifications</p>
        <h1 className="text-2xl">What GenLayer has decided</h1>
        <p className="max-w-2xl text-sm text-[var(--muted)]">
          A verification is a round in which every validator fetched the evidence and answered each
          requirement. A round that reached no majority recorded nothing and does not appear here.
        </p>
      </header>

      {protocols.error ? (
        <p role="alert" className="card border-[var(--error)] p-4 text-sm">
          The contract could not be read: {protocols.error}{" "}
          <button type="button" className="underline" onClick={protocols.reload}>Try again</button>
        </p>
      ) : null}

      <section className="grid gap-3">
        <h2 className="label">Decided ({decided.length})</h2>
        {decided.length === 0 ? (
          <p className="card p-4 text-sm text-[var(--muted)]">
            Nothing has been verified on this contract yet.
          </p>
        ) : (
          <ul className="grid gap-2">
            {decided.map((p) => (
              <li key={p.protocol_id}>
                <Link href={`/protocols/${p.protocol_id}`}
                      className="card block p-4 hover:border-[var(--signal)]">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="mono text-xs text-[var(--muted)]">
                      {protocolLabel(p.protocol_id)}
                    </span>
                    <div className="flex flex-wrap gap-2">
                      <ResultChip result={p.overall_result} />
                      <LifecycleChip state={p.lifecycle} />
                    </div>
                  </div>
                  <p className="mt-1.5 text-sm">{p.title}</p>
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    {p.round_count} round{p.round_count === 1 ? "" : "s"} ·{" "}
                    {p.evidence_count} evidence item{p.evidence_count === 1 ? "" : "s"} ·{" "}
                    last activity {formatTime(p.updated_at)}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="grid gap-3">
        <h2 className="label">Carrying evidence, not yet verified ({waiting.length})</h2>
        {waiting.length === 0 ? (
          <p className="card p-4 text-sm text-[var(--muted)]">Nothing is waiting.</p>
        ) : (
          <ul className="grid gap-2">
            {waiting.map((p) => (
              <li key={p.protocol_id}>
                <Link href={`/protocols/${p.protocol_id}`}
                      className="card block p-3 hover:border-[var(--signal)]">
                  <span className="mono text-xs text-[var(--muted)]">
                    {protocolLabel(p.protocol_id)}
                  </span>
                  <p className="mt-1 text-sm">{p.title}</p>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
