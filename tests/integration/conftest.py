"""The live StudioNet suite: one protocol taken through TRACE for real.

Nothing here is mocked. Validators fetch the demonstration pages from GitHub,
read each requirement for themselves, and must agree before anything is
recorded; the GEN moves on the chain.

    SKIP_INTEGRATION=0 TRACE_DEMO_COMMIT=<sha> python -m pytest tests/integration -v -s

It is skipped by default: a full run is real consensus rounds on a shared public
network and takes about half an hour. Every phase runs once, however many tests
ask for it, and the record is written to docs/live-e2e.json, which the
end-to-end document is generated from -- so no hash in the documentation is
typed by hand.

TRACE_REPLAY=1 re-checks the assertions against an earlier run's record and the
protocols it left on the chain, without sending anything. It proves nothing new;
it makes a wrong test cheap to fix.
"""
import json
import os
import pathlib
import re
import time

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
RECORD = ROOT / "docs" / "live-e2e.json"
RPC = "https://studio.genlayer.com/api"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")
LIVE = os.environ.get("SKIP_INTEGRATION", "1") == "0"
REPLAY = os.environ.get("TRACE_REPLAY") == "1"

from scenario import (BOND, DEMO_COMMIT, REQUIREMENTS, REWARD, definition, evidence,  # noqa: E402
                      DESCRIPTION, SUBJECT, SUBJECT_TYPE, TITLE, source)

ACCEPTANCE_DELAY = 300


def rpc(method, params, attempts=8):
    import urllib.request
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                RPC, data=body, headers={"Content-Type": "application/json", "User-Agent": UA})
            out = json.load(urllib.request.urlopen(request, timeout=150))
            if "error" in out:
                wait = _rate_limited(str(out["error"]))
                if wait:
                    time.sleep(wait)
                    continue
                raise RuntimeError(f"{method}: {out['error']}")
            return out["result"]
        except RuntimeError:
            raise
        except Exception:
            if attempt == attempts - 1:
                raise
            time.sleep(5 + 5 * attempt)


def _rate_limited(text: str) -> int:
    """StudioNet refuses a call over its allowance before processing it, so
    waiting and sending again is safe rather than a retry of real work."""
    if "-32029" not in text and "Rate limit" not in text and "429" not in text:
        return 0
    found = re.search(r"retry_after_seconds\D+(\d+)", text)
    if found:
        return min(int(found.group(1)), 3600) + 5
    return 65 if "per minute" in text else 300


def _patient_transport():
    from genlayer_py.provider.provider import GenLayerProvider
    original = GenLayerProvider.make_request

    def patient(self, method, params):
        attempts = 0
        while attempts < 10:
            try:
                return original(self, method, params)
            except Exception as err:
                text = str(err)
                wait = _rate_limited(text)
                if wait:
                    time.sleep(wait)
                    continue                       # a refusal by the limiter is not an attempt
                if not any(s in text for s in ("Connection", "timed out", "SSL", "502", "503",
                                               "504", "<!DOCTYPE", "RemoteDisconnected", "reset",
                                               "temporarily unavailable", "-32002")):
                    raise
                attempts += 1
                time.sleep(5 + 5 * attempts)
        return original(self, method, params)

    GenLayerProvider.make_request = patient


def _hex(tx) -> str:
    return tx.hex() if hasattr(tx, "hex") else str(tx)


def _returned(leader) -> str:
    """The leader's return value as text. Three shapes turn up for the same
    value, so this looks through whatever came back rather than guessing which
    client produced it."""
    import base64
    result = leader.get("result")
    if result is None:
        return ""
    blob = json.dumps(result, default=str)
    if "[REFUNDED]" in blob:
        text = blob[blob.index("[REFUNDED]"):]
        for stop in ('\\"', '"', "\\n"):
            if stop in text:
                text = text[:text.index(stop)]
        return text.strip()
    raw = result.get("raw") if isinstance(result, dict) else result
    if isinstance(raw, str):
        try:
            decoded = base64.b64decode(raw, validate=True)
        except Exception:
            return ""
        return "".join(chr(b) if 32 <= b < 127 else " " for b in decoded).strip()
    return ""


