"""Direct Mode harness for contracts/trace.py.

Nothing is deployed and nothing is fetched: GenVM runs in process, the web and
the model are mocked by support.py, and the validator closure is replayed
through `direct_vm.run_validator()` against results a test invents. That is the
only way to test what a validator does with a leader who is wrong, which is the
part of TRACE that matters most.
"""
import json
import os

import pytest

from tests.direct.support import (BOND, CONTRACT, DEADLINE, NOW, NOW_UNIX, RESPONSIBLE, REWARD,
                                  STRANGER, SUBJECT, SUBMITTER,
                                  SUBJECT_TYPE, TITLE, DESCRIPTION, URL_INDEX, URL_RELEASE,
                                  WEB_VERIFIED, VERIFIED_ANSWERS, answer, draft, evidence, page)


# -- Windows compatibility shim for genlayer-test 0.29.2 ----------------------
# The direct runner injects the transaction message by writing a temp file,
# dup2-ing it onto fd 0 and unlinking the path while fd 0 still holds it. POSIX
# allows that; Windows refuses with WinError 32, so every direct test would
# error at deploy on a fresh Windows checkout. The shim tolerates that one
# refusal and is a no-op elsewhere, so CI runs the published runner unchanged.
def _tolerate_windows_unlink():
    if os.name != "nt":
        return
    try:
        from gltest.direct import loader as _loader
    except ImportError:
        return
    original = _loader._inject_message_to_fd0
    if getattr(original, "_trace_shim", False):
        return

    def inject_tolerant(vm):
        real_unlink = os.unlink

        def unlink_tolerant(path, *args, **kwargs):
            try:
                real_unlink(path, *args, **kwargs)
            except PermissionError:
                pass

        os.unlink = unlink_tolerant
        try:
            return original(vm)
        finally:
            os.unlink = real_unlink

    inject_tolerant._trace_shim = True
    _loader._inject_message_to_fd0 = inject_tolerant


_tolerate_windows_unlink()


# -- warp() must move the transaction's clock ---------------------------------
# Every window in TRACE is measured against gl.message_raw["datetime"], the
# transaction's own time, because that is the one clock two validators running
# the same round agree on. direct_vm.warp() sets the block timestamp and
# refreshes gl.message, but it only rewrites the sender in message_raw -- so
# without this, a test could cross a deadline and the contract would never
# notice.
def _warp_moves_the_message_clock():
    import sys
    from gltest.direct.vm import VMContext

    original = VMContext.warp
    if getattr(original, "_trace_shim", False):
        return

    def warp_and_tell_the_contract(self, timestamp: str) -> None:
        original(self, timestamp)
        module = sys.modules.get("genlayer.gl")
        raw = getattr(module, "message_raw", None) if module else None
        if isinstance(raw, dict):
            raw["datetime"] = timestamp

    warp_and_tell_the_contract._trace_shim = True
    VMContext.warp = warp_and_tell_the_contract


_warp_moves_the_message_clock()


@pytest.fixture
def trace(direct_vm, direct_deploy):
    """A fresh contract, with the clock at a known moment and pickling checked:
    GenLayer persists contract state through serialization, so a storage object
    that cannot be pickled is a defect worth finding here rather than on chain.
    """
    direct_vm.check_pickling = True
    direct_vm.warp(NOW)
    return direct_deploy(str(CONTRACT))


@pytest.fixture
def creator(direct_vm):
    return direct_vm.sender


@pytest.fixture
def responsible():
    """The account the creator names as answerable, and the only one that can
    accept the protocol or post its bond."""
    return RESPONSIBLE


@pytest.fixture
def submitter():
    """Whoever registers evidence. Deliberately NOT the bond depositor: that
    conflation is the defect this suite exists to keep fixed."""
    return SUBMITTER


@pytest.fixture
def stranger():
    return STRANGER


@pytest.fixture
def finalizer():
    """Someone with no stake at all, who merely sends the settling
    transaction."""
    return "0x4444444444444444444444444444444444444444"


def hex_of(account) -> str:
    """An account as the contract spells it, whatever the harness handed us."""
    if hasattr(account, "as_bytes"):
        return "0x" + account.as_bytes.hex()
    if isinstance(account, (bytes, bytearray)):
        return "0x" + bytes(account).hex()
    return str(account)


def warp_to(direct_vm, unix_seconds: int) -> None:
    import datetime
    moment = datetime.datetime.fromtimestamp(unix_seconds, datetime.timezone.utc)
    direct_vm.warp(moment.isoformat().replace("+00:00", "+00:00"))


