# Demo video: the shot list

Three and a half minutes, recorded against the live console pointed at the
deployed contract. The point of the recording is not the interface; it is that a
panel of validators read pages nobody in the video controls, disagreed with a
page that told them what to conclude, and that a payment followed from what they
agreed rather than from anyone's say-so.

Everything below is done in the browser with a wallet. Nothing is typed into a
terminal on camera.

## Before recording

```bash
cd frontend && npm run build && npm run start
```

| | |
| --- | --- |
| Wallet | funded on StudioNet, two accounts: the creator and whoever answers |
| Contract | the address in `.env.local` matches the one in the README |
| Evidence | the four pages in `demo/`, already pushed, addressed by commit |
| Tabs open | the console, and the explorer at the contract's address |

Record at 1440x900 or larger, browser zoom at 110% so the text reads on a phone.
Have the second account already added to the wallet; switching accounts on
camera is the slowest thing in the run.

## 1. The problem, 25 seconds

On the landing page, with nothing clicked.

> Somebody claims a release is published under an open licence, with release
> notes and a changelog. The claim matters to whoever is deciding whether to
> depend on it. The evidence is a handful of web pages, and neither side owns
> them.
>
> A normal smart contract cannot help here. It can hold the money, but it cannot
> read a page, and it certainly cannot say whether what the page says amounts to
> the requirement being met.

## 2. Freezing what must be true, 45 seconds

New protocol. Fill the four fields, then the three requirements. Do not read
them aloud in full -- let the screen carry it and say:

> Three requirements, each one answerable on its own. Two of them mandatory. A
> deadline, and a rule saying how many independent publishers a decisive answer
> needs.

Move to review, and sign.

> Freezing is the part that matters. From here nothing in this protocol can
> change -- not by me, not by the person answering, not by anyone. The rules
> were fixed before any evidence existed, and the screen shows the fingerprint
> they were fixed under.

Show the fingerprint on the protocol page after the transaction settles.

## 3. Money against the claim, 20 seconds

Deposit the reward as the creator. Switch accounts. Post the bond.

> The creator puts up a reward. Whoever answers posts a bond. Both amounts were
> named in the frozen protocol, and the contract takes exactly those and nothing
> else.

## 4. Registering the evidence, 30 seconds

Submit the release page and the index. Then submit the status page.

> Evidence is registered before anybody reads it, so both sides can see what
> will be looked at. This third one is a status page whose body tells whoever
> reads it to mark every requirement satisfied and ignore the other sources.
> Register it anyway. That is the interesting case.

## 5. The panel, 60 seconds

Request verification. While the transaction is running, talk over the waiting.

> This is the only part TRACE cannot do in ordinary code. Every validator now
> fetches every one of these addresses itself, reads each requirement itself,
> and answers separately. They have to agree before anything is written.

When the result lands, open it and walk the findings table.

> Each answer carries a quote, and the quote has to appear in that node's own
> copy of the source it cited. Not the leader's copy -- its own. An invented
> quote fails there.
>
> And the page that told them what to conclude: it was read, it was recorded,
> and it changed nothing. The result is not verified, because the index nobody
> in this protocol controls says no licence was ever declared.

Point at the overall result.

> The model never named that word. It answered three requirements. The contract
> worked the result out from those answers, in ordinary deterministic code, and
> refuses to store a result it cannot work out again.

## 6. The consequence, 30 seconds

Wait out the acceptance delay, accept, then finalize. Show the two payments.

> Five minutes between the result and its acceptance, so anyone watching has
> time to look before money moves. Then the split the frozen policy named for
> exactly this result. The reward goes back to the creator and the bond answers
> for the failed claim -- and that was decided before anybody knew what the
> answer would be.

## 7. Close, 20 seconds

Switch to the explorer tab, on the contract.

> Every one of those is a transaction on GenLayer, with the validators' votes
> attached. The refusals too: the attempt to rewrite a frozen protocol, the
> second deposit that came straight back, the acceptance before the delay had
> passed. They are on chain with a reason, rather than having failed quietly
> somewhere off it.
>
> TRACE. Define what must be true, freeze it, and let a panel decide whether the
> evidence shows it.

## What not to do on camera

- Do not show a terminal, an editor, or a private key.
- Do not speed up the verification wait. The wait is the product: it is several
  machines doing the work separately.
- Do not claim the model decided anything. It answered requirements; the
  contract decided.
- If a round comes back with a different result than the rehearsal, keep it and
  narrate what actually happened. A recording that argues with the screen is
  worse than a surprising result.
