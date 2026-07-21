#!/usr/bin/env python3
"""Mine Claude Code session logs into per-phase size/cost stats.

Phase = which superpowers skill is active (spec/plan/execute), detected from
`Skill` tool_use calls. Subagent tokens roll up into the active phase. Cost is
derived cache-aware from prices.json (no cost field exists in the logs).

The per-(session x phase) attribution here is the primitive; grouping sessions
into features (by gitBranch + time) is a layer on top (see group_features).
"""
import json
import os
import re
import sys

SKILL_PHASE = {
    "superpowers:brainstorming": "spec",
    "superpowers:writing-plans": "plan",
    "superpowers:subagent-driven-development": "execute",
    "superpowers:executing-plans": "execute",
    "superpowers:test-driven-development": "execute",
}
PHASES = ("other", "spec", "plan", "execute")
_SUBTOK = re.compile(r"subagent_tokens:\s*(\d+)")


def _bucket():
    return {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0,
            "subagent_tokens": 0, "tool_calls": 0, "cost": 0.0}


def _msg_cost(model, i, o, cr, cw, prices):
    p = prices.get(model)
    if not p:
        return 0.0
    return (i * p["input"] + o * p["output"]
            + cr * p["cache_read"] + cw * p["cache_write"]) / 1_000_000


def attribute_phases(records, prices):
    """records: ordered list of parsed JSONL objects for one session.
    Returns {phase: bucket}. Pure — no I/O.

    Usage lines are deduped by (message.id, requestId): Claude Code replays
    duplicate entries, and counting them inflates tokens/cost (matches ccusage)."""
    out = {ph: _bucket() for ph in PHASES}
    phase = "other"
    model = None
    seen = set()
    for o in records:
        msg = o.get("message") if isinstance(o.get("message"), dict) else {}
        if msg.get("model"):
            model = msg["model"]
        content = msg.get("content") or []
        for c in content:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "tool_use":
                out[phase]["tool_calls"] += 1
                if c.get("name") == "Skill":
                    sk = (c.get("input") or {}).get("skill")
                    if sk in SKILL_PHASE:
                        phase = SKILL_PHASE[sk]
            elif c.get("type") == "tool_result":
                m = _SUBTOK.search(json.dumps(c.get("content")))
                if m:
                    tok = int(m.group(1))
                    out[phase]["subagent_tokens"] += tok
                    p = prices.get(model)
                    if p:
                        out[phase]["cost"] += tok * p["blended"] / 1_000_000
        u = msg.get("usage")
        if isinstance(u, dict):
            uid = (msg.get("id"), o.get("requestId"))
            if uid != (None, None):
                if uid in seen:
                    continue
                seen.add(uid)
            i = u.get("input_tokens", 0)
            oo = u.get("output_tokens", 0)
            cr = u.get("cache_read_input_tokens", 0)
            cw = u.get("cache_creation_input_tokens", 0)
            b = out[phase]
            b["input"] += i
            b["output"] += oo
            b["cache_read"] += cr
            b["cache_write"] += cw
            b["cost"] += _msg_cost(model, i, oo, cr, cw, prices)
    return out


_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}-")
_ARTIFACT = ("docs/superpowers/specs/", "docs/superpowers/plans/")


def normalize_slug(filename):
    """Feature key shared by a spec and its plan, robust to differing date
    prefixes and the spec's `-design` suffix."""
    s = filename[:-3] if filename.endswith(".md") else filename
    s = _DATE.sub("", s)
    if s.endswith("-design"):
        s = s[:-len("-design")]
    return s


def session_artifacts(records):
    """{slug: touch_count} for spec/plan docs the session read or wrote."""
    slugs = {}
    for o in records:
        msg = o.get("message") if isinstance(o.get("message"), dict) else {}
        for c in (msg.get("content") or []):
            if not (isinstance(c, dict) and c.get("type") == "tool_use"):
                continue
            if c.get("name") not in ("Read", "Write", "Edit"):
                continue
            fp = (c.get("input") or {}).get("file_path", "") or ""
            if any(a in fp for a in _ARTIFACT):
                slug = normalize_slug(fp.split("/")[-1])
                slugs[slug] = slugs.get(slug, 0) + 1
    return slugs


