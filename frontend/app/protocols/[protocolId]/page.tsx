"use client";

import Link from "next/link";
import { use, useMemo, useState } from "react";

import { addressLink, configResult } from "@/lib/config/env";
import { writes } from "@/lib/genlayer/contract";
import { readClient } from "@/lib/genlayer/client";
import { actsFor, type ActId } from "@/lib/genlayer/acts";
import {
  useEvidence,
  useHistory,
  useNow,
  useProtocol,
  useSend,
  useVerifications,
} from "@/lib/genlayer/hooks";
import {
  ACTION_WORDS,
  custodyWords,
  formatGen,
  formatTime,
  humaniseNote,
  LIFECYCLE_WORDS,
  protocolLabel,
  relativeTime,
  resultHeadline,
  shortAddress,
  shortDigest,
  words,
} from "@/lib/formatting/present";
import { LifecycleChip, ResultChip } from "@/components/ui/chips";
import { ConfigProblem } from "@/components/ui/config-problem";
import { ConsensusPanel } from "@/components/verification/consensus-panel";
import { EvidenceForm } from "@/components/evidence/evidence-form";
import { EvidenceList } from "@/components/evidence/evidence-list";
import { RequirementList } from "@/components/verification/requirement-list";
import { TxPanel } from "@/components/transaction/tx-panel";
import { useWallet } from "@/components/wallet/wallet-provider";

const TABS = ["Protocol", "Requirements", "Evidence", "Verification", "Consensus"] as const;
type Tab = (typeof TABS)[number];

