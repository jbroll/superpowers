#!/usr/bin/env python3
"""Plain-assert tests (no pytest dep). Run: python3 analysis/tests/test_mine.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mine import attribute_phases  # noqa: E402

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
