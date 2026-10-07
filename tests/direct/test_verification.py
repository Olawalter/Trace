"""A round: what the panel is asked, what it may answer, and what the contract
does with the answers.

The model is mocked here, so each test can say exactly what a reader concluded
and then check that the contract derived the right thing from it -- including
when the reader is wrong, lazy, or being told what to say by the evidence.
"""
import json

import pytest

from tests.direct.conftest import (active, latest, mock_world, verify, warp_to, with_evidence)
from tests.direct.support import (CONTRADICTION_ANSWERS, CONTRADICTION_PICKS_A_SIDE,
                                  INCONCLUSIVE_ANSWERS, NOT_VERIFIED_ANSWERS, NOW_UNIX,
                                  PAGE_INDEX, PAGE_INDEX_NO_NOTES, PAGE_INSTRUCTIONS, PAGE_RELEASE,
                                  PAGE_NOTES, PARTIAL_ANSWERS, URL_GONE, URL_INDEX, URL_NOTES, URL_RELEASE,
                                  VERIFIED_ANSWERS, WEB_INSTRUCTIONS, WEB_NOT_VERIFIED,
                                  WEB_CONTRADICTION, WEB_PARTIAL, WEB_VERIFIED, answer,
                                  draft, evidence, page)


class TestARound:
    def test_a_round_records_one_answer_per_requirement(self, trace, direct_vm, creator,
                                                        submitter):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        vid = verify(trace, direct_vm, creator, pid)
        record = trace.get_verification(pid, 0)
        assert vid == "V0"
        assert [f["requirement_id"] for f in record["findings"]] == ["R1", "R2", "R3"]
        assert record["overall_result"] == "VERIFIED"
        assert record["status"] == "VERDICT_PROPOSED"
        assert record["rules"] == "TRACE-AGG-1"
        assert trace.get_protocol(pid)["lifecycle"] == "VERDICT_PROPOSED"

    def test_the_record_says_what_each_node_found_at_each_address(self, trace, direct_vm, creator,
                                                                  submitter):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid)
        record = trace.get_verification(pid, 0)
        found = {e["evidence_id"]: e for e in record["evidence"]}
        assert found["E1"]["availability"] == "READ"
        assert found["E1"]["publisher"] == "widgetworks.example"
        assert PAGE_RELEASE[:40] in found["E1"]["excerpt"]
        assert len(found["E1"]["excerpt_digest"]) == 64
        assert found["E1"]["observed_at"] == NOW_UNIX

    def test_the_history_shows_the_round_passing_through_pending(self, trace, direct_vm, creator,
                                                                 submitter):
        """VERIFICATION_PENDING lives inside one transaction. It is in the
        history so the path is visible, and it cannot persist, because a round
        that reaches no majority writes nothing at all."""
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid)
        steps = [h["to"] for h in trace.get_history(pid, 0, 30)["items"]]
        assert "VERIFICATION_PENDING" in steps
        assert steps[-1] == "VERDICT_PROPOSED"

    def test_verification_needs_evidence(self, trace, direct_vm, creator):
        pid = active(trace, direct_vm, creator)
        direct_vm.sender = creator
        with direct_vm.expect_revert("no evidence has been registered yet"):
            trace.request_verification(pid)

    def test_rounds_are_spaced_and_capped(self, trace, direct_vm, creator, submitter):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid)
        direct_vm.sender = creator
        with direct_vm.expect_revert("verification needs a protocol with evidence"):
            trace.request_verification(pid)


