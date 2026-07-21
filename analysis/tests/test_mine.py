#!/usr/bin/env python3
"""Plain-assert tests (no pytest dep). Run: python3 analysis/tests/test_mine.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mine import (attribute_phases, normalize_slug, group_features, PHASES,  # noqa: E402
                  _bucket, uses_superpowers)

PRICES = {
    "m": {"input": 10.0, "output": 100.0, "cache_read": 1.0, "cache_write": 12.5, "blended": 20.0},
}


def asst(model, i=0, o=0, cr=0, cw=0):
    return {"message": {"model": model, "usage": {
        "input_tokens": i, "output_tokens": o,
        "cache_read_input_tokens": cr, "cache_creation_input_tokens": cw}}}


def skill(name):
    return {"message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": name}}]}}


def agent_result(sub_tokens):
    return {"message": {"content": [{"type": "tool_result",
            "content": f"agentId: x\n<usage>subagent_tokens: {sub_tokens} tool_uses: 2</usage>"}]}}


def test_phase_attribution_and_rollup():
    records = [
        asst("m", i=100),                                   # other (before any skill)
        skill("superpowers:brainstorming"),
        asst("m", i=200, o=50),                             # spec
        skill("superpowers:writing-plans"),
        asst("m", i=300, o=60),                             # plan
        skill("superpowers:subagent-driven-development"),
        asst("m", i=400, o=70),                             # execute
        agent_result(1000),                                 # subagent rolls into execute
    ]
    phases = attribute_phases(records, PRICES)

    assert phases["other"]["input"] == 100, phases["other"]
    assert phases["spec"]["input"] == 200 and phases["spec"]["output"] == 50, phases["spec"]
    assert phases["plan"]["input"] == 300, phases["plan"]
    assert phases["execute"]["input"] == 400, phases["execute"]
    assert phases["execute"]["subagent_tokens"] == 1000, phases["execute"]

    # cost: spec = 200*10/1e6 + 50*100/1e6 = 0.002 + 0.005 = 0.007
    assert abs(phases["spec"]["cost"] - 0.007) < 1e-9, phases["spec"]["cost"]
    # execute cost includes subagent blended: main 400*10/1e6 + 70*100/1e6 = 0.004+0.007=0.011
    #   + subagent 1000*20/1e6 = 0.02  => 0.031
    assert abs(phases["execute"]["cost"] - 0.031) < 1e-9, phases["execute"]["cost"]


def test_cache_aware_cost():
    records = [skill("superpowers:brainstorming"),
               asst("m", i=100, cr=1000, cw=200)]
    phases = attribute_phases(records, PRICES)
    # 100*10 + 1000*1 + 200*12.5 = 1000 + 1000 + 2500 = 4500 micro-usd => 0.0045
    assert abs(phases["spec"]["cost"] - 0.0045) < 1e-9, phases["spec"]["cost"]


def test_uses_superpowers_requires_real_invocation():
    # A real superpowers Skill call counts.
    assert uses_superpowers([skill("superpowers:brainstorming")])
    # A non-superpowers skill does not.
    assert not uses_superpowers([skill("react-typescript")])
    # Mere mention in text (the injected bootstrap) does NOT count — no tool_use.
    injected = {"message": {"role": "user", "content": [
        {"type": "text", "text": "You have superpowers. Use superpowers:brainstorming ..."}]}}
    assert not uses_superpowers([injected])
    # Touching a superpowers artifact counts.
    artifact = {"message": {"content": [{"type": "tool_use", "name": "Write",
                "input": {"file_path": "docs/superpowers/specs/2026-07-20-x-design.md"}}]}}
    assert uses_superpowers([artifact])


def test_normalize_slug():
    # spec and plan of the same feature must normalize to the same slug,
    # even when the date prefixes differ (phases days apart).
    assert normalize_slug("2026-07-20-parsimony-cut-rules-design.md") == "parsimony-cut-rules"
    assert normalize_slug("2026-07-21-parsimony-cut-rules.md") == "parsimony-cut-rules"
    assert normalize_slug("2026-06-09-visual-companion-issues.md") == "visual-companion-issues"


def _sess(sid, slugs, **phase_cost):
    phases = {ph: _bucket() for ph in PHASES}
    for ph, cost in phase_cost.items():
        phases[ph]["cost"] = cost
    return {"id": sid, "meta": {}, "phases": phases, "slugs": slugs}


def test_group_features_across_sessions():
    sessions = [
        _sess("A", {"foo": 2}, spec=0.5),          # spec of foo
        _sess("B", {"foo": 1}, plan=0.3),          # plan of foo, DIFFERENT session
        _sess("C", {}, execute=0.9),               # no artifact -> unlinked
        _sess("D", {"bar": 3, "foo": 1}, execute=2.0),  # primary = bar
    ]
    feats = group_features(sessions)

    assert set(feats["foo"]["sessions"]) == {"A", "B"}, feats["foo"]["sessions"]
    assert abs(feats["foo"]["phases"]["spec"]["cost"] - 0.5) < 1e-9
    assert abs(feats["foo"]["phases"]["plan"]["cost"] - 0.3) < 1e-9
    assert feats["bar"]["sessions"] == ["D"]
    assert abs(feats["bar"]["phases"]["execute"]["cost"] - 2.0) < 1e-9
    assert feats["_unlinked"]["sessions"] == ["C"]


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"PASS {name}")
            except AssertionError as e:
                fails += 1; print(f"FAIL {name}: {e}")
    print(f"--- {fails} failure(s)")
    sys.exit(1 if fails else 0)
