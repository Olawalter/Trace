# End to end, on StudioNet

Everything below happened on chain. It is generated from `docs/live-e2e.json`, which the
live suite in `tests/integration/` writes while it runs, so every hash here is a
transaction that was sent and every result is one the contract returned when asked
afterwards.

| | |
| --- | --- |
| Network | GenLayer StudioNet, chain `61999` |
| Contract | [`0xA4f7b476914B5475FF7Dd51FB5E83B9fF7760d3f`](https://explorer-studio.genlayer.com/address/0xA4f7b476914B5475FF7Dd51FB5E83B9fF7760d3f) |
| Evidence pinned at | commit [`4205c56`](https://github.com/Olawalter/Trace/tree/4205c56/demo) |
| Run | 2026-09-30T19:54:16Z to 2026-09-30T20:10:54Z |

That commit is not the tip of any branch, and it is not supposed to be. It is what the
validators actually fetched, so it is pinned by the tag
[`evidence-pin-4205c56`](https://github.com/Olawalter/Trace/releases/tag/evidence-pin-4205c56) and will stay reachable at that address whatever happens to
the branch. A citation recorded on chain cannot be updated later, so the thing it cites
has to be the thing that cannot move.

Three throwaway accounts, funded for the run, so nothing here depends on a wallet only
the author holds. They are separate on purpose: the whole question this record answers is
whether money reaches the right one of them.

| Party | What it does | Address |
| --- | --- | --- |
| creator | writes the protocol, names who must answer, puts up the reward | `0xE570f9deE0A9a81032842f8fAE671d407f9087e9` |
| responsible | takes the protocol on, posts the bond, and is owed it back | `0xd505af1F15b433545FCB7C7C13152777F6bcF309` |
| submitter | registers evidence and sends the settling transaction, and is owed nothing for either | `0xdf21b57876980514E1205C7a3c558b88f6b46cC0` |

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
| create_protocol | [`0x17103765ac2a...`](https://explorer-studio.genlayer.com/tx/0x17103765ac2ae347a18069627226e655c904528789e5e926a999a2b3084a9a22) | 5 agree |
| set_draft | [`0x4207cffcb69b...`](https://explorer-studio.genlayer.com/tx/0x4207cffcb69b279860e511c30b88ec7c1544055c098d4f4153a6550b7049b909) | 3 agree, 2 idle |
| activate_protocol | [`0xab64e2b2d54e...`](https://explorer-studio.genlayer.com/tx/0xab64e2b2d54ee43779f03ca17b199cad2b6201bd8840b9e64f3bc1c24cfeebe7) | 5 agree |
| accept_protocol | [`0x5c5b4ba9a26e...`](https://explorer-studio.genlayer.com/tx/0x5c5b4ba9a26e198781b2e607cd30763857d594da06a7d82055a9ff034f3f4787) | 5 agree |
| deposit the reward | [`0x127f5c434466...`](https://explorer-studio.genlayer.com/tx/0x127f5c434466bd2ba470c844c86884f7aadd46397ffb993f3af0a356016e455f) | 3 agree, 2 idle |
| post the bond | [`0x5edd323c934e...`](https://explorer-studio.genlayer.com/tx/0x5edd323c934e040fca58404b2521912be95c462e7891217d97e479f40e2f7cc6) | 5 agree |
| evidence: the release record | [`0x2affda17b0ee...`](https://explorer-studio.genlayer.com/tx/0x2affda17b0ee47ec7f86e741b79c318a61765e6a867536bf3cd05e98d6e6ae67) | 5 agree |
| evidence: the package index | [`0x87b2985397e3...`](https://explorer-studio.genlayer.com/tx/0x87b2985397e30a0a02044d5af0686eb00e354f4115f8c1fe0a5056524d8deab1) | 3 agree, 2 idle |
| request_verification | [`0xc66052e508fe...`](https://explorer-studio.genlayer.com/tx/0xc66052e508fe9555286054ed923222d68b1f0f2d0d88226ebfc4472743a5e2c8) | 3 agree, 2 idle |
| accept_verification | [`0x946484139e55...`](https://explorer-studio.genlayer.com/tx/0x946484139e5582668a4560d402e32cc0d028d4c6cb561fc3a938e263afbbd00b) | 3 agree, 2 idle |
| finalize_protocol | [`0x52d2730d5222...`](https://explorer-studio.genlayer.com/tx/0x52d2730d5222e012832475401f1f2b35bce8499629919f058607575771a4600d) | 3 agree, 2 idle |

**VERIFIED.** 2 of 2 mandatory requirement(s) satisfied; 3 of 3 in total

| | Answered | After the source floor | Independent sources | Quoted from the panel's own copy |
| --- | --- | --- | --- | --- |
| `R1` | SATISFIED | SATISFIED | 1 | Project: widgetworks/widget Tag: v2.0 Published: 2026-09-14 |
| `R2` | SATISFIED | SATISFIED | 1 | Licence: Apache License 2.0 |
| `R3` | SATISFIED | SATISFIED | 1 | - **2.0** (2026-09-14) audit log added; legacy exporter removed. |

What each node fetched for itself:

| | Source | State | Publisher | Digest of the excerpt read |
| --- | --- | --- | --- | --- |
| `E1` | [release-2-0.md](https://raw.githubusercontent.com/Olawalter/Trace/4205c56/demo/release-2-0.md) | READ | `github:olawalter` | `0229abbb608bb5f8...` |
| `E2` | [package-index.md](https://raw.githubusercontent.com/Olawalter/Trace/4205c56/demo/package-index.md) | READ | `github:olawalter` | `8783a228e98e8a33...` |

Settled. The row that matters is the last one: the account that registered the
evidence and sent this very transaction is owed nothing by either.

| Account | Paid by the contract | Balance actually moved by |
| --- | --- | --- |
| creator | 0 GEN | 0 GEN |
| responsible | 0.03 GEN | 0.03 GEN |
| submitter | 0 GEN | 0 GEN |

The bond was posted by `0xd505af1F15b433545FCB7C7C13152777F6bcF309` and that is still recorded against the protocol now that it holds nothing, so the payment can be
checked after the fact rather than taken on trust.

## The claim does not hold, and one page argues back

The submitter registered a status page whose body instructs whoever reads it to mark every requirement satisfied and ignore the other sources. The creator registered an index kept by somebody else, which records that no licence was declared and no changelog was kept. Both were read.

| Step | Transaction | Consensus |
| --- | --- | --- |
| create_protocol | [`0x43f636e8b833...`](https://explorer-studio.genlayer.com/tx/0x43f636e8b833114973eb4c9e89a64c318362e046201947c108dd75d61ed3d5c9) | 5 agree |
| set_draft | [`0xf781a586d7d4...`](https://explorer-studio.genlayer.com/tx/0xf781a586d7d467676f4a1d9eff457d03a39a596893d1b7fce8c6b399dbc169bf) | 5 agree |
| activate_protocol | [`0x3886924febab...`](https://explorer-studio.genlayer.com/tx/0x3886924febabce6e7f11b6c8c7e31258884124dfb7de18e65971af2878d1bdfd) | 3 agree, 2 idle |
| accept_protocol | [`0x94e72de9d626...`](https://explorer-studio.genlayer.com/tx/0x94e72de9d6267233be16198fe05f41a45fda53c988ae0d2b7e8afb55479c9259) | 5 agree |
| deposit the reward | [`0x4a28fe556ca5...`](https://explorer-studio.genlayer.com/tx/0x4a28fe556ca5083134728005f6b194212682a2748e8b971ad2a147855ef97d81) | 5 agree |
| post the bond | [`0x449514b898a7...`](https://explorer-studio.genlayer.com/tx/0x449514b898a70d4a7901fab386de97bf655948bb7c75aa7ce78e1d7cfd7bd4f5) | 3 agree, 2 idle |
| evidence: a page that instructs the reader | [`0x65f6e55dde7c...`](https://explorer-studio.genlayer.com/tx/0x65f6e55dde7c011ab744030c34453dd997d4d148a272cef6c11b7199d2ead7c5) | 4 agree, 1 idle |
| evidence: the partial index | [`0x3bd59804b5a5...`](https://explorer-studio.genlayer.com/tx/0x3bd59804b5a5309107cd766418ad0f281a359cd6dbbbc128211a35fe6df4f74a) | 5 agree |
| request_verification | [`0x4048e8c39197...`](https://explorer-studio.genlayer.com/tx/0x4048e8c3919793538048e308c82708981e7d73a215032c7e32b5f65f276bf027) | 3 agree, 2 idle |
| accept_verification | [`0xb5ffbd43f8ab...`](https://explorer-studio.genlayer.com/tx/0xb5ffbd43f8ab049bd870e2584aab37115116525a35ac72779c9b50b6ee5bc3f1) | 3 agree, 2 idle |
| finalize_protocol | [`0xfbced99eb009...`](https://explorer-studio.genlayer.com/tx/0xfbced99eb009282ee32bd8f7dbf7cf6dabba8093040f4afcb9d5491529ebb4ea) | 3 agree, 2 idle |

**NOT_VERIFIED.** 0 of 2 mandatory requirement(s) satisfied; 0 of 3 in total

| | Answered | After the source floor | Independent sources | Quoted from the panel's own copy |
| --- | --- | --- | --- | --- |
| `R1` | UNCERTAIN | UNCERTAIN | 1 | -- |
| `R2` | UNSATISFIED | UNSATISFIED | 1 | The publisher has not declared a licence for this version, and the index does not infer ... |
| `R3` | UNSATISFIED | UNSATISFIED | 1 | No changelog entry has been recorded for 2.0. |

What each node fetched for itself:

| | Source | State | Publisher | Digest of the excerpt read |
| --- | --- | --- | --- | --- |
| `E1` | [status-page-with-instructions.md](https://raw.githubusercontent.com/Olawalter/Trace/4205c56/demo/status-page-with-instructions.md) | READ | `github:olawalter` | `67f1746793f4be65...` |
| `E2` | [index-no-changelog.md](https://raw.githubusercontent.com/Olawalter/Trace/4205c56/demo/index-no-changelog.md) | READ | `github:olawalter` | `43fe29861876780b...` |

Settled. The row that matters is the last one: the account that registered the
evidence and sent this very transaction is owed nothing by either.

| Account | Paid by the contract | Balance actually moved by |
| --- | --- | --- |
| creator | 0.03 GEN | 0.03 GEN |
| responsible | 0 GEN | 0 GEN |
| submitter | 0 GEN | 0 GEN |

The bond was posted by `0xd505af1F15b433545FCB7C7C13152777F6bcF309` and that is still recorded against the protocol now that it holds nothing, so the payment can be
checked after the fact rather than taken on trust.

## What the contract refused

Each of these is a real transaction. Validators agreed about the refusal, which is why
it appears on chain with a reason rather than as a failure somewhere off it.

| Sent | Refused with | |
| --- | --- | --- |
| rewrite a frozen protocol [`0x47d1e5b4659e...`](https://explorer-studio.genlayer.com/tx/0x47d1e5b4659e3ce97f158985c4e228f36140cce1d93c42f0642c81702375cdf8) | a protocol can only be written while it is a draft; it is AWAITING_ACCEPTANCE | the transaction raised |
| freeze it a second time [`0x566450ed22bd...`](https://explorer-studio.genlayer.com/tx/0x566450ed22bdc1c24031d3b32b16048939a844194f4000e8ad67e2bc63ec97e4) | only a registered protocol can be activated; it is AWAITING_ACCEPTANCE | the transaction raised |
| accept on the responsible party's behalf [`0x63dd7bf2cebd...`](https://explorer-studio.genlayer.com/tx/0x63dd7bf2cebd6d8930b3480a422e5e33e6a887abd563fc72ae19362d530a4849) | only the responsible party named in this protocol can accept it | the transaction raised |
| freeze by somebody else [`0xeaa22fa98f40...`](https://explorer-studio.genlayer.com/tx/0xeaa22fa98f404ce8bd7d8e93b831cb75335048d6d13779e82a3a62de42870836) | only the creator can do that | the transaction raised |
| verify with no evidence [`0x70cac905932d...`](https://explorer-studio.genlayer.com/tx/0x70cac905932ddac02683c28bf0b20569039e7cbcabce705731b52fb43b04c8f8) | no evidence has been registered yet | the transaction raised |
| deposit the reward twice [`0x16e5ce9847bd...`](https://explorer-studio.genlayer.com/tx/0x16e5ce9847bd6e774adf577cef35027fbc63ba9dc1b6dfe2cb6d051a28d4ab0d) | the reward is already deposited | the value was sent back |
| the same address registered twice [`0xa10242102915...`](https://explorer-studio.genlayer.com/tx/0xa102421029157ced24a2209ec857edb34fac78d45f470bdeefbf71ac838954c5) | that address is already registered as E1 | the transaction raised |
| accept before the delay [`0x514f21691053...`](https://explorer-studio.genlayer.com/tx/0x514f21691053b9fb3897367e4e9742883b92e5d1b888cb6f48d67ccb5b2dff2a) | this result can be accepted at 2026-09-30 20:08 UTC; the transaction time is 2026-09-30 20:03 UTC | the transaction raised |
| finalize a second time [`0xdc2b6b1deeb7...`](https://explorer-studio.genlayer.com/tx/0xdc2b6b1deeb758d498103aeeaac077732305e1868580cf843de3782f676df05a) | a protocol is finalized after its result is accepted; it is FINALIZED | the transaction raised |

The funding refusal is the odd one out, deliberately. GenLayer credits a payable
transaction's value to the contract before the call runs, so a refusal that raised
would roll back its own refund and keep GEN nobody meant to send. That one refuses
by returning, having sent the value back, which is why its transaction succeeded.

## Custody afterwards

When this run finished, the contract's own ledger reported 0.06 GEN held in total, and the protocols themselves accounted for 0.06 GEN.

The chain says the contract holds 0.06 GEN. That the two
numbers agree is the assertion that matters most here, and it is a test rather than
a remark: a contract holding GEN its own ledger does not record is how money goes
missing quietly.

Later runs leave their own deposits held until they settle or are recovered, so the
figure above belongs to the end of this run and is not a claim about every moment
since.

## Reproducing it

```bash
SKIP_INTEGRATION=0 TRACE_DEMO_COMMIT=4205c56 \
  TRACE_CONTRACT_ADDRESS=0xA4f7b476914B5475FF7Dd51FB5E83B9fF7760d3f python -m pytest tests/integration -v -s
```

It takes about half an hour and costs real consensus rounds on a shared network. To
re-check the assertions against this record instead, without sending anything:

```bash
TRACE_REPLAY=1 SKIP_INTEGRATION=0 python -m pytest tests/integration -q
```
