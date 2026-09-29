"""What a validator does with the leader's proposal.

A validator that looked at the leader's answer and said "that is a valid status"
would be agreeing with a number, not verifying a claim. These tests replay the
captured validator closure against results a leader could have proposed --
honest ones, careless ones and forged ones -- and check what it does with each.

The whole point is the last two cases: a different explanation for the same
decision is accepted, and the same explanation for a different decision is not.
"""
import copy
import json

import pytest

from tests.direct.conftest import active, mock_world, with_evidence
from tests.direct.support import (PAGE_INDEX, PAGE_RELEASE, URL_INDEX, URL_RELEASE,
                                  VERIFIED_ANSWERS, WEB_VERIFIED, answer, evidence, page)


@pytest.fixture
def round_of(trace, direct_vm, creator, submitter):
    """Run one honest round and hand back what the leader returned, so a test
    can bend it and ask the validator what it thinks."""
    def run(pages=None, answers=None):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        mock_world(direct_vm, pages if pages is not None else WEB_VERIFIED,
                   answers if answers is not None else VERIFIED_ANSWERS)
        direct_vm.sender = creator
        trace.request_verification(pid)
        record = trace.get_verification(pid, 0)
        proposal = {
            "overall_result": record["overall_result"],
            "held_for_sources": record["held_for_sources"],
            "deviation": record["deviation"],
            "summary": record["summary"],
            "observed_at": record["evidence"][0]["observed_at"],
            "findings": [dict(f) for f in record["findings"]],
            "evidence": [dict(e) for e in record["evidence"]],
        }
        return pid, proposal
    return run


def agrees(direct_vm, proposal) -> bool:
    return direct_vm.run_validator(leader_result=json.dumps(proposal))


class TestAnHonestLeader:
    def test_a_validator_agrees_with_what_it_would_have_said_itself(self, direct_vm, round_of):
        _, proposal = round_of()
        assert agrees(direct_vm, proposal) is True

    def test_different_words_for_the_same_decision_are_accepted(self, direct_vm, round_of):
        """Two readers never write the same sentence. If prose had to match, no
        round would ever pass, and nothing would be safer for it."""
        _, proposal = round_of()
        for finding in proposal["findings"]:
            finding["reason"] = "Different wording entirely, reached the same way."
        proposal["summary"] = "rewritten summary"
        assert agrees(direct_vm, proposal) is True

    def test_citing_a_different_subset_of_the_same_sources_is_accepted(self, direct_vm, round_of):
        """What the floor uses is how many independent publishers stood behind a
        finding, and that is compared. Which ids a node happened to list is not:
        two honest nodes routinely list different subsets."""
        _, proposal = round_of()
        for finding in proposal["findings"]:
            if len(finding["evidence_refs"]) > 1:
                finding["evidence_refs"] = finding["evidence_refs"][:1]
        assert agrees(direct_vm, proposal) is True