def group_features(sessions):
    """Group per-session summaries into features keyed on artifact slug.
    A session's primary feature is the slug it touched most; artifact-less
    sessions fall into `_unlinked`. Phase buckets sum across a feature's
    sessions (so spec/plan/execute spanning restarts reconstruct into one row)."""
    feats = {}
    for s in sessions:
        slugs = s.get("slugs") or {}
        key = max(slugs, key=lambda k: slugs[k]) if slugs else "_unlinked"
        f = feats.setdefault(key, {"sessions": [],
                                    "phases": {ph: _bucket() for ph in PHASES}})
        f["sessions"].append(s["id"])
        for ph in PHASES:
            for k, v in s["phases"][ph].items():
                f["phases"][ph][k] += v
    return feats


def uses_superpowers(records):
    """True iff the session actually invoked a superpowers skill or touched a
    superpowers artifact. NOT mere mention — the SessionStart hook injects the
    `superpowers:` bootstrap into every session, so string presence is not a
    signal; an actual `Skill` tool_use is."""
    if session_artifacts(records):
        return True
    for o in records:
        msg = o.get("message") if isinstance(o.get("message"), dict) else {}
        for c in (msg.get("content") or []):
            if (isinstance(c, dict) and c.get("type") == "tool_use"
                    and c.get("name") == "Skill"):
                if str((c.get("input") or {}).get("skill", "")).startswith("superpowers:"):
                    return True
    return False


def summarize_session(path, prices):
    recs = load_session(path)
    return {"id": os.path.basename(path).replace(".jsonl", ""),
            "meta": session_meta(recs),
            "phases": attribute_phases(recs, prices),
            "slugs": session_artifacts(recs),
            "uses_sp": uses_superpowers(recs)}


def load_session(path):
    recs = []
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            recs.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return recs


def session_meta(records):
    """Best-effort branch + time span for a session (for feature grouping)."""
    branch, first, last = None, None, None
    for o in records:
        if o.get("gitBranch"):
            branch = o["gitBranch"]
        ts = o.get("timestamp")
        if ts:
            first = first or ts
            last = ts
    return {"branch": branch, "start": first, "end": last}


def _load_prices():
    here = os.path.dirname(os.path.abspath(__file__))
    return json.load(open(os.path.join(here, "prices.json")))


def main(argv):
    by_feature = only_sp = False
    while argv and argv[0].startswith("--"):
        flag = argv.pop(0)
        if flag == "--by-feature":
            by_feature = True
        elif flag == "--only-superpowers":
            only_sp = True
        else:
            print(f"unknown flag: {flag}", file=sys.stderr)
            return 2
    if not argv:
        print("usage: mine.py [--by-feature] [--only-superpowers] SESSION.jsonl ...", file=sys.stderr)
        return 2
    prices = _load_prices()

    if by_feature:
        summaries = [summarize_session(p, prices) for p in argv]
        if only_sp:
            kept = [s for s in summaries if s["uses_sp"]]
            print(f"# {len(kept)}/{len(summaries)} sessions use superpowers "
                  f"({len(summaries) - len(kept)} excluded)", file=sys.stderr)
            summaries = kept
        feats = group_features(summaries)
        print("feature,n_sessions,spec_cost,plan_cost,exec_cost,total_cost,spec_out_tok,plan_out_tok,exec_out_tok")
        rows = []
        for slug, f in feats.items():
            ph = f["phases"]
            total = sum(ph[p]["cost"] for p in PHASES)
            rows.append((total, slug, len(f["sessions"]),
                         ph["spec"]["cost"], ph["plan"]["cost"], ph["execute"]["cost"], total,
                         ph["spec"]["output"], ph["plan"]["output"], ph["execute"]["output"]))
        for r in sorted(rows, reverse=True):
            _, slug, n, sc, pc, ec, tc, so, po, eo = r
            print(f"{slug},{n},{sc:.4f},{pc:.4f},{ec:.4f},{tc:.4f},{so},{po},{eo}")
        return 0

    print("session,branch,phase,input,output,cache_read,cache_write,subagent_tokens,tool_calls,cost_usd")
    for path in argv:
        recs = load_session(path)
        meta = session_meta(recs)
        phases = attribute_phases(recs, prices)
        sid = os.path.basename(path).replace(".jsonl", "")
        for ph in PHASES:
            b = phases[ph]
            if b["input"] or b["output"] or b["subagent_tokens"]:
                print(f"{sid},{meta['branch']},{ph},{b['input']},{b['output']},"
                      f"{b['cache_read']},{b['cache_write']},{b['subagent_tokens']},"
                      f"{b['tool_calls']},{b['cost']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
