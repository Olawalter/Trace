# Deployment

## What is deployed

| | |
| --- | --- |
| Network | GenLayer StudioNet, chain `61999` |
| RPC | `https://studio.genlayer.com/api` |
| Contract | `0x36BDfe5228DFC595Ec4f378DcB50D53a925522c9` |
| Explorer | [address](https://explorer-studio.genlayer.com/address/0x36BDfe5228DFC595Ec4f378DcB50D53a925522c9) |
| Runner | `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6` |

The full record -- deploy transaction, source commit, source digest, on-chain
digest and the method list read back from the chain -- is in
[docs/deployment.json](docs/deployment.json), written by the deploy script rather
than by hand.

## The runner is pinned to what the network runs, not to what the docs say

The GenLayer SDK reference names a newer runner as current:

```
py-genlayer   5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng   (v0.3.0-rc9)
```

StudioNet refuses a contract built against it with `invalid_contract`. That was
settled by deploying a minimal contract for each runner and watching what
happened, rather than by believing either source:

| Runner | SDK style | StudioNet |
| --- | --- | --- |
| `1jb45aa8…` | `from genlayer import *`, `u256(0)`, `gl.vm.run_nondet_unsafe` | deploys, reads, writes |
| `5jycge4q…` | `import genlayer as gl`, plain ints, `gl.vm.run_nondet` | `invalid_contract` |

So TRACE targets the generation the network actually runs. Two consequences
worth knowing:

- the v0.3 renames in the reference (`StorageView.LATEST_FINALIZED`,
  `run_nondet` meaning the unsafe one) **do not apply here**;
- when StudioNet moves to the v0.3 line, the contract needs the migration in the
  SDK's own guide -- the namespace restructuring, the loss of `u256(...)`
  wrapping, and `run_nondet_unsafe` becoming `run_nondet`.

## Deploying

```bash
python -m pip install -r requirements.txt
python deploy/deploy.py
```

The script deploys the committed source from a throwaway faucet-funded account,
waits for the transaction, then reads the contract back off the chain and
compares it byte for byte with the file it sent. It writes
`docs/deployment.json` and records the comparison either way.

The deployer keeps nothing: TRACE has no owner field and no privileged account.

Two things that are easy to get wrong:

- **StudioNet returns contract code as base64**, not hex and not raw bytes. A
  naive comparison compares the encoding and calls a correct deployment
  different. `contract_bytes()` in both scripts decodes what the chain actually
  sends.
- **`gen_getContractCode` takes the address alone** on this network; adding a
  block tag is `too many parameters`.

## Proving the deployed bytes are this source

```bash
python deploy/verify_deployment.py 0x36BDfe5228DFC595Ec4f378DcB50D53a925522c9 --write-schema
```

It prints the sha-256 of the deployed bytes beside the sha-256 of
`contracts/trace.py`, then the method list the chain reports with each method's
arguments, and checks it against the twenty this repository expects.

`--write-schema` writes `frontend/lib/genlayer/trace-schema.json`. The console
checks itself against that file: an interface test asserts every method it calls
exists in the deployment with the arity it sends, and that value goes to exactly
one method. A console pointed at an older deployment says so instead of failing
when somebody signs.

## Pointing the console at a deployment

```bash
cd frontend
cp .env.example .env.local
```

| Variable | |
| --- | --- |
| `NEXT_PUBLIC_GENLAYER_NETWORK` | `studionet` |
| `NEXT_PUBLIC_CHAIN_ID` | `61999` |
| `NEXT_PUBLIC_TRACE_CONTRACT_ADDRESS` | the deployed address |

All three are validated at startup. If one is missing or malformed the console
renders which variable is wrong rather than reading somebody else's contract.
There is no server, no route handler, no database and no secret: the browser
reads GenLayer and the person's wallet signs every write.

**A redeploy changes the address.** Update `.env.local` (and the hosting
environment), regenerate the schema file in the same step, and rebuild -- or the
console will keep serving the old contract.

```bash
npm install
npm run dev        # http://localhost:3270
npm run build
```

## The demonstration evidence

The live runs verify the pages in `demo/`, fetched over commit-pinned
`raw.githubusercontent.com` addresses. Pinning to a commit matters: an address
that serves whatever is on a branch today is not evidence of anything, because
the bytes a validator read could change afterwards. The commit is recorded with
every run.

After changing anything in `demo/`, commit and push first, then pass the new
commit to a run:

```bash
python deploy/live_probe.py <address> --scenario injection --commit <sha>
```

An honest limitation: every demonstration page is published from one GitHub
account, so they are **one publisher**, and the live protocols ask for one
independent source. A protocol that needed two would need pages from two
accounts. The record says `github:olawalter` twice, and does not pretend
otherwise.

## The live suite

```bash
SKIP_INTEGRATION=0 TRACE_DEMO_COMMIT=<sha> \
  TRACE_CONTRACT_ADDRESS=<address> python -m pytest tests/integration -v -s
```

It takes about half an hour of real consensus rounds on a shared network, and it
writes `docs/live-e2e.json`. Turn that record into the document:

```bash
python deploy/write_end_to_end.py
```

Nothing in [END-TO-END.md](END-TO-END.md) is typed by hand, because a hash typed
by hand is a claim rather than a record.

To re-check the assertions against an earlier run's record without sending
anything:

```bash
TRACE_REPLAY=1 SKIP_INTEGRATION=0 python -m pytest tests/integration -q
```

## Environment notes for anyone reproducing this

- **Seed the GenVM runner bundle before linting or testing on a fresh machine.**
  `gltest` asks GitHub for an asset that was renamed, 404s, and every direct test
  errors at import while the linter still passes. `python
  deploy/fetch_genvm_bundle.py` puts the bundle that exists where both tools look
  for it.
- **A machine with newer GenVM bundles already cached will fail the linter's
  validate step**, with `E101 Failed to load SDK: filename
  'runners/py-genlayer/1j/...tar' not found`. Both tools prefer the newest
  cached version, and the newer bundles do not carry the runner StudioNet runs.
  The lint rules themselves still pass; it is the SDK load that cannot find the
  pin. CI caches only the pinned bundle, which is why it is green there. To
  reproduce CI locally, move the other versions out of `~/.cache/genvm-linter`.
- **On Windows, `ComSpec` must be set** for `npm install` to run postinstall
  scripts. Without it packages extract without their type declarations and
  nothing type-checks, with no obvious error.
- StudioNet's allowance is 30 calls a minute and 500 an hour per IP, shared
  between reads and sends. Every script here waits out a `-32029` and retries
  transport failures; none of them retries a real answer.
