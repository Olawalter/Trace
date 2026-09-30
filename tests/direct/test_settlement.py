"""The money.

Every economic test here is about one of three things: what the contract is
allowed to hold, what it pays for a given result, and what it must refuse to do
twice. The result's name is the only thing a model contributes to any of it.
"""
import pytest

from tests.direct.conftest import (accept, active, fund, hex_of, latest, transfers_to, verify,
                                   warp_to, with_evidence)
from tests.direct.support import (BOND, DEADLINE, RESPONSIBLE, URL_INDEX, INCONCLUSIVE_ANSWERS, NOT_VERIFIED_ANSWERS,
                                  NOW_UNIX, PARTIAL_ANSWERS, RECOVERY_WINDOW, REWARD, URL_RELEASE,
                                  VERIFIED_ANSWERS, WEB_NOT_VERIFIED, WEB_PARTIAL, WEB_VERIFIED,
                                  evidence)


def settled(trace, direct_vm, creator, submitter, pages, answers, **over):
    """A protocol taken all the way: funded, evidenced, verified, accepted and
    finalized."""
    pid = with_evidence(trace, direct_vm, creator, submitter, **over)
    verify(trace, direct_vm, creator, pid, pages, answers)
    accept(trace, direct_vm, creator, pid)
    direct_vm.sender = creator
    trace.finalize_protocol(pid)
    return pid