class TestWhatTheContractDerives:
    """The model answers requirements. The overall result is arithmetic over
    those answers, done here, and the same answers always produce the same
    result."""

    def test_every_mandatory_requirement_satisfied_is_verified(self, trace, direct_vm, creator,
                                                               submitter):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid)
        assert trace.get_verification(pid, 0)["overall_result"] == "VERIFIED"

    def test_a_mandatory_requirement_the_evidence_disproves_is_not_verified(self, trace, direct_vm,
                                                                            creator, submitter):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid, WEB_NOT_VERIFIED, NOT_VERIFIED_ANSWERS)
        record = trace.get_verification(pid, 0)
        assert record["overall_result"] == "NOT_VERIFIED"
        assert "1 of 2 mandatory" in record["summary"]

    def test_a_mandatory_requirement_nothing_settles_is_inconclusive(self, trace, direct_vm,
                                                                     creator, submitter):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid, WEB_NOT_VERIFIED, INCONCLUSIVE_ANSWERS)
        assert trace.get_verification(pid, 0)["overall_result"] == "INCONCLUSIVE"

    def test_only_an_optional_requirement_failing_is_partial(self, trace, direct_vm, creator,
                                                             submitter):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid, WEB_PARTIAL, PARTIAL_ANSWERS)
        record = trace.get_verification(pid, 0)
        assert record["overall_result"] == "PARTIALLY_VERIFIED"
        assert "2 of 2 mandatory requirement(s) satisfied" in record["summary"]

    def test_a_proven_failure_outranks_an_unresolved_one(self, trace, direct_vm, creator,
                                                         submitter):
        """Deliberately not the ordering the brief suggests. If one mandatory
        requirement is definitively not met, resolving another cannot make the
        protocol verified, so calling the whole thing INCONCLUSIVE would throw
        away something the evidence actually settled."""
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid, WEB_NOT_VERIFIED, {
            "R1": answer("UNCERTAIN"),
            "R2": answer("UNSATISFIED", "Declared licence: not stated by the publisher.", "E2"),
            "R3": answer("UNCERTAIN"),
        })
        assert trace.get_verification(pid, 0)["overall_result"] == "NOT_VERIFIED"

    def test_a_requirement_with_no_evidence_against_it_is_uncertain(self, trace, direct_vm,
                                                                    creator, submitter):
        pid = active(trace, direct_vm, creator)
        direct_vm.sender = submitter
        trace.submit_evidence(pid, evidence(URL_RELEASE, ["R1"], "PUBLICATION"))
        verify(trace, direct_vm, creator, pid, {URL_RELEASE: page(PAGE_RELEASE)}, {
            "R1": answer("SATISFIED", "Widget 2.0 Release. Tag: v2.0.", "E1")})
        record = trace.get_verification(pid, 0)
        answers = {f["requirement_id"]: f for f in record["findings"]}
        assert answers["R2"]["status"] == "UNCERTAIN"
        assert "no evidence" in answers["R2"]["reason"]
        assert record["overall_result"] == "INCONCLUSIVE"


class TestEvidenceThatContradictsItself:
    """What the frozen contradiction policy actually means.

    TRACE freezes one contradiction rule, UNCERTAIN, and these are the tests
    that it is a rule the contract carries out rather than a stored string: two
    sources that state different licences for the same release leave the
    mandatory requirement unresolved, and an unresolved mandatory requirement
    is INCONCLUSIVE.
    """

    def test_two_sources_that_disagree_leave_the_requirement_unresolved(
            self, trace, direct_vm, creator, submitter):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid, WEB_CONTRADICTION, CONTRADICTION_ANSWERS)
        record = trace.get_verification(pid, 0)
        answers = {f["requirement_id"]: f for f in record["findings"]}

        # both pages were read, and they say different things about the licence
        read = {item["evidence_id"]: item for item in record["evidence"]}
        assert read["E1"]["availability"] == "READ" and read["E2"]["availability"] == "READ"
        assert "Apache License 2.0" in read["E1"]["excerpt"]
        assert "proprietary" in read["E2"]["excerpt"]

        assert answers["R2"]["status"] == "UNCERTAIN"
        assert answers["R2"]["effective_status"] == "UNCERTAIN"
        # the requirement the sources agree about is still settled
        assert answers["R1"]["effective_status"] == "SATISFIED"
        assert record["overall_result"] == "INCONCLUSIVE"

    def test_picking_a_side_and_citing_the_wrong_source_does_not_ground_it(
            self, trace, direct_vm, creator, submitter):
        """The demotion is the contract's, not the reader's.

        Here the panel does answer decisively -- SATISFIED, the Apache
        sentence -- but cites the index, which is the source that says the
        opposite. The words are not in the page it cited, so the answer cannot
        be decisive, and the protocol lands in the same place."""
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid, WEB_CONTRADICTION, CONTRADICTION_PICKS_A_SIDE)
        record = trace.get_verification(pid, 0)
        answers = {f["requirement_id"]: f for f in record["findings"]}
        assert answers["R2"]["status"] == "UNCERTAIN"
        assert answers["R2"]["quote"] == "" and answers["R2"]["quote_evidence_id"] == ""
        assert record["overall_result"] == "INCONCLUSIVE"