export default function ProtocolPage({ params }: { params: Promise<{ protocolId: string }> }) {
  const { protocolId } = use(params);
  const [tab, setTab] = useState<Tab>("Protocol");
  const [showEvidenceForm, setShowEvidenceForm] = useState(false);

  const protocol = useProtocol(protocolId);
  const evidence = useEvidence(protocolId);
  const history = useHistory(protocolId);
  const rounds = protocol.data?.round_count ?? 0;
  const verifications = useVerifications(protocolId, rounds);
  const now = useNow();

  const { account, wallet, wrongNetwork, writeClientFor } = useWallet();
  const { tx, send, reset } = useSend(wallet?.provider, writeClientFor);

  const latest = useMemo(() => {
    const items = verifications.data?.items ?? [];
    return items.length > 0 ? items[items.length - 1] : undefined;
  }, [verifications.data]);

  const acts = useMemo(
    () => (protocol.data ? actsFor(protocol.data, latest?.verified_at, now, account) : []),
    [protocol.data, latest, now, account],
  );

  if (!configResult.ok) return <ConfigProblem />;

  if (protocol.error) {
    return (
      <div className="card border-[var(--error)] p-6">
        <h1 className="text-lg">This protocol could not be read</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">{protocol.error}</p>
        <button type="button" className="btn mt-4" onClick={protocol.reload}>Try again</button>
      </div>
    );
  }

  if (!protocol.data) {
    return <div className="h-64 animate-pulse rounded-sm bg-[var(--surface)]" aria-busy="true"
                aria-label="Loading" />;
  }

  const p = protocol.data;
  const definition = p.definition;
  const available = acts.filter((a) => !a.blocked);
  const blocked = acts.filter((a) => a.blocked);

  const afterWrite = async () => {
    protocol.reload();
    evidence.reload();
    history.reload();
    verifications.reload();
  };

  const run = (id: ActId) => {
    if (!wallet || wrongNetwork) return;
    const call =
      id === "activate" ? writes.activate(p.protocol_id)
      : id === "fund_reward" ? writes.fund(p.protocol_id,
          BigInt(p.reward_required) - BigInt(p.reward_deposited))
      : id === "fund_bond" ? writes.fund(p.protocol_id,
          BigInt(p.bond_required) - BigInt(p.bond_deposited))
      : id === "request_verification" ? writes.requestVerification(p.protocol_id)
      : id === "accept" ? writes.accept(p.protocol_id)
      : id === "finalize" ? writes.finalize(p.protocol_id)
      : id === "recover" ? writes.recover(p.protocol_id)
      : id === "cancel" ? writes.cancel(p.protocol_id)
      : undefined;
    if (!call) return;

    void send({
      call,
      reconciled: async () => {
        const fresh = await readClient().readContract({
          address: configResult.ok ? configResult.config.contractAddress : "0x",
          functionName: "get_protocol",
          args: [p.protocol_id],
        } as never);
        const seen = fresh as { lifecycle?: string; reward_deposited?: string;
                               bond_deposited?: string };
        if (id === "fund_reward") return seen.reward_deposited === p.reward_required;
        if (id === "fund_bond") return seen.bond_deposited === p.bond_required;
        return seen.lifecycle !== p.lifecycle;
      },
      onRecorded: afterWrite,
    });
  };

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] gap-6">
      <header className="grid gap-2">
        <div className="flex flex-wrap items-center gap-3">
          <span className="mono text-xs text-[var(--muted)]">{protocolLabel(p.protocol_id)}</span>
          <LifecycleChip state={p.lifecycle} />
          <ResultChip result={p.overall_result} />
        </div>
        <h1 className="max-w-4xl text-2xl sm:text-[1.75rem]">{p.title}</h1>
        <p className="max-w-3xl text-sm text-[var(--muted)]">{p.subject}</p>
        <dl className="mt-1 flex flex-wrap gap-x-6 gap-y-1 text-xs text-[var(--muted)]">
          <div className="flex gap-2">
            <dt>Creator</dt>
            <dd className="mono">{shortAddress(p.creator)}</dd>
          </div>
          <div className="flex gap-2">
            <dt>Evidence due</dt>
            <dd>{formatTime(p.deadline)} ({relativeTime(p.deadline, now)})</dd>
          </div>
          {p.frozen ? (
            <div className="flex gap-2">
              <dt>Frozen as</dt>
              <dd className="mono">{shortDigest(p.fingerprint)}</dd>
            </div>
          ) : null}
        </dl>
      </header>

      <nav className="no-scrollbar flex gap-1 overflow-x-auto border-b" aria-label="Sections">
        {TABS.map((name) => (
          <button key={name} type="button" role="tab" aria-selected={tab === name}
                  onClick={() => setTab(name)}
                  className={`shrink-0 border-b-2 px-3 py-2 text-sm ${
                    tab === name
                      ? "border-[var(--signal)] text-[var(--text)]"
                      : "border-transparent text-[var(--muted)] hover:text-[var(--text)]"}`}>
            {name}
          </button>
        ))}
      </nav>

      {tab === "Protocol" ? (
        <section className="grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
          <div className="grid gap-4">
            <div className="card">
              <div className="card-head"><h2 className="label">What must be true</h2></div>
              <p className="p-4 text-sm">{p.description}</p>
            </div>

            {definition ? (
              <div className="card">
                <div className="card-head"><h2 className="label">Evidence policy</h2></div>
                <div className="grid gap-1.5 p-4 text-sm text-[var(--muted)]">
                  <p>
                    At least {definition.evidence_policy.minimum_sources} independent publisher
                    {definition.evidence_policy.minimum_sources === 1 ? "" : "s"}.
                    {definition.evidence_policy.allowed_domains.length > 0
                      ? ` Only from ${definition.evidence_policy.allowed_domains.join(", ")}.`
                      : " Any publisher."}
                  </p>
                  {definition.evidence_policy.required_source_types.length > 0 ? (
                    <p>
                      Must include: {definition.evidence_policy.required_source_types
                        .join(", ").toLowerCase()}.
                    </p>
                  ) : null}
                  <p>
                    Where sources contradict each other and neither is stronger, the requirement is
                    recorded as uncertain rather than decided.
                  </p>
                  <p>
                    Evidence that does not meet this policy makes the whole protocol a deviation,
                    decided in code before any answer is weighed.
                  </p>
                </div>
              </div>
            ) : null}

            <div className="card">
              <div className="card-head"><h2 className="label">History</h2></div>
              <ol className="divide-y divide-[var(--border)]">
                {(history.data?.items ?? []).map((row, index) => (
                  <li key={`${row.at}-${index}`} className="p-3 text-sm">
                    <span className="text-xs text-[var(--muted)]">{formatTime(row.at)}</span>
                    <p>
                      {row.from ? `${words(LIFECYCLE_WORDS, row.from)} to ` : ""}
                      {words(LIFECYCLE_WORDS, row.to)}
                    </p>
                    {row.note ? (
                      <p className="text-xs text-[var(--muted)]">{humaniseNote(row.note)}</p>
                    ) : null}
                  </li>
                ))}
              </ol>
            </div>
          </div>

          <div className="grid gap-4">
            <ActsPanel acts={acts} available={available} blocked={blocked} tx={tx}
                       connected={Boolean(account)} wrongNetwork={wrongNetwork} onRun={run}
                       onReset={reset} />

            <div className="card">
              <div className="card-head"><h2 className="label">Consequence</h2></div>
              <div className="grid gap-2 p-4 text-sm">
                <p>{custodyWords(p)}</p>
                {p.economic && definition?.economic_policy.enabled ? (
                  <>
                    <dl className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <dt className="label">Reward</dt>
                        <dd className="mt-0.5">
                          {formatGen(p.reward_deposited)} of {formatGen(p.reward_required)}
                        </dd>
                      </div>
                      <div>
                        <dt className="label">Bond</dt>
                        <dd className="mt-0.5">
                          {formatGen(p.bond_deposited)} of {formatGen(p.bond_required)}
                        </dd>
                      </div>
                    </dl>
                    <ul className="grid gap-1 text-xs text-[var(--muted)]">
                      <li>
                        Verified releases {(definition.economic_policy.verified_payout_bps ?? 0) / 100}%
                        of the reward to the submitter.
                      </li>
                      <li>
                        Partially verified releases{" "}
                        {(definition.economic_policy.partial_payout_bps ?? 0) / 100}%.
                      </li>
                      <li>
                        Not verified: {words(ACTION_WORDS,
                          definition.economic_policy.not_verified_action ?? "REFUND")}, and the bond
                        is forfeit to the creator.
                      </li>
                      <li>
                        Inconclusive: {words(ACTION_WORDS,
                          definition.economic_policy.inconclusive_action ?? "REFUND")}.
                      </li>
                      <li>
                        If nobody finishes it: {words(ACTION_WORDS,
                          definition.economic_policy.timeout_action ?? "REFUND")}, from{" "}
                        {formatTime(p.deadline + p.recovery_window)}.
                      </li>
                    </ul>
                    {p.settled_at ? (
                      <p className="text-sm text-[var(--signal)]">
                        Settled: {formatGen(p.paid_submitter)} to the submitter,{" "}
                        {formatGen(p.paid_creator)} to the creator.
                      </p>
                    ) : null}
                  </>
                ) : null}
              </div>
            </div>

            <div className="card">
              <div className="card-head"><h2 className="label">Verify this yourself</h2></div>
              <div className="grid gap-2 p-4 text-xs text-[var(--muted)]">
                <p className="mono break-all">
                  Contract{" "}
                  <a className="underline decoration-dotted underline-offset-2"
                     href={addressLink(configResult.config, configResult.config.contractAddress)}
                     target="_blank" rel="noreferrer">
                    {configResult.config.contractAddress}
                  </a>
                </p>
                {p.frozen ? <p className="mono break-all">Frozen as {p.fingerprint}</p> : null}
                <p>
                  Every protocol on this contract is public. What you see here was read from it just
                  now; nothing is stored by this console.
                </p>
              </div>
            </div>
          </div>
        </section>
      ) : null}

      {tab === "Requirements" ? (
        <section className="grid gap-3">
          {definition ? (
            <>
              <p className="text-sm text-[var(--muted)]">
                {latest
                  ? resultHeadline(latest.overall_result, latest.findings, definition.requirements)
                  : "This protocol has not been verified yet."}
              </p>
              <RequirementList requirements={definition.requirements} findings={latest?.findings}
                               observed={latest?.evidence} held={latest?.held_for_sources} />
            </>
          ) : (
            <p className="card p-4 text-sm text-[var(--muted)]">
              This protocol has no requirements yet.
            </p>
          )}
        </section>
      ) : null}

      {tab === "Evidence" ? (
        <section className="grid gap-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm text-[var(--muted)]">
              {p.evidence_count} registered. Every validator fetches each address itself when the
              protocol is verified.
            </p>
            {acts.find((a) => a.id === "submit_evidence" && !a.blocked) && account ? (
              <button type="button" className="btn"
                      onClick={() => setShowEvidenceForm((v) => !v)}>
                {showEvidenceForm ? "Cancel" : "Register evidence"}
              </button>
            ) : null}
          </div>

          {showEvidenceForm && definition ? (
            <EvidenceForm protocolId={p.protocol_id} requirements={definition.requirements}
                          onDone={() => {
                            setShowEvidenceForm(false);
                            void afterWrite();
                          }} />
          ) : null}

          <EvidenceList evidence={evidence.data?.items ?? []} observed={latest?.evidence} />
        </section>
      ) : null}

      {tab === "Verification" ? (
        <section className="grid gap-3">
          {!latest ? (
            <p className="card p-4 text-sm text-[var(--muted)]">
              This protocol has not been verified yet. Once evidence is registered, anybody can ask
              GenLayer to decide every requirement against it.
            </p>
          ) : (
            <>
              <div className="card p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <ResultChip result={latest.overall_result} />
                  <span className="mono text-xs text-[var(--muted)]">
                    round {latest.round + 1} of {p.round_count}
                  </span>
                </div>
                <p className="mt-2 text-sm">{latest.summary}</p>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  Proposed {formatTime(latest.verified_at)}
                  {latest.finalized_at ? `, accepted ${formatTime(latest.finalized_at)}` : ""}.
                </p>
              </div>
              {definition ? (
                <RequirementList requirements={definition.requirements} findings={latest.findings}
                                 observed={latest.evidence} held={latest.held_for_sources} />
              ) : null}
            </>
          )}
        </section>
      ) : null}

      {tab === "Consensus" ? (
        <section className="grid gap-3">
          {latest ? (
            <ConsensusPanel verification={latest} />
          ) : (
            <p className="card p-4 text-sm text-[var(--muted)]">
              Nothing has been decided yet, so there is no consensus to show. When a round runs,
              this page will show what happened -- not who voted, which GenLayer does not publish.
            </p>
          )}
        </section>
      ) : null}

      <p className="text-xs text-[var(--muted)]">
        <Link href="/protocols" className="underline">All protocols</Link>
      </p>
    </div>
  );
}

