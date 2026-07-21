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
from datetime import date

SKILL_PHASE = {
    "superpowers:brainstorming": "spec",
    "superpowers:writing-plans": "plan",
    "superpowers:subagent-driven-development": "execute",
    "superpowers:executing-plans": "execute",
    "superpowers:test-driven-development": "execute",
}
PHASES = ("other", "spec", "plan", "execute", "replan")
# "replan" = a DELIBERATE re-invocation of a planning skill (brainstorming /
# writing-plans) after building began — a planning-failure signal. Routine doc
# edits during the build loop (checking off tasks, re-reading the spec) are NOT
# replan; tool metadata can't distinguish those from a redesign, so we require the
# explicit planning-skill call as the high-precision signal.
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


SPEC_SKILL = "superpowers:brainstorming"
PLAN_SKILL = "superpowers:writing-plans"
EXEC_SKILLS = {"superpowers:subagent-driven-development",
               "superpowers:executing-plans", "superpowers:test-driven-development"}
# Bash commands that mean "building/verifying code" (execution). NOT git (commits
# happen in every phase — a spec commit is not execution).
_EXEC_BASH = re.compile(
    r"\b(pytest|jest|vitest|bun test|go test|cargo (test|build|run)|"
    r"npm (test|run test|run build|start)|make|tsc|mvn|gradle|"
    r"python[0-9.]* -m pytest|\./gradlew)\b")


def classify_turn(blocks):
    """Phase of one assistant turn from what its tools DO, not which skill was
    announced. Priority execute > plan > spec; returns None for tool-less or
    read-only turns (caller carries the phase from adjacent turns)."""
    votes = set()
    for c in blocks:
        if not (isinstance(c, dict) and c.get("type") == "tool_use"):
            continue
        name = c.get("name")
        inp = c.get("input") or {}
        if name == "Skill":
            sk = str(inp.get("skill", ""))
            if sk == SPEC_SKILL:
                votes.add("spec")
            elif sk == PLAN_SKILL:
                votes.add("plan")
            elif sk in EXEC_SKILLS:
                votes.add("execute")
        elif name in ("Write", "Edit"):
            fp = inp.get("file_path", "") or ""
            if "docs/superpowers/specs/" in fp:
                votes.add("spec")
            elif "docs/superpowers/plans/" in fp:
                votes.add("plan")
            else:                       # authoring any other file = building
                votes.add("execute")
        elif name == "Agent":
            votes.add("execute")
        elif name == "Bash":
            if _EXEC_BASH.search(inp.get("command", "") or ""):
                votes.add("execute")
    for ph in ("execute", "plan", "spec"):  # priority
        if ph in votes:
            return ph
    return None


def attribute_phases_by_activity(records, prices):
    """Activity-based attribution: each turn's phase comes from its own tool use
    (classify_turn); tool-less/read-only turns inherit the last classified phase.
    Fixes the sticky-skill problem — inline implementation lands in execute even
    when no execute skill was invoked. Same dedup + subagent rollup as
    attribute_phases. Pure."""
    out = {ph: _bucket() for ph in PHASES}
    phase = "other"
    state = "pre"       # pre -> planned (saw spec/plan) -> building (execute after planning)
    model = None
    seen = set()
    for o in records:
        msg = o.get("message") if isinstance(o.get("message"), dict) else {}
        if msg.get("model"):
            model = msg["model"]
        blocks = msg.get("content") or []
        vote = classify_turn(blocks)
        planning_skill = any(
            isinstance(c, dict) and c.get("type") == "tool_use"
            and c.get("name") == "Skill"
            and str((c.get("input") or {}).get("skill", "")) in (SPEC_SKILL, PLAN_SKILL)
            for c in blocks)
        if state == "building":
            if planning_skill:
                phase = "replan"       # deliberately re-opened planning mid-build
            elif vote is not None:
                phase = "execute"      # any tool work during build, incl. doc bookkeeping
            # vote None -> carry current phase
        elif vote == "execute":
            phase = "execute"
            if state == "planned":
                state = "building"     # real execution began (after planning)
        elif vote in ("spec", "plan"):
            phase = vote
            state = "planned"
        # vote None -> carry current phase (adjacent-turn inheritance)
        for c in blocks:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "tool_use":
                out[phase]["tool_calls"] += 1
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


