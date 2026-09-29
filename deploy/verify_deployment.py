"""Prove a deployed contract is this source, and read its schema off the chain.

    python deploy/verify_deployment.py <address> [--write-schema]

Two questions, both answered by the network rather than by this repository:

  * are the deployed bytes the file in contracts/? (sha256, both sides)
  * what functions does the chain say the contract has, with what arguments?

--write-schema saves the second answer to frontend/lib/genlayer/trace-schema.json,
which the interface checks itself against at load, so a frontend pointed at an
older deployment says so instead of failing when somebody signs.
"""
import argparse
import hashlib
import json
import pathlib
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "contracts" / "trace.py"
SCHEMA_OUT = ROOT / "frontend" / "lib" / "genlayer" / "trace-schema.json"
RECORD = ROOT / "docs" / "deployment.json"
RPC = "https://studio.genlayer.com/api"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")

EXPECTED_WRITES = ("create_protocol", "set_draft", "activate_protocol", "cancel_protocol",
                   "fund_protocol", "submit_evidence", "request_verification",
                   "accept_verification", "finalize_protocol", "recover_protocol")
EXPECTED_VIEWS = ("get_protocol_info", "get_protocol", "list_protocols", "list_by_creator",
                  "get_evidence", "list_evidence", "get_verification", "list_verifications",
                  "get_history", "list_activity")


def rpc(method, params, attempts=6):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for i in range(attempts):
        try:
            request = urllib.request.Request(
                RPC, data=body, headers={"Content-Type": "application/json", "User-Agent": UA})
            out = json.load(urllib.request.urlopen(request, timeout=180))
            if "error" in out:
                raise RuntimeError(f"{method}: {out['error']}")
            return out["result"]
        except RuntimeError:
            raise
        except Exception:
            if i == attempts - 1:
                raise
            time.sleep(4 + 4 * i)


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("address", nargs="?", help="defaults to the address in docs/deployment.json")
    ap.add_argument("--write-schema", action="store_true")
    args = ap.parse_args()

    address = args.address
    if not address:
        if not RECORD.exists():
            print("no address given and no docs/deployment.json to read one from", file=sys.stderr)
            return 1
        address = json.loads(RECORD.read_text(encoding="utf-8"))["contract_address"]

    code = SOURCE.read_bytes()
    here = hashlib.sha256(code).hexdigest()
    chain_bytes = contract_bytes(rpc("gen_getContractCode", [address]))
    there = hashlib.sha256(chain_bytes).hexdigest()

    print(f"on-chain  {address}  {len(chain_bytes)} bytes  sha256 {there}")
    print(f"source    contracts/trace.py{' ' * 22}{len(code)} bytes  sha256 {here}")
    identical = here == there
    print("MATCH - the deployment is byte-identical to the repository source" if identical
          else "DIFFERENT - the deployed contract is not this source")

    schema = rpc("gen_getContractSchema", [address])
    methods = (schema or {}).get("methods", {}) if isinstance(schema, dict) else {}
    print(f"\n-- schema: {len(methods)} method(s) the chain reports --")
    for name in sorted(methods):
        entry = methods[name] or {}
        params = entry.get("params") or entry.get("inputs") or []
        names = [p[0] if isinstance(p, (list, tuple)) else (p.get("name") if isinstance(p, dict)
                                                            else str(p)) for p in params]
        kind = "view" if entry.get("readonly") or entry.get("view") else "write"
        payable = " payable" if entry.get("payable") else ""
        print(f"  {kind:<5}{payable:<8} {name}({', '.join(str(n) for n in names)})")

    missing = [m for m in EXPECTED_WRITES + EXPECTED_VIEWS if m not in methods]
    extra = [m for m in methods if m not in EXPECTED_WRITES + EXPECTED_VIEWS]
    if missing:
        print(f"\nMISSING from the chain: {', '.join(missing)}")
    if extra:
        print(f"\nnot expected by this script: {', '.join(sorted(extra))}")

    if args.write_schema:
        SCHEMA_OUT.parent.mkdir(parents=True, exist_ok=True)
        SCHEMA_OUT.write_text(json.dumps({
            "contract_address": address,
            "read_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "methods": {name: sorted((methods[name] or {}).keys()) for name in sorted(methods)},
            "schema": schema,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"\nwrote {SCHEMA_OUT.relative_to(ROOT).as_posix()}")

    return 0 if identical and not missing else 1


if __name__ == "__main__":
    sys.exit(main())
