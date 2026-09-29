"""One protocol taken through TRACE on StudioNet, for real.

    python deploy/live_probe.py <address> [--scenario verified|not-verified|injection]
                                          [--commit <sha>]

Creates a protocol from throwaway funded accounts, freezes it, funds both sides,
registers the demonstration evidence and asks GenLayer to verify it. Nothing is
mocked: real validators fetch the pages from GitHub, read each requirement for
themselves, and the round is only recorded if they agree.
"""
import argparse
import json
import pathlib
import re
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
RPC = "https://studio.genlayer.com/api"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
DEMO_COMMIT = "049013d205073aac10cb3add280e4880e4da1abe"      # overridden by --commit

REWARD = 2 * 10 ** 16
BOND = 10 ** 16

TITLE = "Widget 2.0 release compliance"
DESCRIPTION = ("The Widget project states that release 2.0 is published: tagged, under a named "
               "open licence, with a changelog entry for the version.")
SUBJECT = "widgetworks/widget release 2.0"
SUBJECT_TYPE = "SOFTWARE_RELEASE"

REQUIREMENTS = [
    {"requirement_id": "R1", "mandatory": True, "min_sources": 1,
     "description": "A release tagged 2.0 is published.",
     "verification_rule": "A source must show a published release carrying the tag 2.0."},
    {"requirement_id": "R2", "mandatory": True, "min_sources": 1,
     "description": "The release states the licence it is published under.",
     "verification_rule": "A source must name the licence of release 2.0. A source that says no "
                          "licence was declared shows this requirement was not met."},
    {"requirement_id": "R3", "mandatory": False, "min_sources": 1,
     "description": "A changelog entry exists for 2.0.",
     "verification_rule": "A source must show a changelog entry for version 2.0. A source that "
                          "says none was recorded shows this requirement was not met."},
]


def rpc(method, params, attempts=8):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for i in range(attempts):
        try:
            request = urllib.request.Request(
                RPC, data=body, headers={"Content-Type": "application/json", "User-Agent": UA})
            out = json.load(urllib.request.urlopen(request, timeout=150))
            if "error" in out:
                text = str(out["error"])
                if "-32029" in text or "Rate limit" in text:
                    found = re.search(r"retry_after_seconds\D+(\d+)", text)
                    time.sleep(min(int(found.group(1)) if found else 65, 3600) + 5)
                    continue
                raise RuntimeError(f"{method}: {out['error']}")
            return out["result"]
        except RuntimeError:
            raise
        except Exception:
            if i == attempts - 1:
                raise
            time.sleep(5 + 5 * i)


