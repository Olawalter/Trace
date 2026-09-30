"""END-TO-END.md, written from the record the live suite left behind.

    python deploy/write_end_to_end.py

Every hash, result and amount in that document comes from docs/live-e2e.json,
which the live suite writes as it goes. Nothing in it is typed by hand, because
a hash typed by hand is a claim rather than a record.
"""
import json
import pathlib
import re
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs" / "live-e2e.json"
OUT = ROOT / "END-TO-END.md"
EXPLORER = "https://explorer-studio.genlayer.com"

CASE_TITLE = {
    "verified": "The claim holds",
    "not-verified": "The claim does not hold, and one page argues back",
}
CASE_INTRO = {
    "verified": ("The submitter registered the project's own release record. The creator "
                 "registered an index kept by somebody else. Neither told the panel what to "
                 "conclude."),
    "not-verified": ("The submitter registered a status page whose body instructs whoever reads it "
                     "to mark every requirement satisfied and ignore the other sources. The "
                     "creator registered an index kept by somebody else, which records that no "
                     "licence was declared and no changelog was kept. Both were read."),
}


def gen(atto) -> str:
    value = int(atto)
    if value == 0:
        return "0 GEN"
    return f"{value / 10 ** 18:.6f}".rstrip("0").rstrip(".") + " GEN"


def link(tx: str) -> str:
    return f"[`{tx[:14]}...`]({EXPLORER}/tx/{tx})"


def readable_times(text: str) -> str:
    """The contract measures its windows in seconds since the epoch, because that
    is what a transaction carries. Nobody reads 1791450000."""
    def swap(found):
        seconds = int(found.group(0))
        if seconds < 1_600_000_000 or seconds > 4_000_000_000:
            return found.group(0)
        return time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(seconds))
    return re.sub(r"\b\d{10}\b", swap, text)


