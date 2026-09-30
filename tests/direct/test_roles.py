"""Who is who, and whose money is whose.

TRACE has five accounts in play and they are easy to blur, because in the happy
path one person often plays several parts. They are separated here on purpose:

    creator             writes the protocol and puts up the reward
    responsible_party   is named in it, accepts it, and posts the bond
    bond_depositor      is whoever's transaction actually paid the bond
    evidence submitter  registers addresses, and is owed nothing for it
    settlement caller   presses the button, and is owed nothing for that either

The last three are the interesting ones. Submitting evidence is provenance, not
a claim on money; sending a settlement is a trigger, not a title to the funds it
moves. Every test below runs with those roles held by different accounts, which
is the only way a payment to the right place can be told from a coincidence.
"""
import pytest

from tests.direct.conftest import (accept, active, frozen, fund, hex_of, registered,
                                   transfers_to, verify, warp_to, with_evidence)
from tests.direct.support import (BOND, DEADLINE, RECOVERY_WINDOW, RESPONSIBLE, REWARD,
                                  URL_INDEX, URL_RELEASE, evidence)


class TestAcceptance:
    def test_the_creator_cannot_accept_on_the_responsible_party_s_behalf(self, trace, direct_vm,
                                                                         creator):
        """The whole value of the step is that somebody else agreed. A creator
        who can accept for them has agreed with themselves."""
        pid = frozen(trace, direct_vm, creator)
        direct_vm.sender = creator
        with direct_vm.expect_revert("only the responsible party"):
            trace.accept_protocol(pid)

    def test_a_stranger_cannot_accept(self, trace, direct_vm, creator, stranger):
        pid = frozen(trace, direct_vm, creator)
        direct_vm.sender = stranger
        with direct_vm.expect_revert("only the responsible party"):
            trace.accept_protocol(pid)

    def test_the_evidence_submitter_cannot_accept(self, trace, direct_vm, creator, submitter):
        """Being willing to do the work is not the same as being the party the
        protocol is about."""
        pid = frozen(trace, direct_vm, creator)
        direct_vm.sender = submitter
        with direct_vm.expect_revert("only the responsible party"):
            trace.accept_protocol(pid)

    def test_the_responsible_party_accepts_and_the_protocol_starts(self, trace, direct_vm, creator,
                                                                    responsible):
        pid = frozen(trace, direct_vm, creator)
        before = trace.get_protocol(pid)
        assert before["lifecycle"] == "AWAITING_ACCEPTANCE" and before["accepted_at"] == 0

        direct_vm.sender = responsible
        trace.accept_protocol(pid)

        p = trace.get_protocol(pid)
        assert p["lifecycle"] == "ACTIVE"
        assert p["responsible_party"].lower() == responsible.lower()
        assert p["accepted_at"] > 0

    def test_a_protocol_cannot_be_accepted_twice(self, trace, direct_vm, creator, responsible):
        pid = active(trace, direct_vm, creator)
        direct_vm.sender = responsible
        with direct_vm.expect_revert("awaiting an answer"):
            trace.accept_protocol(pid)

    def test_a_draft_has_nothing_to_accept_yet(self, trace, direct_vm, creator, responsible):
        pid = registered(trace, direct_vm, creator)
        direct_vm.sender = responsible
        with direct_vm.expect_revert("has not been frozen yet"):
            trace.accept_protocol(pid)

    def test_the_responsible_party_is_frozen_with_everything_else(self, trace, direct_vm, creator,
                                                                  stranger):
        """Who is answerable is part of what was agreed, so it is inside the
        fingerprint rather than beside it. A creator who could point it at
        somebody else after the evidence arrived would be choosing who loses."""
        pid = active(trace, direct_vm, creator)
        direct_vm.sender = creator
        with direct_vm.expect_revert("can only be written while it is a draft"):
            trace.set_draft(pid, "{}")
        assert json_of(trace, pid)["responsible_party"].lower() == RESPONSIBLE.lower()

    def test_the_creator_cannot_name_themselves(self, trace, direct_vm, creator):
        """One account on both sides would make the funding path ambiguous, and
        would mean nobody independent ever accepted anything."""
        pid = create_only(trace, direct_vm, creator)
        direct_vm.sender = creator
        with direct_vm.expect_revert("different account from the creator"):
            trace.set_draft(pid, draft_naming(hex_of(creator)))