def summarize_session(path, dated_prices):
    recs = load_session(path)
    meta = session_meta(recs)
    prices = resolve_prices(dated_prices, meta.get("start"))  # contemporary pricing
    return {"id": os.path.basename(path).replace(".jsonl", ""),
            "meta": meta,
            "phases": attribute_phases_by_activity(recs, prices),
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


def resolve_prices(dated, date_str):
    """Flatten a date-effective price table to {model: rates} for a given date.
    Picks each model's entry with the latest `effective` <= date; a date before
    the earliest entry falls back to the earliest (historic sessions get today's
    prices). Pure."""
    day = (date_str or "")[:10] or "9999-99-99"
    flat = {}
    for model, entries in dated.items():
        if not isinstance(entries, list) or not entries:
            continue
        ordered = sorted(entries, key=lambda e: e["effective"])
        applicable = [e for e in ordered if e["effective"] <= day]
        flat[model] = applicable[-1] if applicable else ordered[0]
    return flat


def _load_prices():
    here = os.path.dirname(os.path.abspath(__file__))
    return json.load(open(os.path.join(here, "prices.json")))


def _phase_tokens(b):
    return (b["input"] + b["output"] + b["cache_read"]
            + b["cache_write"] + b["subagent_tokens"])


def timeline_rows(summaries):
    """Per-session records for a time series, sorted by start. Effectiveness
    proxy = spec+plan output tokens (planning verbosity: lower = leaner, the
    thing the parsimony mods target). Labelled a proxy, not a verdict."""
    rows = []
    for s in summaries:
        ph = s["phases"]
        slugs = s.get("slugs") or {}
        rows.append({
            "date": (s["meta"].get("start") or "")[:10],
            "id": s["id"],
            "slug": max(slugs, key=lambda k: slugs[k]) if slugs else "",
            "total_cost": round(sum(ph[p]["cost"] for p in PHASES), 2),
            "total_tokens": sum(_phase_tokens(ph[p]) for p in PHASES),
            "spec_cost": round(ph["spec"]["cost"], 2),
            "plan_cost": round(ph["plan"]["cost"], 2),
            "exec_cost": round(ph["execute"]["cost"], 2),
            "planning_out_tokens": ph["spec"]["output"] + ph["plan"]["output"],
        })
    rows.sort(key=lambda r: (r["date"], r["id"]))
    return rows


def _median(xs):
    s = sorted(xs)
    n = len(s)
    if not n:
        return None
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _human(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(int(n))


def _split_rows(parts, total_rows):
    """Split total_rows across parts proportionally (largest-remainder)."""
    tot = sum(parts) or 1
    raw = [p / tot * total_rows for p in parts]
    base = [int(x) for x in raw]
    short = total_rows - sum(base)
    order = sorted(range(len(parts)), key=lambda i: raw[i] - base[i], reverse=True)
    for i in order[:short]:
        base[i] += 1
    return base


def render_plot(summaries, height=16, barw=3, trailing=8):
    """Stacked weekly column chart: X=week, Y=tokens split by phase
    (spec/plan/execute), with the effectiveness proxy overlaid as a marker line
    on a secondary 0-100% axis. Pre-skill 'other' tokens are excluded."""
    wk = {}
    for s in summaries:
        d = (s["meta"].get("start") or "")[:10]
        if not d:
            continue
        y, w, _ = date.fromisoformat(d).isocalendar()
        b = wk.setdefault(f"{y}-W{w:02d}", {"spec": 0, "plan": 0, "exec": 0, "n": 0})
        b["spec"] += _phase_tokens(s["phases"]["spec"])
        b["plan"] += _phase_tokens(s["phases"]["plan"])
        b["exec"] += _phase_tokens(s["phases"]["execute"])
        b["n"] += 1
    weeks = sorted(wk)
    if not weeks:
        print("(no dated sessions to plot)")
        return

    tot = {w: wk[w]["spec"] + wk[w]["plan"] + wk[w]["exec"] for w in weeks}
    mx = max(tot.values()) or 1

    # Per-FEATURE effectiveness: group sessions by artifact slug, compute each
    # feature's planning share, anchor it to the week it started, then average
    # the features equal-weighted (so one huge feature can't dominate the line).
    feat = {}
    for s in summaries:
        slugs = s.get("slugs") or {}
        if not slugs:
            continue
        slug = max(slugs, key=lambda k: slugs[k])
        d = (s["meta"].get("start") or "")[:10]
        f = feat.setdefault(slug, {"spec": 0, "plan": 0, "exec": 0, "first": "9999-99-99"})
        f["spec"] += _phase_tokens(s["phases"]["spec"])
        f["plan"] += _phase_tokens(s["phases"]["plan"])
        f["exec"] += _phase_tokens(s["phases"]["execute"])
        if d and d < f["first"]:
            f["first"] = d
    # Effectiveness proxy = (spec+plan)/execute tokens per feature ("planning per
    # unit build"). Zero-execution features are attribution-suspect (sticky phase:
    # brainstorm/plan fired but no execute skill) — excluded, counted separately.
    pts, started, suspect = [], {w: 0 for w in weeks}, {w: 0 for w in weeks}
    for f in feat.values():
        if f["first"] == "9999-99-99":
            continue
        y, w, _ = date.fromisoformat(f["first"]).isocalendar()
        fw = f"{y}-W{w:02d}"
        if fw in started:
            started[fw] += 1
        p, e = f["spec"] + f["plan"], f["exec"]
        if e <= 0:
            if fw in suspect:
                suspect[fw] += 1
            continue
        pts.append((f["first"], p / e))
    pts.sort()
    # Trailing-N: at each week, MEDIAN ratio of the last N features started by then.
    eff = {}
    for w in weeks:
        cutoff = date.fromisocalendar(int(w[:4]), int(w[6:]), 7)  # ISO week Sunday
        window = [r for d, r in pts if date.fromisoformat(d) <= cutoff][-trailing:]
        eff[w] = _median(window)
    nfeat = started
    maxeff = max([e for e in eff.values() if e is not None], default=1) or 1

    stacks, effrow = {}, {}
    for w in weeks:
        trows = round(height * tot[w] / mx)
        sp, pl, ex = _split_rows([wk[w]["spec"], wk[w]["plan"], wk[w]["exec"]], trows)
        stacks[w] = (sp, pl, ex)
        e = eff[w]
        effrow[w] = round(height * e / maxeff) if e is not None else -1

    slot = barw + 2  # bar + marker lane + gap
    print(f"Weekly tokens by phase   (░ spec/brainstorm  ▒ plan/writing  █ execute)")
    print(f"◆ = trailing-{trailing} median (spec+plan)/execute tokens per feature "
          f"— planning per unit build\n"
          f"  right axis 0..{maxeff:.2f}x, lower = leaner. Zero-exec features excluded "
          f"(attribution-suspect)\n")
    for row in range(height, 0, -1):
        ylab = _human(mx * row / height) if row in (height, height * 3 // 4,
                                                     height // 2, height // 4) else ""
        line = f"{ylab:>7} │"
        for w in weeks:
            sp, pl, ex = stacks[w]
            if row <= sp:
                ch = "░"
            elif row <= sp + pl:
                ch = "▒"
            elif row <= sp + pl + ex:
                ch = "█"
            else:
                ch = " "
            mk = "◆" if row == effrow[w] and effrow[w] > 0 else " "
            line += ch * barw + mk + " "
        print(line)
    print(f"{'0':>7} └" + "─" * (slot * len(weeks)))
    print(" " * 8 + "".join(f"{w[-3:]:^{slot}}" for w in weeks))
    print(" " * 8 + "".join((f"{eff[w]:.2f}" if eff[w] is not None else "–")
                            .rjust(barw + 1).ljust(slot) for w in weeks)
          + f"  ← trailing-{trailing} plan/exec ratio")
    print(" " * 8 + "".join(f"nf={nfeat[w]}".center(slot) for w in weeks)
          + "  ← features started")
    print(" " * 8 + "".join(f"sx={suspect[w]}".center(slot) for w in weeks)
          + "  ← zero-exec (excluded)")
    print(" " * 8 + "".join(f"n={wk[w]['n']}".center(slot) for w in weeks)
          + "  ← sessions")


def main(argv):
    by_feature = only_sp = timeline = plot = False
    while argv and argv[0].startswith("--"):
        flag = argv.pop(0)
        if flag == "--by-feature":
            by_feature = True
        elif flag == "--only-superpowers":
            only_sp = True
        elif flag == "--timeline":
            timeline = True
        elif flag == "--plot":
            plot = True
        else:
            print(f"unknown flag: {flag}", file=sys.stderr)
            return 2
    if not argv:
        print("usage: mine.py [--by-feature] [--only-superpowers] SESSION.jsonl ...", file=sys.stderr)
        return 2
    prices = _load_prices()
    summaries = []

    if by_feature or timeline or plot:
        summaries = [summarize_session(p, prices) for p in argv]
        if only_sp:
            kept = [s for s in summaries if s["uses_sp"]]
            print(f"# {len(kept)}/{len(summaries)} sessions use superpowers "
                  f"({len(summaries) - len(kept)} excluded)", file=sys.stderr)
            summaries = kept

    if plot:
        render_plot(summaries)
        return 0

    if timeline:
        print(json.dumps(timeline_rows(summaries), indent=2))
        return 0

    if by_feature:
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
        phases = attribute_phases_by_activity(recs, resolve_prices(prices, meta.get("start")))
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
