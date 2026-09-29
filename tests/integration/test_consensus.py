"""Acceptance, finality and the GEN, on the chain.

The brief's distinction matters here: GenLayer's transaction states and TRACE's
protocol states are different things, and a transaction can finalize while the
protocol it carried is anything at all. These tests check both, separately.
"""
import pytest

from scenario import BOND, REWARD

BPS = 10_000
SHARE = {"VERIFIED": 10_000, "PARTIALLY_VERIFIED": 5_000}


class TestAcceptance:
    def test_a_fresh_result_cannot_be_accepted(self, world):
        world.verified()
        wall = world.live.record["walls"]["accept_early"]
        assert wall["refused"], wall
        assert "can be accepted at" in wall["refusal"], wall
        assert wall["consensus"] == "MAJORITY_AGREE", wall

    def test_after_the_delay_the_result_becomes_the_protocol_s_answer(self, world):
        world.settled()
        for case in ("verified", "not-verified"):
            accepted = world.live.record["protocols"][case]["accepted"]
            record = world.verification(case)
            assert accepted["lifecycle"] in ("ACCEPTED", "FINALIZED"), case
            assert accepted["overall_result"] == record["overall_result"], case
            assert int(record["finalized_at"]) >= int(record["verified_at"]) + 300, (
                case, record["verified_at"], record["finalized_at"])

    def test_genlayer_finality_and_the_trace_result_are_different_things(self, world):
        """A transaction can be FINALIZED while the protocol it carried is
        NOT_VERIFIED. One is GenLayer saying the transaction is settled; the
        other is what the evidence showed."""
        world.settled()
        facts = world.live.record["protocols"]["not-verified"]["verification_facts"]
        result = world.verification("not-verified")["overall_result"]
        assert facts["consensus"] == "MAJORITY_AGREE"
        assert result in ("NOT_VERIFIED", "INCONCLUSIVE", "PROTOCOL_DEVIATION"), result


class TestTheMoney:
    def test_the_contract_held_exactly_what_was_sent(self, world):
        """Read from the snapshot each phase recorded, not from the protocol as
        it stands now: by the time the later tests run it has settled."""
        world.funded()
        for case in ("verified", "not-verified"):
            funded = world.live.record["protocols"][case]["funded"]
            assert int(funded["reward_deposited"]) == REWARD, case
            assert int(funded["bond_deposited"]) == BOND, case

    def test_a_second_deposit_comes_back_rather_than_being_kept(self, world):
        """GenLayer credits a payable transaction's value before the call runs,
        so funding refuses by returning. The transaction succeeds, having sent
        the value straight back."""
        world.settled()
        wall = world.live.record["walls"]["fund_twice"]
        assert wall["refused"], wall
        assert wall.get("refunded"), "a refused deposit must refuse by returning, not by raising"
        assert wall["execution"] == "SUCCESS", wall
        after = world.live.record["protocols"]["verified"].get("after_walls")
        if after:
            assert int(after["reward_deposited"]) == REWARD, (
                "a refused second deposit was added to custody anyway")

    @pytest.mark.parametrize("case", ["verified", "not-verified"])
    def test_the_split_follows_the_frozen_policy_and_the_accepted_result(self, world, case):
        world.settled()
        settled = world.live.record["protocols"][case]["settled"]
        result = settled["overall_result"]

        if result in SHARE:
            released = REWARD * SHARE[result] // BPS
            expected_submitter = released + BOND
            expected_creator = REWARD - released
        elif result == "NOT_VERIFIED":
            expected_creator = REWARD + BOND          # the bond answers for a proven failure
            expected_submitter = 0
        else:                                          # INCONCLUSIVE, PROTOCOL_DEVIATION
            expected_creator = REWARD
            expected_submitter = BOND

        assert int(settled["paid_submitter"]) == expected_submitter, (case, result, settled)
        assert int(settled["paid_creator"]) == expected_creator, (case, result, settled)
        assert expected_creator + expected_submitter == REWARD + BOND, "GEN was created or destroyed"

    def test_a_settled_protocol_holds_nothing(self, world):
        world.settled()
        for case in ("verified", "not-verified"):
            settled = world.live.record["protocols"][case]["settled"]
            assert settled["lifecycle"] == "FINALIZED", case
            assert settled["reward_deposited"] == "0" and settled["bond_deposited"] == "0", case
            assert int(settled["settled_at"]) > 0, case

    def test_finalizing_twice_pays_nothing(self, world):
        world.settled()
        wall = world.live.record["walls"]["finalize_twice"]
        assert wall["refused"], "a protocol was allowed to finalize twice"
        settled = world.live.record["protocols"]["verified"]["settled"]
        now = world.protocol("verified")
        assert now["paid_creator"] == settled["paid_creator"]
        assert now["paid_submitter"] == settled["paid_submitter"]

    def test_the_chain_and_the_ledger_agree_about_what_the_contract_holds(self, world):
        """The assertion worth having: if the contract ever holds GEN its own
        ledger does not record, this is what says so.

        Both numbers are read from the chain, after the settling transactions
        have FINALIZED. That wait is not a convenience. TRACE zeroes a
        protocol's ledger when the payment is accepted, and GenLayer moves the
        GEN when the transaction finalizes, so between those two moments the
        chain honestly holds more than the ledger admits. Reading in that gap
        reports a leak that is only a clock."""
        world.settled()
        balance = world.live.contract_balance()
        custody = int(world.live.read("get_protocol_info")["total_custody"])
        assert balance == custody, (
            f"the chain says the contract holds {balance} atto and its ledger says {custody}: "
            f"{balance - custody} atto is unaccounted for")