class TestCustody:
    def test_each_side_deposits_exactly_what_the_frozen_policy_names(self, trace, direct_vm,
                                                                     creator, responsible, submitter):
        pid = active(trace, direct_vm, creator)
        fund(trace, direct_vm, creator, pid, REWARD)
        fund(trace, direct_vm, responsible, pid, BOND)
        p = trace.get_protocol(pid)
        assert p["reward_deposited"] == str(REWARD)
        assert p["bond_deposited"] == str(BOND)
        assert trace.get_protocol_info()["total_custody"] == str(REWARD + BOND)

    def test_what_is_credited_is_the_transaction_value_and_not_an_argument(self, trace, direct_vm,
                                                                          creator):
        pid = active(trace, direct_vm, creator)
        direct_vm.sender = creator
        with direct_vm.expect_revert("attach the deposit as the transaction's value"):
            trace.fund_protocol(pid)

    @pytest.mark.parametrize("amount", [REWARD - 1, REWARD + 1, REWARD // 2])
    def test_a_deposit_that_is_not_exact_comes_back(self, trace, direct_vm, creator, transfers,
                                                    amount):
        """"At least" is not a deposit. A wrong amount is returned, and the
        refusal returns rather than raising, because GenLayer credits a payable
        transaction's value before the call runs -- a raise would roll the
        refund back and keep GEN nobody meant to send."""
        pid = active(trace, direct_vm, creator)
        answer = fund(trace, direct_vm, creator, pid, amount)
        assert answer.startswith("[REFUNDED]") and "exactly" in answer
        assert transfers_to(transfers, hex_of(creator)) == amount
        assert trace.get_protocol(pid)["reward_deposited"] == "0"
        assert trace.get_protocol_info()["total_custody"] == "0"

    @pytest.mark.parametrize("amount", [BOND - 1, BOND + 1, BOND * 2])
    def test_a_bond_that_is_not_exact_comes_back_too(self, trace, direct_vm, creator, submitter, responsible,
                                                      transfers, amount):
        """The reward and the bond are separate paths through the same method,
        and a suite that only exercises the creator's side proves nothing about
        the side that answers."""
        pid = active(trace, direct_vm, creator)
        fund(trace, direct_vm, creator, pid, REWARD)
        answer = fund(trace, direct_vm, responsible, pid, amount)
        assert answer.startswith("[REFUNDED]") and "exactly" in answer
        assert transfers_to(transfers, responsible) == amount
        assert trace.get_protocol(pid)["bond_deposited"] == "0"
        assert trace.get_protocol_info()["total_custody"] == str(REWARD), (
            "a refused bond was added to custody anyway")

    def test_funding_a_protocol_with_no_economic_consequence_comes_back(self, trace, direct_vm,
                                                                        creator, transfers):
        pid = active(trace, direct_vm, creator, economic_policy={"enabled": False})
        answer = fund(trace, direct_vm, creator, pid, REWARD)
        assert "carries no economic consequence" in answer
        assert transfers_to(transfers, hex_of(creator)) == REWARD
        assert trace.get_protocol_info()["total_custody"] == "0"

    def test_funding_twice_comes_back(self, trace, direct_vm, creator, transfers):
        pid = active(trace, direct_vm, creator)
        fund(trace, direct_vm, creator, pid, REWARD)
        answer = fund(trace, direct_vm, creator, pid, REWARD)
        assert "already deposited" in answer
        assert transfers_to(transfers, hex_of(creator)) == REWARD
        assert trace.get_protocol(pid)["reward_deposited"] == str(REWARD)

    def test_funding_a_protocol_that_is_not_open_comes_back(self, trace, direct_vm, creator,
                                                            submitter, responsible, transfers):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid)
        answer = fund(trace, direct_vm, responsible, pid, BOND)
        assert "while the protocol is open for evidence" in answer
        assert transfers_to(transfers, hex_of(responsible)) == BOND


class TestWhatEachResultPays:
    def test_verified_releases_the_reward_and_returns_the_bond(self, trace, direct_vm, creator,
                                                               submitter, responsible, transfers):
        pid = settled(trace, direct_vm, creator, submitter, WEB_VERIFIED, VERIFIED_ANSWERS)
        p = trace.get_protocol(pid)
        assert p["overall_result"] == "VERIFIED"
        assert p["lifecycle"] == "FINALIZED"
        assert int(p["paid_bond_depositor"]) == REWARD + BOND
        assert int(p["paid_creator"]) == 0
        assert transfers_to(transfers, hex_of(responsible)) == REWARD + BOND

    def test_partially_verified_releases_the_share_the_policy_names(self, trace, direct_vm,
                                                                    creator, submitter):
        pid = settled(trace, direct_vm, creator, submitter, WEB_PARTIAL, PARTIAL_ANSWERS)
        p = trace.get_protocol(pid)
        assert p["overall_result"] == "PARTIALLY_VERIFIED"
        assert int(p["paid_bond_depositor"]) == REWARD // 2 + BOND
        assert int(p["paid_creator"]) == REWARD - REWARD // 2

    def test_not_verified_returns_the_reward_and_forfeits_the_bond(self, trace, direct_vm, creator,
                                                                   submitter):
        """The bond answers for a protocol the evidence showed was not met.
        Every other ending returns it."""
        pid = settled(trace, direct_vm, creator, submitter, WEB_NOT_VERIFIED, NOT_VERIFIED_ANSWERS)
        p = trace.get_protocol(pid)
        assert p["overall_result"] == "NOT_VERIFIED"
        assert int(p["paid_creator"]) == REWARD + BOND
        assert int(p["paid_bond_depositor"]) == 0

    def test_inconclusive_returns_everything_where_it_came_from(self, trace, direct_vm, creator,
                                                                submitter):
        pid = settled(trace, direct_vm, creator, submitter, WEB_NOT_VERIFIED, INCONCLUSIVE_ANSWERS)
        p = trace.get_protocol(pid)
        assert p["overall_result"] == "INCONCLUSIVE"
        assert int(p["paid_creator"]) == REWARD
        assert int(p["paid_bond_depositor"]) == BOND

    def test_nothing_is_created_or_destroyed_on_any_path(self, trace, direct_vm, creator,
                                                         submitter):
        for pages, answers in ((WEB_VERIFIED, VERIFIED_ANSWERS),
                               (WEB_PARTIAL, PARTIAL_ANSWERS),
                               (WEB_NOT_VERIFIED, NOT_VERIFIED_ANSWERS),
                               (WEB_NOT_VERIFIED, INCONCLUSIVE_ANSWERS)):
            pid = settled(trace, direct_vm, creator, submitter, pages, answers)
            p = trace.get_protocol(pid)
            assert int(p["paid_creator"]) + int(p["paid_bond_depositor"]) == REWARD + BOND
            assert p["reward_deposited"] == "0" and p["bond_deposited"] == "0"

    def test_the_payout_is_read_from_what_was_deposited_not_from_the_terms(self, trace, direct_vm,
                                                                            creator, submitter, responsible,
                                                                            transfers):
        """A term is what the protocol asked for; the ledger is what the contract
        actually holds. Only one side funded here, so the two differ, and a
        settlement that read the terms would pay out money nobody deposited."""
        pid = active(trace, direct_vm, creator)
        fund(trace, direct_vm, creator, pid, REWARD)          # the bond is never posted
        direct_vm.sender = submitter
        trace.submit_evidence(pid, evidence(URL_RELEASE, ["R1", "R2"], "PUBLICATION"))
        trace.submit_evidence(pid, evidence(URL_INDEX, ["R1", "R2", "R3"], "REGISTRY"))
        verify(trace, direct_vm, creator, pid)
        accept(trace, direct_vm, creator, pid)
        direct_vm.sender = creator
        trace.finalize_protocol(pid)

        p = trace.get_protocol(pid)
        assert p["bond_deposited"] == "0" and p["bond_required"] == str(BOND)
        assert int(p["paid_bond_depositor"]) == REWARD, "a bond nobody posted cannot be paid out"
        assert int(p["paid_creator"]) == 0
        assert transfers_to(transfers, hex_of(responsible)) == REWARD
        assert trace.get_protocol_info()["total_custody"] == "0"

    def test_a_protocol_with_no_money_finalizes_all_the_same(self, trace, direct_vm, creator,
                                                             submitter):
        """The consequence is optional. Verification is the product."""
        pid = with_evidence(trace, direct_vm, creator, submitter,
                            economic_policy={"enabled": False})
        verify(trace, direct_vm, creator, pid)
        accept(trace, direct_vm, creator, pid)
        direct_vm.sender = creator
        assert trace.finalize_protocol(pid) == "VERIFIED"
        assert trace.get_protocol(pid)["lifecycle"] == "FINALIZED"


class TestTheOrderOfThings:
    def test_a_result_must_stand_before_it_is_accepted(self, trace, direct_vm, creator, submitter):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid)
        direct_vm.sender = creator
        with direct_vm.expect_revert("can be accepted at"):
            trace.accept_verification(pid)

    def test_nothing_is_paid_before_the_result_is_accepted(self, trace, direct_vm, creator,
                                                           submitter):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid)
        direct_vm.sender = creator
        with direct_vm.expect_revert("finalized after its result is accepted"):
            trace.finalize_protocol(pid)

    def test_anyone_may_accept_and_finalize_but_only_the_parties_are_paid(self, trace, direct_vm,
                                                                          creator, submitter, responsible,
                                                                          stranger, transfers):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid)
        accept(trace, direct_vm, stranger, pid)
        direct_vm.sender = stranger
        trace.finalize_protocol(pid)
        assert transfers_to(transfers, hex_of(stranger)) == 0
        assert transfers_to(transfers, hex_of(responsible)) == REWARD + BOND

    def test_the_ledger_is_zeroed_before_a_single_gen_leaves(self, trace, direct_vm, creator,
                                                             submitter, monkeypatch):
        """Read, zero, persist, then transfer. A re-entrant call during the
        transfer must find nothing left to pay."""
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid)
        accept(trace, direct_vm, creator, pid)

        seen = {}
        from gltest.direct import wasi_mock
        original = wasi_mock._handle_gl_call

        def watch(vm, request):
            if isinstance(request, dict) and "EthSend" in request and "ledger" not in seen:
                seen["ledger"] = (trace.get_protocol(pid)["reward_deposited"],
                                  trace.get_protocol(pid)["bond_deposited"])
            return original(vm, request)

        monkeypatch.setattr(wasi_mock, "_handle_gl_call", watch)
        direct_vm.sender = creator
        trace.finalize_protocol(pid)
        assert seen["ledger"] == ("0", "0")

    def test_a_protocol_cannot_be_finalized_twice(self, trace, direct_vm, creator, submitter):
        pid = settled(trace, direct_vm, creator, submitter, WEB_VERIFIED, VERIFIED_ANSWERS)
        direct_vm.sender = creator
        with direct_vm.expect_revert("finalized after its result is accepted"):
            trace.finalize_protocol(pid)

    def test_a_result_cannot_be_accepted_twice(self, trace, direct_vm, creator, submitter):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid)
        accept(trace, direct_vm, creator, pid)
        direct_vm.sender = creator
        with direct_vm.expect_revert("only a proposed result can be accepted"):
            trace.accept_verification(pid)


