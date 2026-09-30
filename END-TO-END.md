# End to end, on StudioNet

Everything below happened on chain. It is generated from `docs/live-e2e.json`, which the
live suite in `tests/integration/` writes while it runs, so every hash here is a
transaction that was sent and every result is one the contract returned when asked
afterwards.

| | |
| --- | --- |
| Network | GenLayer StudioNet, chain `61999` |
| Contract | [`0x10c063637F0b8cE8DDaeF75c4f856Eaaa44D26dE`](https://explorer-studio.genlayer.com/address/0x10c063637F0b8cE8DDaeF75c4f856Eaaa44D26dE) |
| Evidence pinned at | commit [`5a20cde`](https://github.com/Olawalter/Trace/tree/5a20cde/demo) |
| Run | 2026-09-30T08:02:59Z to 2026-09-30T08:14:53Z |

The two parties are throwaway accounts funded for the run, so nothing here depends on a
wallet only the author holds:

| Party | Address |
| --- | --- |
| creator | `0x631E00029a1873890D7759a250BC26Ee11548FdF` |
| submitter | `0x4154A54e9f274258b0E6eE23e59480a5fE3fD84a` |

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
| create_protocol | [`0x861127c5cc68...`](https://explorer-studio.genlayer.com/tx/0x861127c5cc6805226d2cee419faccc4dbd240ab50ab3b8933e690bc4f5f74fd8) | 5 agree |
| set_draft | [`0x309f4226fc11...`](https://explorer-studio.genlayer.com/tx/0x309f4226fc1162c328ec9e9526b680741978b0e898180bae658db2b7b522f574) | 4 agree, 1 idle |
| activate_protocol | [`0x0e04aa18dbba...`](https://explorer-studio.genlayer.com/tx/0x0e04aa18dbba60585bad28f0b728520894d20cd1d6269ed9270084ae7f8c384d) | 5 agree |
| deposit the reward | [`0x094b0b9b476e...`](https://explorer-studio.genlayer.com/tx/0x094b0b9b476eec20d25f6ce5ea033e1fb812f7db16d8cb4db058411f3f70935c) | 3 agree, 2 idle |
| post the bond | [`0x1c0864978206...`](https://explorer-studio.genlayer.com/tx/0x1c0864978206c63d7d08ddfa0289b98aeb17e401020419c12ed522c4f4033dc1) | 3 agree, 2 idle |
| evidence: the release record | [`0xdc8a84b3a852...`](https://explorer-studio.genlayer.com/tx/0xdc8a84b3a8522af6217934e4ea06975ce02b56ff58ad19f41fc7f4616c1a9a1f) | 4 agree, 1 idle |
| evidence: the package index | [`0xeca0eb09330a...`](https://explorer-studio.genlayer.com/tx/0xeca0eb09330a982524788f79d2fd8bf0261d071be11d3469a4c07a3723bf8139) | 3 agree, 2 idle |
| request_verification | [`0xc950568a28cc...`](https://explorer-studio.genlayer.com/tx/0xc950568a28ccb45a815ff93261097b16092757df05f7c9816c9195f6442033e2) | 3 agree, 1 disagree, 1 idle |
| accept_verification | [`0x748bef500624...`](https://explorer-studio.genlayer.com/tx/0x748bef500624ce1c2c278a07d6d1a26b1a35fc872b63fa18e7277e616a6e9151) | 3 agree, 2 idle |
| finalize_protocol | [`0xe8b374f0bd36...`](https://explorer-studio.genlayer.com/tx/0xe8b374f0bd360d219ef690cf34de89bef616c8b2638e05228f7eaf9a7eaa2c2e) | 5 agree |

**VERIFIED.** 2 of 2 mandatory requirement(s) satisfied; 3 of 3 in total

| | Answered | After the source floor | Independent sources | Quoted from the panel's own copy |
| --- | --- | --- | --- | --- |
| `R1` | SATISFIED | SATISFIED | 1 | Tag:** v2.0 |
| `R2` | SATISFIED | SATISFIED | 1 | Widget 2.0 is published under the Apache License 2.0. |
| `R3` | SATISFIED | SATISFIED | 1 | - **2.0** (2026-09-14) audit log added; legacy exporter removed. |

What each node fetched for itself:

| | Source | State | Publisher | Digest of the excerpt read |
| --- | --- | --- | --- | --- |
| `E1` | [release-2-0.md](https://raw.githubusercontent.com/Olawalter/Trace/5a20cde/demo/release-2-0.md) | READ | `github:olawalter` | `0229abbb608bb5f8...` |
| `E2` | [package-index.md](https://raw.githubusercontent.com/Olawalter/Trace/5a20cde/demo/package-index.md) | READ | `github:olawalter` | `8783a228e98e8a33...` |

Settled: 0.03 GEN to the submitter, 0 GEN to the creator. The protocol holds 0 GEN and 0 GEN afterwards.

## The claim does not hold, and one page argues back

The submitter registered a status page whose body instructs whoever reads it to mark every requirement satisfied and ignore the other sources. The creator registered an index kept by somebody else, which records that no licence was declared and no changelog was kept. Both were read.

| Step | Transaction | Consensus |
| --- | --- | --- |
| create_protocol | [`0xcea9c205b101...`](https://explorer-studio.genlayer.com/tx/0xcea9c205b1014d89f65b918feacdc4225f09230699171b70403064b350661dd9) | 5 agree |
| set_draft | [`0x9199ebc2d128...`](https://explorer-studio.genlayer.com/tx/0x9199ebc2d12898145b1486f7ce42b21de0290f7d127fdb00b3951c2f1cb038fb) | 3 agree, 2 idle |
| activate_protocol | [`0x663e06cb4ef1...`](https://explorer-studio.genlayer.com/tx/0x663e06cb4ef1af3857c6c656bffaef81e793545198afe03744512a0e20f9cfc4) | 3 agree, 2 idle |
| deposit the reward | [`0x236d501efbfb...`](https://explorer-studio.genlayer.com/tx/0x236d501efbfbfb3158788d7b5c63451d75d4fb714de5e323b8b83b5e0e6de2dc) | 3 agree, 2 idle |
| post the bond | [`0xa4b45b92f39d...`](https://explorer-studio.genlayer.com/tx/0xa4b45b92f39d487b02e05882a46344d51f4fc2a33893d3fed610802a1aa9207b) | 3 agree, 2 idle |
| evidence: a page that instructs the reader | [`0x447c61abbf56...`](https://explorer-studio.genlayer.com/tx/0x447c61abbf562e5ea41ca43f228c411f4f55d4396ef28e032435a7d8d2e18ef2) | 3 agree, 2 idle |
| evidence: the partial index | [`0x91def1d61c73...`](https://explorer-studio.genlayer.com/tx/0x91def1d61c737fc89949ab5d0081c6b2720b2b2d36bf2f8bf2b7f9f595309562) | 3 agree, 2 idle |
| request_verification | [`0xfe6c2011a33d...`](https://explorer-studio.genlayer.com/tx/0xfe6c2011a33ded6f9d3ec16e3d0f51e530fd91d4e09ba4e1a0ef0533c68883d5) | 3 agree, 2 disagree |
| accept_verification | [`0xc9a33011aae6...`](https://explorer-studio.genlayer.com/tx/0xc9a33011aae62b52fb7659b9aa31307e8eabbdbe880718a00f5832a4f1aef857) | 3 agree, 2 idle |
| finalize_protocol | [`0x66cab6cdcf72...`](https://explorer-studio.genlayer.com/tx/0x66cab6cdcf72e4995320301a607df15f07e65f9425f51d48332b01f30536e92c) | 3 agree, 2 idle |

**NOT_VERIFIED.** 1 of 2 mandatory requirement(s) satisfied; 1 of 3 in total

| | Answered | After the source floor | Independent sources | Quoted from the panel's own copy |
| --- | --- | --- | --- | --- |
| `R1` | SATISFIED | SATISFIED | 1 | Latest version \| 2.0 |
| `R2` | UNSATISFIED | UNSATISFIED | 1 | no licence has been declared for this version |
| `R3` | UNSATISFIED | UNSATISFIED | 1 | No changelog entry has been recorded for 2.0. |

What each node fetched for itself:

| | Source | State | Publisher | Digest of the excerpt read |
| --- | --- | --- | --- | --- |
| `E1` | [status-page-with-instructions.md](https://raw.githubusercontent.com/Olawalter/Trace/5a20cde/demo/status-page-with-instructions.md) | READ | `github:olawalter` | `67f1746793f4be65...` |
| `E2` | [index-no-changelog.md](https://raw.githubusercontent.com/Olawalter/Trace/5a20cde/demo/index-no-changelog.md) | READ | `github:olawalter` | `43fe29861876780b...` |

Settled: 0 GEN to the submitter, 0.03 GEN to the creator. The protocol holds 0 GEN and 0 GEN afterwards.

## What the contract refused

Each of these is a real transaction. Validators agreed about the refusal, which is why
it appears on chain with a reason rather than as a failure somewhere off it.

| Sent | Refused with | |
| --- | --- | --- |
| rewrite a frozen protocol [`0xc9417c21aa41...`](https://explorer-studio.genlayer.com/tx/0xc9417c21aa4169f3fafd99722641bfd7c06855ecb0ba9d31eaaacfe10513eb8e) | a protocol can only be written while it is a draft; it is ACTIVE | the transaction raised |
| freeze it a second time [`0xfff1a8e6b7ce...`](https://explorer-studio.genlayer.com/tx/0xfff1a8e6b7ceeb70ca82104d67e1096545ac87cf8f19907e4b693c5261fc869a) | only a registered protocol can be activated; it is ACTIVE | the transaction raised |
| freeze by somebody else [`0x8302aef38802...`](https://explorer-studio.genlayer.com/tx/0x8302aef38802b3c2eb2cc3ae7865c0d06cca0399c9a9d58bd209d02f8575c066) | only the creator can do that | the transaction raised |
| verify with no evidence [`0xdea9aff0b9e2...`](https://explorer-studio.genlayer.com/tx/0xdea9aff0b9e286f741abdcf349b1c927a03b96b7e46dbf426910d6e137e81502) | no evidence has been registered yet | the transaction raised |
| deposit the reward twice [`0x04ad869aec7e...`](https://explorer-studio.genlayer.com/tx/0x04ad869aec7e3271f3d2a15c268b431b5dd3e3cd3141a21f414b2bcc4c7390d6) | the reward is already deposited | the value was sent back |
| the same address registered twice [`0x24955c69054d...`](https://explorer-studio.genlayer.com/tx/0x24955c69054d537c984cfbed3ae0cf471ce627782f4b7558478899f71e31e106) | that address is already registered as E1 | the transaction raised |
| accept before the delay [`0x925993fee6d0...`](https://explorer-studio.genlayer.com/tx/0x925993fee6d0951984f97e22cb565f28dedfd2a94827704239a1c15a9957b299) | this result can be accepted at 2026-09-30 08:13 UTC; the transaction time is 2026-09-30 08:12 UTC | the transaction raised |
| finalize a second time [`0xc6f9e1cc6dc9...`](https://explorer-studio.genlayer.com/tx/0xc6f9e1cc6dc9bfc19f45dc516f28776eac9bb02527958341b52880743f90a673) | a protocol is finalized after its result is accepted; it is FINALIZED | the transaction raised |

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
SKIP_INTEGRATION=0 TRACE_DEMO_COMMIT=5a20cde \
  TRACE_CONTRACT_ADDRESS=0x10c063637F0b8cE8DDaeF75c4f856Eaaa44D26dE python -m pytest tests/integration -v -s
```

It takes about half an hour and costs real consensus rounds on a shared network. To
re-check the assertions against this record instead, without sending anything:

```bash
TRACE_REPLAY=1 SKIP_INTEGRATION=0 python -m pytest tests/integration -q
```