class TestTheEvidencePolicy:
    def test_evidence_the_policy_does_not_accept_is_a_protocol_deviation(self, trace, direct_vm,
                                                                         creator, submitter):
        """A protocol verified against evidence it never accepted would be worth
        nothing, so this is decided in code and outranks everything the model
        said."""
        pid = active(trace, direct_vm, creator,
                     evidence_policy={"allowed_domains": ["openindex.example"],
                                      "minimum_sources": 1, "required_source_types": [],
                                      "allow_multiple_sources": True,
                                      "contradiction_policy": "UNCERTAIN"})
        direct_vm.sender = submitter
        trace.submit_evidence(pid, evidence(URL_RELEASE, ["R1", "R2", "R3"]))
        verify(trace, direct_vm, creator, pid, {URL_RELEASE: page(PAGE_RELEASE)}, VERIFIED_ANSWERS)
        record = trace.get_verification(pid, 0)
        assert record["overall_result"] == "PROTOCOL_DEVIATION"
        assert "not one of the domains the policy allows" in record["deviation"]

    def test_too_few_independent_publishers_is_a_protocol_deviation(self, trace, direct_vm,
                                                                    creator, submitter):
        pid = active(trace, direct_vm, creator,
                     evidence_policy={"allowed_domains": [], "minimum_sources": 2,
                                      "required_source_types": [], "allow_multiple_sources": True,
                                      "contradiction_policy": "UNCERTAIN"})
        direct_vm.sender = submitter
        trace.submit_evidence(pid, evidence(URL_RELEASE, ["R1", "R2", "R3"]))
        trace.submit_evidence(pid, evidence(URL_RELEASE + "/notes", ["R1"]))
        verify(trace, direct_vm, creator, pid,
               {URL_RELEASE: page(PAGE_RELEASE), URL_RELEASE + "/notes": page(PAGE_RELEASE)},
               VERIFIED_ANSWERS)
        record = trace.get_verification(pid, 0)
        assert record["overall_result"] == "PROTOCOL_DEVIATION"
        assert "independent source" in record["deviation"]

    def test_a_missing_source_type_is_a_protocol_deviation(self, trace, direct_vm, creator,
                                                           submitter):
        pid = active(trace, direct_vm, creator,
                     evidence_policy={"allowed_domains": [], "minimum_sources": 1,
                                      "required_source_types": ["REGISTRY"],
                                      "allow_multiple_sources": True,
                                      "contradiction_policy": "UNCERTAIN"})
        direct_vm.sender = submitter
        trace.submit_evidence(pid, evidence(URL_RELEASE, ["R1", "R2", "R3"], "PUBLICATION"))
        verify(trace, direct_vm, creator, pid, {URL_RELEASE: page(PAGE_RELEASE)}, VERIFIED_ANSWERS)
        assert trace.get_verification(pid, 0)["overall_result"] == "PROTOCOL_DEVIATION"


class TestWhenASourceCannotBeRead:
    def test_a_source_that_is_gone_is_recorded_as_missing_and_proves_nothing(self, trace,
                                                                             direct_vm, creator,
                                                                             submitter):
        """Inability to read a source is not evidence that a requirement was not
        met. It is recorded as what it is, and the requirement stays open."""
        pid = active(trace, direct_vm, creator)
        direct_vm.sender = submitter
        trace.submit_evidence(pid, evidence(URL_GONE, ["R1", "R2", "R3"]))
        verify(trace, direct_vm, creator, pid, {URL_GONE: page("", status=404)}, {
            "R1": answer("UNCERTAIN"), "R2": answer("UNCERTAIN"), "R3": answer("UNCERTAIN")})
        record = trace.get_verification(pid, 0)
        assert record["evidence"][0]["availability"] == "MISSING"
        assert record["evidence"][0]["excerpt"] == ""
        assert record["overall_result"] == "INCONCLUSIVE"

    def test_an_answer_cannot_rest_on_a_source_that_was_not_read(self, trace, direct_vm, creator,
                                                                 submitter):
        """A model insisting a requirement is satisfied, citing a page that
        returned 404, is demoted rather than believed."""
        pid = active(trace, direct_vm, creator)
        direct_vm.sender = submitter
        trace.submit_evidence(pid, evidence(URL_GONE, ["R1", "R2", "R3"]))
        verify(trace, direct_vm, creator, pid, {URL_GONE: page("", status=404)}, {
            "R1": answer("SATISFIED", "Widget 2.0 was released under Apache 2.0.", "E1"),
            "R2": answer("SATISFIED", "Widget 2.0 was released under Apache 2.0.", "E1"),
            "R3": answer("UNCERTAIN")})
        answers = {f["requirement_id"]: f for f in trace.get_verification(pid, 0)["findings"]}
        assert answers["R1"]["status"] == "UNCERTAIN"
        assert answers["R1"]["quote"] == ""