class Live:
    """One live session: two funded throwaway parties, and the record of what
    happened to them."""

    def __init__(self, funded=True):
        from eth_account import Account
        from genlayer_py import create_client
        from genlayer_py.chains import studionet

        _patient_transport()
        self.address = os.environ.get("TRACE_CONTRACT_ADDRESS") or json.loads(
            (ROOT / "docs" / "deployment.json").read_text(encoding="utf-8"))["contract_address"]
        # three, deliberately: the account that writes the protocol, the account
        # that answers for it and posts the bond, and the account that only
        # registers evidence. Money reaching the right one of them is the thing
        # this suite is for, and two accounts cannot show it
        self.creator = Account.create()
        self.responsible = Account.create()
        self.submitter = Account.create()
        self.accounts = {"creator": self.creator, "responsible": self.responsible,
                         "submitter": self.submitter}
        self.clients = {name: create_client(chain=studionet, account=account)
                        for name, account in self.accounts.items()}
        if funded:                                 # a replay only reads; it signs nothing
            for account in self.accounts.values():
                rpc("sim_fundAccount", [account.address, 10 ** 18])
            for name, client in self.clients.items():
                for _ in range(40):
                    if int(client.get_balance(self.accounts[name].address)) > 0:
                        break
                    time.sleep(3)
        self.record = {
            "network": "GenLayer StudioNet", "chain_id": 61999, "contract": self.address,
            "demo_commit": DEMO_COMMIT, "title": TITLE, "description": DESCRIPTION,
            "subject": SUBJECT, "subject_type": SUBJECT_TYPE,
            "accounts": {name: account.address for name, account in self.accounts.items()},
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "transactions": [], "protocols": {}, "walls": {},
        }

    # -- acts ----------------------------------------------------------------
    def write(self, who, fn, *args, value=0, step=None, protocol=None):
        from genlayer_py.types import TransactionStatus
        client = self.clients[who]
        tx = client.write_contract(address=self.address, function_name=fn, args=list(args),
                                   value=value)
        receipt = client.wait_for_transaction_receipt(transaction_hash=tx,
                                                      status=TransactionStatus.ACCEPTED,
                                                      interval=5000, retries=300)
        leader = ((receipt.get("consensus_data") or {}).get("leader_receipt") or [{}])[0]
        votes = list(((receipt.get("consensus_data") or {}).get("votes") or {}).values())
        entry = {
            "step": step or fn, "function": fn, "caller": who, "protocol": protocol,
            "tx": _hex(tx), "value": value, "status": receipt.get("status_name"),
            "consensus": receipt.get("result_name"), "execution": leader.get("execution_result"),
            "votes": {v: votes.count(v) for v in sorted(set(votes))},
            "refused": leader.get("execution_result") not in (None, "SUCCESS"),
        }
        if entry["refused"]:
            payload = leader.get("result") or {}
            entry["refusal"] = str(payload.get("payload") or payload)[:200]
        else:
            # funding refuses by returning, so a successful transaction can still
            # be a refusal; the value came back with it
            returned = _returned(leader)
            if "[REFUNDED]" in returned:
                entry.update({"refused": True, "refunded": True,
                              "refusal": returned[returned.index("[REFUNDED]"):][:200]})
        self.record["transactions"].append(entry)
        print(f"  {entry['step']:<38} {entry['tx'][:16]}...  {entry['status']} "
              f"{entry['consensus']} {entry['execution']} {entry['votes']}"
              + (f"  REFUSED: {entry.get('refusal', '')[:80]}" if entry["refused"] else ""),
              flush=True)
        return entry

    def read(self, fn, *args):
        return self.clients["creator"].read_contract(address=self.address, function_name=fn,
                                                     args=list(args))

    def contract_balance(self) -> int:
        """What the chain says TRACE holds, which is a different question from
        what TRACE's own ledger says it holds. The two must agree."""
        out = rpc("eth_getBalance", [self.address, "latest"])
        return int(out, 16) if isinstance(out, str) else int(out)

    def wait_for_finality(self, tx_hash, why=""):
        """GEN that a contract sends leaves it when the transaction FINALIZES,
        not when it is accepted. Anything comparing the chain's balance against
        the ledger has to wait for that, or it compares two different moments
        and calls the difference a leak."""
        from genlayer_py.types import TransactionStatus
        print(f"  ... waiting for {why or 'finality'}", flush=True)
        self.clients["creator"].wait_for_transaction_receipt(
            transaction_hash=tx_hash, status=TransactionStatus.FINALIZED,
            interval=5000, retries=300)

    def tx_facts(self, tx_hash):
        tx = rpc("eth_getTransactionByHash", [tx_hash]) or {}
        votes = list(((tx.get("consensus_data") or {}).get("votes") or {}).values())
        return {"status": tx.get("status"), "consensus": tx.get("result_name"),
                "votes": {v: votes.count(v) for v in sorted(set(votes))}}

    def sleep_until(self, unix_seconds, why=""):
        wait = int(unix_seconds) - int(time.time()) + 5
        if wait > 0:
            print(f"  ... waiting {wait}s of real time {why}", flush=True)
            time.sleep(wait)

    def save(self):
        self.record["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        RECORD.parent.mkdir(parents=True, exist_ok=True)
        RECORD.write_text(json.dumps(self.record, indent=2, default=str) + "\n", encoding="utf-8")


class World:
    """The phases, each run once however many tests ask for them."""

    def __init__(self, live: Live):
        self.live = live
        self.done = set()
        self.failed = {}
        self.ids = {}
        self.replaying = REPLAY
        if self.replaying:
            if not RECORD.exists():
                pytest.skip(f"TRACE_REPLAY needs an earlier run's record at {RECORD}")
            self.live.record = json.loads(RECORD.read_text(encoding="utf-8"))
            self.ids = {case: entry["protocol_id"]
                        for case, entry in self.live.record["protocols"].items()}
            print(f"replaying {RECORD} from {self.live.record.get('started_at')}", flush=True)

    def _once(self, name, run):
        if self.replaying:
            return
        if name in self.failed:
            raise RuntimeError(f"phase {name} already failed: {self.failed[name]}")
        if name in self.done:
            return
        print(f"\nPHASE {name}", flush=True)
        try:
            run()
        except Exception as err:
            self.failed[name] = f"{type(err).__name__}: {err}"
            raise
        finally:
            self.live.save()
        self.done.add(name)

    def protocol(self, case):
        return self.live.read("get_protocol", self.ids[case])

    def verification(self, case, index=0):
        return self.live.read("get_verification", self.ids[case], index)

    # -- define and freeze ---------------------------------------------------
    def frozen(self):
        def run():
            live = self.live
            for case in ("verified", "not-verified"):
                live.write("creator", "create_protocol", TITLE, DESCRIPTION, SUBJECT, SUBJECT_TYPE,
                           step=f"create_protocol [{case}]")
                mine = live.read("list_by_creator", live.creator.address, 0, 50)["items"]
                pid = mine[-1]["protocol_id"]
                self.ids[case] = pid
                live.record["protocols"][case] = {"protocol_id": pid}
                live.write("creator", "set_draft", pid, definition(responsible_party=live.responsible.address),
                           step=f"set_draft [{case}]", protocol=case)
                live.write("creator", "activate_protocol", pid,
                           step=f"activate_protocol [{case}]", protocol=case)
                live.record["protocols"][case]["frozen"] = live.read("get_protocol", pid)

            pid = self.ids["verified"]
            live.record["walls"]["write_after_freezing"] = live.write(
                "creator", "set_draft", pid, definition(responsible_party=live.responsible.address),
                step="rewrite a frozen protocol (refused)")
            live.record["walls"]["freeze_twice"] = live.write(
                "creator", "activate_protocol", pid, step="freeze it a second time (refused)")
            live.record["walls"]["stranger_accepts"] = live.write(
                "submitter", "accept_protocol", self.ids["verified"],
                step="accept on the responsible party's behalf (refused)")
            for case in ("verified", "not-verified"):
                live.write("responsible", "accept_protocol", self.ids[case],
                           step=f"accept_protocol [{case}]", protocol=case)
                live.record["protocols"][case]["taken_on"] = live.read("get_protocol",
                                                                       self.ids[case])
            live.record["walls"]["stranger_freezes"] = live.write(
                "submitter", "activate_protocol", self.ids["not-verified"],
                step="freeze by somebody else (refused)")
            live.record["walls"]["verify_without_evidence"] = live.write(
                "creator", "request_verification", pid,
                step="verify with no evidence (refused)")
        self._once("define and freeze", run)

    # -- fund ----------------------------------------------------------------
    def funded(self):
        self.frozen()

        def run():
            live = self.live
            for case in ("verified", "not-verified"):
                pid = self.ids[case]
                live.write("creator", "fund_protocol", pid, value=REWARD,
                           step=f"deposit the reward [{case}]", protocol=case)
                live.write("responsible", "fund_protocol", pid, value=BOND,
                           step=f"post the bond [{case}]", protocol=case)
                live.record["protocols"][case]["funded"] = live.read("get_protocol", pid)
            live.record["walls"]["fund_twice"] = live.write(
                "creator", "fund_protocol", self.ids["verified"], value=REWARD,
                step="deposit the reward twice (refused)")
            live.record["protocols"]["verified"]["after_walls"] = live.read(
                "get_protocol", self.ids["verified"])
        self._once("fund", run)

    # -- evidence ------------------------------------------------------------
    def evidenced(self):
        self.funded()

        def run():
            live = self.live
            all_three = ["R1", "R2", "R3"]
            live.write("submitter", "submit_evidence", self.ids["verified"],
                       evidence(source("release-2-0"), all_three, "PUBLICATION",
                                "the publisher's own release record"),
                       step="evidence: the release record", protocol="verified")
            live.write("creator", "submit_evidence", self.ids["verified"],
                       evidence(source("package-index"), all_three, "REGISTRY",
                                "an index kept by somebody else"),
                       step="evidence: the package index", protocol="verified")

            live.write("submitter", "submit_evidence", self.ids["not-verified"],
                       evidence(source("status-page-with-instructions"), all_three, "STATEMENT",
                                "a status page"),
                       step="evidence: a page that instructs the reader",
                       protocol="not-verified")
            live.write("creator", "submit_evidence", self.ids["not-verified"],
                       evidence(source("index-no-changelog"), all_three, "REGISTRY",
                                "an index kept by somebody else"),
                       step="evidence: the partial index", protocol="not-verified")

            for case in ("verified", "not-verified"):
                live.record["protocols"][case]["evidence"] = live.read(
                    "list_evidence", self.ids[case], 0, 30)
            live.record["walls"]["same_address_twice"] = live.write(
                "submitter", "submit_evidence", self.ids["verified"],
                evidence(source("release-2-0"), ["R1"], "PUBLICATION", "the same page again"),
                step="the same address registered twice (refused)")
        self._once("evidence", run)

    # -- verify --------------------------------------------------------------
    def verified(self):
        self.evidenced()

        def run():
            live = self.live
            for case in ("verified", "not-verified"):
                self._round_until_agreed(case)
            live.record["walls"]["accept_early"] = live.write(
                "creator", "accept_verification", self.ids["not-verified"],
                step="accept before the delay (refused)")
        self._once("verify", run)

    # A round where the validators do not agree writes nothing at all. That is
    # TRACE working as designed, and on a shared network with mixed models it
    # happens: the grounded not-verified case splits the panel from time to
    # time. The suite used to assume agreement, so the next read asked for a
    # verification record that correctly did not exist and the whole run died
    # with a JSON-RPC error that said nothing about the cause. Now a failed
    # round is recorded and asked again, because anybody may ask again, and only
    # a run that cannot get an answer at all is a failure.
    ROUND_ATTEMPTS = 3

    def _round_until_agreed(self, case: str) -> None:
        live = self.live
        attempts = []
        for attempt in range(1, self.ROUND_ATTEMPTS + 1):
            suffix = "" if attempt == 1 else f", attempt {attempt}"
            entry = live.write("creator", "request_verification", self.ids[case],
                               step=f"request_verification [{case}]{suffix}", protocol=case)
            assert not entry["refused"], entry
            attempts.append({"tx": entry["tx"], "consensus": entry["consensus"],
                             "votes": entry["votes"]})
            if entry["consensus"] == "MAJORITY_AGREE":
                live.record["protocols"][case]["verification_tx"] = entry["tx"]
                live.record["protocols"][case]["verification_facts"] = live.tx_facts(entry["tx"])
                live.record["protocols"][case]["round_attempts"] = attempts
                record = self.verification(case)
                live.record["protocols"][case]["verification"] = record
                print(f"    -> {record['overall_result']}: {record['summary']}", flush=True)
                return
            print(f"    -> no majority ({entry['consensus']}, {entry['votes']}); nothing was "
                  f"written, asking again", flush=True)
        live.record["protocols"][case]["round_attempts"] = attempts
        raise AssertionError(
            f"the panel did not agree about [{case}] in {self.ROUND_ATTEMPTS} rounds: "
            f"{attempts}. Nothing was written, which is correct, but this run cannot go on.")

    # -- accept and finalize -------------------------------------------------
    def settled(self):
        self.verified()

        def run():
            live = self.live
            settling = []
            for case in ("verified", "not-verified"):
                record = self.verification(case)
                live.sleep_until(int(record["verified_at"]) + ACCEPTANCE_DELAY,
                                 why=f"for the acceptance delay [{case}]")
                live.write("submitter", "accept_verification", self.ids[case],
                           step=f"accept_verification [{case}]", protocol=case)
                live.record["protocols"][case]["accepted"] = live.read("get_protocol",
                                                                        self.ids[case])
                # all three, so the record can show not only that the right
                # accounts gained but that the wrong ones did not
                who_is_who = ("creator", "responsible", "submitter")
                before = {who: int(live.clients[who].get_balance(live.accounts[who].address))
                          for who in who_is_who}
                paying = live.write("submitter", "finalize_protocol", self.ids[case],
                                    step=f"finalize_protocol [{case}]", protocol=case)
                settling.append((case, paying["tx"]))
                live.record["protocols"][case]["settled"] = live.read("get_protocol",
                                                                       self.ids[case])
                # This case's window has to close before the next one opens.
                # The GEN leaves at finality, not at acceptance, so the wait is
                # required; and the two protocols pay opposite sides, so reading
                # both `after` values at the end would credit each case with the
                # other's payments and still look plausible.
                live.wait_for_finality(paying["tx"],
                                       why=f"the payout to settle on chain [{case}]")
                after = {who: int(live.clients[who].get_balance(live.accounts[who].address))
                         for who in who_is_who}
                live.record["protocols"][case]["balances_before"] = {k: str(v)
                                                                      for k, v in before.items()}
                live.record["protocols"][case]["balances_after"] = {k: str(v)
                                                                     for k, v in after.items()}
                live.record["protocols"][case]["settlement_deltas"] = {
                    k: str(after[k] - before[k]) for k in who_is_who}
            live.record["walls"]["finalize_twice"] = live.write(
                "submitter", "finalize_protocol", self.ids["verified"],
                step="finalize a second time (refused)")
            live.record["protocol_after"] = live.read("get_protocol_info")
            live.record["contract_balance"] = str(live.contract_balance())
            held = 0
            for protocol in live.read("list_protocols", 0, 50)["items"]:
                held += int(protocol["reward_deposited"]) + int(protocol["bond_deposited"])
            live.record["custody_held_by_protocols"] = str(held)
        self._once("accept and finalize", run)


@pytest.fixture(scope="session")
def world():
    if not LIVE:
        pytest.skip("live StudioNet suite; set SKIP_INTEGRATION=0 to run it (about half an hour)")
    if not DEMO_COMMIT and not REPLAY:
        pytest.skip("set TRACE_DEMO_COMMIT to the commit the demonstration pages are pinned at")
    live = Live(funded=not REPLAY)
    w = World(live)
    yield w
    if not w.replaying:
        live.save()
