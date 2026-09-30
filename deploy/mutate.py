"""Break the contract on purpose, and see whether the suite notices.

    python deploy/mutate.py [--only <substring>]

Each mutant is a single edit that makes TRACE wrong in a way somebody could
plausibly ship: a guard inverted, a floor removed, a check deleted. A green
suite that survives one of these is not holding the thing it claims to hold.

A mutant that survives is either a missing test or a genuinely equivalent
change; the second kind is listed in EQUIVALENT with the reason, so nobody has
to rediscover it.
"""
import argparse
import os
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "contracts" / "trace.py").read_text(encoding="utf-8")

MUTANTS = [
    # --- roles, and whose money is whose --------------------------------------
    ('anybody may accept a protocol',
     'if self._sender().lower() != str(p.responsible_party).lower():\n            _fail("only the responsible party named in this protocol can accept it")',
     'pass'),
    ('a protocol may be accepted before it is frozen',
     'if str(p.lifecycle) != L_AWAITING:',
     'if False:'),
    ('the creator may name themselves responsible',
     'if responsible.lower() == str(p.creator).lower():',
     'if False:'),
    ('anybody may post the bond',
     'elif sender.lower() == str(p.responsible_party).lower():',
     'elif True:'),
    ('the bond depositor is never recorded',
     '            p.bond_depositor = sender',
     '            pass'),
    ('a refused bond names a depositor anyway',
     '            need = int(p.bond_required) - int(p.bond_deposited)',
     '            p.bond_depositor = sender\n            need = int(p.bond_required) - int(p.bond_deposited)'),
    ('the bond goes to whoever sends the settlement',
     '        depositor = str(p.bond_depositor)',
     '        depositor = self._sender()'),
    ('the bond goes to the creator',
     '        if depositor:\n            return depositor',
     '        if True:\n            return str(p.creator)'),
    ('a bond with no depositor is paid out anyway',
     '        if bond_held > 0 and not depositor:',
     '        if False:'),
    ('cancellation hands the bond to whoever cancelled',
     '        bond_side = self._bond_side(p, bond, bond)',
     '        bond_side = self._sender()'),
    ('the responsible party is not frozen with the rest',
     '"economic_policy": economic_policy, "responsible_party": responsible,',
     '"economic_policy": economic_policy,'),
    ('the bond side falls back to the evidence submitter',
     '        answering = str(p.responsible_party)',
     '        answering = self._first_evidence_submitter(p)'),
    # --- who may act ---------------------------------------------------------
    ("anyone may write the draft",
     "if self._sender().lower() != str(p.creator).lower():", "if False:"),
    ("a stranger may freeze a protocol",
     "        self._creator_only(p)\n        if str(p.lifecycle) != L_REGISTERED:",
     "        if str(p.lifecycle) != L_REGISTERED:"),
    ("the creator is whoever the caller says",
     "creator = self._sender()", "creator = self._sender() or ''"),

    # --- what a protocol may say --------------------------------------------
    ("a protocol needs no mandatory requirement",
     'if not any(r["mandatory"] for r in requirements):', "if False:"),
    ("requirement ids may repeat", "    if rid in seen:", "    if False:"),
    ("a requirement id may be anything", 'if not re.fullmatch(r"R[0-9]{1,3}", rid):', "if False:"),
    ("the title may carry a fence",
     '    if ANGLE_RUN.search(out):\n        _fail(f"{field} cannot contain three or more angle '
     'brackets in a row")', "    pass"),
    ("the deadline may be in the past", "if deadline < now + MIN_DEADLINE_AHEAD:", "if False:"),
    ("a protocol may hold any number of requirements", "if len(items) > MAX_REQUIREMENTS:",
     "if False:"),

    # --- freezing ------------------------------------------------------------
    ("a frozen protocol may be rewritten",
     "if str(p.lifecycle) not in (L_DRAFT, L_REGISTERED):\n            _fail(f\"a protocol can "
     "only be written while it is a draft; it is {p.lifecycle}\")", "pass"),
    ("the fingerprint ignores the definition",
     'p.fingerprint = _sha256_hex(str(p.definition_json).encode("utf-8"))',
     'p.fingerprint = _sha256_hex(b"fixed")'),
    ("a protocol may be frozen twice", "if str(p.lifecycle) != L_REGISTERED:", "if False:"),

    # --- evidence ------------------------------------------------------------
    ("evidence may be registered after the deadline",
     "if now > int(p.deadline) + CLOCK_SKEW:", "if False:"),
    ("evidence may be registered before the freeze",
     "if str(p.lifecycle) not in (L_ACTIVE, L_EVIDENCE):\n            _fail(f\"evidence can be "
     "registered while the protocol is open; it is {p.lifecycle}\")", "pass"),
    ("the same page may be registered twice",
     'if existing["source_url"] == row["source_url"]:', "if False:"),
    ("evidence may name a requirement that does not exist", "if unknown:", "if False:"),
    ("plain http is a source", 'if not url.lower().startswith("https://"):', "if False:"),
    ("an address may be an IP", "if IPV4.match(host):", "if False:"),
    ("a credentialed address is a source", 'if "@" in host:', "if False:"),
    ("one publisher counts as several", 'for known, label in ACCOUNT_HOSTS.items():',
     "for known, label in []:"),
    ("a protocol holds unlimited evidence", "if int(p.evidence_count) >= MAX_EVIDENCE:",
     "if False:"),

    # --- what the panel is asked and what is kept ----------------------------
    ("evidence is not fenced before the model sees it",
     'lines.append(f"<<<BEGIN EVIDENCE {item[\'evidence_id\']}>>>")', "pass"),
    ("a fence in a page is deleted rather than replaced",
     'return ANGLE_RUN.sub(" ", text)', 'return ANGLE_RUN.sub("", text)'),
    ("the page is never sanitized", "_sanitize(body)", "body"),
    ("the protocol is not named as the authority",
     '"=== PROTOCOL (authoritative) ===",', '"",'),
    ("a 404 is treated as readable", "if status in (404, 410):", "if False:"),

    # --- grounding -----------------------------------------------------------
    ("a decisive answer needs no quote", "if not grounded:", "if False:"),
    ("a quote may come from any source",
     'if item["evidence_id"] != cited or cited not in allowed:', "if False:"),
    ("a scrap of a quote grounds an answer",
     "    return len(cleaned) >= 8 and len(cleaned.split(\" \")) >= 2",
     "    return len(cleaned) >= 1"),
    ("a quote need not be on this node's copy",
     "grounded = _for_matching(quote) in _for_matching(item[\"excerpt\"])",
     "grounded = True"),
    ("an unknown status is accepted", "if status not in STATUSES:", "if False:"),

    # --- the independent-source floor ---------------------------------------
    ("the floor is removed",
     'if status in (S_SATISFIED, S_UNSATISFIED) and support < rule["min_sources"]:', "if False:"),
    ("the floor catches a success but not a failure",
     "if status in (S_SATISFIED, S_UNSATISFIED) and support",
     "if status in (S_SATISFIED,) and support"),
    ("support is counted from unread sources too",
     'if row and row["availability"] == A_READ:', "if row:"),
    ("support counts addresses rather than publishers",
     'publishers.add(row["publisher"])', 'publishers.add(row["evidence_id"])'),

    # --- the evidence policy -------------------------------------------------
    ("the evidence policy is not checked", "def _policy_deviation(policy: dict, rows: list) -> str:",
     "def _policy_deviation(policy: dict, rows: list) -> str:\n    return ''"),
    ("a domain outside the policy is accepted",
     "            if not any(bare == d or bare.endswith(\".\" + d) for d in allowed):", "            if False:"),
    ("too few publishers passes the policy", 'if len(publishers) < policy["minimum_sources"]:',
     "if False:"),
    ("a missing source type passes the policy", "        if missing:", "        if False:"),

    # --- deterministic aggregation ------------------------------------------
    ("a mandatory failure is not decisive",
     "if any(f[\"effective_status\"] == S_UNSATISFIED for f in mandatory):", "if False:"),
    ("an unresolved mandatory requirement is ignored",
     "elif any(f[\"effective_status\"] == S_UNCERTAIN for f in mandatory):", "elif False:"),
    ("an optional failure is treated as a success",
     "elif all(f[\"effective_status\"] == S_SATISFIED for f in optional):", "elif True:"),
    ("a deviation does not outrank the answers",
     "    if deviation:\n        state = R_DEVIATION", "    if False:\n        state = R_DEVIATION"),
    ("mandatory and optional are the same thing",
     'mandatory = [f for f in final if by_id[f["requirement_id"]]["mandatory"]]',
     "mandatory = list(final)"),

    # --- the boundary between the round and the record -----------------------
    ("the agreed result is stored without being re-derived",
     "if _fingerprint(rederived) != _fingerprint(agreed):", "if False:"),
    ("the shape of the agreed result is not checked",
     "        if not _well_formed(result, definition):\n            _fail(\"the agreed result did "
     "not have the shape this contract requires\")", "        pass"),
    ("the validator accepts any shape", "            if not _well_formed(theirs, definition):",
     "            if False:"),
    ("the validator does not compare fingerprints",
     "return _fingerprint(theirs) == _fingerprint(mine)", "return True"),
    ("the validator does not check the quotes", "            if not _quotes_stand(theirs, mine):",
     "            if False:"),
    ("the validator ignores what each node found",
     '        if ours["availability"] != item.get("availability"):', "        if False:"),
    ("the validator ignores the publisher",
     '        if ours["publisher"] != item.get("publisher"):', "        if False:"),
    ("a different excerpt is the same document", "        if ours[\"availability\"] == A_READ and "
     "not _prefix_compatible(", "        if False and _prefix_compatible("),
    ("the digest need not cover the excerpt",
     '            if e.get("excerpt_digest") != _sha256_hex(excerpt.encode("utf-8")):',
     "            if False:"),
    ("the fingerprint ignores the answers",
     '        "findings": [(f["requirement_id"], f["status"], f["effective_status"],\n'
     '                      f["independent_sources"]) for f in sorted(',
     '        "findings": [(f["requirement_id"],) for f in sorted('),
    ("the fingerprint ignores the overall result", '        "result": result["overall_result"],',
     '        "result": "",'),
    ("the fingerprint ignores what was read",
     '        "evidence": [(e["evidence_id"], e["availability"], e["publisher"])',
     '        "evidence": [(e["evidence_id"],)'),

    # --- rounds --------------------------------------------------------------
    ("a protocol with no evidence may be verified",
     "if str(p.lifecycle) != L_EVIDENCE:", "if False:"),

    # --- acceptance and finality --------------------------------------------
    ("a result is accepted the moment it is proposed", "if now < ready:\n            _fail(f\"this "
     "result can be accepted at {ready}; the transaction time is {now}\")", "pass"),
    ("a result may be accepted twice", 'if str(p.lifecycle) != L_PROPOSED:', "if False:"),
    ("a protocol is paid before its result is accepted",
     'if str(p.lifecycle) != L_ACCEPTED:', "if False:"),

    # --- money ---------------------------------------------------------------
    ("the reward need not be exact",
     'if sent != need:\n                return self._refund(sent, f"the reward must be exactly',
     'if False:\n                return self._refund(sent, f"the reward must be exactly'),
    ("the bond need not be exact",
     'if sent != need:\n                return self._refund(sent, f"the bond must be exactly',
     'if False:\n                return self._refund(sent, f"the bond must be exactly'),
    ("a deposit of nothing is accepted", "if sent <= 0:", "if False:"),
    ("a refused deposit is kept, not sent back",
     "self._send_gen(self._sender(), sent)\n        return REFUNDED + reason",
     "return REFUNDED + reason"),
    ("a refused deposit raises, rolling back its own refund",
     'return self._refund(sent, f"funding is possible while the protocol is open for "',
     '_fail(f"funding is possible while the protocol is open for "'),
    ("the ledger is not zeroed before the transfer",
     "            p.bond_deposited = u256(0)\n"
     "            p.reward_deposited = u256(0)\n"
     "            self.total_custody = u256(int(self.total_custody) - bond - reward)\n"
     "            p.paid_creator = u256(int(p.paid_creator) + to_creator)\n"
     "            p.paid_submitter = u256(int(p.paid_submitter) + to_submitter)\n"
     "            note = f",
     "            note = f"),
    ("every result pays the same", "    if result == R_VERIFIED:\n        release = "
     'policy["verified_payout_bps"]', "    if True:\n        release = BPS"),
    ("a breach forfeits nothing", "forfeit = bond if result == R_NOT_VERIFIED else 0",
     "forfeit = 0"),
    ("a partial result may pay more than a verified one", "if partial > verified:", "if False:"),
    ("the payout is read from the terms rather than the ledger",
     "bond, reward = int(p.bond_deposited), int(p.reward_deposited)\n        to_creator, "
     "to_submitter = 0, 0\n        note = \"finalized\"",
     "bond, reward = int(p.bond_required), int(p.reward_required)\n        to_creator, "
     "to_submitter = 0, 0\n        note = \"finalized\""),
    ("the payee is whoever sends the transaction",
     "        self._send_gen(self._submitter_of(p), to_submitter)\n        return str("
     "p.overall_result)\n\n    @gl.public.write\n    def recover_protocol",
     "        self._send_gen(self._sender(), to_submitter)\n        return str(p.overall_result)"
     "\n\n    @gl.public.write\n    def recover_protocol"),
    ("recovery ignores the window", "if now < ready:\n            _fail(f\"recovery is possible at "
     "{ready}; the transaction time is {now}\")", "pass"),
    ("recovery applies to a finished protocol",
     "if str(p.lifecycle) not in (L_ACTIVE, L_EVIDENCE, L_PROPOSED):", "if False:"),
    ("a protocol with evidence may be cancelled",
     "if str(p.lifecycle) == L_EVIDENCE or int(p.evidence_count) > 0:", "if False:"),
    ("cancelling keeps the deposits",
     "        self._send_gen(str(p.creator), reward)\n        if bond > 0:", "        if bond > 0:"),
]

