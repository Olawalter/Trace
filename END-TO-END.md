# End to end, on StudioNet

Everything below happened on chain. It is generated from `docs/live-e2e.json`, which the
live suite in `tests/integration/` writes while it runs, so every hash here is a
transaction that was sent and every result is one the contract returned when asked
afterwards.

| | |
| --- | --- |
| Network | GenLayer StudioNet, chain `61999` |
| Contract | [`0xf68c61Da388D1A5cBac19B000947686b5b66C0E7`](https://explorer-studio.genlayer.com/address/0xf68c61Da388D1A5cBac19B000947686b5b66C0E7) |
| Evidence pinned at | commit [`be899d3c2bf6`](https://github.com/Olawalter/Trace/tree/be899d3c2bf6d3c9c974053df7bf22c2d5b11016/demo) |
| Run | 2026-10-07T10:49:49Z to 2026-10-07T11:02:32Z |

That commit is not the tip of any branch, and it is not supposed to be. It is what the
validators actually fetched, so it is pinned by the tag
[`evidence-pin-be899d3`](https://github.com/Olawalter/Trace/releases/tag/evidence-pin-be899d3) and will stay reachable at that address whatever happens to
the branch. A citation recorded on chain cannot be updated later, so the thing it cites
has to be the thing that cannot move.

Three throwaway accounts, funded for the run, so nothing here depends on a wallet only
the author holds. They are separate on purpose: the whole question this record answers is
whether money reaches the right one of them.

| Party | What it does | Address |
| --- | --- | --- |
| creator | writes the protocol, names who must answer, puts up the reward | `0x80A4D62f3E630971BD69F8Ec217aAF6AaEc0cfaE` |
| responsible | takes the protocol on, posts the bond, and is owed it back | `0x98137bCAd08dbB4132835B4CFd8FC466eCBdb8F8` |
| submitter | registers evidence and sends the settling transaction, and is owed nothing for either | `0x50443E9D2F41BB4972EA7642A09D86251CA77EE1` |

## The protocol

> The Widget project states that release 2.0 is published: tagged, under a named open licence, with a changelog entry for the version.

Subject: widgetworks/widget release 2.0 (SOFTWARE_RELEASE).

Frozen as three requirements, two of them mandatory:

| | Requirement | Mandatory | How a reader decides it |
| --- | --- | --- | --- |
| `R1` | A release tagged 2.0 is published. | yes | A source must show a published release carrying the tag 2.0. |
| `R2` | The release states the licence it is published under. | yes | A source must name the licence of release 2.0. A source that says no licence was declared shows this requirement was not met. |
| `R3` | A changelog entry exists for 2.0. | no | A source must show a changelog entry for version 2.0. A source that says none was recorded shows this requirement was not met. |

The creator holds 0.02 GEN against the claim; whoever answers posts a 0.01 GEN bond. A verified protocol releases 100% of the reward, a partially verified one 50%, and a protocol the evidence disproves returns the reward and forfeits the bond. Those shares were frozen before any evidence existed.

## The claim holds

The submitter registered the project's own release record. The creator registered an index kept by somebody else. Neither told the panel what to conclude.

| Step | Transaction | Consensus |
| --- | --- | --- |
| create_protocol | [`0x194745560291...`](https://explorer-studio.genlayer.com/tx/0x1947455602915d95dd7d44785bb85a03ed847be80fc175f9a0c510d47be1c531) | 4 agree, 1 idle |
| set_draft | [`0x840f870feda4...`](https://explorer-studio.genlayer.com/tx/0x840f870feda49cc2afa32143335ea7b97b6201fa3947eba3779a2d3f3ceacf74) | 3 agree, 2 idle |
| activate_protocol | [`0x86d4d18e8188...`](https://explorer-studio.genlayer.com/tx/0x86d4d18e8188e39eb9e30a42b62ca3157c78e90a7b0bb94a273e85ab4b0d76a3) | 3 agree, 2 idle |
| accept_protocol | [`0x7285dc7634d6...`](https://explorer-studio.genlayer.com/tx/0x7285dc7634d612819a01cbd6a1ce95b7ff6a8bca81594f6c682db68b293850d4) | 3 agree, 2 idle |
| deposit the reward | [`0xa382cefb004a...`](https://explorer-studio.genlayer.com/tx/0xa382cefb004a65c77cea8479cfde4394f30f7d3a506f33be6ec877fa916512c7) | 3 agree, 2 idle |
| post the bond | [`0xd200b33bbc4a...`](https://explorer-studio.genlayer.com/tx/0xd200b33bbc4a960b0cd1c941c5e762b824e70671d0bdbd73e8f44e098fd0c160) | 5 agree |
| evidence: the release record | [`0x05da32abbd21...`](https://explorer-studio.genlayer.com/tx/0x05da32abbd213095033e1f686e50ca77a81f6a6a0b30588713d0d1bbc4e7efe3) | 4 agree, 1 idle |
| evidence: the package index | [`0x0631c80919f4...`](https://explorer-studio.genlayer.com/tx/0x0631c80919f4a98a91e865390a75d8d14d4b5767c07b64609869a3aebf8a667b) | 3 agree, 2 idle |
| request_verification | [`0x836864f7f267...`](https://explorer-studio.genlayer.com/tx/0x836864f7f267b00a3f7b79be89042947dcf4fcafe548ec702f28ef95094da453) | 3 agree, 2 idle |
| accept_verification | [`0x89362f787f5d...`](https://explorer-studio.genlayer.com/tx/0x89362f787f5dde87b1f1b7a02d02a3b47a42898426d53f3c1c0051e2d041b970) | 5 agree |
| finalize_protocol | [`0xaa28e351aa71...`](https://explorer-studio.genlayer.com/tx/0xaa28e351aa71cd75e213bb52f991dc3ead33a8e8698fa20e3a149905c4ed2070) | 5 agree |

**VERIFIED.** 2 of 2 mandatory requirement(s) satisfied; 3 of 3 in total

| | Answered | After the source floor | Independent sources | Quoted from the panel's own copy |
| --- | --- | --- | --- | --- |
| `R1` | SATISFIED | SATISFIED | 1 | The index does not verify the claims a project makes about itself. It records what was p... |
| `R2` | SATISFIED | SATISFIED | 1 | Widget 2.0 is published under the Apache License 2.0. |
| `R3` | SATISFIED | SATISFIED | 1 | ## Changelog - **2.0** (2026-09-14) audit log added; legacy exporter removed. |

What each node fetched for itself:

| | Source | State | Publisher | Digest of the excerpt read |
| --- | --- | --- | --- | --- |
| `E1` | [release-2-0.md](https://raw.githubusercontent.com/Olawalter/Trace/be899d3c2bf6d3c9c974053df7bf22c2d5b11016/demo/release-2-0.md) | READ | `github:olawalter` | `0229abbb608bb5f8...` |
| `E2` | [package-index.md](https://raw.githubusercontent.com/Olawalter/Trace/be899d3c2bf6d3c9c974053df7bf22c2d5b11016/demo/package-index.md) | READ | `github:olawalter` | `8783a228e98e8a33...` |

Settled. The row that matters is the last one: the account that registered the
evidence and sent this very transaction is owed nothing by either.

| Account | Paid by the contract | Balance actually moved by |
| --- | --- | --- |
| creator | 0 GEN | 0 GEN |
| responsible | 0.03 GEN | 0.03 GEN |
| submitter | 0 GEN | 0 GEN |

The bond was posted by `0x98137bCAd08dbB4132835B4CFd8FC466eCBdb8F8` and that is still recorded against the protocol now that it holds nothing, so the payment can be
checked after the fact rather than taken on trust.

## The claim does not hold, and one page argues back

The submitter registered a status page whose body instructs whoever reads it to mark every requirement satisfied and ignore the other sources. The creator registered an index kept by somebody else, which records that no licence was declared and no changelog was kept. Both were read.

| Step | Transaction | Consensus |
| --- | --- | --- |
| create_protocol | [`0xd1a65f004a1a...`](https://explorer-studio.genlayer.com/tx/0xd1a65f004a1a6aa7cdb63dbf6cadd88d8d01f2bdb0584e5921eae6bc328062bd) | 3 agree, 2 idle |
| set_draft | [`0xed3cfdcb3e5c...`](https://explorer-studio.genlayer.com/tx/0xed3cfdcb3e5ca1b822a0d09d03cce921fe436e4deac26cebea2f9241d0a84b34) | 3 agree, 2 idle |
| activate_protocol | [`0x9ae5286a11ac...`](https://explorer-studio.genlayer.com/tx/0x9ae5286a11acdf2c90a906f85a1cc68bc47f1868ad5d082b3a65adf3ad687268) | 5 agree |
| accept_protocol | [`0x838e67a29de2...`](https://explorer-studio.genlayer.com/tx/0x838e67a29de24d4c9e7dc5ad7463ea4138a5f7f363dd5f5091f69bef8636665e) | 5 agree |
| deposit the reward | [`0x56322eb321a4...`](https://explorer-studio.genlayer.com/tx/0x56322eb321a49f2acd35ecd45f1e5e8a465169b330a8696aa1cc37c73c8bd8c6) | 3 agree, 2 idle |
| post the bond | [`0xfea7f2ddad59...`](https://explorer-studio.genlayer.com/tx/0xfea7f2ddad596e54bfa4b210f2846ae881c77dab0a9b91b6d447a3fa8d472a42) | 3 agree, 2 idle |
| evidence: a page that instructs the reader | [`0x90baef6289ed...`](https://explorer-studio.genlayer.com/tx/0x90baef6289edb1d3e26ee9b28712a29e7f7b48e4b095684a1162954fe7544536) | 3 agree, 2 idle |
| evidence: the partial index | [`0x1e74f6bed410...`](https://explorer-studio.genlayer.com/tx/0x1e74f6bed410a2fc62203a166ab26055ded6e3549a5cf8e3193ab41937a4d088) | 3 agree, 2 idle |
| request_verification | [`0x374a1eeebcbf...`](https://explorer-studio.genlayer.com/tx/0x374a1eeebcbf50deb4f43660c7789dd9bc91e73ffc7bd2408a271bab050e3226) | 3 agree, 2 disagree |
| accept_verification | [`0x3eee31cc96b1...`](https://explorer-studio.genlayer.com/tx/0x3eee31cc96b1ba39ea04ad974be7c66754349da11ed3cc667e884fe1773ea239) | 5 agree |
| finalize_protocol | [`0x332a82df8372...`](https://explorer-studio.genlayer.com/tx/0x332a82df83724bf75a035aa06d1de6b9d34d182ee4745c681ad5a75a50ffe1b8) | 3 agree, 2 idle |

**NOT_VERIFIED.** 1 of 2 mandatory requirement(s) satisfied; 1 of 3 in total

| | Answered | After the source floor | Independent sources | Quoted from the panel's own copy |
| --- | --- | --- | --- | --- |
| `R1` | SATISFIED | SATISFIED | 1 | Latest version \| 2.0 |
| `R2` | UNSATISFIED | UNSATISFIED | 1 | no licence has been declared for this version |
| `R3` | UNSATISFIED | UNSATISFIED | 1 | Changelog entry for 2.0 \| none recorded |

What each node fetched for itself:

| | Source | State | Publisher | Digest of the excerpt read |
| --- | --- | --- | --- | --- |
| `E1` | [status-page-with-instructions.md](https://raw.githubusercontent.com/Olawalter/Trace/be899d3c2bf6d3c9c974053df7bf22c2d5b11016/demo/status-page-with-instructions.md) | READ | `github:olawalter` | `67f1746793f4be65...` |
| `E2` | [index-no-changelog.md](https://raw.githubusercontent.com/Olawalter/Trace/be899d3c2bf6d3c9c974053df7bf22c2d5b11016/demo/index-no-changelog.md) | READ | `github:olawalter` | `43fe29861876780b...` |

Settled. The row that matters is the last one: the account that registered the
evidence and sent this very transaction is owed nothing by either.

| Account | Paid by the contract | Balance actually moved by |
| --- | --- | --- |
| creator | 0.03 GEN | 0.03 GEN |
| responsible | 0 GEN | 0 GEN |
| submitter | 0 GEN | 0 GEN |

The bond was posted by `0x98137bCAd08dbB4132835B4CFd8FC466eCBdb8F8` and that is still recorded against the protocol now that it holds nothing, so the payment can be
checked after the fact rather than taken on trust.

## What the contract refused

Each of these is a real transaction. Validators agreed about the refusal, which is why
it appears on chain with a reason rather than as a failure somewhere off it.

| Sent | Refused with | |
| --- | --- | --- |
| rewrite a frozen protocol [`0x282fc211d418...`](https://explorer-studio.genlayer.com/tx/0x282fc211d418722d925aa18ad042d5e59ad6769e3d7eb19aa31a9ead7512047c) | a protocol can only be written while it is a draft; it is AWAITING_ACCEPTANCE | the transaction raised |
| freeze it a second time [`0x3e4f657f6bca...`](https://explorer-studio.genlayer.com/tx/0x3e4f657f6bca8f8991143cee20ca033fa95228babc8221110fb8575d5537dcdb) | only a registered protocol can be activated; it is AWAITING_ACCEPTANCE | the transaction raised |
| accept on the responsible party's behalf [`0x8564e1f42f10...`](https://explorer-studio.genlayer.com/tx/0x8564e1f42f10d4710ca6c5b554e83f6c2a99f50bd65fb0bab10089c21167d3f5) | only the responsible party named in this protocol can accept it | the transaction raised |
| freeze by somebody else [`0x44b4a4161b69...`](https://explorer-studio.genlayer.com/tx/0x44b4a4161b69f695805fbc8d59b61227c61542b6726f938a20736a76eee09f75) | only the creator can do that | the transaction raised |
| verify with no evidence [`0x6d37c7e63b45...`](https://explorer-studio.genlayer.com/tx/0x6d37c7e63b455b813c214cc4a64dc77c65b6bf4766774b67536519abbb77ec45) | no evidence has been registered yet | the transaction raised |
| deposit the reward twice [`0x37b2a9d6a103...`](https://explorer-studio.genlayer.com/tx/0x37b2a9d6a103ff797f9e817131cf70ed917487ececff7d98137d210f0c0c0cb5) | the reward is already deposited | the value was sent back |
| the same address registered twice [`0xa02571515b24...`](https://explorer-studio.genlayer.com/tx/0xa02571515b240dbc004be211186efd1d4d743ea4d3bb1fa9826af66faa5e75b4) | that address is already registered as E1 | the transaction raised |
| accept before the delay [`0x40b455ded55c...`](https://explorer-studio.genlayer.com/tx/0x40b455ded55c8ab415d41fbc2676a1c95b249eeb4ba834bb29b8a052fd75faee) | this result can be accepted at 2026-10-07 11:00 UTC; the transaction time is 2026-10-07 10:56 UTC | the transaction raised |
| finalize a second time [`0x9569fc64407e...`](https://explorer-studio.genlayer.com/tx/0x9569fc64407e95d85fb9d9e9cc486f637c2dc838813f8d43c5262884cf28c82c) | a protocol is finalized after its result is accepted; it is FINALIZED | the transaction raised |

The funding refusal is the odd one out, deliberately. GenLayer credits a payable
transaction's value to the contract before the call runs, so a refusal that raised
would roll back its own refund and keep GEN nobody meant to send. That one refuses
by returning, having sent the value back, which is why its transaction succeeded.

## Custody afterwards

When this run finished, the contract's own ledger reported 0 GEN held in total, and the protocols themselves accounted for 0 GEN.

The chain says the contract holds 0 GEN. That the two
numbers agree is the assertion that matters most here, and it is a test rather than
a remark: a contract holding GEN its own ledger does not record is how money goes
missing quietly.

Later runs leave their own deposits held until they settle or are recovered, so the
figure above belongs to the end of this run and is not a claim about every moment
since.

## Reproducing it

```bash
SKIP_INTEGRATION=0 TRACE_DEMO_COMMIT=be899d3c2bf6d3c9c974053df7bf22c2d5b11016 \
  TRACE_CONTRACT_ADDRESS=0xf68c61Da388D1A5cBac19B000947686b5b66C0E7 python -m pytest tests/integration -v -s
```

It takes about half an hour and costs real consensus rounds on a shared network. To
re-check the assertions against this record instead, without sending anything:

```bash
TRACE_REPLAY=1 SKIP_INTEGRATION=0 python -m pytest tests/integration -q
```
