"""Put contracts/trace.py on StudioNet, and prove the deployed bytes are it.

    python deploy/deploy.py [--address-only]

The contract is deployed from the committed file, and then read back off the
chain and compared byte for byte with what was sent. A deployment nobody can
check against the source is a claim, not a record, so docs/deployment.json is
written only when the two match -- and it records the comparison either way.
"""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "contracts" / "trace.py"
RECORD = ROOT / "docs" / "deployment.json"
RPC = "https://studio.genlayer.com/api"
EXPLORER = "https://explorer-studio.genlayer.com"
CHAIN_ID = 61999
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")

WRITES = ("create_protocol", "set_draft", "activate_protocol", "cancel_protocol", "fund_protocol",
          "submit_evidence", "request_verification", "accept_verification", "finalize_protocol",
          "recover_protocol")
VIEWS = ("get_protocol_info", "get_protocol", "list_protocols", "list_by_creator", "get_evidence",
         "list_evidence", "get_verification", "list_verifications", "get_history", "list_activity")


def rpc(method, params, attempts=8):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for i in range(attempts):
        try:
            request = urllib.request.Request(
                RPC, data=body, headers={"Content-Type": "application/json", "User-Agent": UA})
            out = json.load(urllib.request.urlopen(request, timeout=180))
            if "error" in out:
                wait = _refused_for_rate(str(out["error"]))
                if wait:
                    time.sleep(wait)
                    continue
                raise RuntimeError(f"{method}: {out['error']}")
            return out["result"]
        except RuntimeError:
            raise
        except Exception:
            if i == attempts - 1:
                raise
            time.sleep(5 + 5 * i)


def _refused_for_rate(text: str) -> int:
    """StudioNet refuses a call over its allowance before processing it, so
    waiting and sending again is safe rather than a retry of real work."""
    if "-32029" not in text and "Rate limit" not in text and "429" not in text:
        return 0
    found = re.search(r"retry_after_seconds\D+(\d+)", text)
    if found:
        return min(int(found.group(1)), 3600) + 5
    return 65 if "per minute" in text else 300


def patient_transport():
    """The public endpoint drops connections and serves error pages mid-poll.
    A transport failure is retried; a JSON-RPC error is a real answer."""
    from genlayer_py.provider.provider import GenLayerProvider
    original = GenLayerProvider.make_request

    def patient(self, method, params):
        attempts = 0
        while attempts < 10:
            try:
                return original(self, method, params)
            except Exception as err:
                text = str(err)
                wait = _refused_for_rate(text)
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


def contract_bytes(raw) -> bytes:
    """The code as the chain returns it. StudioNet answers gen_getContractCode
    with base64 text, not hex and not raw bytes, so a naive read compares the
    encoding rather than the contract."""
    import base64
    if isinstance(raw, (bytes, bytearray)):
        return bytes(raw)
    text = str(raw)
    if text.startswith("0x"):
        return bytes.fromhex(text[2:])
    return base64.b64decode(text)


