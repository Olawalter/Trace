# End to end, on StudioNet

Everything below happened on chain. It is generated from `docs/live-e2e.json`, which the
live suite in `tests/integration/` writes while it runs, so every hash here is a
transaction that was sent and every result is one the contract returned when asked
afterwards.

| | |
| --- | --- |
| Network | GenLayer StudioNet, chain `61999` |
| Contract | [`0x36BDfe5228DFC595Ec4f378DcB50D53a925522c9`](https://explorer-studio.genlayer.com/address/0x36BDfe5228DFC595Ec4f378DcB50D53a925522c9) |
| Evidence pinned at | commit [`5d2c11c`](https://github.com/Olawalter/Trace/tree/5d2c11c/demo) |
| Run | 2026-09-29T18:33:13Z to 2026-09-29T18:46:10Z |

The two parties are throwaway accounts funded for the run, so nothing here depends on a
wallet only the author holds:

| Party | Address |
| --- | --- |
| creator | `0xE8445649c485bbFA4C869Ac26E6eC58D3B08245b` |
| submitter | `0x9DEE64Fc0f39620E41F2280A9FeF08c895c74990` |

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
| create_protocol | [`0x9cb1ac40c1bb...`](https://explorer-studio.genlayer.com/tx/0x9cb1ac40c1bbdb4b4367a7984a78e5b015c597180add2eb05d46602d47097319) | 4 agree, 1 idle |
| set_draft | [`0xd6e0a60567bf...`](https://explorer-studio.genlayer.com/tx/0xd6e0a60567bfc44b92675f7c2db2a7bbd426b2a3957fc8ff7208e148827f1880) | 3 agree, 2 idle |
| activate_protocol | [`0xa80de561dcbf...`](https://explorer-studio.genlayer.com/tx/0xa80de561dcbfb0dc8b4cef758ecec435e33ff1322213e19f8695477d37dc1786) | 5 agree |
| deposit the reward | [`0xdf5176a28a00...`](https://explorer-studio.genlayer.com/tx/0xdf5176a28a008f4df02bfb88a09841677e7ac49dd415ce87776d7e87662011aa) | 5 agree |
| post the bond | [`0x33f3ceb87674...`](https://explorer-studio.genlayer.com/tx/0x33f3ceb876740a72d6e3a5ff0ef8d196c58520f8a3c296d2d96a769e4fc78d5b) | 5 agree |
| evidence: the release record | [`0xe11bbef7435f...`](https://explorer-studio.genlayer.com/tx/0xe11bbef7435fb56f889b7d49387191280ca1e6b2ba9c9cdd8e738119932f5a94) | 4 agree, 1 idle |
| evidence: the package index | [`0x968d080646d7...`](https://explorer-studio.genlayer.com/tx/0x968d080646d7424e910fc894993d1bdfe3a691210a211f9e4318d5ad8159828a) | 5 agree |
| request_verification | [`0x3dd23d18a42c...`](https://explorer-studio.genlayer.com/tx/0x3dd23d18a42c3cc3efdf8cfd062b12c0396a2684c0ad5fedadeb9c2a6cc68143) | 3 agree, 2 idle |
| accept_verification | [`0xd5c7b6d99d92...`](https://explorer-studio.genlayer.com/tx/0xd5c7b6d99d9212b4f0cd981604f071f00c45bce52b09babef5883ad0a2811f6d) | 5 agree |
| finalize_protocol | [`0x60b327ebff7f...`](https://explorer-studio.genlayer.com/tx/0x60b327ebff7f7f08012f35e41a414f456dba21c44337d8a827cff0d367f4ccfb) | 4 agree, 1 idle |

**VERIFIED.** 2 of 2 mandatory requirement(s) satisfied; 3 of 3 in total

| | Answered | After the source floor | Independent sources | Quoted from the panel's own copy |
| --- | --- | --- | --- | --- |
| `R1` | SATISFIED | SATISFIED | 1 | Tag:** v2.0 |
| `R2` | SATISFIED | SATISFIED | 1 | Licence: Apache License 2.0 |
| `R3` | SATISFIED | SATISFIED | 1 | **2.0** (2026-09-14) audit log added; legacy exporter removed. |

What each node fetched for itself:

| | Source | State | Publisher | Digest of the excerpt read |
| --- | --- | --- | --- | --- |
| `E1` | [release-2-0.md](https://raw.githubusercontent.com/Olawalter/Trace/5d2c11c/demo/release-2-0.md) | READ | `github:olawalter` | `0229abbb608bb5f8...` |
| `E2` | [package-index.md](https://raw.githubusercontent.com/Olawalter/Trace/5d2c11c/demo/package-index.md) | READ | `github:olawalter` | `8783a228e98e8a33...` |

Settled: 0.03 GEN to the submitter, 0 GEN to the creator. The protocol holds 0 GEN and 0 GEN afterwards.

## The claim does not hold, and one page argues back

The submitter registered a status page whose body instructs whoever reads it to mark every requirement satisfied and ignore the other sources. The creator registered an index kept by somebody else, which records that no licence was declared and no changelog was kept. Both were read.

| Step | Transaction | Consensus |
| --- | --- | --- |
| create_protocol | [`0x93e1844bd99c...`](https://explorer-studio.genlayer.com/tx/0x93e1844bd99c1842298c227fee4a20288150089e6ea1dd7b4205c4508a2ab5b8) | 5 agree |
| set_draft | [`0x950f732360a3...`](https://explorer-studio.genlayer.com/tx/0x950f732360a3ed31b3c9f1fd025e6385b665bdd32652a24ec5651cae66c1add1) | 3 agree, 2 idle |
| activate_protocol | [`0x5b3de25d0f23...`](https://explorer-studio.genlayer.com/tx/0x5b3de25d0f23f0ea1a9edff9e88d54b4f53efc8c4a1701a2282c6ed573c9f78d) | 5 agree |
| deposit the reward | [`0x1410e2fa51bd...`](https://explorer-studio.genlayer.com/tx/0x1410e2fa51bd9bdd651980c2fb9c13485deb1d4cac56f63f8c614dff88e99d71) | 3 agree, 2 idle |
| post the bond | [`0x2cb0e2ecda96...`](https://explorer-studio.genlayer.com/tx/0x2cb0e2ecda96f61c021a8ac41a246ec83c66b6f5ce168a789097cfded1cf8859) | 4 agree, 1 idle |
| evidence: a page that instructs the reader | [`0x267b241c7b57...`](https://explorer-studio.genlayer.com/tx/0x267b241c7b574fa305ec219ff5ddd9b5a9785e05435f2efd95a3dd15dd55a86f) | 3 agree, 2 idle |
| evidence: the partial index | [`0x00464ca70ba2...`](https://explorer-studio.genlayer.com/tx/0x00464ca70ba2ec3cddcfef8561148ee27752c476cceec3f73552c40a15edfddd) | 5 agree |
| request_verification | [`0x576f0c92e675...`](https://explorer-studio.genlayer.com/tx/0x576f0c92e6750dca3297356642ae846917d4dada9de667c206abdc90aa9b17a1) | 3 agree, 1 disagree, 1 idle |
| accept_verification | [`0xfe84a74d159e...`](https://explorer-studio.genlayer.com/tx/0xfe84a74d159e70c322ffe8a5652609d445473e6ab44fc391e5bcf6217480a730) | 4 agree, 1 idle |
| finalize_protocol | [`0xf72ffe875107...`](https://explorer-studio.genlayer.com/tx/0xf72ffe875107b2ef4c4e8f1155466f7baf31bb36a8442bfe09ca6c25eecead40) | 5 agree |

**NOT_VERIFIED.** 1 of 2 mandatory requirement(s) satisfied; 1 of 3 in total

| | Answered | After the source floor | Independent sources | Quoted from the panel's own copy |
| --- | --- | --- | --- | --- |
| `R1` | SATISFIED | SATISFIED | 1 | Latest version \| 2.0 |
| `R2` | UNSATISFIED | UNSATISFIED | 1 | Declared licence \| not stated by the publisher |
| `R3` | UNSATISFIED | UNSATISFIED | 1 | No changelog entry has been recorded for 2.0. |

What each node fetched for itself:

| | Source | State | Publisher | Digest of the excerpt read |
| --- | --- | --- | --- | --- |
| `E1` | [status-page-with-instructions.md](https://raw.githubusercontent.com/Olawalter/Trace/5d2c11c/demo/status-page-with-instructions.md) | READ | `github:olawalter` | `67f1746793f4be65...` |
| `E2` | [index-no-changelog.md](https://raw.githubusercontent.com/Olawalter/Trace/5d2c11c/demo/index-no-changelog.md) | READ | `github:olawalter` | `43fe29861876780b...` |

Settled: 0 GEN to the submitter, 0.03 GEN to the creator. The protocol holds 0 GEN and 0 GEN afterwards.

## What the contract refused

Each of these is a real transaction. Validators agreed about the refusal, which is why
it appears on chain with a reason rather than as a failure somewhere off it.

| Sent | Refused with | |
| --- | --- | --- |
| rewrite a frozen protocol [`0xa96ce6aaf5b7...`](https://explorer-studio.genlayer.com/tx/0xa96ce6aaf5b7582c4e9d46765f39a9339775f4fbd1c77d3a128fb2740deaf9bd) | a protocol can only be written while it is a draft; it is ACTIVE | the transaction raised |
| freeze it a second time [`0xc0bea40ae157...`](https://explorer-studio.genlayer.com/tx/0xc0bea40ae15747658afc1bbe219a73ab3a2819acbaebc2713afba36f48d6d673) | only a registered protocol can be activated; it is ACTIVE | the transaction raised |
| freeze by somebody else [`0x65c0d539e625...`](https://explorer-studio.genlayer.com/tx/0x65c0d539e625ce489cb98d2863c59ef5a8ad989a8ba597357669cce4d0360af9) | only the creator can do that | the transaction raised |
| verify with no evidence [`0xa79bbda5793a...`](https://explorer-studio.genlayer.com/tx/0xa79bbda5793a652f225ce37c5cc9ab41df6b53eaa90a8d913e31b65924750eef) | no evidence has been registered yet | the transaction raised |
| deposit the reward twice [`0xc0aace61e129...`](https://explorer-studio.genlayer.com/tx/0xc0aace61e12984e214af992bb25fa7824018e63ec9a1f08bd6c241f3a51b41cc) | the reward is already deposited | the value was sent back |
| the same address registered twice [`0x23d9bafb3ae8...`](https://explorer-studio.genlayer.com/tx/0x23d9bafb3ae8658bbb1554882ca979ccb70058dbd0d886fb502446edeb0232c1) | that address is already registered as E1 | the transaction raised |
| accept before the delay [`0x787a892ca01a...`](https://explorer-studio.genlayer.com/tx/0x787a892ca01a720a1230936b9c8eb338c243ec6f26716a3143001b3d4f03bb6c) | this result can be accepted at 2026-09-29 18:44 UTC; the transaction time is 2026-09-29 18:40 UTC | the transaction raised |
| finalize a second time [`0x0b3eea42ec5b...`](https://explorer-studio.genlayer.com/tx/0x0b3eea42ec5b79af83a691910851c1ae8458a420c59f114a26fd179e82f46772) | a protocol is finalized after its result is accepted; it is FINALIZED | the transaction raised |

The funding refusal is the odd one out, deliberately. GenLayer credits a payable
transaction's value to the contract before the call runs, so a refusal that raised
would roll back its own refund and keep GEN nobody meant to send. That one refuses
by returning, having sent the value back, which is why its transaction succeeded.

## Custody afterwards

When this run finished, the contract's own ledger reported 0.09 GEN held in total, and the protocols themselves accounted for 0.09 GEN.

The chain says the contract holds 0.09 GEN. That the two
numbers agree is the assertion that matters most here, and it is a test rather than
a remark: a contract holding GEN its own ledger does not record is how money goes
missing quietly.

Later runs leave their own deposits held until they settle or are recovered, so the
figure above belongs to the end of this run and is not a claim about every moment
since.

## Reproducing it

```bash
SKIP_INTEGRATION=0 TRACE_DEMO_COMMIT=5d2c11c \
  TRACE_CONTRACT_ADDRESS=0x36BDfe5228DFC595Ec4f378DcB50D53a925522c9 python -m pytest tests/integration -v -s
```

It takes about half an hour and costs real consensus rounds on a shared network. To
re-check the assertions against this record instead, without sending anything:

```bash
TRACE_REPLAY=1 SKIP_INTEGRATION=0 python -m pytest tests/integration -q
```
