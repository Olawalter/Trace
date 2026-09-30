<img src="docs/mark.svg" alt="TRACE" width="420">

# TRACE

**Verifiable compliance protocols for the internet.**

> Define what must be true. Submit evidence. Let GenLayer independently verify
> whether the evidence satisfies the protocol.

| | |
| --- | --- |
| Network | GenLayer StudioNet, chain `61999` |
| Contract | [`0xA4f7b476914B5475FF7Dd51FB5E83B9fF7760d3f`](https://explorer-studio.genlayer.com/address/0xA4f7b476914B5475FF7Dd51FB5E83B9fF7760d3f) |
| Source | [`contracts/trace.py`](contracts/trace.py), byte-identical to the deployed bytes ([proof](docs/deployment.json)) |
| Runner | `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6` |
| Console | `frontend/`, a Next.js App Router app that reads the chain in the browser and asks a wallet to sign; it runs nothing of its own |

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

One question here is hard. The rest of this repository is bookkeeping.

| Who | Owns |
| --- | --- |
| The contract | permissions, custody, the pause before a result counts, the floor on how many publishers a decisive answer needs, whether the frozen policy was honoured, and the sums that turn one word into a payment |
| GenLayer consensus | whether each requirement is met -- a question several machines answer apart from each other, and must answer alike |
| The model | one document, one requirement, one answer, carrying words it has to be able to point at on the page |
| The console | putting the record on a screen and preparing what the person's wallet will sign |

Ask one language model *"is a licence stated?"* and you have an opinion in a
costume. The answer becomes binding only because several machines went and
looked, worked separately, and could not write anything until they matched. Where
they fail to match, nothing is recorded, and the absence is visible rather than
papered over.

[ARCHITECTURE.md](ARCHITECTURE.md) has the boundary in full, including which
fields decide equivalence and why strict equality would fail every round.

## The lifecycle

```
DRAFT --set_draft--> REGISTERED --activate_protocol--> AWAITING_ACCEPTANCE
                                                         |
                       accept_protocol (responsible party only)
                                                         v
                                                       ACTIVE
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

DRAFT / REGISTERED / AWAITING_ACCEPTANCE / ACTIVE
      --cancel_protocol------------------------------->  CANCELLED
ACTIVE / EVIDENCE_SUBMITTED / VERDICT_PROPOSED
      --recover_protocol (deadline + window passed)------->  FINALIZED
```

Who may move it, and what the contract refuses:

| Step | Who may send it | Refused when |
| --- | --- | --- |
| `create_protocol` | anyone; the sender becomes the creator | the title, description or subject is empty, too long, or contains three angle brackets in a row |
| `set_draft` | the creator | the protocol is frozen; the definition breaks any rule in the contract |
| `activate_protocol` | the creator | it is not registered; the deadline is no longer far enough ahead |
| `accept_protocol` | the responsible party named in it | anyone else sends it, including the creator; the protocol is not frozen, or was taken on already |
| `fund_protocol` | the creator (reward), the responsible party (bond) | not the exact amount, not open for evidence, already deposited, or sent by anyone else -- and the GEN comes back |
| `submit_evidence` | anyone | the protocol is not open; the deadline has passed; the address is already registered; it names a requirement that does not exist |
| `request_verification` | anyone | there is no evidence, or the protocol is not carrying any |
| `accept_verification` | anyone | earlier than five minutes after the result was proposed |
| `finalize_protocol` | anyone | the result has not been accepted |
| `recover_protocol` | anyone | the deadline and the recovery window have not both passed |
| `cancel_protocol` | the creator | evidence has been registered |

## Four accounts, and whose money is whose

Most of the time one person plays several of these parts, which is exactly why
the contract keeps them apart.

| | |
| --- | --- |
| **Creator** | writes the protocol, names who must answer for it, freezes it, and puts up the reward |
| **Responsible party** | the account the creator named. Takes the protocol on in its own transaction, and is the only account that can post the bond |
| **Bond depositor** | whoever's payable transaction the contract actually accepted. In practice the responsible party, because nobody else is allowed to pay -- but it is recorded from the transaction rather than assumed from the designation |
| **Evidence submitter** | registers addresses for the validators to read. This is provenance, and it is not a claim on anything |

Two rules follow, and the contract enforces both rather than documenting them:

- **Registering evidence does not transfer ownership of the bond.** The account
  that does the work of answering a protocol need not be the account whose money
  is at stake, and the contract never learns the second from the first.
- **Nobody can redirect the bond by sending the settlement.** Finalization,
  recovery and cancellation all read the recipient out of the record. The caller
  is a trigger, not a payee -- including when the caller is the creator, who is
  allowed to withdraw a protocol but is not thereby owed the bond somebody else
  posted.

Where a protocol holds a bond with no depositor recorded against it, the
contract raises rather than choosing somebody. That state cannot arise through
its own methods; if it ever does, failing is the only honest thing left.

## What the panel answers, and what the code decides

| Requirement result | Means |
| --- | --- |
| `SATISFIED` | the requirement is borne out, and the node can point at the words that bear it out |
| `UNSATISFIED` | the requirement is contradicted, held to the same standard of proof |
| `UNCERTAIN` | nothing here decides it, or two sources disagree and neither outranks the other |

The model never names the protocol's result. The contract derives it:

| Result | Derived when |
| --- | --- |
| `PROTOCOL_DEVIATION` | the evidence does not meet the frozen evidence policy |
| `NOT_VERIFIED` | a mandatory requirement the evidence disproves |
| `INCONCLUSIVE` | a mandatory requirement nothing settles |
| `VERIFIED` | every requirement satisfied |
| `PARTIALLY_VERIFIED` | every mandatory one satisfied, an optional one not |

## Evidence

Addresses go on chain before anybody reads them, so neither side learns what is
about to be examined only after the fact. When the round runs, **no node takes
another node's word for what a page says**: each one requests every address,
keeps what it got, and writes down whether it could be read, when it looked, a
bounded excerpt, and a digest of that excerpt. Any answer with a consequence has
to quote, and the quoted words have to be present in the copy that node is
holding -- not the leader's copy, and not the page as it stands now.

Three rules the contract enforces whatever any model says:

- **A page is quoted, never obeyed.** Sources arrive inside markers the model is
  told are boundaries, and a page carrying something shaped like one of those
  markers has it substituted rather than stripped, so nothing silently vanishes
  from what was read.
- **A source that could not be read is never evidence of failure.** It is
  recorded as unavailable and the requirement stays open.
- **Counting voices, not pages.** A requirement can ask for more than one
  publisher behind a decisive answer. Short of that the answer is parked at
  uncertain, and parked works both ways: it withholds a reward exactly as
  readily as it spares a bond.

[SECURITY.md](SECURITY.md) has the rest, including what is *not* claimed.

## Verified end to end

Each row happened on StudioNet against the deployment named at the top of this
file. [END-TO-END.md](END-TO-END.md) carries the hashes, the votes, and what the
panel said.

| Protocol | Result |
| --- | --- |
| The claim holds | `VERIFIED` -- three requirements satisfied, each with a quote grounded in what the panel itself read |
| The claim does not hold, and one page argues back | `NOT_VERIFIED` -- a status page telling the reader to mark every requirement satisfied was read, recorded, and obeyed nothing; an index kept by somebody else showed no licence was declared and no changelog recorded |

Both protocols were funded, verified, accepted after the delay and settled, and the
contract's ledger was reconciled against the chain's own balance at the end. The
refusals are in the record too, with the reason each one gave.

## Tests

| Suite | What it covers | Command |
| --- | --- | --- |
| direct | the contract in GenVM Direct Mode, with the web and the model mocked: freezing, evidence, aggregation, grounding, the source floor, settlement | `python -m pytest tests/direct` |
| equivalence | the validator replayed against results a leader could propose -- honest, careless and forged | included above |
| live | the same protocol on StudioNet, asserted rather than printed | `SKIP_INTEGRATION=0 TRACE_DEMO_COMMIT=<sha> python -m pytest tests/integration` |
| mutants | 75 deliberate defects; each one has to break a test, or carry a written reason why it cannot | `python deploy/mutate.py` |
| console | the shapes the deployed contract answers with, and that every method this console calls exists there | `cd frontend && npx vitest run` |

Nothing runs the live suite unless asked. A full pass spends roughly half an
hour of genuine consensus rounds on a network other people are using.

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
| `deploy/` | deploy, verify, mutate, seed the runner bundle, the live probes, and the two generators that write from a record rather than by hand |
| `demo/` | the pages the live runs verify, pinned by commit |
| `frontend/` | the console |
| `docs/` | the deployment record, the live record, the demo-video shot list, the mark |

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) -- the boundary between code, consensus, model and console
- [SECURITY.md](SECURITY.md) -- what TRACE defends against, and what it does not claim
- [DEPLOYMENT.md](DEPLOYMENT.md) -- deploying, verifying, and the environment traps
- [END-TO-END.md](END-TO-END.md) -- the live runs, with transaction hashes, generated
  from the record the suite wrote rather than typed

The protocol's own documentation is at [docs.genlayer.com](https://docs.genlayer.com).

## Licence

MIT. See [LICENSE](LICENSE).