class TestWhoMayPostTheBond:
    def test_the_bond_cannot_be_posted_before_acceptance(self, trace, direct_vm, creator,
                                                          responsible, transfers):
        pid = frozen(trace, direct_vm, creator)
        answer = fund(trace, direct_vm, responsible, pid, BOND)
        assert answer.startswith("[REFUNDED]"), answer
        assert transfers_to(transfers, responsible) == BOND
        assert trace.get_protocol(pid)["bond_deposited"] == "0"
        assert trace.get_protocol(pid)["bond_depositor"] == ""

    def test_a_stranger_cannot_buy_into_somebody_else_s_protocol(self, trace, direct_vm, creator,
                                                                  stranger, transfers):
        """Otherwise anyone could post the bond and hold a claim on the payout of
        an agreement they were never part of."""
        pid = active(trace, direct_vm, creator)
        answer = fund(trace, direct_vm, stranger, pid, BOND)
        assert answer.startswith("[REFUNDED]") and "creator or the responsible party" in answer
        assert transfers_to(transfers, stranger) == BOND
        assert trace.get_protocol(pid)["bond_depositor"] == ""

    def test_the_evidence_submitter_cannot_post_the_bond(self, trace, direct_vm, creator,
                                                          submitter, transfers):
        pid = active(trace, direct_vm, creator)
        answer = fund(trace, direct_vm, submitter, pid, BOND)
        assert answer.startswith("[REFUNDED]"), answer
        assert trace.get_protocol(pid)["bond_depositor"] == ""

    def test_the_responsible_party_posts_it_and_is_recorded(self, trace, direct_vm, creator,
                                                            responsible):
        pid = active(trace, direct_vm, creator)
        fund(trace, direct_vm, responsible, pid, BOND)
        p = trace.get_protocol(pid)
        assert p["bond_deposited"] == str(BOND)
        assert p["bond_depositor"].lower() == responsible.lower()

    def test_a_wrong_amount_buys_no_title_to_anything(self, trace, direct_vm, creator,
                                                       responsible, transfers):
        """Only a payment the contract accepted establishes a depositor. A
        refunded one leaves the field exactly as empty as it was."""
        pid = active(trace, direct_vm, creator)
        answer = fund(trace, direct_vm, responsible, pid, BOND - 1)
        assert answer.startswith("[REFUNDED]") and "exactly" in answer
        p = trace.get_protocol(pid)
        assert p["bond_depositor"] == ""
        assert p["bond_deposited"] == "0"
        assert transfers_to(transfers, responsible) == BOND - 1

    def test_a_second_attempt_cannot_take_the_first_one_s_place(self, trace, direct_vm, creator,
                                                                 responsible, transfers):
        pid = active(trace, direct_vm, creator)
        fund(trace, direct_vm, responsible, pid, BOND)
        answer = fund(trace, direct_vm, responsible, pid, BOND)
        assert answer.startswith("[REFUNDED]") and "already deposited" in answer
        p = trace.get_protocol(pid)
        assert p["bond_depositor"].lower() == responsible.lower()
        assert p["bond_deposited"] == str(BOND)


class TestEvidenceIsNotOwnership:
    def test_submitting_evidence_does_not_touch_the_bond_depositor(self, trace, direct_vm, creator,
                                                                    responsible, submitter):
        """The original defect in one test: the account that does the work of
        answering is not the account whose money is at stake, and the contract
        must not learn the second from the first."""
        pid = active(trace, direct_vm, creator)
        fund(trace, direct_vm, creator, pid, REWARD)
        fund(trace, direct_vm, responsible, pid, BOND)
        assert trace.get_protocol(pid)["bond_depositor"].lower() == responsible.lower()

        direct_vm.sender = submitter
        trace.submit_evidence(pid, evidence(URL_RELEASE, ["R1", "R2"], "PUBLICATION"))
        trace.submit_evidence(pid, evidence(URL_INDEX, ["R1", "R2", "R3"], "REGISTRY"))

        p = trace.get_protocol(pid)
        assert p["bond_depositor"].lower() == responsible.lower(), "evidence moved the money"
        rows = trace.list_evidence(pid, 0, 10)["items"]
        assert {r["submitter"].lower() for r in rows} == {submitter.lower()}
        assert submitter.lower() != responsible.lower()


class TestNobodyCanRedirectTheBond:
    """Four accounts, one question: does the money reach the right two of them
    when a fifth presses the button."""

    def test_finalization_pays_the_creator_and_the_depositor_whoever_sends_it(
            self, trace, direct_vm, creator, responsible, submitter, finalizer, transfers):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid)
        accept(trace, direct_vm, creator, pid)

        direct_vm.sender = finalizer
        trace.finalize_protocol(pid)

        assert transfers_to(transfers, responsible) == REWARD + BOND, (
            "a VERIFIED protocol releases the reward and returns the bond to the party that "
            "answered and posted it")
        assert transfers_to(transfers, submitter) == 0, "the evidence submitter was paid"
        assert transfers_to(transfers, finalizer) == 0, "the caller paid themselves"
        assert transfers_to(transfers, hex_of(creator)) == 0

    def test_recovery_pays_the_same_two_accounts_whoever_sends_it(
            self, trace, direct_vm, creator, responsible, submitter, finalizer, transfers):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        warp_to(direct_vm, DEADLINE + RECOVERY_WINDOW + 60)

        direct_vm.sender = finalizer
        trace.recover_protocol(pid)

        assert transfers_to(transfers, hex_of(creator)) == REWARD, "the reward did not come back"
        assert transfers_to(transfers, responsible) == BOND, "the bond did not come back"
        assert transfers_to(transfers, submitter) == 0, "the evidence submitter was paid"
        assert transfers_to(transfers, finalizer) == 0, "the caller paid themselves"

    def test_nothing_can_be_paid_twice(self, trace, direct_vm, creator, responsible, submitter,
                                       finalizer, transfers):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid)
        accept(trace, direct_vm, creator, pid)
        direct_vm.sender = finalizer
        trace.finalize_protocol(pid)
        paid_once = list(transfers)

        direct_vm.sender = finalizer
        with direct_vm.expect_revert("finalized after its result is accepted"):
            trace.finalize_protocol(pid)

        assert list(transfers) == paid_once, "a second settlement moved more GEN"
        p = trace.get_protocol(pid)
        assert p["bond_deposited"] == "0" and p["reward_deposited"] == "0"


# ── small helpers, kept at the bottom so the tests read first ────────────────

def json_of(trace, pid) -> dict:
    import json
    return json.loads(trace.get_protocol(pid)["definition"]) if isinstance(
        trace.get_protocol(pid)["definition"], str) else trace.get_protocol(pid)["definition"]


def create_only(trace, direct_vm, signer) -> str:
    from tests.direct.support import DESCRIPTION, SUBJECT, SUBJECT_TYPE, TITLE
    direct_vm.sender = signer
    return trace.create_protocol(TITLE, DESCRIPTION, SUBJECT, SUBJECT_TYPE)


def draft_naming(address: str) -> str:
    from tests.direct.support import draft
    return draft(responsible_party=address)