function ActsPanel({ acts, available, blocked, tx, connected, wrongNetwork, onRun, onReset }: {
  acts: ReturnType<typeof actsFor>;
  available: ReturnType<typeof actsFor>;
  blocked: ReturnType<typeof actsFor>;
  tx: ReturnType<typeof useSend>["tx"];
  connected: boolean;
  wrongNetwork: boolean;
  onRun: (id: ActId) => void;
  onReset: () => void;
}) {
  const [showBlocked, setShowBlocked] = useState(false);
  const running = tx.phase === "RUNNING";
  const offered = available.filter((a) => a.id !== "set_draft" && a.id !== "submit_evidence");

  return (
    <div className="card">
      <div className="card-head"><h2 className="label">What can be done now</h2></div>
      <div className="grid gap-3 p-4">
        {!connected ? (
          <p className="text-sm text-[var(--muted)]">
            Connect a wallet to act on this protocol. Reading it needs nothing.
          </p>
        ) : wrongNetwork ? (
          <p className="text-sm text-[var(--warning)]">
            Your wallet is on another network. Switch it to StudioNet to act.
          </p>
        ) : offered.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">
            Nothing can be done to this protocol at the moment. The list below says why.
          </p>
        ) : (
          offered.map((act) => (
            <div key={act.id} className="grid gap-1">
              <button type="button" className="btn btn-primary w-fit" disabled={running}
                      onClick={() => onRun(act.id)}>
                {act.label}
              </button>
              <p className="text-xs text-[var(--muted)]">{act.detail}</p>
            </div>
          ))
        )}

        <TxPanel state={tx}
                 leaderNote="Every validator is fetching the evidence and deciding each requirement."
                 done="Recorded in the contract." />
        {tx.phase === "FAILED" || tx.phase === "DONE" ? (
          <button type="button" className="btn w-fit" onClick={onReset}>Clear</button>
        ) : null}

        {blocked.length > 0 ? (
          <details open={showBlocked} onToggle={(e) => setShowBlocked(e.currentTarget.open)}>
            <summary className="cursor-pointer text-xs text-[var(--muted)]">
              Not available yet ({blocked.length})
            </summary>
            <ul className="mt-2 grid gap-1.5">
              {blocked.map((act) => (
                <li key={act.id} className="text-xs">
                  <span className="text-[var(--text)]">{act.label}</span>
                  <span className="text-[var(--muted)]"> — {act.blocked}</span>
                </li>
              ))}
            </ul>
          </details>
        ) : null}
      </div>
    </div>
  );
}
