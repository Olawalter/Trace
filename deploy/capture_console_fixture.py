"""Capture what the deployed contract answers, for the console's tests.

    python deploy/capture_console_fixture.py <address>

The console asserts its schemas against a recorded answer rather than a shape
somebody typed, so that a contract which changes what it returns fails a test
instead of leaving a page rendering "undefined". That only works if the
recording comes from the chain, which is what this does.

It reads every view the console reads, twice over: once through the Python
client, and once through the browser's own client for one protocol. The two
clients disagree about how a large integer comes back -- a number from
genlayer-py, a string from genlayer-js -- and a fixture captured from only one
of them proves nothing about the other.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "tests" / "fixtures" / "chain.json"
TEST = ROOT / "frontend" / "tests" / "contract.test.ts"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    address = sys.argv[1]

    from eth_account import Account
    from genlayer_py import create_client
    from genlayer_py.chains import studionet

    client = create_client(chain=studionet, account=Account.create())

    def read(fn, *args):
        return client.read_contract(address=address, function_name=fn, args=list(args))

    protocols = read("list_protocols", 0, 50)
    if not protocols["items"]:
        print("that contract holds no protocols yet; run the live suite against it first",
              file=sys.stderr)
        return 1
    # the newest protocol that actually carries a round, so the verification and
    # history shapes in the fixture are the full ones rather than empty lists
    with_round = [p for p in protocols["items"] if int(p["round_count"]) > 0]
    subject = (with_round or protocols["items"])[-1]
    pid = subject["protocol_id"]

    captured = {
        "list_protocols": protocols,
        "get_protocol_info": read("get_protocol_info"),
        "get_verification": read("get_verification", pid, 0) if with_round else None,
        "list_evidence": read("list_evidence", pid, 0, 50),
        "list_activity": read("list_activity", 0, 40),
        "get_history": read("get_history", pid, 0, 50),
        # what the BROWSER's client returns for the same protocol: a fixture
        # from one client is not evidence about the other
        "protocol_from_browser_client": browser_answer(address, pid),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(captured, indent=1, default=str) + "\n", encoding="utf-8")
    print(f"captured {pid} from {address} into {OUT.relative_to(ROOT)}")

    # the test file says where the recording came from; a stale address there is
    # a claim about provenance that is simply false
    text = TEST.read_text(encoding="utf-8")
    import re
    fixed = re.sub(r"0x[0-9a-fA-F]{40}", address, text)
    if fixed != text:
        TEST.write_text(fixed, encoding="utf-8")
        print(f"updated the address in {TEST.name}")
    return 0


def browser_answer(address: str, pid: str):
    """Read one protocol the way the console does: through genlayer-js, in node."""
    import subprocess
    import tempfile
    script = f"""
import {{ createClient, createAccount }} from "genlayer-js";
import {{ studionet }} from "genlayer-js/chains";
const client = createClient({{ chain: studionet, account: createAccount() }});
const out = await client.readContract({{
  address: "{address}",
  functionName: "get_protocol",
  args: ["{pid}"],
  transactionHashVariant: "latest-final",
}});
process.stdout.write(JSON.stringify(out, (_, v) =>
  typeof v === "bigint" ? v.toString() : v));
"""
    frontend = ROOT / "frontend"
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", dir=frontend, delete=False,
                                     encoding="utf-8") as handle:
        handle.write(script)
        path = pathlib.Path(handle.name)
    try:
        done = subprocess.run(["node", path.name], cwd=frontend, capture_output=True, text=True,
                              shell=True)
        if done.returncode != 0:
            print(f"the browser client could not be read: {done.stderr[-400:]}", file=sys.stderr)
            return None
        return json.loads(done.stdout)
    finally:
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
