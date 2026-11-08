#!/usr/bin/env python3
"""Criterion 4 (appeals) and the parts of criteria 3 and 5 run_eval.py can't send.

    python app.py                                   # one terminal
    python tools/eval_appeals_and_raw.py --label before

Three trials. Trials are spaced 61 seconds apart on purpose: the rate limiter
runs BEFORE my validation, and requests with no usable creator_id all count
against one address. Without the gap, trial 3's bad requests come back 429
instead of 400 and criterion 5 would be measuring the limiter, not validation.

Writes results/extra_<stamp>_<label>.json with every request and response.
"""
import argparse, datetime as dt, json, sys, time, uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import requests
import config, scoring, scenarios

URL = f"http://{config.HOST}:{config.PORT}"


def log():
    return requests.get(f"{URL}/log").json()["entries"]


def criterion_3_grid():
    """The pure-function half of criterion 3: every score maps, disagreement stays unsure."""
    grid_ok = all(scoring.score_to_label(i / 1000)[1] for i in range(1001))
    differ = scoring.score_to_label(0.51)[0] != scoring.score_to_label(0.95)[0]
    pairs = [(a / 100, b / 100) for a in range(101) for b in range(101) if abs(a - b) >= 50]
    disagree_ok = all(scoring.score_to_label(scoring.combine_signals(x, y))[0] == "unsure" for x, y in pairs)
    return {"grid_1001_all_labelled": grid_ok, "0.51_vs_0.95_differ": differ,
            "disagreement_pairs_checked": len(pairs), "disagreement_all_unsure": disagree_ok}


def criterion_4(trial):
    """5 submissions, 5 appeals, one repeat appeal, one unknown id."""
    checks = []
    for i, text in enumerate(scenarios.HUMAN_STAND_INS[:5], 1):
        creator = f"eval_appeal_t{trial}_{i}"
        sub = requests.post(f"{URL}/submit", json={"text": text, "creator_id": creator}).json()
        cid = sub["content_id"]
        before = [e for e in log() if e.get("content_id") == cid]
        reason = f"Trial {trial} appeal {i}: I drafted this over two evenings and can share my notes."
        ap = requests.post(f"{URL}/appeal", json={"content_id": cid, "reasoning": reason})
        after = [e for e in log() if e.get("content_id") == cid]
        appeals = [e for e in after if e.get("event") == "appeal"]
        content = requests.get(f"{URL}/content/{cid}").json()
        ok = (ap.status_code == 200 and ap.json().get("status") == "under_review"
              and len(appeals) == 1 and appeals[0]["reasoning"] == reason
              and appeals[0]["creator_id"] == creator
              and after[0] == before[0] and content.get("status") == "under_review")
        checks.append({"content_id": cid, "appeal_status": ap.status_code, "appeal_body": ap.json(),
                       "appeal_entries": len(appeals), "original_unchanged": after[0] == before[0],
                       "content_status": content.get("status"), "pass": ok})
    # repeat appeal on the last one
    rep = requests.post(f"{URL}/appeal", json={"content_id": cid, "reasoning": "Adding one more detail."})
    repeat_ok = rep.status_code == 200 and len([e for e in log() if e.get("content_id") == cid and e.get("event") == "appeal"]) == 2
    # unknown id
    fake = str(uuid.uuid4())
    unk = requests.post(f"{URL}/appeal", json={"content_id": fake, "reasoning": "Please review."})
    unknown_ok = unk.status_code == 404 and not [e for e in log() if e.get("content_id") == fake]
    return {"appeals": checks, "passed": sum(c["pass"] for c in checks),
            "repeat_appeal_recorded": repeat_ok, "unknown_id_404_no_entry": unknown_ok,
            "unknown_response": {"status": unk.status_code, "body": unk.json()}}


def criterion_5(trial):
    """All 15 invalid cases from criteria.md, checked for status, JSON shape, and no decision."""
    raw = [("malformed JSON", '{"text": "unterminated', 400),
           ("JSON list", '["text", "creator_id"]', 400)]
    bodies = [(f"body: {json.dumps(b)[:60]}", b, 413 if "long_text" in str(b.get("creator_id")) or "huge" in str(b.get("creator_id")) else 400)
              for b in next(s for s in scenarios.SCENARIOS if s["criterion"] == 5)["bodies"]]
    known = {e.get("content_id") for e in log()}
    results = []
    for name, body, want in raw:
        r = requests.post(f"{URL}/submit", data=body, headers={"Content-Type": "application/json"})
        results.append((name, r, want))
    for name, body, want in bodies:
        r = requests.post(f"{URL}/submit", json=body)
        results.append((name, r, want))
    sub = requests.post(f"{URL}/submit", json={"text": scenarios.HUMAN_STAND_INS[0], "creator_id": f"eval_bad_appeal_t{trial}"}).json()
    cid = sub["content_id"]
    for name, body in [("appeal: missing reasoning", {"content_id": cid}),
                       ("appeal: blank reasoning", {"content_id": cid, "reasoning": "  "}),
                       ("appeal: 2,001-char reasoning", {"content_id": cid, "reasoning": "x" * 2001}),
                       ("appeal: JSON list", ["content_id", cid])]:
        r = requests.post(f"{URL}/appeal", json=body)
        results.append((name, r, 400))
    new_decisions = [e for e in log() if e.get("status") == "decided" and e.get("content_id") not in known
                     and e.get("content_id") != cid]
    appeal_entries = [e for e in log() if e.get("content_id") == cid and e.get("event") == "appeal"]
    out = []
    for name, r, want in results:
        try:
            body = r.json()
        except ValueError:
            body = {"not_json": r.text[:120]}
        ok = r.status_code == want and "error" in body and "message" in body
        out.append({"case": name, "want": want, "got": r.status_code, "body": body, "pass": ok})
    return {"cases": out, "passed": sum(c["pass"] for c in out), "total": len(out),
            "decisions_created_by_bad_input": len(new_decisions),
            "appeals_recorded_by_bad_appeals": len(appeal_entries)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="")
    ap.add_argument("--gap", type=int, default=61)
    args = ap.parse_args()
    trials = []
    for t in range(1, 4):
        # Wait before trial 1 too: run_eval.py usually ran just before this.
        if args.gap:
            print(f"waiting {args.gap}s so the per-minute window resets...")
            time.sleep(args.gap)
        trial = {"trial": t, "criterion_3_grid": criterion_3_grid(),
                 "criterion_4": criterion_4(t), "criterion_5": criterion_5(t)}
        c4, c5 = trial["criterion_4"], trial["criterion_5"]
        print(f"trial {t}: C4 {c4['passed']}/5 repeat={c4['repeat_appeal_recorded']} unknown={c4['unknown_id_404_no_entry']} | "
              f"C5 {c5['passed']}/{c5['total']} decisions={c5['decisions_created_by_bad_input']} appeals={c5['appeals_recorded_by_bad_appeals']} | "
              f"C3 grid {trial['criterion_3_grid']}")
        trials.append(trial)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    path = config.RESULTS_DIR / f"extra_{stamp}{'_' + args.label if args.label else ''}.json"
    path.write_text(json.dumps({"produced_by": "tools/eval_appeals_and_raw.py::main", "trials": trials}, indent=2), encoding="utf-8")
    print(f"Wrote {path.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