EQUIVALENT = {
    "a bond with no depositor is paid out anyway":
        "unreachable through the contract's own surface, which is the point of it. The "
        "only writer of bond_deposited is the branch in fund_protocol that sets "
        "bond_depositor in the same breath, so no sequence of public calls leaves a bond "
        "with nobody recorded against it. The guard is for the day that stops being true "
        "-- a storage migration, a second funding path -- and it raises instead of paying "
        "somebody's money to a guess. Reaching the state in a test would mean writing "
        "storage the API does not expose, which tests the test rather than the contract",
    "the shape of the agreed result is not checked":
        "this one cannot be isolated, by construction. Every validator runs the SAME predicate on "
        "the SAME payload as _well_formed(theirs) -- which the mutant below it does kill -- so a "
        "leader whose result fails the shape check never survives consensus to reach this line. "
        "The line is defence against a consensus layer handing back something no validator saw, "
        "and direct mode cannot produce that because the leader is this same code",
    "the creator is whoever the caller says":
        "gl.message.sender_address is never empty inside a write, so `or ''` cannot change it; the "
        "mutant exists to show that the creator comes from the signature and not from an argument",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="run only mutants whose name contains this")
    args = ap.parse_args()

    chosen = [m for m in MUTANTS if args.only.lower() in m[0].lower()]
    survivors, bad = [], []
    with tempfile.TemporaryDirectory() as tmp:
        for name, old, new in chosen:
            if SOURCE.count(old) != 1:
                print(f"BAD MUTANT {name!r}: pattern found {SOURCE.count(old)} times", flush=True)
                bad.append(name)
                continue
            path = pathlib.Path(tmp) / "trace.py"
            path.write_text(SOURCE.replace(old, new), encoding="utf-8")
            env = {**os.environ, "TRACE_CONTRACT": str(path), "PYTHONUTF8": "1"}
            proc = subprocess.run([sys.executable, "-m", "pytest", "tests/direct", "-q", "-x",
                                   "-p", "no:cacheprovider"], cwd=ROOT, env=env,
                                  capture_output=True, text=True)
            killed = proc.returncode != 0
            print(f"{'killed  ' if killed else 'SURVIVED'} {name}", flush=True)
            if not killed:
                survivors.append(name)

    equivalent = [s for s in survivors if s in EQUIVALENT]
    undocumented = [s for s in survivors if s not in EQUIVALENT]
    ran = len(chosen) - len(bad)
    print(f"\n{ran - len(survivors)}/{ran} mutants killed, {len(equivalent)} documented equivalent, "
          f"{len(undocumented)} undocumented" + (f", {len(bad)} bad pattern(s)" if bad else ""))
    for name in undocumented:
        print(f"  SURVIVOR    {name}")
    for name in equivalent:
        print(f"  equivalent  {name}: {EQUIVALENT[name]}")
    return 1 if undocumented or bad else 0


if __name__ == "__main__":
    sys.exit(main())
