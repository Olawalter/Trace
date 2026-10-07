<img src="docs/mark.svg" alt="TRACE" width="420">

# Reply to the steward review

The current review is answered first. The reply to the earlier review
follows it unchanged, because it is a record of what was said at the time.

---

# This review: the frozen contradiction policy

> Please align the frozen contradiction policy with the adjudication TRACE
> actually performs. The current contract accepts UNCERTAIN, NEWEST, and
> STRICTEST, but NEWEST and STRICTEST are only parsed and stored; they are not
> consumed by the verification/aggregation path. This allows a
> consequence-bearing protocol to advertise and freeze a contradiction rule that
> does not affect its result. Either implement each exposed policy
> deterministically with targeted tests showing conflicting evidence produces
> the intended different outcomes, or restrict the accepted policy to the
> behavior actually implemented. Please include tests covering the resulting
> economic outcome where the contradiction policy changes the verification
> result.

The finding is correct. The contract now accepts only the rule it carries out,
and the tests follow a real contradiction -- two sources that state different
things -- all the way to the GEN that moves.

| | |
| --- | --- |
| Contract | [`0xf68c61Da388D1A5cBac19B000947686b5b66C0E7`](https://explorer-studio.genlayer.com/address/0xf68c61Da388D1A5cBac19B000947686b5b66C0E7) on StudioNet, chain `61999` |
| Deploy | [`0xd60d5fb291...`](https://explorer-studio.genlayer.com/tx/0xd60d5fb2910f8bb767d68d8a6c1aeb9880cb8329d863944c66f0f7fb75069cca), FINALIZED, byte-identical to `contracts/trace.py` |
| Fix | [`6eb3d65`](https://github.com/Olawalter/Trace/commit/6eb3d65d976a3242ec13562f7ff9a75dd7e731a2) |
| Full record | [END-TO-END.md](END-TO-END.md), generated from the run rather than written |

## What was wrong

`_read_evidence_policy` accepted three contradiction rules and put whichever one
it was given into the definition, which `activate_protocol` freezes and the
fingerprint covers. The string then appeared nowhere else in the contract.
`_derive_result` works from each requirement's effective status and the
independent-source floor; it never reads the policy, and nor does anything it
calls.

So a protocol could freeze `NEWEST`, show it to the party being asked to post a
bond, and adjudicate exactly as if it said `UNCERTAIN`. A frozen term with no
effect is worse than no term, because it reads like a promise.

## Why the two unsupported rules were refused rather than implemented

Both were checked against the data model before either was ruled out.

**NEWEST** needs to know when each source was published. TRACE does not know
that. The evidence record carries two times and neither one is it:

- `submitted_at` is when the evidence row was registered on chain. It describes
  the order somebody pressed submit, and whoever submits can move it at will by
  registering later. Deciding a contradiction with it would mean the last
  submitter wins.
- `observed_at` is stamped once per round by the leader and then *adopted* by
  every validator, so that independent readings can still produce the same
  fingerprint. Every source in a round carries the same value, so it cannot
  order two sources even in principle.

**STRICTEST** needs a verdict for each source to take the strictest of. The
panel answers one status per *requirement*, having read every source behind it:
`SATISFIED`, `UNSATISFIED` or `UNCERTAIN`. There are no per-source verdicts to
rank. Producing them would mean new evidence metadata, source-level
adjudication, new consensus fields and new equivalence rules -- a protocol
redesign rather than a correction to this one.

Neither is refused because it is hard. They are refused because this contract
cannot carry them out honestly, and the review explicitly allows restricting the
accepted policy to the implemented behaviour.

## What changed

One validation, in `_read_evidence_policy`:

```
UNCERTAIN  -> accepted
NEWEST     -> refused
STRICTEST  -> refused
```

Refused at the contract boundary, before anything can be frozen, and **not**
mapped quietly onto `UNCERTAIN`: somebody who asked for a rule that does not
exist is told so, rather than handed a different protocol than the one they
wrote. The refusal names the value it refused.

`contradiction_policy` stays in the definition and in the fingerprint. It is
still worth freezing explicitly; what it says is now what happens.

The invariant holds by construction and not only by test: `_read_evidence_policy`
has one caller, `draft_json` is written in exactly two places -- empty at
creation, and in `set_draft` after that validation -- and `create_protocol`
takes no policy at all. There is no route by which an unsupported rule reaches a
frozen protocol.

## What UNCERTAIN actually does

It is the rule, not a fallback:

```
two sources that state different things about one requirement
        -> no decisive answer can be grounded          -> UNCERTAIN
a mandatory requirement left UNCERTAIN                 -> INCONCLUSIVE
INCONCLUSIVE                                           -> the frozen
                                                          inconclusive_action
                                                       -> deterministic payout
```

## The tests

Eleven, all through public contract methods rather than helpers.

| Test | What it establishes |
| --- | --- |
| `test_the_only_contradiction_rule_is_the_one_the_contract_carries_out` | `UNCERTAIN` is accepted, and is in the frozen definition |
| `test_a_contradiction_rule_the_contract_does_not_carry_out_is_refused` | `NEWEST`, `STRICTEST` and their lower-case forms are refused through `set_draft` -- the path a hand-built transaction uses |
| `test_an_unsupported_rule_cannot_reach_a_frozen_protocol` | the refusal happens before freezing, and there is then nothing to activate |
| `test_the_frozen_rule_cannot_be_rewritten_afterwards` | once frozen the policy cannot be changed, and the definition is untouched by the attempt |
| `test_two_sources_that_disagree_leave_the_requirement_unresolved` | both pages are read, they state different licences, the requirement is `UNCERTAIN` and the protocol `INCONCLUSIVE` |
| `test_picking_a_side_and_citing_the_wrong_source_does_not_ground_it` | the demotion is the contract's: a decisive answer citing the opposing source fails grounding and lands in the same place |
| `test_contradictory_evidence_pays_out_the_frozen_inconclusive_action` | the economic consequence, below |
| `test_the_same_conflict_pays_differently_from_a_proven_failure` | `INCONCLUSIVE` and `NOT_VERIFIED` are economically distinct |

No existing check was weakened to make any of them pass. The grounding rules,
the source-availability rules and the independent-publisher floor are as they
were, and their tests still pass untouched.

## The economic outcome, in atto-GEN

The accounts are kept apart on purpose: the creator funds the reward, the
responsible party posts the bond, a third account submits the evidence, and the
call that finalizes is made by somebody who is owed nothing.

```
custody            reward 20000000000000000   bond 10000000000000000
R2 (mandatory)     answered UNCERTAIN -> effective UNCERTAIN
overall result     INCONCLUSIVE
frozen action      inconclusive_action = SPLIT
paid               20000000000000000  to the bond depositor
                   10000000000000000  to the creator
                                   0  to the account that submitted the evidence
custody after      0      ledgers: reward 0, bond 0
```

The bond side is paid from the stored `bond_depositor`, so the account that
found the evidence is not the account that gets paid, and the account that
triggered finalization does not become a payee.

The same conflict under `REFUND` returns 20000000000000000 to the creator and
10000000000000000 to the bond depositor. A mandatory requirement the evidence
*disproves* forfeits the bond instead, paying the creator 30000000000000000.
Three different endings, one frozen policy, and whether the evidence contradicts
itself is what decides between them.

## Checking it

| Command | Result |
| --- | --- |
| `genvm-lint check contracts/trace.py --json` | lint ok, validate ok, 21 methods |
| `python -m pytest tests/direct -q` | 181 passed |
| `SKIP_INTEGRATION=0 TRACE_DEMO_COMMIT=<sha> python -m pytest tests/integration -q -s` | 32 passed in 12m51s, real consensus on StudioNet, against this deployment |
| `python deploy/deploy.py` | on-chain sha256 matches `contracts/trace.py` |
| CI (`contract`, `mutants`, `console`) | green, including the full 87-mutant sweep |

## What is not claimed

TRACE still decides nothing about which contradicting source is right. It
records that they contradict, declines to call the requirement either way, and
pays what the protocol said it would pay when nothing is settled. A rule that
picked a winner would need information this protocol does not have, and
inventing it is the failure this review was about.

---

# Earlier review: the bond depositor

> Please record the account that actually deposits the bond and use that address
> for every bond return or submitter-side payout, including finalization,
> timeout recovery, and creator cancellation. Add tests where the creator, bond
> depositor, and first evidence submitter are different accounts and verify each
> recipient.

Fixed, redeployed and verified on chain with three different accounts. The
details are below, along with what was wrong, because the finding was broader
than one payout path and it is worth being exact about it.

| | |
| --- | --- |
| Contract | [`0xA4f7b476914B5475FF7Dd51FB5E83B9fF7760d3f`](https://explorer-studio.genlayer.com/address/0xA4f7b476914B5475FF7Dd51FB5E83B9fF7760d3f) on StudioNet, chain `61999` |
| Deploy | [`0x6757e2b389...`](https://explorer-studio.genlayer.com/tx/0x6757e2b389025e5ad85e16c26c5d946ae514a4db1669df73a881485d3c701c6e), FINALIZED, byte-identical to `contracts/trace.py` |
| Full record | [END-TO-END.md](END-TO-END.md), generated from the run rather than written |

## What was wrong

The contract never recorded who paid the bond. Every settlement path worked the
recipient out instead, and all three ways of working it out could be wrong.

`finalize_protocol` and `recover_protocol` paid a helper called `_submitter_of`,
which returned whoever registered the first evidence. That treats answering a
protocol and funding it as the same act. They are not, and nothing in the
contract required one account to do both. When a protocol carried no evidence at
all, the same helper fell back to the creator.

`cancel_protocol` was worse, and this is the part worth dwelling on.
Cancellation is creator-authorized, and it paid `self._sender()`. Because the
authorization and the recipient were read from the same place, the code looked
correct: of course the caller is the creator, cancellation is creator-only. The
reward going back to the caller was right. The bond going back to the caller
meant a creator withdrawing a protocol collected money another account had
posted, and nothing about the code's shape suggested it.

The common failure was not three bugs. It was deriving an identity that should
have been recorded.

## What changed

Three fields now persist on every protocol.

| Field | What it is | Where it comes from |
| --- | --- | --- |
| `responsible_party` | the account the creator says must answer for the subject | named in the draft, and frozen **inside** the definition, so it is covered by the same fingerprint as the requirements |
| `accepted_at` | when that account took the protocol on | its own `accept_protocol` transaction |
| `bond_depositor` | the account whose payable transaction actually funded the bond | `gl.message.sender_address` on the funding call the contract accepted, after every check has passed |

Freezing and starting are now separate acts. `activate_protocol` leaves a
protocol at `AWAITING_ACCEPTANCE`; only the named account can move it to
`ACTIVE`, and only that account can post the bond. The creator cannot accept on
their behalf, and a stranger can no longer buy a stake in somebody else's
protocol. `_submitter_of` is deleted rather than renamed: it had no remaining
honest use.

Putting the responsible party inside the frozen definition was deliberate. Who
is answerable is part of what both sides agreed, so it should not be something a
creator can point elsewhere once the evidence has arrived.

## Where every payment goes now

| Payment | Recipient | Established by |
| --- | --- | --- |
| a refused deposit | the account that sent it | the payable transaction being refunded |
| the reward, on any ending | `p.creator` | the transaction that created the protocol |
| the bond, on any ending | `p.bond_depositor` | the payable transaction the contract accepted |
| a released reward where no bond was posted | `p.responsible_party` | the frozen definition, plus that account's own acceptance |

Two cases needed a decision rather than a rule, so they are called out here.

**A released reward with no bond posted.** A `VERIFIED` protocol releases the
creator's reward to the side that answered, and that side may never have posted
a bond. There is still a payee to find. It is `responsible_party` — an identity
fixed in the frozen definition and confirmed by an on-chain acceptance, not the
caller and not an evidence submitter. It is a recorded identity, not a fallback.

**A bond with no depositor recorded.** This cannot arise through the contract's
own methods: the only writer of `bond_deposited` sets `bond_depositor` in the
same branch. If it ever does arise, the contract raises. Choosing a recipient
there is the one failure worse than stopping.

No settlement method takes a recipient argument. `finalize_protocol`,
`recover_protocol` and `cancel_protocol` still take `protocol_id` and nothing
else, which the deployed schema shows.

## The tests you asked for

`tests/direct/test_roles.py` holds creator, responsible party, evidence
submitter and settlement caller as four different accounts throughout, and every
assertion names a recipient rather than checking that a payout happened.

| Test | Proves |
| --- | --- |
| the creator cannot accept on the responsible party's behalf | acceptance is the named account's own act |
| a stranger, and the evidence submitter, cannot accept | the same, from the other side |
| the bond cannot be posted before acceptance | nothing is staked on an account that has not agreed |
| a stranger cannot buy into somebody else's protocol | funding is not open to whoever has GEN |
| a wrong amount buys no title to anything | only an **accepted** payment records a depositor |
| a second attempt cannot take the first one's place | `bond_depositor` is written once |
| submitting evidence does not touch the bond depositor | provenance is not ownership |
| finalization pays the creator and the depositor whoever sends it | the caller is a trigger, not a payee |
| recovery pays the same two accounts whoever sends it | the same, on the timeout path |
| cancelling returns each deposit to whoever made it | the creator may cancel; the bond is still not theirs |
| nothing can be paid twice | the ledger zeroes before any transfer |

The cancellation test is the one that answers your report most directly. Under
the old contract it asserted that the creator received `REWARD + BOND`, and it
passed.

## Proved on chain, with three accounts

One live run, three accounts created for it, against the deployment above.

| Account | Role | Address |
| --- | --- | --- |
| A | creator; funds the reward | `0xE570f9deE0A9a81032842f8fAE671d407f9087e9` |
| B | responsible party; accepts, posts the bond | `0xd505af1F15b433545FCB7C7C13152777F6bcF309` |
| C | registers the first evidence, and sends both settling transactions | `0xdf21b57876980514E1205C7a3c558b88f6b46cC0` |

C is deliberately the strongest version of the original defect: under the old
contract it was both the first evidence submitter **and** the settlement caller,
so it would have collected the bond on either of the two inferences.

| Step | Transaction |
| --- | --- |
| A attempts to accept on B's behalf | [`0x63dd7bf2ce...`](https://explorer-studio.genlayer.com/tx/0x63dd7bf2cebd6d8930b3480a422e5e33e6a887abd563fc72ae19362d530a4849) — refused, `only the responsible party named in this protocol can accept it`, five validators agreeing |
| B accepts | [`0x5c5b4ba9a2...`](https://explorer-studio.genlayer.com/tx/0x5c5b4ba9a26e198781b2e607cd30763857d594da06a7d82055a9ff034f3f4787) |
| B posts the bond | [`0x5edd323c93...`](https://explorer-studio.genlayer.com/tx/0x5edd323c934e040fca58404b2521912be95c462e7891217d97e479f40e2f7cc6) |
| C finalizes `P7` | [`0x52d2730d52...`](https://explorer-studio.genlayer.com/tx/0x52d2730d5222e012832475401f1f2b35bce8499629919f058607575771a4600d) |
| C finalizes `P8` | [`0xfbced99eb0...`](https://explorer-studio.genlayer.com/tx/0xfbced99eb009282ee32bd8f7dbf7cf6dabba8093040f4afcb9d5491529ebb4ea) |

After funding, both protocols record `bond_depositor` as B, and `E1` — the first
evidence — as submitted by C. The two are different accounts in the record, which
is the thing the old contract could not represent.

Balances, read from the chain either side of each settlement, after the paying
transaction finalized:

| Protocol | Result | Contract paid A | Contract paid the bond side | A moved | B moved | **C moved** |
| --- | --- | --- | --- | --- | --- | --- |
| `P7` | `VERIFIED` | 0 | 0.03 GEN | 0 | **+0.03 GEN** | **0** |
| `P8` | `NOT_VERIFIED` | 0.03 GEN | 0 | **+0.03 GEN** | 0 | **0** |

C registered the first evidence and sent both settling transactions, and
received nothing either time. Under the old contract, `P7` would have paid C the
entire 0.03 GEN.

`bond_depositor` is still recorded as B on both protocols now that they hold
nothing, so the payments can be checked after the fact rather than taken on
trust.

## Checking it

```bash
python -m pytest tests/direct -q
```

```bash
python deploy/mutate.py
```

```bash
python deploy/verify_deployment.py 0xA4f7b476914B5475FF7Dd51FB5E83B9fF7760d3f
```

The live run costs real consensus rounds and is skipped by default:

```bash
SKIP_INTEGRATION=0 TRACE_DEMO_COMMIT=4205c56 \
  TRACE_CONTRACT_ADDRESS=0xA4f7b476914B5475FF7Dd51FB5E83B9fF7760d3f python -m pytest tests/integration -v -s
```

| | |
| --- | --- |
| Direct Mode | 170 passed |
| Live StudioNet | 32 passed, three accounts |
| Mutants | 84 of 87 killed, 3 documented equivalent, 0 undocumented |
| Console | lint, types, tests and build clean |
| CI | contract, console and mutants all green |

## What is not claimed

The guard for a bond held with no depositor recorded is **not** covered by a
test. It cannot be reached through the contract's own methods, so a test could
only produce the state by writing storage the API does not expose, which would
test the test. It is documented as an equivalent mutant with that reasoning
rather than counted as verified.

Redeployment was required: the storage layout changed and there is no upgrade
path, so the address above is new and the console points at it. The two earlier
deployments are superseded and the protocols on them are not part of this
record.
