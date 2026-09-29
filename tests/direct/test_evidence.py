"""Registering what the panel will read.

Nothing is fetched here. What matters at this point is that both sides can see
which addresses will be read before anybody reads them, and that an address
cannot be registered twice under two spellings of the same thing.
"""
import pytest

from tests.direct.conftest import active, hex_of, registered, warp_to, with_evidence
from tests.direct.support import DEADLINE, URL_INDEX, URL_RELEASE, evidence


class TestSubmitting:
    def test_evidence_is_numbered_and_carries_who_registered_it(self, trace, direct_vm, creator,
                                                                submitter):
        pid = active(trace, direct_vm, creator)
        direct_vm.sender = submitter
        eid = trace.submit_evidence(pid, evidence(URL_RELEASE, ["R1", "R2"], "PUBLICATION", "page"))
        row = trace.get_evidence(pid, eid)
        assert eid == "E1"
        assert row["source_url"] == URL_RELEASE
        assert row["supports"] == ["R1", "R2"]
        assert row["submitter"].lower() == hex_of(submitter).lower()
        assert row["source_domain"] == "widgetworks.example"
        assert row["publisher"] == "widgetworks.example"
        assert trace.get_protocol(pid)["lifecycle"] == "EVIDENCE_SUBMITTED"

    def test_anybody_may_submit_evidence_not_only_the_creator(self, trace, direct_vm, creator,
                                                              stranger):
        """A compliance protocol that only its author could answer would be a
        private opinion with extra steps."""
        pid = active(trace, direct_vm, creator)
        direct_vm.sender = stranger
        assert trace.submit_evidence(pid, evidence(URL_RELEASE, ["R1"])) == "E1"

    def test_evidence_must_speak_to_a_requirement_this_protocol_has(self, trace, direct_vm,
                                                                    creator, submitter):
        pid = active(trace, direct_vm, creator)
        direct_vm.sender = submitter
        with direct_vm.expect_revert("has no requirement R9"):
            trace.submit_evidence(pid, evidence(URL_RELEASE, ["R9"]))
        with direct_vm.expect_revert("must name the requirements"):
            trace.submit_evidence(pid, evidence(URL_RELEASE, []))

    def test_the_same_address_cannot_be_registered_twice(self, trace, direct_vm, creator,
                                                         submitter):
        pid = active(trace, direct_vm, creator)
        direct_vm.sender = submitter
        trace.submit_evidence(pid, evidence(URL_RELEASE, ["R1"]))
        with direct_vm.expect_revert("already registered as E1"):
            trace.submit_evidence(pid, evidence(URL_RELEASE + "/", ["R2"]))

    def test_evidence_is_refused_before_the_protocol_is_frozen(self, trace, direct_vm, creator,
                                                              submitter):
        pid = registered(trace, direct_vm, creator)
        direct_vm.sender = submitter
        with direct_vm.expect_revert("while the protocol is open"):
            trace.submit_evidence(pid, evidence(URL_RELEASE, ["R1"]))

    def test_evidence_is_refused_after_the_deadline(self, trace, direct_vm, creator, submitter):
        pid = active(trace, direct_vm, creator)
        warp_to(direct_vm, DEADLINE + 300)
        direct_vm.sender = submitter
        with direct_vm.expect_revert("deadline for submitting evidence has passed"):
            trace.submit_evidence(pid, evidence(URL_RELEASE, ["R1"]))

    def test_there_is_a_ceiling_on_how_much_evidence_one_protocol_holds(self, trace, direct_vm,
                                                                        creator, submitter):
        pid = active(trace, direct_vm, creator)
        direct_vm.sender = submitter
        for i in range(20):
            trace.submit_evidence(pid, evidence(f"https://openindex.example/p/{i}", ["R1"]))
        with direct_vm.expect_revert("at most 20 evidence items"):
            trace.submit_evidence(pid, evidence("https://openindex.example/p/last", ["R1"]))


class TestWhatCountsAsAnAddress:
    @pytest.mark.parametrize("url,message", [
        ("http://widgetworks.example/x", "must be an https address"),
        ("https://192.0.2.10/x", "not an IP address"),
        ("https://localhost/x", "must be a public address"),
        ("https://user:pass@widgetworks.example/x", "cannot carry credentials"),
        ("https://widgetworks/x", "no valid host"),
        ("https://widgetwörks.example/x", "must be ascii"),
        ("https://widgetworks.example:8443/x", "standard https port"),
    ])
    def test_addresses_this_contract_will_not_accept(self, trace, direct_vm, creator, submitter,
                                                     url, message):
        pid = active(trace, direct_vm, creator)
        direct_vm.sender = submitter
        with direct_vm.expect_revert(message):
            trace.submit_evidence(pid, evidence(url, ["R1"]))

    def test_one_spelling_per_address(self, trace, direct_vm, creator, submitter):
        """Tracking parameters, a trailing slash, a fragment and a capitalised
        host all name the same page, so they must not be able to pass as
        independent sources."""
        pid = active(trace, direct_vm, creator)
        direct_vm.sender = submitter
        eid = trace.submit_evidence(pid, evidence(
            "https://WidgetWorks.example/releases/2-0/?utm_source=x&ref=y#top", ["R1"]))
        assert trace.get_evidence(pid, eid)["source_url"] == (
            "https://widgetworks.example/releases/2-0?ref=y")

    @pytest.mark.parametrize("url,publisher", [
        ("https://raw.githubusercontent.com/acme/widget/main/README.md", "github:acme"),
        ("https://github.com/acme/widget", "github:acme"),
        ("https://acme.github.io/widget", "github:acme"),
        ("https://www.openindex.example/packages/widget", "openindex.example"),
        ("https://news.bbc.co.uk/story", "bbc.co.uk"),
    ])
    def test_two_pages_from_one_account_are_one_publisher(self, trace, direct_vm, creator,
                                                          submitter, url, publisher):
        """Independence is counted by who is speaking, not by how many addresses
        they published at."""
        pid = active(trace, direct_vm, creator)
        direct_vm.sender = submitter
        eid = trace.submit_evidence(pid, evidence(url, ["R1"]))
        assert trace.get_evidence(pid, eid)["publisher"] == publisher


class TestReading:
    def test_the_evidence_of_a_protocol_can_be_listed(self, trace, direct_vm, creator, submitter):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        listing = trace.list_evidence(pid, 0, 30)
        assert listing["total"] == 2
        assert [e["evidence_id"] for e in listing["items"]] == ["E1", "E2"]
        assert [e["source_url"] for e in listing["items"]] == [URL_RELEASE, URL_INDEX]

    def test_asking_for_evidence_that_does_not_exist_says_so(self, trace, direct_vm, creator,
                                                             submitter):
        pid = with_evidence(trace, direct_vm, creator, submitter)
        with direct_vm.expect_revert("no evidence E9"):
            trace.get_evidence(pid, "E9")