class TestWhenNobodyFinishes:
    def test_recovery_ends_a_protocol_the_deadline_outlived(self, trace, direct_vm, creator,
                                                            submitter, stranger, transfers):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        warp_to(direct_vm, DEADLINE + RECOVERY_WINDOW + 60)
        direct_vm.sender = stranger
        assert trace.recover_protocol(pid) == "INCONCLUSIVE"
        p = trace.get_protocol(pid)
        assert p["lifecycle"] == "FINALIZED"
        assert int(p["paid_creator"]) == REWARD
        assert int(p["paid_bond_depositor"]) == BOND
        assert transfers_to(transfers, hex_of(stranger)) == 0

    def test_recovery_is_refused_before_the_window_has_passed(self, trace, direct_vm, creator,
                                                              submitter):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        warp_to(direct_vm, DEADLINE + 60)
        direct_vm.sender = creator
        with direct_vm.expect_revert("recovery is possible at"):
            trace.recover_protocol(pid)

    def test_a_protocol_already_finalized_cannot_be_recovered(self, trace, direct_vm, creator,
                                                              submitter):
        pid = settled(trace, direct_vm, creator, submitter, WEB_VERIFIED, VERIFIED_ANSWERS)
        warp_to(direct_vm, DEADLINE + RECOVERY_WINDOW + 60)
        direct_vm.sender = creator
        with direct_vm.expect_revert("was never finished"):
            trace.recover_protocol(pid)

    def test_cancelling_returns_each_deposit_to_whoever_made_it(self, trace, direct_vm, creator,
                                                                responsible, transfers):
        """The creator may call a protocol off. That does not make the bond
        theirs.

        Cancellation is creator-authorized, so reading the recipient off the
        caller looks harmless and pays another account's money to the person who
        pressed the button. The reward goes back to the creator because the
        creator posted it; the bond goes back to the responsible party for
        exactly the same reason, and for no other."""
        pid = active(trace, direct_vm, creator)
        fund(trace, direct_vm, creator, pid, REWARD)
        fund(trace, direct_vm, responsible, pid, BOND)
        direct_vm.sender = creator
        trace.cancel_protocol(pid)

        assert transfers_to(transfers, hex_of(creator)) == REWARD, (
            "the creator was paid the bond as well as their own reward")
        assert transfers_to(transfers, responsible) == BOND, (
            "the bond did not go back to the account that posted it")
        assert trace.get_protocol_info()["total_custody"] == "0"

    def test_a_protocol_with_evidence_cannot_simply_be_cancelled(self, trace, direct_vm, creator,
                                                                 submitter):
        """Once somebody has answered a protocol, its creator cannot withdraw it
        from under them."""
        pid = with_evidence(trace, direct_vm, creator, submitter)
        direct_vm.sender = creator
        with direct_vm.expect_revert("must be verified or recovered"):
            trace.cancel_protocol(pid)
