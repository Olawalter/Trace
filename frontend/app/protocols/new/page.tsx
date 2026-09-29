"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { configResult } from "@/lib/config/env";
import { readClient } from "@/lib/genlayer/client";
import { writes } from "@/lib/genlayer/contract";
import { useNow, useSend } from "@/lib/genlayer/hooks";
import {
  ACTIONS,
  blankDraft,
  blankRequirement,
  draftJson,
  SOURCE_TYPES,
  validateDraft,
  type Draft,
} from "@/lib/validation/protocol";
import { ACTION_WORDS, formatTime, SOURCE_TYPE_WORDS, words } from "@/lib/formatting/present";
import { ConfigProblem } from "@/components/ui/config-problem";
import { TxPanel } from "@/components/transaction/tx-panel";
import { useWallet } from "@/components/wallet/wallet-provider";

const STAGES = ["Define", "Requirements", "Evidence policy", "Review and freeze"] as const;
type Stage = (typeof STAGES)[number];

export default function NewProtocol() {
  const router = useRouter();
  const now = useNow();
  const { account, wallet, wrongNetwork, writeClientFor } = useWallet();
  const { tx, send } = useSend(wallet?.provider, writeClientFor);

  const [stage, setStage] = useState<Stage>("Define");
  const [draft, setDraft] = useState<Draft>(() => blankDraft(Math.floor(Date.now() / 1000)));
  const [protocolId, setProtocolId] = useState<string>();
  const [touched, setTouched] = useState(false);

  const problems = useMemo(() => validateDraft(draft, now), [draft, now]);
  const set = <K extends keyof Draft>(key: K, value: Draft[K]) =>
    setDraft((d) => ({ ...d, [key]: value }));

  if (!configResult.ok) return <ConfigProblem />;

  const problem = (key: string) =>
    touched && problems[key] ? (
      <p className="mt-1 text-xs text-[var(--error)]">{problems[key]}</p>
    ) : null;

  const contract = configResult.config.contractAddress;
  const running = tx.phase === "RUNNING";

  /** Stage 1 sends create_protocol; the draft only exists on chain after this. */
  const createDraft = () => {
    setTouched(true);
    if (problems.title || problems.description || problems.subject || problems.subjectType) return;
    if (!wallet || wrongNetwork) return;
    void send({
      call: writes.createProtocol(draft.title.trim(), draft.description.trim(),
                                  draft.subject.trim(), draft.subjectType.trim()),
      reconciled: async () => {
        const mine = (await readClient().readContract({
          address: contract,
          functionName: "list_by_creator",
          args: [account ?? "", 0, 50],
        } as never)) as { items?: { protocol_id: string }[] };
        const items = mine.items ?? [];
        if (items.length === 0) return false;
        setProtocolId(items[items.length - 1].protocol_id);
        return true;
      },
      onRecorded: () => setStage("Requirements"),
    });
  };

  /** Stages 2 and 3 are written together: set_draft takes the whole definition. */
  const writeDraft = (nextStage: Stage) => {
    setTouched(true);
    if (Object.keys(problems).length > 0 || !protocolId) return;
    void send({
      call: writes.setDraft(protocolId, draftJson(draft)),
      reconciled: async () => {
        const fresh = (await readClient().readContract({
          address: contract, functionName: "get_protocol", args: [protocolId],
        } as never)) as { lifecycle?: string };
        return fresh.lifecycle === "REGISTERED";
      },
      onRecorded: () => setStage(nextStage),
    });
  };

  const freeze = () => {
    if (!protocolId) return;
    void send({
      call: writes.activate(protocolId),
      reconciled: async () => {
        const fresh = (await readClient().readContract({
          address: contract, functionName: "get_protocol", args: [protocolId],
        } as never)) as { lifecycle?: string };
        return fresh.lifecycle === "ACTIVE";
      },
      onRecorded: () => router.push(`/protocols/${protocolId}`),
    });
  };

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] gap-6">
      <header className="grid gap-2">
        <p className="label">Create a protocol</p>
        <h1 className="text-2xl">Say what must be true, then freeze it</h1>
        <p className="max-w-2xl text-sm text-[var(--muted)]">
          Once a protocol is activated, its requirements, its policies and its deadline cannot
          change. Everything before that is a draft.
        </p>
      </header>

      <ol className="no-scrollbar flex gap-1 overflow-x-auto" aria-label="Stages">
        {STAGES.map((name, index) => {
          const reached = STAGES.indexOf(stage) >= index;
          return (
            <li key={name}>
              <button type="button" onClick={() => protocolId && setStage(name)}
                      disabled={!protocolId && index > 0}
                      aria-current={stage === name ? "step" : undefined}
                      className={`shrink-0 rounded-sm border px-3 py-1.5 text-left text-[13px] ${
                        stage === name
                          ? "border-[var(--signal)] text-[var(--signal)]"
                          : reached
                            ? "border-[var(--border)] text-[var(--text)]"
                            : "border-[var(--border)] text-[var(--muted)]"}`}>
                <span className="mono mr-2 text-[11px]">{String(index + 1).padStart(2, "0")}</span>
                {name}
              </button>
            </li>
          );
        })}
      </ol>

      {!account ? (
        <p className="card p-4 text-sm text-[var(--muted)]">
          Connect a wallet to create a protocol. Each stage is a transaction you sign.
        </p>
      ) : null}

      {stage === "Define" ? (
        <section className="card grid gap-4 p-4">
          <h2 className="label">01 · Define</h2>
          <div>
            <label className="label" htmlFor="title">Title</label>
            <input id="title" className="control mt-1" value={draft.title}
                   placeholder="Widget 2.0 release compliance"
                   onChange={(e) => set("title", e.target.value)} />
            {problem("title")}
          </div>
          <div>
            <label className="label" htmlFor="subject">Subject</label>
            <input id="subject" className="control mt-1" value={draft.subject}
                   placeholder="widgetworks/widget release 2.0"
                   onChange={(e) => set("subject", e.target.value)} />
            {problem("subject")}
          </div>
          <div>
            <label className="label" htmlFor="subject-type">What kind of subject</label>
            <input id="subject-type" className="control mt-1" value={draft.subjectType}
                   placeholder="Software release"
                   onChange={(e) => set("subjectType", e.target.value)} />
            <p className="mt-1 text-xs text-[var(--faint)]">
              Your own words. It is stored with the protocol and shown to whoever reads it.
            </p>
            {problem("subjectType")}
          </div>
          <div>
            <label className="label" htmlFor="description">What the protocol is about</label>
            <textarea id="description" className="control mt-1 min-h-28" value={draft.description}
                      placeholder="The project states that release 2.0 is published: tagged, under a named open licence, with a changelog entry."
                      onChange={(e) => set("description", e.target.value)} />
            {problem("description")}
          </div>
          <div>
            <button type="button" className="btn btn-primary w-fit" disabled={running || !account}
                    onClick={createDraft}>
              Create the draft
            </button>
            <p className="mt-1 text-xs text-[var(--muted)]">
              This writes the protocol to the contract as a draft. Nothing is binding yet.
            </p>
          </div>
          <TxPanel state={tx} done="The draft is on chain." />
        </section>
      ) : null}

      {stage === "Requirements" ? (
        <section className="card grid gap-4 p-4">
          <h2 className="label">02 · Requirements {protocolId ? `· draft ${protocolId}` : ""}</h2>
          <p className="text-sm text-[var(--muted)]">
            Each requirement is answered on its own, against the evidence. Write them so a reader
            could decide one without deciding the others.
          </p>

          {draft.requirements.map((requirement, index) => (
            <fieldset key={index} className="grid gap-3 rounded-sm border border-[var(--border)] p-3">
              <legend className="mono px-1 text-xs text-[var(--muted)]">
                {requirement.requirementId}
              </legend>
              <div>
                <label className="label" htmlFor={`req-${index}`}>What must be true</label>
                <input id={`req-${index}`} className="control mt-1" value={requirement.description}
                       placeholder="A release tagged 2.0 is published."
                       onChange={(e) => {
                         const next = [...draft.requirements];
                         next[index] = { ...requirement, description: e.target.value };
                         set("requirements", next);
                       }} />
                {problem(`requirements.${index}.description`)}
              </div>
              <div>
                <label className="label" htmlFor={`rule-${index}`}>How a reader decides it</label>
                <input id={`rule-${index}`} className="control mt-1"
                       value={requirement.verificationRule}
                       placeholder="A source must show a published release carrying the tag 2.0."
                       onChange={(e) => {
                         const next = [...draft.requirements];
                         next[index] = { ...requirement, verificationRule: e.target.value };
                         set("requirements", next);
                       }} />
                {problem(`requirements.${index}.verificationRule`)}
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={requirement.mandatory}
                         onChange={(e) => {
                           const next = [...draft.requirements];
                           next[index] = { ...requirement, mandatory: e.target.checked };
                           set("requirements", next);
                         }} />
                  Mandatory: the protocol cannot be verified without it
                </label>
                <div>
                  <label className="label" htmlFor={`sources-${index}`}>
                    Independent publishers needed
                  </label>
                  <input id={`sources-${index}`} className="control mt-1"
                         value={requirement.minSources}
                         onChange={(e) => {
                           const next = [...draft.requirements];
                           next[index] = { ...requirement, minSources: e.target.value };
                           set("requirements", next);
                         }} />
                  {problem(`requirements.${index}.minSources`)}
                </div>
              </div>
              {draft.requirements.length > 1 ? (
                <button type="button" className="btn w-fit"
                        onClick={() => set("requirements",
                          draft.requirements.filter((_, i) => i !== index)
                            .map((r, i) => ({ ...r, requirementId: `R${i + 1}` })))}>
                  Remove
                </button>
              ) : null}
            </fieldset>
          ))}

          {problem("requirements")}

          <div className="flex flex-wrap gap-2">
            <button type="button" className="btn"
                    onClick={() => set("requirements",
                      [...draft.requirements, blankRequirement(draft.requirements.length)])}>
              Add a requirement
            </button>
            <button type="button" className="btn btn-primary" disabled={running}
                    onClick={() => setStage("Evidence policy")}>
              Evidence policy
            </button>
          </div>
        </section>
      ) : null}

      {stage === "Evidence policy" ? (
        <section className="card grid gap-4 p-4">
          <h2 className="label">03 · Evidence policy</h2>
          <p className="text-sm text-[var(--muted)]">
            What counts as evidence for this protocol. Evidence that does not meet this policy makes
            the whole protocol a deviation, decided in code before any answer is weighed.
          </p>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="label" htmlFor="min-sources">Independent publishers needed</label>
              <input id="min-sources" className="control mt-1" value={draft.minimumSources}
                     onChange={(e) => set("minimumSources", e.target.value)} />
              <p className="mt-1 text-xs text-[var(--muted)]">
                Counted by publisher: two pages from one account are one source.
              </p>
              {problem("minimumSources")}
            </div>
            <div>
              <label className="label" htmlFor="domains">Only from these hosts (optional)</label>
              <input id="domains" className="control mt-1" value={draft.allowedDomains}
                     placeholder="example.org, openindex.example"
                     onChange={(e) => set("allowedDomains", e.target.value)} />
              {problem("allowedDomains")}
            </div>
          </div>

          <fieldset>
            <legend className="label">Kinds of source the protocol requires (optional)</legend>
            <div className="mt-2 flex flex-wrap gap-3">
              {SOURCE_TYPES.map((kind) => (
                <label key={kind} className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={draft.requiredSourceTypes.includes(kind)}
                         onChange={() =>
                           set("requiredSourceTypes",
                               draft.requiredSourceTypes.includes(kind)
                                 ? draft.requiredSourceTypes.filter((k) => k !== kind)
                                 : [...draft.requiredSourceTypes, kind])} />
                  {words(SOURCE_TYPE_WORDS, kind)}
                </label>
              ))}
            </div>
          </fieldset>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="label" htmlFor="deadline">Evidence deadline (UTC)</label>
              <input id="deadline" type="datetime-local" className="control mt-1"
                     value={new Date(draft.deadline * 1000).toISOString().slice(0, 16)}
                     onChange={(e) =>
                       set("deadline", Math.floor(new Date(`${e.target.value}Z`).getTime() / 1000))} />
              {problem("deadline")}
            </div>
            <div>
              <label className="label" htmlFor="recovery">Recovery window, in hours</label>
              <input id="recovery" className="control mt-1" value={draft.recoveryHours}
                     onChange={(e) => set("recoveryHours", e.target.value)} />
              <p className="mt-1 text-xs text-[var(--muted)]">
                If nobody finishes the protocol, this is when the frozen rule ends it.
              </p>
              {problem("recoveryHours")}
            </div>
          </div>

          <fieldset className="grid gap-3 rounded-sm border border-[var(--border)] p-3">
            <legend className="px-1">
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={draft.economic}
                       onChange={(e) => set("economic", e.target.checked)} />
                This protocol carries an economic consequence
              </label>
            </legend>
            {draft.economic ? (
              <>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className="label" htmlFor="reward">Reward held, in GEN</label>
                    <input id="reward" className="control mt-1" value={draft.reward}
                           onChange={(e) => set("reward", e.target.value)} />
                    {problem("reward")}
                  </div>
                  <div>
                    <label className="label" htmlFor="bond">Bond from the submitter, in GEN</label>
                    <input id="bond" className="control mt-1" value={draft.bond}
                           onChange={(e) => set("bond", e.target.value)} />
                    {problem("bond")}
                  </div>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className="label" htmlFor="verified-pct">Verified releases, %</label>
                    <input id="verified-pct" className="control mt-1" value={draft.verifiedPct}
                           onChange={(e) => set("verifiedPct", e.target.value)} />
                    {problem("verifiedPct")}
                  </div>
                  <div>
                    <label className="label" htmlFor="partial-pct">Partially verified releases, %</label>
                    <input id="partial-pct" className="control mt-1" value={draft.partialPct}
                           onChange={(e) => set("partialPct", e.target.value)} />
                    {problem("partialPct")}
                  </div>
                </div>
                <div className="grid gap-3 sm:grid-cols-3">
                  {([["notVerifiedAction", "If not verified"],
                     ["inconclusiveAction", "If inconclusive"],
                     ["timeoutAction", "If nobody finishes it"]] as const).map(([key, label]) => (
                    <div key={key}>
                      <label className="label" htmlFor={key}>{label}</label>
                      <select id={key} className="control mt-1" value={draft[key]}
                              onChange={(e) => set(key, e.target.value)}>
                        {ACTIONS.map((action) => (
                          <option key={action} value={action}>{words(ACTION_WORDS, action)}</option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-[var(--muted)]">
                  These shares are frozen with the protocol. No model output reaches this
                  arithmetic: only the name of the result does.
                </p>
              </>
            ) : (
              <p className="text-sm text-[var(--muted)]">
                Verification is the product; money is optional. Without a consequence, TRACE records
                the result and nothing moves.
              </p>
            )}
          </fieldset>

          <div className="flex flex-wrap gap-2">
            <button type="button" className="btn" onClick={() => setStage("Requirements")}>Back</button>
            <button type="button" className="btn btn-primary" disabled={running}
                    onClick={() => writeDraft("Review and freeze")}>
              Save the draft on chain
            </button>
          </div>
          <TxPanel state={tx} done="The draft is written. Nothing is frozen yet." />
        </section>
      ) : null}

      {stage === "Review and freeze" ? (
        <section className="card grid gap-4 p-4">
          <h2 className="label">04 · Review and freeze {protocolId ? `· ${protocolId}` : ""}</h2>

          <div className="grid gap-1">
            <h3 className="text-[17px]">{draft.title}</h3>
            <p className="text-sm text-[var(--muted)]">{draft.subject} · {draft.subjectType}</p>
            <p className="mt-1 text-sm">{draft.description}</p>
          </div>

          <div>
            <h3 className="label">Requirements ({draft.requirements.length})</h3>
            <ul className="mt-2 grid gap-2">
              {draft.requirements.map((requirement) => (
                <li key={requirement.requirementId} className="text-sm">
                  <span className="mono mr-2 text-xs text-[var(--muted)]">
                    {requirement.requirementId}
                  </span>
                  {requirement.description}
                  <span className="ml-2 text-xs text-[var(--muted)]">
                    {requirement.mandatory ? "mandatory" : "optional"}
                    {Number(requirement.minSources) > 1
                      ? ` · ${requirement.minSources} independent publishers`
                      : ""}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          <div className="grid gap-1 text-sm text-[var(--muted)]">
            <h3 className="label">Evidence policy</h3>
            <p>
              At least {draft.minimumSources} independent publisher
              {draft.minimumSources === "1" ? "" : "s"}.
              {draft.allowedDomains.trim() ? ` Only from ${draft.allowedDomains}.` : " Any publisher."}
              {draft.requiredSourceTypes.length > 0
                ? ` Must include ${draft.requiredSourceTypes.join(", ").toLowerCase()}.`
                : ""}
            </p>
            <p>Evidence is due {formatTime(draft.deadline)}.</p>
            <p>
              If nobody finishes it, the frozen rule ends the protocol{" "}
              {draft.recoveryHours} hours after that.
            </p>
          </div>

          {draft.economic ? (
            <div className="grid gap-1 text-sm text-[var(--muted)]">
              <h3 className="label">Consequence</h3>
              <p>{draft.reward} GEN held, bond {draft.bond} GEN.</p>
              <p>
                Verified releases {draft.verifiedPct}%, partially verified {draft.partialPct}%.
                Not verified: {words(ACTION_WORDS, draft.notVerifiedAction)}, and the bond is
                forfeit.
              </p>
            </div>
          ) : null}

          <p className="rounded-sm border border-[var(--warning)] p-3 text-sm">
            Once activated, these verification rules cannot be changed — by you, by anyone, for any
            reason. The fingerprint recorded at that moment is what every later result points back
            at.
          </p>

          <div className="flex flex-wrap gap-2">
            <button type="button" className="btn" onClick={() => setStage("Evidence policy")}>
              Back
            </button>
            <button type="button" className="btn btn-primary" disabled={running || !protocolId}
                    onClick={freeze}>
              Freeze this protocol
            </button>
          </div>
          <TxPanel state={tx} done="Frozen. The protocol is open for evidence." />
        </section>
      ) : null}
    </div>
  );
}
