"""The steward's question, asked on chain.

Direct Mode already proves the contract sends the bond to the account that
posted it. That is the important proof, because it is exhaustive. This file
asks the narrower question that only a real network can answer: when three
separate accounts do three separate things against a deployed contract, and a
fourth kind of caller triggers the settlement, does the GEN actually land where
the record says it should.

Every assertion here reads the chain: a balance that moved, a field the contract
returned, or a transaction that was refused with validators agreeing about it.
"""
import pytest

from scenario import BOND, REWARD


class TestTheRolesAreDifferentAccounts:
    def test_the_run_uses_three_distinct_accounts(self, world):
        """If these ever collapsed into one, every assertion below would still
        pass and none of them would mean anything."""
        world.frozen()
        accounts = world.live.record["accounts"]
        addresses = {accounts["creator"].lower(), accounts["responsible"].lower(),
                     accounts["submitter"].lower()}
        assert len(addresses) == 3, accounts

    def test_the_protocol_names_the_responsible_party_and_freezes_it(self, world):
        world.frozen()
        accounts = world.live.record["accounts"]
        for case in ("verified", "not-verified"):
            p = world.live.record["protocols"][case]["frozen"]
            assert p["responsible_party"].lower() == accounts["responsible"].lower()
            assert p["definition"]["responsible_party"].lower() == accounts["responsible"].lower(), (
                "who is answerable has to be inside the fingerprint, not beside it")


class TestAcceptance:
    def test_nobody_else_can_accept_on_the_responsible_party_s_behalf(self, world):
        world.frozen()
        wall = world.live.record["walls"]["stranger_accepts"]
        assert wall["refused"], wall
        assert "only the responsible party" in wall["refusal"], wall
        assert wall["consensus"] == "MAJORITY_AGREE", (
            "the refusal has to be something the validators agreed about, not a local error")

    def test_the_responsible_party_accepts_before_anything_is_staked(self, world):
        world.frozen()
        accounts = world.live.record["accounts"]
        for case in ("verified", "not-verified"):
            accepted = world.live.record["protocols"][case]["taken_on"]
            assert accepted["lifecycle"] == "ACTIVE"
            assert int(accepted["accepted_at"]) > 0
            assert accepted["responsible_party"].lower() == accounts["responsible"].lower()
            assert accepted["bond_deposited"] == "0", "the bond was posted before acceptance"


class TestWhoseMoneyItIs:
    def test_the_bond_is_recorded_against_the_account_that_sent_it(self, world):
        world.funded()
        accounts = world.live.record["accounts"]
        for case in ("verified", "not-verified"):
            funded = world.live.record["protocols"][case]["funded"]
            assert int(funded["bond_deposited"]) == BOND, case
            assert funded["bond_depositor"].lower() == accounts["responsible"].lower(), case
            assert funded["bond_depositor"].lower() != accounts["submitter"].lower()
            assert funded["bond_depositor"].lower() != accounts["creator"].lower()

    def test_registering_evidence_does_not_move_the_bond(self, world):
        """The defect in one sentence: the account that does the answering is
        not the account whose money is at stake."""
        world.evidenced()
        accounts = world.live.record["accounts"]
        for case in ("verified", "not-verified"):
            items = world.live.record["protocols"][case]["evidence"]["items"]
            submitters = {row["submitter"].lower() for row in items}
            assert submitters, case
            now = world.protocol(case)
            assert now["bond_depositor"].lower() == accounts["responsible"].lower(), (
                "evidence moved the bond")
            assert accounts["submitter"].lower() in submitters
            assert accounts["responsible"].lower() not in submitters, (
                "this run stopped proving anything: the same account submitted and bonded")


class TestSettlementReachesTheRightAccounts:
    @pytest.mark.parametrize("case", ["verified", "not-verified"])
    def test_the_gen_lands_where_the_record_says(self, world, case):
        """Balance deltas, read from the chain either side of the settlement.

        The settling transaction is sent by the evidence submitter, which is the
        strongest version of the original bug: under the old contract that
        account both looked like the bond side and was the caller. It must come
        out of this with nothing.
        """
        world.settled()
        deltas = {k: int(v) for k, v in
                  world.live.record["protocols"][case]["settlement_deltas"].items()}
        settled = world.live.record["protocols"][case]["settled"]
        paid_creator = int(settled["paid_creator"])
        paid_bond_side = int(settled["paid_bond_depositor"])

        assert paid_creator + paid_bond_side == REWARD + BOND, settled
        assert deltas["responsible"] == paid_bond_side, (
            f"the bond side was paid {paid_bond_side} but the responsible party's balance moved "
            f"by {deltas['responsible']}")
        assert deltas["submitter"] <= 0, (
            f"the evidence submitter gained {deltas['submitter']} atto for submitting evidence "
            f"and sending a transaction")
        assert deltas["creator"] == paid_creator, (
            f"the creator was paid {paid_creator} but their balance moved by {deltas['creator']}")

    def test_the_bond_depositor_is_still_recorded_after_settlement(self, world):
        """The ledger zeroes; the identity does not. A record that forgot who
        paid could not be audited afterwards."""
        world.settled()
        accounts = world.live.record["accounts"]
        for case in ("verified", "not-verified"):
            settled = world.live.record["protocols"][case]["settled"]
            assert settled["bond_deposited"] == "0"
            assert settled["bond_depositor"].lower() == accounts["responsible"].lower()