class TestALeaderWhoIsWrong:
    def test_a_different_decision_is_refused(self, direct_vm, round_of):
        _, proposal = round_of()
        proposal["findings"][0]["status"] = "UNSATISFIED"
        proposal["findings"][0]["effective_status"] = "UNSATISFIED"
        assert agrees(direct_vm, proposal) is False

    def test_the_same_words_with_a_different_decision_are_refused(self, direct_vm, round_of):
        """The mirror of the test above: identical prose does not buy a verdict."""
        _, proposal = round_of()
        proposal["overall_result"] = "NOT_VERIFIED"
        assert agrees(direct_vm, proposal) is False

    def test_an_invented_quote_is_refused(self, direct_vm, round_of):
        _, proposal = round_of()
        proposal["findings"][0]["quote"] = "The maintainers confirmed everything by telephone."
        assert agrees(direct_vm, proposal) is False

    def test_a_quote_moved_to_a_source_that_does_not_carry_it_is_refused(self, direct_vm, round_of):
        _, proposal = round_of()
        proposal["findings"][0]["quote_evidence_id"] = "E2"
        assert agrees(direct_vm, proposal) is False

    def test_a_forged_state_for_a_source_is_refused(self, direct_vm, round_of):
        """Every node fetches every address itself, so a leader claiming a page
        was missing when this node just read it is caught here."""
        _, proposal = round_of()
        proposal["evidence"][0]["availability"] = "MISSING"
        assert agrees(direct_vm, proposal) is False

    def test_a_forged_publisher_is_refused(self, direct_vm, round_of):
        """The publisher decides how many independent voices a finding has, so
        renaming one is a way to buy the independence floor."""
        _, proposal = round_of()
        proposal["evidence"][1]["publisher"] = "someone.else.example"
        assert agrees(direct_vm, proposal) is False

    def test_an_excerpt_that_is_a_different_document_is_refused(self, direct_vm, round_of):
        _, proposal = round_of()
        proposal["evidence"][0]["excerpt"] = "An entirely different page about something else."
        assert agrees(direct_vm, proposal) is False

    def test_a_digest_that_does_not_cover_the_excerpt_is_refused(self, direct_vm, round_of):
        _, proposal = round_of()
        proposal["evidence"][0]["excerpt_digest"] = "0" * 64
        assert agrees(direct_vm, proposal) is False

    def test_an_independent_source_count_the_evidence_does_not_support_is_refused(
            self, direct_vm, round_of):
        _, proposal = round_of()
        proposal["findings"][0]["independent_sources"] = 5
        assert agrees(direct_vm, proposal) is False

    def test_an_answer_for_a_requirement_this_protocol_does_not_have_is_refused(self, direct_vm,
                                                                                round_of):
        _, proposal = round_of()
        proposal["findings"][0]["requirement_id"] = "R9"
        assert agrees(direct_vm, proposal) is False

    def test_a_missing_requirement_is_refused(self, direct_vm, round_of):
        _, proposal = round_of()
        proposal["findings"] = proposal["findings"][:-1]
        assert agrees(direct_vm, proposal) is False

    def test_a_status_this_contract_does_not_know_is_refused(self, direct_vm, round_of):
        _, proposal = round_of()
        proposal["findings"][0]["status"] = "PROBABLY"
        assert agrees(direct_vm, proposal) is False

    def test_an_overall_result_that_does_not_follow_is_refused(self, direct_vm, round_of):
        """Even with every requirement answered identically, a leader cannot
        name a different overall result: it is derived, not proposed."""
        _, proposal = round_of()
        proposal["overall_result"] = "PARTIALLY_VERIFIED"
        assert agrees(direct_vm, proposal) is False

    def test_a_result_that_is_not_an_object_is_refused(self, direct_vm, round_of):
        round_of()
        assert direct_vm.run_validator(leader_result='"VERIFIED"') is False

    def test_a_leader_who_failed_where_this_node_did_not_is_refused(self, direct_vm, round_of):
        round_of()
        assert direct_vm.run_validator(leader_error=RuntimeError("[TRANSIENT] web trouble")) is False


class TestWhatTheRecordKeeps:
    def test_the_stored_result_carries_the_frozen_fingerprint(self, trace, direct_vm, creator,
                                                              submitter):
        """Every result points back at the exact definition it was measured
        against, so a reader can tell which rules produced it."""
        pid = with_evidence(trace, direct_vm, creator, submitter)
        mock_world(direct_vm, WEB_VERIFIED, VERIFIED_ANSWERS)
        direct_vm.sender = creator
        trace.request_verification(pid)
        record = trace.get_verification(pid, 0)
        assert record["fingerprint"] == trace.get_protocol(pid)["fingerprint"]
        assert record["protocol_id"] == pid

    def test_a_result_the_contract_cannot_re_derive_is_refused(self, trace, direct_vm, creator,
                                                               submitter, monkeypatch):
        """The last gate. Even after the panel agreed, the contract works the
        overall result out again from the agreed answers and refuses to store a
        result that does not follow from them."""
        pid = with_evidence(trace, direct_vm, creator, submitter)
        mock_world(direct_vm, WEB_VERIFIED, VERIFIED_ANSWERS)

        import sys
        # the harness loaded the contract as its own module; importing the file
        # again would be a second contract class, which GenVM refuses
        module = sys.modules["_contract_trace"]
        original = module._derive_result
        calls = {"n": 0}

        def wrong_after_agreement(requirements, findings, rows_by_id, deviation):
            out = original(requirements, findings, rows_by_id, deviation)
            calls["n"] += 1
            if calls["n"] > 1:                      # the re-derivation, not the round itself
                out["overall_result"] = "NOT_VERIFIED"
            return out

        monkeypatch.setattr(module, "_derive_result", wrong_after_agreement)
        direct_vm.sender = creator
        with direct_vm.expect_revert("does not follow this protocol's own rules"):
            trace.request_verification(pid)


