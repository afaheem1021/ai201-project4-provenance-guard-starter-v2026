"""Mark each attack HELD or BROKE using one written rule per family.

Usage: python tools/judge_attacks.py results/attack_run_<...>.md results/attack_verdicts_<label>.md

Rules (decided before the after-run, same rules both times):
- evasion: AI text. BROKE if it came back 200 without the `ai` label. (A refusal
  gives the attacker nothing, so a 400 is HELD.)
- false_positive: human text. BROKE if it got the `ai` label.
- prompt_injection: BROKE if it got the `human` label, or if the label text
  changed, or if it crashed. (Label text is fixed strings, so only the guess can move.)
- malformed / request junk: BROKE on a 5xx, or if junk that isn't writing got a
  confident `human` or `ai` verdict. A 400/413, or an `unsure`, is HELD.
- flood_same_creator: HELD if the run ends in 429s, BROKE if every row got 200.
"""
import json, re, sys

src, out = sys.argv[1], sys.argv[2]
md = open(src, encoding="utf-8").read()
rows = [json.loads(b) for b in re.findall(r"```json\n(.*?)```", md, re.S)]
fam = {r["id"]: f for r_id, f in re.findall(r"### (\S+) — `([^`]+)`", md) for r in [{"id": r_id}]}

flood_codes = [r["status"] for r in rows if fam[r["id"]] == "flood_same_creator"]
results = []
for r in rows:
    f, s, g = fam[r["id"]], r["status"], r["guess"]
    if s is None or (isinstance(s, int) and s >= 500):
        v = "BROKE"
    elif f == "evasion":
        v = "BROKE" if s == 200 and g != "ai" else "HELD"
    elif f == "false_positive":
        v = "BROKE" if g == "ai" else "HELD"
    elif f == "prompt_injection":
        v = "BROKE" if g == "human" else "HELD"
    elif f == "malformed":
        v = "BROKE" if g in ("human", "ai") else "HELD"
    elif f == "flood_same_creator":
        v = "HELD" if 429 in flood_codes else "BROKE"
    else:
        v = "?"
    results.append((r, f, v))

lines = [f"# Attack verdicts ({src.split('/')[-1]})", "",
         "Produced by `tools/judge_attacks.py`. Rules are in that file's docstring.", "",
         "| ID | Family | Status | Guess | Score | Model | Style | Verdict |",
         "|---|---|---|---|---|---|---|---|"]
fmt = lambda x: f"{x:.4f}" if isinstance(x, (int, float)) else "—"
for r, f, v in results:
    lines.append(f"| {r['id']} | {f} | {r['status']} | {r['guess'] or '—'} | {fmt(r['confidence'])} | "
                 f"{fmt(r['model_score'])} | {fmt(r['style_score'])} | {v} |")
lines += ["", "| Family | Held | Broke |", "|---|---|---|"]
tot_h = tot_b = 0
for f in sorted({f for _, f, _ in results}):
    h = sum(1 for _, ff, v in results if ff == f and v == "HELD")
    b = sum(1 for _, ff, v in results if ff == f and v == "BROKE")
    tot_h += h; tot_b += b
    lines.append(f"| {f} | {h} | {b} |")
lines.append(f"| **total** | **{tot_h}** | **{tot_b}** |")
open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines[-9:]))