class TestGrounding:
    def test_a_decisive_answer_needs_words_from_the_page_this_node_read(self, trace, direct_vm,
                                                                        creator, submitter):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid, WEB_VERIFIED, {
            "R1": answer("SATISFIED", "The maintainers assured us it was released.", "E1"),
            "R2": VERIFIED_ANSWERS["R2"], "R3": VERIFIED_ANSWERS["R3"]})
        answers = {f["requirement_id"]: f for f in trace.get_verification(pid, 0)["findings"]}
        assert answers["R1"]["status"] == "UNCERTAIN", "a quote that is not on the page is not proof"
        assert answers["R2"]["status"] == "SATISFIED"

    def test_a_quote_from_the_wrong_source_does_not_ground_an_answer(self, trace, direct_vm,
                                                                     creator, submitter):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid, WEB_VERIFIED, {
            "R1": answer("SATISFIED", "Widget 2.0 Release. Tag: v2.0.", "E2"),
            "R2": VERIFIED_ANSWERS["R2"], "R3": VERIFIED_ANSWERS["R3"]})
        answers = {f["requirement_id"]: f for f in trace.get_verification(pid, 0)["findings"]}
        assert answers["R1"]["status"] == "UNCERTAIN"

    def test_the_words_ground_an_answer_even_without_the_markup(self, trace, direct_vm, creator,
                                                                 submitter):
        """A page writes `**Licence:** Apache License 2.0`; a reader quotes the
        words without the asterisks. Those are the same words, and calling the
        second one invented demotes honest answers all day. Found live: the
        first real round returned INCONCLUSIVE about a licence the page states
        plainly."""
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid,
               {URL_RELEASE: page("# Widget 2.0 record **Licence:** Apache License 2.0 "
                                  "**Tag:** v2.0"),
                URL_INDEX: page(PAGE_INDEX)}, {
                   "R1": answer("SATISFIED", "Tag: v2.0", "E1"),
                   "R2": answer("SATISFIED", "Licence: Apache License 2.0", "E1"),
                   "R3": VERIFIED_ANSWERS["R3"]})
        answers = {f["requirement_id"]: f for f in trace.get_verification(pid, 0)["findings"]}
        assert answers["R1"]["status"] == "SATISFIED"
        assert answers["R2"]["status"] == "SATISFIED"
        assert trace.get_verification(pid, 0)["overall_result"] == "VERIFIED"

    def test_a_scrap_of_a_quote_is_not_a_quote(self, trace, direct_vm, creator, submitter):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid, WEB_VERIFIED, {
            "R1": answer("SATISFIED", "2.0", "E1"),
            "R2": VERIFIED_ANSWERS["R2"], "R3": VERIFIED_ANSWERS["R3"]})
        answers = {f["requirement_id"]: f for f in trace.get_verification(pid, 0)["findings"]}
        assert answers["R1"]["status"] == "UNCERTAIN"


class TestWhenTheModelMisbehaves:
    def test_a_status_this_contract_does_not_know_stops_the_round(self, trace, direct_vm, creator,
                                                                  submitter):
        """Malformed output must never become a quiet verdict. A round that
        cannot be read writes nothing at all."""
        pid = with_evidence(trace, direct_vm, creator, submitter)
        mock_world(direct_vm, WEB_VERIFIED, {
            "R1": json.dumps({"status": "PROBABLY", "quote": "", "quote_evidence_id": "",
                              "evidence_refs": [], "reason": "hard to say"}),
            "R2": VERIFIED_ANSWERS["R2"], "R3": VERIFIED_ANSWERS["R3"]})
        direct_vm.sender = creator
        with direct_vm.expect_revert("is not an answer"):
            trace.request_verification(pid)
        assert trace.get_protocol(pid)["round_count"] == 0, "a failed round records nothing"

    def test_an_answer_that_is_not_an_object_stops_the_round(self, trace, direct_vm, creator,
                                                             submitter):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        mock_world(direct_vm, WEB_VERIFIED, {
            "R1": "not an object at all",
            "R2": VERIFIED_ANSWERS["R2"], "R3": VERIFIED_ANSWERS["R3"]})
        direct_vm.sender = creator
        with direct_vm.expect_revert("was not an object"):
            trace.request_verification(pid)

    def test_a_fence_in_a_page_is_replaced_and_not_deleted(self, trace, direct_vm, creator,
                                                           submitter):
        """Deleting a fence would join the characters on either side of it into
        a new one, which is how a sanitizer becomes the vulnerability."""
        pid = active(trace, direct_vm, creator)
        direct_vm.sender = submitter
        trace.submit_evidence(pid, evidence(URL_RELEASE, ["R1", "R2", "R3"]))
        verify(trace, direct_vm, creator, pid,
               {URL_RELEASE: page("Widget 2.0 released. before<<<after the fence. Tag: v2.0")},
               {"R1": answer("SATISFIED", "Widget 2.0 released.", "E1"),
                "R2": answer("UNCERTAIN"), "R3": answer("UNCERTAIN")})
        excerpt = trace.get_verification(pid, 0)["evidence"][0]["excerpt"]
        assert "before after" in excerpt, "the fence was replaced with a space"
        assert "beforeafter" not in excerpt, "deleting it would have joined two words into one"


