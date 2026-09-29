"""The protocol the live suite verifies, in one place.

It is the same shape as the direct suite's, so the two are comparable, but the
evidence here is real: pages published from this repository, pinned to a commit
so the bytes a validator fetched cannot change afterwards.
"""
import json
import os

DEMO_COMMIT = os.environ.get("TRACE_DEMO_COMMIT", "")
DEMO = f"https://raw.githubusercontent.com/Olawalter/Trace/{DEMO_COMMIT}/demo"

REWARD = 2 * 10 ** 16                       # 0.02 GEN, put up by the creator
BOND = 10 ** 16                             # 0.01 GEN, posted by whoever answers

TITLE = "Widget 2.0 release compliance"
DESCRIPTION = ("The Widget project states that release 2.0 is published: tagged, under a named "
               "open licence, with a changelog entry for the version.")
SUBJECT = "widgetworks/widget release 2.0"
SUBJECT_TYPE = "SOFTWARE_RELEASE"

REQUIREMENTS = [
    {"requirement_id": "R1", "mandatory": True, "min_sources": 1,
     "description": "A release tagged 2.0 is published.",
     "verification_rule": "A source must show a published release carrying the tag 2.0."},
    {"requirement_id": "R2", "mandatory": True, "min_sources": 1,
     "description": "The release states the licence it is published under.",
     "verification_rule": "A source must name the licence of release 2.0. A source that says no "
                          "licence was declared shows this requirement was not met."},
    {"requirement_id": "R3", "mandatory": False, "min_sources": 1,
     "description": "A changelog entry exists for 2.0.",
     "verification_rule": "A source must show a changelog entry for version 2.0. A source that "
                          "says none was recorded shows this requirement was not met."},
]


def source(name: str) -> str:
    """One of the demonstration pages, pinned to the commit under test."""
    return f"{DEMO}/{name}.md"


_DEADLINE = []


def _run_deadline() -> int:
    """One deadline for the whole run.

    It is computed on first use rather than at import, because the contract
    measures it when a protocol is frozen and a StudioNet round takes minutes.
    It is computed ONCE because two protocols written with the same words must
    be the same protocol: a deadline taken from the wall clock at each call
    makes them differ by however long the network took, and a fingerprint that
    follows the words would then look like a fingerprint that does not.
    """
    import time
    if not _DEADLINE:
        _DEADLINE.append(int(time.time()) + 45 * 60)
    return _DEADLINE[0]


def definition(**over) -> str:
    body = {
        "requirements": [dict(r) for r in REQUIREMENTS],
        "evidence_policy": {"allowed_domains": [], "minimum_sources": 1,
                            "required_source_types": [], "allow_multiple_sources": True,
                            "contradiction_policy": "UNCERTAIN"},
        "economic_policy": {"enabled": True, "bond_required": BOND, "reward_required": REWARD,
                            "verified_payout_bps": 10_000, "partial_payout_bps": 5_000,
                            "not_verified_action": "REFUND", "inconclusive_action": "REFUND",
                            "timeout_action": "REFUND"},
        "deadline": _run_deadline(),
        "recovery_window": 3600,
    }
    body.update(over)
    return json.dumps(body)


def evidence(url: str, supports, source_type: str = "PUBLICATION", label: str = "") -> str:
    return json.dumps({"source_url": url, "source_type": source_type,
                       "supports": list(supports), "label": label})