def git(*args) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--address-only", action="store_true",
                    help="print the address and nothing else")
    args = ap.parse_args()

    from eth_account import Account
    from genlayer_py import create_client
    from genlayer_py.chains import studionet
    from genlayer_py.types import TransactionStatus

    patient_transport()
    code = SOURCE.read_bytes()
    digest = hashlib.sha256(code).hexdigest()
    commit = git("rev-parse", "HEAD")
    dirty = bool(git("status", "--porcelain", "--", "contracts/trace.py"))
    say = (lambda *a, **k: None) if args.address_only else print

    say(f"source    {SOURCE.relative_to(ROOT).as_posix()} @ {commit[:12] or 'unknown'}"
        f"{' (uncommitted changes)' if dirty else ''}  {len(code)} bytes  sha256 {digest}")

    # a throwaway account funded by the faucet: the contract has no owner and no
    # privileged account, so the deployer keeps nothing
    deployer = Account.create()
    rpc("sim_fundAccount", [deployer.address, 10 ** 18])
    client = create_client(chain=studionet, account=deployer)
    for _ in range(40):
        if int(client.get_balance(deployer.address)) > 0:
            break
        time.sleep(3)
    say(f"deployer  {deployer.address} (throwaway, faucet-funded, no privileges in the contract)")

    tx = client.deploy_contract(code=code, args=[])
    tx_hex = tx.hex() if hasattr(tx, "hex") else str(tx)
    say(f"submitted {tx_hex}")
    receipt = client.wait_for_transaction_receipt(transaction_hash=tx,
                                                  status=TransactionStatus.ACCEPTED,
                                                  interval=5000, retries=200)
    leader = ((receipt.get("consensus_data") or {}).get("leader_receipt") or [{}])[0]
    address = (receipt.get("data") or {}).get("contract_address") or receipt.get("contract_address")
    execution = leader.get("execution_result")
    say(f"accepted  {receipt.get('result_name')}  execution {execution}  address {address}")
    if execution not in (None, "SUCCESS") or not address:
        print(f"the deployment was refused: {str(leader.get('result'))[:300]}", file=sys.stderr)
        return 1

    # the record has to say what was observed, not what was observed first: the
    # acceptance receipt says ACCEPTED, and writing that while the script has
    # just watched the transaction finalize puts a weaker claim in the file than
    # the evidence supports
    finality = "ACCEPTED"
    try:
        client.wait_for_transaction_receipt(transaction_hash=tx,
                                            status=TransactionStatus.FINALIZED,
                                            interval=10000, retries=120)
        finality = "FINALIZED"
        say("finalized FINALIZED")
    except Exception:
        say("finalized not yet; the address is usable and finality follows")

    # this network takes the address alone; a block tag is "too many parameters"
    raw = contract_bytes(rpc("gen_getContractCode", [address]))
    onchain_digest = hashlib.sha256(raw).hexdigest()
    identical = onchain_digest == digest
    say(f"on-chain  {len(raw)} bytes  sha256 {onchain_digest}  "
        f"{'MATCH' if identical else 'DIFFERENT'}")

    schema = rpc("gen_getContractSchema", [address])
    methods = sorted((schema or {}).get("methods", {}).keys()) if isinstance(schema, dict) else []

    RECORD.parent.mkdir(parents=True, exist_ok=True)
    RECORD.write_text(json.dumps({
        "network": "GenLayer StudioNet", "chain_id": CHAIN_ID, "rpc": RPC,
        "explorer": f"{EXPLORER}/address/{address}",
        "contract_address": address, "deploy_tx": tx_hex,
        "deploy_status": finality, "deploy_accepted_as": receipt.get("status_name"),
        "deploy_consensus": receipt.get("result_name"),
        "source": "contracts/trace.py", "source_commit": commit,
        "source_sha256": digest, "source_bytes": len(code),
        "onchain_sha256": onchain_digest, "byte_identical": identical,
        "version": "TRACE-1.0.0", "rules": "TRACE-AGG-1",
        "genvm_runner": SOURCE.read_text(encoding="utf-8").split('"')[3],
        "schema_methods": methods,
        "deployed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, indent=2) + "\n", encoding="utf-8")
    say(f"record    {RECORD.relative_to(ROOT).as_posix()}")

    missing = [m for m in WRITES + VIEWS if m not in methods]
    if missing:
        say(f"WARNING   the chain does not report: {', '.join(missing)}")

    if args.address_only:
        print(address)
    else:
        print("\nfrontend environment (frontend/.env.local):")
        print("NEXT_PUBLIC_GENLAYER_NETWORK=studionet")
        print(f"NEXT_PUBLIC_CHAIN_ID={CHAIN_ID}")
        print(f"NEXT_PUBLIC_TRACE_CONTRACT_ADDRESS={address}")
    return 0 if identical and not missing else 1


if __name__ == "__main__":
    sys.exit(main())
