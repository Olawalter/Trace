"use client";

import { useMemo, useState } from "react";

import { configResult } from "@/lib/config/env";
import { readClient } from "@/lib/genlayer/client";
import { writes, type Requirement } from "@/lib/genlayer/contract";
import { useSend } from "@/lib/genlayer/hooks";
import {
  evidenceJson,
  publisherOf,
  SOURCE_TYPES,
  validateEvidence,
  type EvidenceDraft,
} from "@/lib/validation/protocol";
import { SOURCE_TYPE_WORDS, words } from "@/lib/formatting/present";
import { TxPanel } from "@/components/transaction/tx-panel";
import { useWallet } from "@/components/wallet/wallet-provider";

/**
 * Register an address the panel will fetch.
 *
 * Nothing is fetched now, deliberately: what matters is that both sides can see
 * which addresses will be read before anybody reads them. The publisher is
 * shown while typing, because independence is counted by publisher and two
 * pages from one account are one voice.
 */
export function EvidenceForm({ protocolId, requirements, onDone }: {
  protocolId: string;
  requirements: Requirement[];
  onDone: () => void;
}) {
  const { wallet, wrongNetwork, writeClientFor } = useWallet();
  const { tx, send } = useSend(wallet?.provider, writeClientFor);
  const [draft, setDraft] = useState<EvidenceDraft>({
    sourceUrl: "",
    sourceType: "PUBLICATION",
    supports: [],
    label: "",
  });
  const [touched, setTouched] = useState(false);

  const problems = useMemo(() => validateEvidence(draft), [draft]);
  const publisher = useMemo(() => publisherOf(draft.sourceUrl), [draft.sourceUrl]);
  const ready = Object.keys(problems).length === 0 && Boolean(wallet) && !wrongNetwork;

  const toggle = (id: string) =>
    setDraft((d) => ({
      ...d,
      supports: d.supports.includes(id)
        ? d.supports.filter((s) => s !== id)
        : [...d.supports, id],
    }));

  const submit = () => {
    setTouched(true);
    if (!ready) return;
    void send({
      call: writes.submitEvidence(protocolId, evidenceJson(draft)),
      reconciled: async () => {
        const fresh = (await readClient().readContract({
          address: configResult.ok ? configResult.config.contractAddress : "0x",
          functionName: "get_protocol",
          args: [protocolId],
        } as never)) as { evidence_count?: number };
        return (fresh.evidence_count ?? 0) > 0;
      },
      onRecorded: onDone,
    });
  };

  const problem = (key: string) =>
    touched && problems[key] ? (
      <p className="mt-1 text-xs text-[var(--error)]">{problems[key]}</p>
    ) : null;

  return (
    <form className="card grid gap-4 p-4" onSubmit={(e) => { e.preventDefault(); submit(); }}>
      <div>
        <label className="label" htmlFor="evidence-url">Address the validators will fetch</label>
        <input id="evidence-url" className="control mt-1" placeholder="https://…"
               value={draft.sourceUrl}
               onChange={(e) => setDraft({ ...draft, sourceUrl: e.target.value })} />
        {publisher ? (
          <p className="mt-1 text-xs text-[var(--muted)]">
            Publisher <span className="mono">{publisher}</span>. Independence is counted by
            publisher, so another page from this one is the same voice.
          </p>
        ) : null}
        {problem("sourceUrl")}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="label" htmlFor="evidence-kind">What kind of source</label>
          <select id="evidence-kind" className="control mt-1" value={draft.sourceType}
                  onChange={(e) => setDraft({ ...draft, sourceType: e.target.value })}>
            {SOURCE_TYPES.map((kind) => (
              <option key={kind} value={kind}>{words(SOURCE_TYPE_WORDS, kind)}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label" htmlFor="evidence-label">Label (optional)</label>
          <input id="evidence-label" className="control mt-1" value={draft.label}
                 placeholder="the publisher's own release record"
                 onChange={(e) => setDraft({ ...draft, label: e.target.value })} />
          {problem("label")}
        </div>
      </div>

      <fieldset>
        <legend className="label">Which requirements it speaks to</legend>
        <div className="mt-2 grid gap-1.5">
          {requirements.map((requirement) => (
            <label key={requirement.requirement_id} className="flex items-start gap-2 text-sm">
              <input type="checkbox" className="mt-1"
                     checked={draft.supports.includes(requirement.requirement_id)}
                     onChange={() => toggle(requirement.requirement_id)} />
              <span>
                <span className="mono mr-2 text-xs text-[var(--muted)]">
                  {requirement.requirement_id}
                </span>
                {requirement.description}
              </span>
            </label>
          ))}
        </div>
        {problem("supports")}
      </fieldset>

      <div className="flex flex-wrap items-center gap-2">
        <button type="submit" className="btn btn-primary" disabled={tx.phase === "RUNNING"}>
          Register this evidence
        </button>
        <button type="button" className="btn" onClick={onDone}>Cancel</button>
      </div>

      <TxPanel state={tx} done="Registered. The panel will fetch it when this protocol is verified." />
    </form>
  );
}