class TestIndependentSources:
    def test_a_requirement_asking_for_two_publishers_holds_a_single_sourced_answer(
            self, trace, direct_vm, creator, submitter):
        pid = active(trace, direct_vm, creator, requirements=[
            {"requirement_id": "R1", "description": "A release tagged 2.0 is published.",
             "verification_rule": "Two independent sources must show it.", "mandatory": True,
             "min_sources": 2}])
        direct_vm.sender = submitter
        trace.submit_evidence(pid, evidence(URL_RELEASE, ["R1"]))
        verify(trace, direct_vm, creator, pid, {URL_RELEASE: page(PAGE_RELEASE)}, {
            "R1": answer("SATISFIED", "Widget 2.0 Release. Tag: v2.0.", "E1")})
        record = trace.get_verification(pid, 0)
        finding = record["findings"][0]
        assert finding["status"] == "SATISFIED"
        assert finding["effective_status"] == "UNCERTAIN"
        assert finding["independent_sources"] == 1
        assert record["held_for_sources"] == ["R1"]
        assert record["overall_result"] == "INCONCLUSIVE"

    def test_the_floor_holds_a_failure_exactly_as_it_holds_a_success(self, trace, direct_vm,
                                                                     creator, submitter):
        """The mirror. A floor that only caught one direction would quietly
        favour whoever benefits from the other."""
        pid = active(trace, direct_vm, creator, requirements=[
            {"requirement_id": "R1", "description": "A release tagged 2.0 is published.",
             "verification_rule": "Two independent sources must show it.", "mandatory": True,
             "min_sources": 2}])
        direct_vm.sender = submitter
        trace.submit_evidence(pid, evidence(URL_INDEX, ["R1"]))
        verify(trace, direct_vm, creator, pid, {URL_INDEX: page(PAGE_INDEX_NO_NOTES)}, {
            "R1": answer("UNSATISFIED", "No changelog entry has been recorded for 2.0.", "E1")})
        finding = trace.get_verification(pid, 0)["findings"][0]
        assert finding["status"] == "UNSATISFIED"
        assert finding["effective_status"] == "UNCERTAIN"
        assert trace.get_verification(pid, 0)["held_for_sources"] == ["R1"]

    def test_two_pages_from_one_publisher_do_not_satisfy_the_floor(self, trace, direct_vm,
                                                                   creator, submitter):
        """Independence is counted by who is speaking. A publisher who says the
        same thing at two addresses has said it once."""
        pid = active(trace, direct_vm, creator, requirements=[
            {"requirement_id": "R1", "description": "A release tagged 2.0 is published.",
             "verification_rule": "Two independent sources must show it.", "mandatory": True,
             "min_sources": 2}])
        direct_vm.sender = submitter
        trace.submit_evidence(pid, evidence(URL_RELEASE, ["R1"]))
        trace.submit_evidence(pid, evidence(URL_NOTES, ["R1"]))
        verify(trace, direct_vm, creator, pid,
               {URL_RELEASE: page(PAGE_RELEASE), URL_NOTES: page(PAGE_NOTES)},
               {"R1": answer("SATISFIED", "Widget 2.0 Release. Tag: v2.0.", "E1",
                             refs=["E1", "E2"])})
        finding = trace.get_verification(pid, 0)["findings"][0]
        assert finding["independent_sources"] == 1, "one publisher, whatever the address"
        assert finding["effective_status"] == "UNCERTAIN"

    def test_a_source_that_could_not_be_read_does_not_count_towards_the_floor(self, trace,
                                                                              direct_vm, creator,
                                                                              submitter):
        """The unreadable source here is a SECOND publisher, deliberately.

        If it were another address belonging to the publisher that was read, the
        floor would hold the answer whether or not unreadable rows counted, and
        this test would pass while proving nothing. Counting this one would take
        the finding from held to decisive, so the assertion below is load-bearing.
        """
        pid = active(trace, direct_vm, creator, requirements=[
            {"requirement_id": "R1", "description": "A release tagged 2.0 is published.",
             "verification_rule": "Two independent sources must show it.", "mandatory": True,
             "min_sources": 2}])
        direct_vm.sender = submitter
        trace.submit_evidence(pid, evidence(URL_RELEASE, ["R1"]))
        trace.submit_evidence(pid, evidence(URL_INDEX, ["R1"]))
        verify(trace, direct_vm, creator, pid,
               {URL_RELEASE: page(PAGE_RELEASE), URL_INDEX: page("", status=404)},
               {"R1": answer("SATISFIED", "Widget 2.0 Release. Tag: v2.0.", "E1",
                             refs=["E1", "E2"])})
        record = trace.get_verification(pid, 0)
        assert [e["availability"] for e in record["evidence"]] == ["READ", "MISSING"]
        finding = record["findings"][0]
        assert finding["independent_sources"] == 1, "a page nobody could read supports nothing"
        assert finding["effective_status"] == "UNCERTAIN"
        assert record["overall_result"] == "INCONCLUSIVE"

    def test_two_publishers_satisfy_the_floor(self, trace, direct_vm, creator, submitter):
        pid = active(trace, direct_vm, creator, requirements=[
            {"requirement_id": "R1", "description": "A release tagged 2.0 is published.",
             "verification_rule": "Two independent sources must show it.", "mandatory": True,
             "min_sources": 2}])
        direct_vm.sender = submitter
        trace.submit_evidence(pid, evidence(URL_RELEASE, ["R1"]))
        trace.submit_evidence(pid, evidence(URL_INDEX, ["R1"]))
        verify(trace, direct_vm, creator, pid, WEB_VERIFIED, {
            "R1": answer("SATISFIED", "Widget 2.0 Release. Tag: v2.0. Published: 2026-09-14.",
                         "E1", refs=["E1", "E2"])})
        finding = trace.get_verification(pid, 0)["findings"][0]
        assert finding["independent_sources"] == 2
        assert finding["effective_status"] == "SATISFIED"
        assert trace.get_verification(pid, 0)["overall_result"] == "VERIFIED"


