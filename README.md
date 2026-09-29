<img src="docs/mark.svg" alt="TRACE" width="420">

# TRACE

**Verifiable compliance protocols for the internet.**

> Define what must be true. Submit evidence. Let GenLayer independently verify
> whether the evidence satisfies the protocol.

| | |
| --- | --- |
| Network | GenLayer StudioNet, chain `61999` |
| Contract | [`0x36BDfe5228DFC595Ec4f378DcB50D53a925522c9`](https://explorer-studio.genlayer.com/address/0x36BDfe5228DFC595Ec4f378DcB50D53a925522c9) |
| Source | [`contracts/trace.py`](contracts/trace.py), byte-identical to the deployed bytes ([proof](docs/deployment.json)) |
| Runner | `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6` |
| Console | `frontend/`, Next.js App Router, wallet-signed writes, no server of its own |

## The problem

Somebody claims something is true: a release is published under an open licence,
a supplier is certified, a report was filed before a deadline. The claim matters
to someone else, and the evidence for it is a set of web pages neither party
controls.

Today either a person decides, or the side with the most to gain decides. A
smart contract cannot help: it can hold money, but it cannot read a page. An
oracle can post a number, but it cannot say whether the number means the
requirement was met.

## What TRACE does

1. Someone writes a **protocol**: requirements that can each be answered on
   their own, an evidence policy, a deadline, and optionally a consequence in
   native GEN.
2. They **freeze** it. After that nothing in it can change, for anyone.
3. Anybody **registers evidence**: addresses that will be fetched, recorded on
   chain before anyone reads them.
4. Anybody asks GenLayer to **verify** it. Every validator fetches every source
   itself, reads each requirement itself, and the round is recorded only if they
   agree.
5. The contract **derives the result** from the agreed answers, in ordinary
   deterministic code, and pays whatever the frozen policy says about that one
   word.

## Why GenLayer

> TRACE uses GenLayer because deciding whether evidence satisfies a requirement
> means interpreting natural-language rules against real-world documents, which
> cannot be reduced to ordinary deterministic smart-contract logic.

The judgement is the product; everything else is ordinary.

| Who | Owns |
| --- | --- |
| The contract | who may act, what is held, the acceptance delay, the independent-source floor, the evidence-policy check, and the arithmetic from a result to a payment |
| GenLayer consensus | whether the evidence satisfies each requirement -- agreed by a panel, not asserted by one node |
| The model | reading a document and answering one requirement, with a quote it must ground in that document |
| The console | showing the record and composing transactions the person signs |

A single LLM call answering *"is a licence stated?"* is one party's opinion with
extra steps. What makes it binding is that several independent nodes fetched the
evidence, answered separately, and had to agree before a single GEN moved -- and
that when they do not agree, nothing is written and that is visible.

[ARCHITECTURE.md](ARCHITECTURE.md) has the boundary in full, including which
fields decide equivalence and why strict equality would fail every round.

## The lifecycle

```
DRAFT --set_draft--> REGISTERED --activate_protocol--> ACTIVE
                                                         |
                                         submit_evidence |
                                                         v
                                               EVIDENCE_SUBMITTED
                                                         |
                                        request_verification
                                                         v
                                                VERDICT_PROPOSED
                                                         |
                               accept_verification (after 5 minutes)
                                                         v
                                                     ACCEPTED
                                                         |
                                             finalize_protocol
                                                         v
                                                    FINALIZED

DRAFT / REGISTERED / ACTIVE            --cancel_protocol-->  CANCELLED
ACTIVE / EVIDENCE_SUBMITTED / VERDICT_PROPOSED
      --recover_protocol (deadline + window passed)------->  FINALIZED
```

Who may move it, and what the contract refuses:

| Step | Who may send it | Refused when |
| --- | --- | --- |
| `create_protocol` | anyone; the sender becomes the creator | the title, description or subject is empty, too long, or contains three angle brackets in a row |
| `set_draft` | the creator | the protocol is frozen; the definition breaks any rule in the contract |
| `activate_protocol` | the creator | it is not registered; the deadline is no longer far enough ahead |
| `fund_protocol` | the creator (reward), anyone else (bond) | not the exact amount, not open for evidence, or already deposited -- and the GEN comes back |
| `submit_evidence` | anyone | the protocol is not open; the deadline has passed; the address is already registered; it names a requirement that does not exist |
| `request_verification` | anyone | there is no evidence, or the protocol is not carrying any |
| `accept_verification` | anyone | earlier than five minutes after the result was proposed |
| `finalize_protocol` | anyone | the result has not been accepted |
| `recover_protocol` | anyone | the deadline and the recovery window have not both passed |
| `cancel_protocol` | the creator | evidence has been registered |

Money only ever moves to the two accounts the record already holds -- the
creator, and whoever registered the first evidence -- whoever sends the
transaction.

## What the panel answers, and what the code decides

| Requirement result | Means |
| --- | --- |
| `SATISFIED` | the evidence shows it was met, with a quote from a source the node itself read |
| `UNSATISFIED` | the evidence shows it was not met, with the same grounding |
| `UNCERTAIN` | the evidence does not settle it, or two sources contradict and neither is stronger |

The model never names the protocol's result. The contract derives it:

| Result | Derived when |
| --- | --- |
| `PROTOCOL_DEVIATION` | the evidence does not meet the frozen evidence policy |
| `NOT_VERIFIED` | a mandatory requirement the evidence disproves |
| `INCONCLUSIVE` | a mandatory requirement nothing settles |
| `VERIFIED` | every requirement satisfied |
| `PARTIALLY_VERIFIED` | every mandatory one satisfied, an optional one not |

## Evidence

Evidence is registered before a round, so both sides can see what will be read.
At verification **every node fetches every source itself** and records what it
found: availability, the time it looked, a bounded excerpt and a digest over
that excerpt. A finding that would move money must carry a quote, and that quote
must appear in that node's own copy of a source it cited.

Three rules the contract enforces whatever any model says:

- **Text inside evidence is text, not instruction.** Every source is fenced
  before the model sees it, and anything resembling a fence in a page is
  replaced, never deleted.
- **A source that could not be read is never evidence of failure.** It is
  recorded as unavailable and the requirement stays open.
- **A decisive answer needs enough independent publishers.** Where it does not
  have them it is held as uncertain -- in either direction, so a held
  `SATISFIED` cannot release a reward any more than a held `UNSATISFIED` can take
  a bond.

[SECURITY.md](SECURITY.md) has the rest, including what is *not* claimed.

## Verified end to end

Every line below is a set of transactions on StudioNet against the contract
above. The full record, with hashes, is in [END-TO-END.md](END-TO-END.md).

| Run | Result |
| --- | --- |
| The claim holds | `VERIFIED` -- three requirements satisfied, each with a quote grounded in what the panel itself read |
| The claim does not hold | `NOT_VERIFIED` -- an index kept by somebody else shows no licence was declared and no changelog recorded |
| A page that argues back | `NOT_VERIFIED` -- a status page telling the reader to mark every requirement satisfied was read, recorded, and obeyed nothing |

## Tests

| Suite | What it covers | Command |
| --- | --- | --- |
| direct | the contract in GenVM Direct Mode, with the web and the model mocked: freezing, evidence, aggregation, grounding, the source floor, settlement | `python -m pytest tests/direct` |
| equivalence | the validator replayed against results a leader could propose -- honest, careless and forged | included above |
| live | the same protocol on StudioNet, asserted rather than printed | `SKIP_INTEGRATION=0 TRACE_DEMO_COMMIT=<sha> python -m pytest tests/integration` |
| mutants | every mutant either dies or is documented as equivalent | `python deploy/mutate.py` |
| console | the shapes the deployed contract answers with, and that every method this console calls exists there | `cd frontend && npx vitest run` |

The live suite is skipped by default: a full run is about half an hour of real
consensus rounds on a shared network.

## Running it

```bash
python -m pip install -r requirements.txt
python deploy/fetch_genvm_bundle.py
```

```bash
python -m pytest tests/direct -q
```

```bash
genvm-lint check contracts/trace.py --json
```

To deploy your own and point the console at it:

```bash
python deploy/deploy.py
```

```bash
python deploy/verify_deployment.py <address> --write-schema
```

```bash
cd frontend && cp .env.example .env.local && npm install && npm run dev
```

[DEPLOYMENT.md](DEPLOYMENT.md) has the details, including why the runner is
pinned to the one StudioNet runs rather than the one the SDK reference calls
current.

## Repository

| Path | |
| --- | --- |
| `contracts/trace.py` | the contract: 10 writes, 10 views |
| `tests/direct/` | Direct Mode suite |
| `tests/integration/` | the live StudioNet suite |
| `deploy/` | deploy, verify, mutate, seed the runner bundle, and the live probes |
| `demo/` | the pages the live runs verify, pinned by commit |
| `frontend/` | the console |
| `docs/` | the deployment record, the live record, the mark |

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) -- the boundary between code, consensus, model and console
- [SECURITY.md](SECURITY.md) -- what TRACE defends against, and what it does not claim
- [DEPLOYMENT.md](DEPLOYMENT.md) -- deploying, verifying, and the environment traps
- [END-TO-END.md](END-TO-END.md) -- the live runs, with transaction hashes

The protocol's own documentation is at [docs.genlayer.com](https://docs.genlayer.com).

## Licence

MIT. See [LICENSE](LICENSE).
