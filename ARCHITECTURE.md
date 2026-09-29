# Architecture

TRACE has four participants, and almost everything that could go wrong is a job
given to the wrong one.

```
  a person                the contract             GenLayer validators          a model
  --------                ------------             -------------------          -------
  writes requirements -->  checks and stores them
  freezes the protocol --> records a fingerprint;
                           nothing can change after
  registers evidence  -->  records the address, the
                           kind, who registered it
  asks for a round    -->  starts one round   -->   every node fetches every
                                                    source itself
                                                                          -->   reads the sources,
                                                                                answers ONE
                                                                                requirement, quotes
                                                                                what it relied on
                                                    each node derives the
                                                    same result and compares
                                                    a fingerprint of it
                           re-derives the result <- the agreed answers
                           from the agreed answers
                           waits five minutes
                           pays by basis points
```

## What each one owns

### The contract owns everything a mistake would be expensive in

Who may act, what is held, the acceptance delay, the independent-source floor,
the caps, and the arithmetic from a result to a payment in GEN. None of it
consults a model. A model's output enters the contract as one of three status
words per requirement, plus a quote, and nothing else it says can move value.

The contract also owns the **aggregation**: given the agreed requirement
answers, it computes `VERIFIED`, `PARTIALLY_VERIFIED`, `NOT_VERIFIED`,
`INCONCLUSIVE` or `PROTOCOL_DEVIATION` itself.

That is deliberate. If a model named the overall result, a model that got one
requirement subtly wrong could name a result that does not follow from its own
answers, and nobody reading the record could tell the difference. The precedence
is written out in `_derive_result` and tested over every combination:

```
the evidence does not meet the frozen evidence policy   -> PROTOCOL_DEVIATION
a mandatory requirement the evidence disproves          -> NOT_VERIFIED
a mandatory requirement nothing settles                 -> INCONCLUSIVE
every requirement satisfied                             -> VERIFIED
every mandatory one satisfied, an optional one not      -> PARTIALLY_VERIFIED
```

One place departs from the ordering the brief suggests, deliberately: a
mandatory requirement that the evidence **shows was not met** decides
`NOT_VERIFIED` even when another mandatory requirement is unresolved. Resolving
the unresolved one cannot make the protocol verified, so calling the whole thing
inconclusive would throw away something the evidence actually settled. It is
tested as `test_a_proven_failure_outranks_an_unresolved_one`.

### GenLayer consensus owns whether the evidence satisfies the protocol

`request_verification` runs `gl.vm.run_nondet_unsafe(leader_fn, validator_fn)`.

The leader fetches every registered source, asks the model once per requirement,
assembles a result and returns it. Every validator does the same work
independently -- its own fetches, its own model calls -- and then compares. It
does not check that the leader's JSON is well shaped and wave it through; it
produces its own answer and compares the fields a consequence depends on.

The comparison is deliberately narrow **and** deliberately complete:

| Compared | Not compared |
| --- | --- |
| each requirement's status | the reasoning text |
| each requirement's status after the independent-source floor | the wording of a quote |
| how many independent publishers stood behind each answer | which evidence ids a node happened to cite |
| the derived overall result, and whether the policy was met | the summary sentence |
| each source's id, availability and publisher | the excerpt, which differs by renderer |

Everything on the left changes what happens to the money or what the record
asserts. Everything on the right is a different way of saying the same thing:
two honest nodes routinely cite different subsets of the same sources while
answering identically, and no two model calls write the same sentence. What the
floor actually uses is the *number* of independent publishers, and that is
compared.

A quote is still required and still checked -- but by each node against **its
own** copy of the source, which is a stronger test than agreeing with the
leader's citation.

Strict equality is not an option here. It would compare two model-written
sentences, which are never identical, so every round would fail even when both
nodes reached the same verdict.

### The model owns reading

One prompt per requirement, with every source fenced, asking for a status, a
quote and the sources relied on. It is never asked what the protocol's overall
result is, never asked what should be paid, and never trusted about whether a
document exists -- availability is decided by the fetch, in code.

Its answer is checked before it counts:

- a decisive status must carry a quote,
- that quote must appear in **this node's own copy** of a source it cited,
- that source must have been readable, and registered against that requirement.

If any of those fails, the status is demoted to `UNCERTAIN` and the reasoning is
kept. A confident answer that cannot be traced to a document is worth less than
an honest "unclear".

### The console owns none of the decisions

`frontend/` is a Next.js app with no server of its own, no route handlers and no
database. It reads the contract and composes transactions the person signs in
their wallet. Every rule it enforces in a form is a mirror of a rule the contract
enforces, so a mistake is caught while typing instead of costing a transaction --
and the contract still checks all of it, because a mirror is a convenience, not a
guarantee.

## Deterministic and nondeterministic, exactly

| Deterministic, in the contract | Nondeterministic, inside the round |
| --- | --- |
| authorization and protocol state | fetching each source |
| requirement ids and immutability after the freeze | reducing a page to text |
| deadline and window checks | reading a source against one requirement |
| the independent-source floor | -- |
| the evidence-policy check | -- |
| aggregation into an overall result | -- |
| the escrow ledger and every payout | -- |

Nothing is written from inside a nondeterministic block. A round returns a value
the validators agreed on; the contract then checks its shape, re-derives the
overall result from the agreed answers, compares the two, and only then writes.

## Why this cannot be a server, an oracle, or one model call

Ask of any step: *could an oracle or plain code do this?* Where the answer is
yes, TRACE does it in plain code -- the deadlines, the splits, the caps, the
custody, the policy check.

Where the answer is no, the step is exactly what GenLayer exists for:

- *"The release states the licence it is published under"* -- needs a reader, and
  a reader hired by one party is that party's opinion.
- *"A changelog entry exists for this version"* -- needs judgement about what a
  document says versus what it implies.
- *"These two sources disagree"* -- needs the disagreement to be recognised
  rather than resolved by whichever page was read last.

A backend could compute all three. It could not make them **binding**, because
the other side has no reason to accept a number produced by a machine one side
controls. The value of putting it on GenLayer is that several independent nodes
fetched the evidence, answered separately, and had to agree before a single GEN
moved -- and that when they do not agree, nothing is written and that is visible.

## One round, and what happens when it fails

A round that reaches no majority writes nothing. The protocol stays as it was,
the evidence stays registered, and anybody can ask again after ten minutes, up to
three rounds. The console shows that as what it is: not a verdict of
`INCONCLUSIVE`, but an absence.

If no round ever succeeds, the deadline and the recovery window pass and
`recover_protocol` ends the protocol under the rule frozen at the start. There is
no path where GEN stays in the contract because a question was never answered.

## Storage

Protocols live in a `TreeMap[str, Protocol]`; each `Protocol` is an
`@allow_storage` dataclass holding its own `DynArray` lists of evidence ids,
verification ids and history rows. Sub-objects that vary in shape -- the frozen
definition, an evidence row, a verification record -- are stored as canonical
JSON strings with sorted keys, so the same content always hashes the same way.

Money is `u256` in atto-GEN throughout. No float touches a balance.

## The lifecycle

```
DRAFT  --set_draft-->  REGISTERED  --activate_protocol-->  ACTIVE
                                                             |
                                          submit_evidence    |
                                                             v
                                                   EVIDENCE_SUBMITTED
                                                             |
                                             request_verification
                                                             |
                                        (VERIFICATION_PENDING, inside
                                         the same transaction)
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

DRAFT / REGISTERED / ACTIVE  --cancel_protocol-->  CANCELLED
ACTIVE / EVIDENCE_SUBMITTED / VERDICT_PROPOSED
        --recover_protocol (deadline + window passed)-->  FINALIZED
```

`VERIFICATION_PENDING` exists inside one transaction: it is recorded in the
history so the path is visible, and it cannot persist, because a round that
reaches no majority writes nothing at all.

These are TRACE's states. GenLayer's own transaction states -- pending,
proposing, accepted, finalized -- are separate and are shown separately in the
console. A transaction can be `FINALIZED` while the protocol it carried is
`PARTIALLY_VERIFIED`: GenLayer finalized the transaction that produced the
result, which says nothing about what the result was.