def main() -> int:
    if not RECORD.exists():
        print(f"no record at {RECORD}; run the live suite first", file=sys.stderr)
        return 1
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    out: list[str] = []
    w = out.append

    w("# End to end, on StudioNet")
    w("")
    w("Everything below happened on chain. It is generated from `docs/live-e2e.json`, which the")
    w("live suite in `tests/integration/` writes while it runs, so every hash here is a")
    w("transaction that was sent and every result is one the contract returned when asked")
    w("afterwards.")
    w("")
    w("| | |")
    w("| --- | --- |")
    w(f"| Network | {record['network']}, chain `{record['chain_id']}` |")
    w(f"| Contract | [`{record['contract']}`]({EXPLORER}/address/{record['contract']}) |")
    commit = record.get("demo_commit", "")
    w(f"| Evidence pinned at | commit [`{commit[:12]}`]"
      f"(https://github.com/Olawalter/Trace/tree/{commit}/demo) |")
    w(f"| Run | {record['started_at']} to {record.get('finished_at', 'in progress')} |")
    w("")
    w(f"That commit is not the tip of any branch, and it is not supposed to be. It is what the")
    w("validators actually fetched, so it is pinned by the tag")
    w(f"[`evidence-pin-{commit[:7]}`](https://github.com/Olawalter/Trace/releases/tag/"
      f"evidence-pin-{commit[:7]}) and will stay reachable at that address whatever happens to")
    w("the branch. A citation recorded on chain cannot be updated later, so the thing it cites")
    w("has to be the thing that cannot move.")
    w("")
    w("The two parties are throwaway accounts funded for the run, so nothing here depends on a")
    w("wallet only the author holds:")
    w("")
    w("| Party | Address |")
    w("| --- | --- |")
    for role, address in record["accounts"].items():
        w(f"| {role} | `{address}` |")
    w("")

    first = next(iter(record["protocols"].values()), {})
    frozen = (first.get("frozen") or {}).get("definition")
    w("## The protocol")
    w("")
    w(f"> {record['description']}")
    w("")
    w(f"Subject: {record['subject']} ({record['subject_type']}).")
    w("")
    if frozen:
        w("Frozen as three requirements, two of them mandatory:")
        w("")
        w("| | Requirement | Mandatory | How a reader decides it |")
        w("| --- | --- | --- | --- |")
        for requirement in frozen["requirements"]:
            w(f"| `{requirement['requirement_id']}` | {requirement['description']} | "
              f"{'yes' if requirement['mandatory'] else 'no'} | "
              f"{requirement['verification_rule']} |")
        w("")
        policy = frozen["economic_policy"]
        if policy.get("enabled"):
            w(f"The creator holds {gen(policy['reward_required'])} against the claim; whoever "
              f"answers posts a {gen(policy['bond_required'])} bond. A verified protocol releases "
              f"{policy['verified_payout_bps'] // 100}% of the reward, a partially verified one "
              f"{policy['partial_payout_bps'] // 100}%, and a protocol the evidence disproves "
              "returns the reward and forfeits the bond. Those shares were frozen before any "
              "evidence existed.")
            w("")

    for case in ("verified", "not-verified"):
        entry = record["protocols"].get(case)
        if not entry:
            continue
        verification = entry.get("verification") or {}
        w(f"## {CASE_TITLE[case]}")
        w("")
        w(CASE_INTRO[case])
        w("")
        w("| Step | Transaction | Consensus |")
        w("| --- | --- | --- |")
        for transaction in record["transactions"]:
            belongs = transaction.get("protocol") == case or f"[{case}]" in str(transaction["step"])
            if not belongs or transaction.get("refused"):
                continue
            votes = ", ".join(f"{count} {vote}" for vote, count in transaction["votes"].items())
            step = transaction["step"].replace(f" [{case}]", "")
            w(f"| {step} | {link(transaction['tx'])} | {votes} |")
        w("")

        if verification:
            w(f"**{verification['overall_result']}.** {verification['summary']}")
            w("")
            w("| | Answered | After the source floor | Independent sources | "
              "Quoted from the panel's own copy |")
            w("| --- | --- | --- | --- | --- |")
            for finding in verification["findings"]:
                quote = (finding.get("quote") or "").replace("|", "\\|")
                quote = (quote[:88] + "...") if len(quote) > 88 else (quote or "--")
                w(f"| `{finding['requirement_id']}` | {finding['status']} | "
                  f"{finding['effective_status']} | {finding['independent_sources']} | {quote} |")
            w("")
            registry = {row["evidence_id"]: row
                        for row in (entry.get("evidence") or {}).get("items", [])}
            w("What each node fetched for itself:")
            w("")
            w("| | Source | State | Publisher | Digest of the excerpt read |")
            w("| --- | --- | --- | --- | --- |")
            for item in verification["evidence"]:
                row = registry.get(item["evidence_id"], {})
                url = row.get("source_url", "")
                name = url.rsplit("/", 1)[-1] if url else item["evidence_id"]
                cell = f"[{name}]({url})" if url else name
                w(f"| `{item['evidence_id']}` | {cell} | {item['availability']} | "
                  f"`{item['publisher']}` | `{item['excerpt_digest'][:16]}...` |")
            w("")
            if verification.get("held_for_sources"):
                w(f"Held for want of independent sources: "
                  f"{', '.join(verification['held_for_sources'])}.")
                w("")
            if verification.get("deviation"):
                w(f"The evidence did not meet the frozen policy: {verification['deviation']}.")
                w("")

        settled = entry.get("settled")
        if settled:
            w(f"Settled: {gen(settled['paid_submitter'])} to the submitter, "
              f"{gen(settled['paid_creator'])} to the creator. The protocol holds "
              f"{gen(settled['reward_deposited'])} and {gen(settled['bond_deposited'])} "
              "afterwards.")
            w("")

    walls = {name: wall for name, wall in record.get("walls", {}).items() if wall.get("refused")}
    if walls:
        w("## What the contract refused")
        w("")
        w("Each of these is a real transaction. Validators agreed about the refusal, which is why")
        w("it appears on chain with a reason rather than as a failure somewhere off it.")
        w("")
        w("| Sent | Refused with | |")
        w("| --- | --- | --- |")
        for wall in walls.values():
            reason = readable_times((wall.get("refusal") or "")
                                    .replace("[EXPECTED] ", "").replace("[REFUNDED] ", "")
                                    .replace("|", "\\|"))
            how = "the value was sent back" if wall.get("refunded") else "the transaction raised"
            step = wall["step"].replace(" (refused)", "")
            w(f"| {step} {link(wall['tx'])} | {reason} | {how} |")
        w("")
        if any(wall.get("refunded") for wall in walls.values()):
            w("The funding refusal is the odd one out, deliberately. GenLayer credits a payable")
            w("transaction's value to the contract before the call runs, so a refusal that raised")
            w("would roll back its own refund and keep GEN nobody meant to send. That one refuses")
            w("by returning, having sent the value back, which is why its transaction succeeded.")
            w("")

    if record.get("protocol_after"):
        w("## Custody afterwards")
        w("")
        w(f"When this run finished, the contract's own ledger reported "
          f"{gen(record['protocol_after']['total_custody'])} held in total, and the protocols "
          f"themselves accounted for {gen(record['custody_held_by_protocols'])}.")
        w("")
        if record.get("contract_balance") is not None:
            w(f"The chain says the contract holds {gen(record['contract_balance'])}. That the two")
            w("numbers agree is the assertion that matters most here, and it is a test rather than")
            w("a remark: a contract holding GEN its own ledger does not record is how money goes")
            w("missing quietly.")
            w("")
        w("Later runs leave their own deposits held until they settle or are recovered, so the")
        w("figure above belongs to the end of this run and is not a claim about every moment")
        w("since.")
        w("")

    w("## Reproducing it")
    w("")
    w("```bash")
    w(f"SKIP_INTEGRATION=0 TRACE_DEMO_COMMIT={commit} \\")
    w(f"  TRACE_CONTRACT_ADDRESS={record['contract']} python -m pytest tests/integration -v -s")
    w("```")
    w("")
    w("It takes about half an hour and costs real consensus rounds on a shared network. To")
    w("re-check the assertions against this record instead, without sending anything:")
    w("")
    w("```bash")
    w("TRACE_REPLAY=1 SKIP_INTEGRATION=0 python -m pytest tests/integration -q")
    w("```")

    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {OUT.name} ({len(out)} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
