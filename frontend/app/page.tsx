"use client";

import Link from "next/link";

import { useActivity, useInfo, useProtocols } from "@/lib/genlayer/hooks";
import { formatGen, protocolLabel, words, LIFECYCLE_WORDS } from "@/lib/formatting/present";
import { LifecycleChip, ResultChip } from "@/components/ui/chips";
import { ConfigProblem } from "@/components/ui/config-problem";
import { configResult } from "@/lib/config/env";

const STEPS = [
  ["Define", "Write what must be true, as requirements that can each be answered on their own."],
  ["Freeze", "Activate the protocol. After that, nothing in it can change -- by anyone."],
  ["Verify", "Every validator fetches the evidence itself and decides each requirement."],
  ["Finalize", "The result is derived in code, and any consequence in GEN follows from it."],
];

export default function Overview() {
  const protocols = useProtocols();
  const activity = useActivity();
  const info = useInfo();

  if (!configResult.ok) return <ConfigProblem />;

  const all = protocols.data?.items ?? [];
  const open = all.filter((p) => ["ACTIVE", "EVIDENCE_SUBMITTED"].includes(p.lifecycle));
  const awaiting = all.filter((p) => ["VERDICT_PROPOSED", "VERIFICATION_PENDING"].includes(p.lifecycle));
  const done = all.filter((p) => ["FINALIZED", "ACCEPTED"].includes(p.lifecycle));

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] gap-10">
      <section className="grid gap-8 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] lg:items-start">
        <div className="grid gap-5">
          <p className="label">Verifiable compliance protocols</p>
          <h1 className="text-[2.1rem] leading-[1.08] sm:text-[2.5rem]">
            Verifiable compliance
            <br />
            for the internet
          </h1>
          <p className="lede max-w-xl">
            Define what must be true. Submit evidence. Let GenLayer independently verify whether the
            evidence satisfies the protocol.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link href="/protocols/new" className="btn btn-primary">Create a protocol</Link>
            <Link href="/protocols" className="btn">Explore protocols</Link>
          </div>
        </div>

        <div className="card">
          <div className="card-head">
            <h2 className="label">How a protocol is decided</h2>
          </div>
          <ol className="grid gap-0 p-4">
            {STEPS.map(([name, text], index) => (
              <li key={name} className="grid grid-cols-[1.75rem_minmax(0,1fr)] gap-3">
                <div className="flex flex-col items-center">
                  <span aria-hidden="true"
                        className={`mono flex h-7 w-7 items-center justify-center rounded-sm border
                                    text-[11px] ${
                                      index === STEPS.length - 1
                                        ? "border-[var(--signal)] text-[var(--signal)]"
                                        : "border-[var(--border)] text-[var(--muted)]"}`}>
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  {index < STEPS.length - 1 ? (
                    <span className="h-full w-px bg-[var(--border)]" aria-hidden />
                  ) : null}
                </div>
                <div className="pb-4">
                  <p className="text-sm font-semibold">{name}</p>
                  <p className="text-sm text-[var(--muted)]">{text}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="rule grid gap-4 pt-8">
        <h2 className="label">On this contract</h2>
        <div className="grid gap-3 sm:grid-cols-4">
          {[
            ["Open for evidence", open.length],
            ["Awaiting a result", awaiting.length],
            ["Finished", done.length],
            ["Held in custody", info.data ? formatGen(info.data.total_custody) : "--"],
          ].map(([label, value]) => (
            <div key={String(label)} className="card p-4">
              <p className="label">{label}</p>
              <p className="mt-1 text-2xl">{value}</p>
            </div>
          ))}
        </div>
        {protocols.error ? (
          <p role="alert" className="card border-[var(--error)] p-4 text-sm">
            The contract could not be read: {protocols.error}{" "}
            <button type="button" className="underline" onClick={protocols.reload}>Try again</button>
          </p>
        ) : null}
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="grid gap-3">
          <h2 className="label">Recent protocols</h2>
          {all.length === 0 && !protocols.loading ? (
            <p className="card p-4 text-sm text-[var(--muted)]">
              No protocol has been created on this contract yet.
            </p>
          ) : (
            <ul className="grid gap-2">
              {all.slice(-5).reverse().map((p) => (
                <li key={p.protocol_id}>
                  <Link href={`/protocols/${p.protocol_id}`}
                        className="card block p-3 hover:border-[var(--signal)]">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="mono text-xs text-[var(--muted)]">
                        {protocolLabel(p.protocol_id)}
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        <LifecycleChip state={p.lifecycle} />
                        <ResultChip result={p.overall_result} />
                      </div>
                    </div>
                    <p className="mt-1 text-sm">{p.title}</p>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="grid gap-3">
          <h2 className="label">Recent activity</h2>
          <ul className="card divide-y divide-[var(--border)]">
            {(activity.data?.items ?? []).slice(-6).reverse().map((row, index) => (
              <li key={`${row.protocol_id}-${row.at}-${index}`} className="p-3 text-sm">
                <span className="mono text-xs text-[var(--muted)]">
                  {protocolLabel(row.protocol_id)}
                </span>{" "}
                {row.from ? `${words(LIFECYCLE_WORDS, row.from)} to ` : ""}
                {words(LIFECYCLE_WORDS, row.to)}
              </li>
            ))}
            {(activity.data?.items ?? []).length === 0 ? (
              <li className="p-3 text-sm text-[var(--muted)]">Nothing has happened yet.</li>
            ) : null}
          </ul>
        </div>
      </section>
    </div>
  );
}