# ── the ordinary path, as helpers, so a test can start where it means to ─────

def create(trace, direct_vm, signer, **over) -> str:
    direct_vm.sender = signer
    return trace.create_protocol(over.get("title", TITLE), over.get("description", DESCRIPTION),
                                 over.get("subject", SUBJECT),
                                 over.get("subject_type", SUBJECT_TYPE))


def registered(trace, direct_vm, signer, **over) -> str:
    pid = create(trace, direct_vm, signer)
    direct_vm.sender = signer
    trace.set_draft(pid, draft(**{k: v for k, v in over.items() if k != "accepted_by"}))
    return pid


def frozen(trace, direct_vm, signer, **over) -> str:
    """Written and frozen, but nobody has taken it on yet."""
    pid = registered(trace, direct_vm, signer, **over)
    direct_vm.sender = signer
    trace.activate_protocol(pid)
    return pid


def active(trace, direct_vm, signer, **over) -> str:
    """Frozen AND accepted, which is what it now takes to be open for business.

    Acceptance is a separate transaction from a separate account on purpose, so
    every test that starts here has already proved the two are different people.
    """
    pid = frozen(trace, direct_vm, signer, **over)
    direct_vm.sender = over.get("accepted_by", RESPONSIBLE)
    trace.accept_protocol(pid)
    return pid


def fund(trace, direct_vm, signer, pid, amount) -> str:
    direct_vm.sender = signer
    direct_vm.value = amount
    try:
        return trace.fund_protocol(pid)
    finally:
        direct_vm.value = 0


def with_evidence(trace, direct_vm, creator_account, submitter_account, **over) -> str:
    """A protocol that is open, funded on both sides, and carries the two
    demonstration sources.

    Three accounts: the creator funds the reward, the responsible party posts
    the bond, and `submitter_account` only submits evidence. They are separated
    here rather than in one test so that EVERY test built on this fixture would
    notice if the bond started going to whoever submitted first.
    """
    pid = active(trace, direct_vm, creator_account, **over)
    fund(trace, direct_vm, creator_account, pid, REWARD)
    fund(trace, direct_vm, RESPONSIBLE, pid, BOND)
    direct_vm.sender = submitter_account
    trace.submit_evidence(pid, evidence(URL_RELEASE, ["R1", "R2"], "PUBLICATION", "release page"))
    trace.submit_evidence(pid, evidence(URL_INDEX, ["R1", "R2", "R3"], "REGISTRY",
                                        "package index"))
    return pid


def mock_world(direct_vm, pages: dict, answers: dict) -> None:
    """What the pages say, and what a reader concludes about each requirement.

    The model is keyed on the requirement the prompt is about, because TRACE
    asks one question per requirement: that is what makes a requirement-level
    disagreement possible at all.
    """
    direct_vm.clear_mocks()
    for url, response in pages.items():
        direct_vm.mock_web(url, response)
    for requirement_id, response in answers.items():
        direct_vm.mock_llm(f"Requirement {requirement_id}:", response)


def verify(trace, direct_vm, signer, pid, pages=None, answers=None) -> str:
    mock_world(direct_vm, pages if pages is not None else WEB_VERIFIED,
               answers if answers is not None else VERIFIED_ANSWERS)
    direct_vm.sender = signer
    return trace.request_verification(pid)


def latest(trace, pid) -> dict:
    return trace.get_verification(pid, trace.get_protocol(pid)["round_count"] - 1)


def accept(trace, direct_vm, signer, pid, at=None) -> str:
    """Wait out the acceptance delay from the round's own time, not from a fixed
    moment: a test that runs two protocols must not accept the second one before
    its result was proposed."""
    if at is None:
        record = latest(trace, pid)
        at = int(record["verified_at"]) + 301
    warp_to(direct_vm, at)
    direct_vm.sender = signer
    return trace.accept_verification(pid)


def transfers_to(sent, address) -> int:
    return sum(value for to, value in sent if to.lower() == str(address).lower())


@pytest.fixture
def transfers(monkeypatch):
    """Every GEN transfer the contract emits, as (recipient_hex, atto)."""
    from gltest.direct import wasi_mock
    sent = []
    original = wasi_mock._handle_gl_call

    def recording(vm, request):
        if isinstance(request, dict) and "EthSend" in request:
            operation = request["EthSend"]
            address = operation["address"]
            raw = address.as_bytes if hasattr(address, "as_bytes") else bytes(address)
            sent.append(("0x" + raw.hex(), int(operation["value"])))
        return original(vm, request)

    monkeypatch.setattr(wasi_mock, "_handle_gl_call", recording)
    return sent