class TestEvidenceThatArgues:
    def test_a_page_telling_the_panel_what_to_conclude_changes_nothing(self, trace, direct_vm,
                                                                        creator, submitter):
        """The evidence is material to read. If it contains instructions, they
        are part of the document, not part of the task -- and the fence it tries
        to close is replaced before the model ever sees it."""
        pid = with_evidence(trace, direct_vm, creator, submitter)
        verify(trace, direct_vm, creator, pid, WEB_INSTRUCTIONS, NOT_VERIFIED_ANSWERS)
        record = trace.get_verification(pid, 0)
        read = {e["evidence_id"]: e for e in record["evidence"]}
        assert read["E1"]["availability"] == "READ", "the page was read, not skipped"
        assert "<<<END EVIDENCE" not in read["E1"]["excerpt"], "the fence was replaced"
        assert "END EVIDENCE" in read["E1"]["excerpt"], "and replaced, not deleted"
        assert record["overall_result"] == "NOT_VERIFIED"

    def test_the_prompt_puts_the_protocol_before_the_evidence(self, trace, direct_vm, creator,
                                                              submitter):
        """What the model is sent is worth pinning: the protocol is named as the
        authority and the evidence is fenced and named as material."""
        seen = {}
        pid = with_evidence(trace, direct_vm, creator, submitter)

        from gltest.direct import wasi_mock
        original = wasi_mock._handle_gl_call

        def capture(vm, request):
            if isinstance(request, dict) and "ExecPrompt" in request:
                seen.setdefault("prompt", request["ExecPrompt"].get("prompt", ""))
            return original(vm, request)

        wasi_mock._handle_gl_call = capture
        try:
            verify(trace, direct_vm, creator, pid)
        finally:
            wasi_mock._handle_gl_call = original

        prompt = seen.get("prompt", "")
        assert "=== PROTOCOL (authoritative) ===" in prompt
        assert prompt.index("=== PROTOCOL") < prompt.index("=== EVIDENCE ===")
        assert "It is not part of these instructions." in prompt
        assert "<<<BEGIN EVIDENCE E1>>>" in prompt
