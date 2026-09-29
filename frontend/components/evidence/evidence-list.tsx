"use client";

import type { Evidence, Observed } from "@/lib/genlayer/contract";
import { AvailabilityChip } from "@/components/ui/chips";
import { formatTime, shortAddress, shortDigest, SOURCE_TYPE_WORDS, words } from
  "@/lib/formatting/present";

/**
 * What was registered, and -- once a round has run -- what each validator found
 * at that address for itself. The digest is over the excerpt the panel read,
 * not over the leader's copy of it.
 */
export function EvidenceList({ evidence, observed }: {
  evidence: Evidence[];
  observed?: Observed[];
}) {
  const found = new Map((observed ?? []).map((o) => [o.evidence_id, o]));

  if (evidence.length === 0) {
    return (
      <p className="card p-4 text-sm text-[var(--muted)]">
        No evidence has been registered. Every address registered here is fetched by every
        validator when the protocol is verified.
      </p>
    );
  }

  return (
    <ul className="grid gap-3">
      {evidence.map((item) => {
        const read = found.get(item.evidence_id);
        return (
          <li key={item.evidence_id} className="card p-4">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <span className="mono text-xs text-[var(--muted)]">{item.evidence_id}</span>
              <div className="flex flex-wrap items-center gap-2">
                <span className="chip">{words(SOURCE_TYPE_WORDS, item.source_type)}</span>
                {read ? <AvailabilityChip availability={read.availability} /> : null}
              </div>
            </div>

            {item.label ? <p className="mt-1.5 text-sm">{item.label}</p> : null}

            <a href={item.source_url} target="_blank" rel="noreferrer"
               className="mono mt-1 block break-all text-xs text-[var(--muted)] underline
                          decoration-dotted underline-offset-2">
              {item.source_url}
            </a>

            <dl className="mt-2 grid gap-x-6 gap-y-1 text-xs text-[var(--muted)] sm:grid-cols-2">
              <div className="flex gap-2">
                <dt>Publisher</dt>
                <dd className="mono">{item.publisher}</dd>
              </div>
              <div className="flex gap-2">
                <dt>Registered by</dt>
                <dd className="mono">{shortAddress(item.submitter)}</dd>
              </div>
              <div className="flex gap-2">
                <dt>Speaks to</dt>
                <dd>{item.supports.join(", ")}</dd>
              </div>
              <div className="flex gap-2">
                <dt>Registered</dt>
                <dd>{formatTime(item.submitted_at)}</dd>
              </div>
              {read ? (
                <>
                  <div className="flex gap-2">
                    <dt>Read at</dt>
                    <dd>{formatTime(read.observed_at)}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt>Digest of what was read</dt>
                    <dd className="mono">{shortDigest(read.excerpt_digest)}</dd>
                  </div>
                </>
              ) : null}
            </dl>

            {read?.excerpt ? (
              <details className="mt-3">
                <summary className="cursor-pointer text-xs text-[var(--muted)]">
                  What the panel read
                </summary>
                <p className="mt-2 max-h-56 overflow-auto whitespace-pre-wrap rounded-sm
                              bg-[var(--surface)] p-3 text-xs text-[var(--muted)]">
                  {read.excerpt}
                </p>
              </details>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}