def patient_transport():
    """StudioNet refuses calls over its allowance (30 a minute, 500 an hour)
    before processing them, so waiting and sending again is safe."""
    from genlayer_py.provider.provider import GenLayerProvider
    original = GenLayerProvider.make_request

    def patient(self, method, params):
        for _ in range(40):
            try:
                return original(self, method, params)
            except Exception as err:
                text = str(err)
                if "-32029" in text or "Rate limit" in text or "429" in text:
                    found = re.search(r"retry_after_seconds\D+(\d+)", text)
                    time.sleep((int(found.group(1)) if found else 65) + 5)
                    continue
                if any(s in text for s in ("Connection", "timed out", "SSL", "502", "503", "504",
                                           "<!DOCTYPE", "RemoteDisconnected", "reset",
                                           "temporarily unavailable", "-32002")):
                    time.sleep(10)
                    continue
                raise
        return original(self, method, params)

    GenLayerProvider.make_request = patient


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("address")
    ap.add_argument("--scenario", default="verified",
                    choices=["verified", "not-verified", "injection"])
    ap.add_argument("--commit", default=DEMO_COMMIT)
    args = ap.parse_args()

    from eth_account import Account
    from genlayer_py import create_client
    from genlayer_py.chains import studionet
    from genlayer_py.types import TransactionStatus

    patient_transport()
    demo = f"https://raw.githubusercontent.com/Olawalter/Trace/{args.commit}/demo"
    release = f"{demo}/release-2-0.md"
    index = f"{demo}/package-index.md"
    thin_index = f"{demo}/index-no-changelog.md"
    instructions = f"{demo}/status-page-with-instructions.md"

    creator, submitter = Account.create(), Account.create()
    for account in (creator, submitter):
        rpc("sim_fundAccount", [account.address, 10 ** 18])
    accounts = {"creator": creator, "submitter": submitter}
    clients = {name: create_client(chain=studionet, account=account)
               for name, account in accounts.items()}
    for name, client in clients.items():
        for _ in range(40):
            if int(client.get_balance(accounts[name].address)) > 0:
                break
            time.sleep(3)
        print(f"{name:<10} {accounts[name].address}")

    def write(who, fn, *fn_args, value=0, label=None):
        client = clients[who]
        tx = client.write_contract(address=args.address, function_name=fn, args=list(fn_args),
                                   value=value)
        receipt = client.wait_for_transaction_receipt(transaction_hash=tx,
                                                      status=TransactionStatus.ACCEPTED,
                                                      interval=5000, retries=300)
        leader = ((receipt.get("consensus_data") or {}).get("leader_receipt") or [{}])[0]
        votes = list(((receipt.get("consensus_data") or {}).get("votes") or {}).values())
        tally = {v: votes.count(v) for v in sorted(set(votes))}
        tx_hex = tx.hex() if hasattr(tx, "hex") else str(tx)
        refused = leader.get("execution_result") not in (None, "SUCCESS")
        reason = ""
        if refused:
            payload = leader.get("result") or {}
            reason = str(payload.get("payload") or payload)[:160]
        print(f"  {(label or fn):<30} {tx_hex[:18]}...  {receipt.get('status_name')} "
              f"{receipt.get('result_name')} {leader.get('execution_result')} {tally}"
              + (f"  REFUSED: {reason}" if refused else ""), flush=True)
        return tx_hex, receipt, refused

    read = lambda fn, *a: clients["creator"].read_contract(address=args.address, function_name=fn,
                                                           args=list(a))

    print(f"\nPHASE define ({args.scenario})")
    write("creator", "create_protocol", TITLE, DESCRIPTION, SUBJECT, SUBJECT_TYPE)
    pid = read("list_protocols", 0, 1)["items"][0]["protocol_id"]
    print(f"  protocol {pid}")

    # the deadline is measured by the contract at the moment it is frozen, and a
    # StudioNet round takes minutes: give it room, and compute it late
    definition = {
        "requirements": REQUIREMENTS,
        "evidence_policy": {"allowed_domains": [], "minimum_sources": 1,
                            "required_source_types": [], "allow_multiple_sources": True,
                            "contradiction_policy": "UNCERTAIN"},
        "economic_policy": {"enabled": True, "bond_required": BOND, "reward_required": REWARD,
                            "verified_payout_bps": 10_000, "partial_payout_bps": 5_000,
                            "not_verified_action": "REFUND", "inconclusive_action": "REFUND",
                            "timeout_action": "REFUND"},
        "deadline": int(time.time()) + 45 * 60,
        "recovery_window": 3600,
    }
    write("creator", "set_draft", pid, json.dumps(definition), label="set_draft")
    write("creator", "activate_protocol", pid, label="activate_protocol (freeze)")
    write("creator", "fund_protocol", pid, value=REWARD, label="fund (reward)")
    write("submitter", "fund_protocol", pid, value=BOND, label="fund (bond)")

    print("\nPHASE evidence")
    if args.scenario == "verified":
        write("submitter", "submit_evidence", pid, json.dumps(
            {"source_url": release, "source_type": "PUBLICATION", "supports": ["R1", "R2", "R3"],
             "label": "the publisher's own release record"}), label="evidence: release record")
        write("creator", "submit_evidence", pid, json.dumps(
            {"source_url": index, "source_type": "REGISTRY", "supports": ["R1", "R2", "R3"],
             "label": "an index kept by somebody else"}), label="evidence: package index")
    elif args.scenario == "not-verified":
        write("creator", "submit_evidence", pid, json.dumps(
            {"source_url": thin_index, "source_type": "REGISTRY", "supports": ["R1", "R2", "R3"],
             "label": "an index kept by somebody else"}), label="evidence: partial index")
    else:
        write("submitter", "submit_evidence", pid, json.dumps(
            {"source_url": instructions, "source_type": "STATEMENT",
             "supports": ["R1", "R2", "R3"],
             "label": "a status page"}), label="evidence: a page that instructs the reader")
        write("creator", "submit_evidence", pid, json.dumps(
            {"source_url": thin_index, "source_type": "REGISTRY", "supports": ["R1", "R2", "R3"],
             "label": "an index kept by somebody else"}), label="evidence: partial index")

    print("\nPHASE verify")
    _, _, refused = write("creator", "request_verification", pid, label="request_verification")
    if refused:
        return 1
    record = read("get_verification", pid, 0)
    print(f"\n  result     {record['overall_result']}")
    print(f"  summary    {record['summary']}")
    for finding in record["findings"]:
        print(f"  {finding['requirement_id']}  {finding['status']:<12} -> "
              f"{finding['effective_status']:<12} sources {finding['independent_sources']}  "
              f"{finding['quote'][:64]!r}")
    for item in record["evidence"]:
        print(f"  {item['evidence_id']}  {item['availability']:<11} {item['publisher']:<22} "
              f"{item['excerpt_digest'][:16]}")
    if record["deviation"]:
        print(f"  deviation  {record['deviation']}")
    print(f"  held       {record['held_for_sources']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