class TestEachLayerOnItsOwn:
    """A forged evidence row is caught twice over: the validator compares what
    each node found at each address, and the fingerprint covers the same fields.
    Either one alone refuses the round, which is exactly why a suite that only
    ever sends a forged result through both cannot tell whether both are still
    there. These reach past the round and ask each layer on its own.
    """

    @staticmethod
    def contract():
        # the harness loaded the contract under this name; importing the file
        # again would be a second contract class, which GenVM refuses
        import sys
        return sys.modules["_contract_trace"]

    def test_the_validator_compares_what_each_node_found_at_each_address(self, round_of):
        _, mine = round_of()
        theirs = copy.deepcopy(mine)
        theirs["evidence"][0]["availability"] = "MISSING"
        assert self.contract()._quotes_stand(theirs, mine) is False

    def test_the_validator_compares_who_published_each_source(self, round_of):
        """The publisher decides how many independent voices a finding has, so a
        leader who renames one is buying the source floor."""
        _, mine = round_of()
        theirs = copy.deepcopy(mine)
        theirs["evidence"][1]["publisher"] = "someone.else.example"
        assert self.contract()._quotes_stand(theirs, mine) is False

    def test_a_reading_that_diverges_is_a_different_document(self, round_of):
        _, mine = round_of()
        theirs = copy.deepcopy(mine)
        theirs["evidence"][0]["excerpt"] = "An entirely different page about something else."
        assert self.contract()._quotes_stand(theirs, mine) is False

    def test_a_shorter_reading_of_the_same_page_is_accepted(self, round_of):
        """The mirror, and the reason the check is a prefix rather than equality:
        one node may keep less of a page than another and still have read it."""
        _, mine = round_of()
        theirs = copy.deepcopy(mine)
        for item in theirs["evidence"]:
            item["excerpt"] = item["excerpt"][: max(12, len(item["excerpt"]) // 2)]
        assert self.contract()._quotes_stand(theirs, mine) is True

    def test_the_fingerprint_covers_what_each_node_found(self, round_of):
        _, mine = round_of()
        theirs = copy.deepcopy(mine)
        theirs["evidence"][0]["availability"] = "MISSING"
        fingerprint = self.contract()._fingerprint
        assert fingerprint(theirs) != fingerprint(mine)

    def test_the_fingerprint_covers_who_published_each_source(self, round_of):
        _, mine = round_of()
        theirs = copy.deepcopy(mine)
        theirs["evidence"][1]["publisher"] = "someone.else.example"
        fingerprint = self.contract()._fingerprint
        assert fingerprint(theirs) != fingerprint(mine)

    def test_the_fingerprint_ignores_the_words(self, round_of):
        """And the mirror again: prose is deliberately outside it, because two
        readers never write the same sentence and every round would fail."""
        _, mine = round_of()
        theirs = copy.deepcopy(mine)
        theirs["summary"] = "rewritten entirely"
        for finding in theirs["findings"]:
            finding["reason"] = "different words, same reading"
        fingerprint = self.contract()._fingerprint
        assert fingerprint(theirs) == fingerprint(mine)
