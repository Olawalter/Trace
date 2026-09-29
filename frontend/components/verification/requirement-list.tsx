"use client";

import type { Finding, Observed, Requirement } from "@/lib/genlayer/contract";
import { StatusChip } from "@/components/ui/chips";

/**
 * Every requirement, on its own, with what the panel concluded about it and the
 * words it relied on. Never one score standing in for all of them.
 */
export function RequirementList({
  requirements,
  findings,
  observed,
  held,
}: {
  requirements: Requirement[];
  findings?: Finding[];
  observed?: Observed[];
  held?: string[];
}) {
  const byId = new Map((findings ?? []).map((f) => [f.requirement_id, f]));
  const publisherOf = new Map((observed ?? []).map((o) => [o.evidence_id, o.publisher]));

  return (
    <ul className="grid gap-3">
      {requirements.map((requirement) => {
        const finding = byId.get(requirement.requirement_id);
        const wasHeld = (held ?? []).includes(requirement.requirement_id);
        return (
          <li key={requirement.requirement_id} className="card p-4">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="text-sm">
                <span className="mono mr-2 text-xs text-[var(--muted)]">
                  {requirement.requirement_id}
                </span>
                {requirement.description}
              </p>
              {finding ? <StatusChip status={finding.effective_status} /> : null}
            </div>

            <p className="mt-1 text-xs text-[var(--muted)]">
              {requirement.mandatory ? "Mandatory" : "Optional"}
              {requirement.min_sources > 1
                ? ` · at least ${requirement.min_sources} independent sources`
                : ""}
              {" · "}
              {requirement.verification_rule}
            </p>

            {finding ? (
              <div className="mt-3 grid gap-2 border-t border-[var(--border)] pt-3">
                {finding.quote ? (
                  <blockquote className="border-l-2 border-[var(--border-strong)] pl-3 text-sm">
                    “{finding.quote}”
                    <span className="mono ml-2 text-xs text-[var(--muted)]">
                      {finding.quote_evidence_id}
                      {publisherOf.get(finding.quote_evidence_id)
                        ? ` · ${publisherOf.get(finding.quote_evidence_id)}`
                        : ""}
                    </span>
                  </blockquote>
                ) : (
                  <p className="text-sm text-[var(--muted)]">
                    {finding.reason || "The evidence did not settle this requirement."}
                  </p>
                )}

                <p className="text-xs text-[var(--muted)]">
                  {finding.independent_sources} independent source
                  {finding.independent_sources === 1 ? "" : "s"} stood behind this
                  {finding.evidence_refs.length > 0
                    ? `, from ${finding.evidence_refs.join(", ")}`
                    : ""}
                  .
                </p>

                {wasHeld ? (
                  <p className="text-xs text-[var(--warning)]">
                    The panel answered {finding.status.toLowerCase()}, and the protocol asked for
                    more independent sources than stood behind it, so it is held as uncertain.
                    A held answer moves no money in either direction.
                  </p>
                ) : null}
              </div>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}
