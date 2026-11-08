#!/usr/bin/env python3
"""Turn a run_eval.py report + an extra_*.json file into the five-row run log.

    python tools/score_eval.py results/run_<...>_before.md results/extra_<...>_before.json

Each trial is checked against the exact target in criteria.md. A criterion is
MET only if every trial meets it.
"""
import json, re, statistics, sys

run_md, extra_path = sys.argv[1], sys.argv[2]
md = open(run_md, encoding="utf-8").read()
extra = json.load(open(extra_path, encoding="utf-8"))["trials"]

# Pull the per-scenario trial JSON blocks out of the report, in order.
sections = re.split(r"^### ", md, flags=re.M)[1:]
data = {}
for sec in sections:
    name = sec.splitlines()[0].strip()
    data[name] = [json.loads(b) for b in re.findall(r"```json\n(.*?)```", sec, re.S)]

human = data["own writing stand-ins"]
ai = data["matched AI set"]
fixtures = data["label coverage fixtures"]
bad = data["bad input"]

rows, details = [], {}

# 1. at most 1 of 10 stand-ins labelled ai
c1 = [sum(r["guess"] == "ai" for r in t) for t in human]
rows.append(("1. Own-writing stand-ins labelled AI", "≤ 1 of 10", [f"{n}/10" for n in c1], all(n <= 1 for n in c1)))

# 2. mean AI score − mean human score ≥ 0.20
gaps = []
for h, a in zip(human, ai):
    mh = statistics.mean(r["confidence"] for r in h)
    ma = statistics.mean(r["confidence"] for r in a)
    gaps.append((round(ma - mh, 4), round(mh, 4), round(ma, 4)))
rows.append(("2. Mean AI score minus mean human score", "≥ 0.20", [f"{g[0]:+.4f}" for g in gaps], all(g[0] >= 0.20 for g in gaps)))
details["c2"] = gaps

# 3. all three labels reached by the six fixtures AND the grid/disagreement checks pass
c3 = []
for t, x in zip(fixtures, extra):
    labels = {r["guess"] for r in t}
    g = x["criterion_3_grid"]
    grid_ok = g["grid_1001_all_labelled"] and g["0.51_vs_0.95_differ"] and g["disagreement_all_unsure"]
    c3.append((len(labels & {"human", "unsure", "ai"}), grid_ok))
rows.append(("3. All three labels reached (+ grid checks)", "3 of 3, grid passes",
             [f"{n}/3{'' if ok else ' grid FAIL'}" for n, ok in c3], all(n == 3 and ok for n, ok in c3)))

# 4. five appeals, repeat recorded, unknown id 404
c4 = [(x["criterion_4"]["passed"], x["criterion_4"]["repeat_appeal_recorded"], x["criterion_4"]["unknown_id_404_no_entry"]) for x in extra]
rows.append(("4. Appeals recorded, original kept", "5 of 5 + repeat + 404",
             [f"{p}/5{'' if r and u else ' (extra check failed)'}" for p, r, u in c4], all(p == 5 and r and u for p, r, u in c4)))

# 5. every invalid case gets the right JSON error and creates nothing
c5 = [(x["criterion_5"]["passed"], x["criterion_5"]["total"],
       x["criterion_5"]["decisions_created_by_bad_input"], x["criterion_5"]["appeals_recorded_by_bad_appeals"]) for x in extra]
rows.append(("5. Bad input rejected before scoring", "15 of 15, 0 decisions",
             [f"{p}/{t}{'' if d == 0 and a == 0 else f' ({d} decisions, {a} appeals)'}" for p, t, d, a in c5],
             all(p == t and d == 0 and a == 0 for p, t, d, a in c5)))

print("| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |")
print("|---|---|---|---|---|---|")
for name, target, runs, met in rows:
    print(f"| {name} | {target} | {' | '.join(runs)} | {'MET' if met else 'MISSED'} |")
print()
print("C2 per trial (gap, human mean, AI mean):", details["c2"])
print("C1 per-text scores, trial 1:", [r["confidence"] for r in human[0]])
print("C2 AI per-text scores, trial 1:", [r["confidence"] for r in ai[0]])
print("C3 fixture guesses, trial 1:", [(r["guess"], r["confidence"]) for r in fixtures[0]])
print("C5 run_eval statuses, trial 1:", [r["status"] for r in bad[0]])
