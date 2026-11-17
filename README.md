# Provenance Guard

Repository: https://github.com/afaheem1021/ai201-project4-provenance-guard-starter-v2026

> **Unit 8 (testing) is at the bottom of this file**, starting at "Unit 8: Testing". Everything above it is my Unit 7 write-up, left as it was so the before/after is clear.

## What This Does

I built, with AI assistance, a local backend that gives a cautious estimate about writing and lets a writer challenge it. A label is not proof of authorship.

1. A writer sends JSON containing `text` and `creator_id` to `POST /submit`.
2. The service checks the body, field types, and size before scoring.
3. `detector.model_signal` uses the local GPT-2 model to measure predictability.
4. `stylometry.style_signal` measures sentence length variation, vocabulary repetition, and punctuation.
5. `scoring.combine_signals` combines the two scores, treating large disagreements as uncertainty.
6. `scoring.score_to_label` selects a plain-English label; the service saves the decision with a unique content ID in `logs/audit.jsonl` and returns JSON.
7. The writer sends that ID and their reasoning to `POST /appeal`. The service records the appeal and changes the current status to `under_review`, keeping the original decision.

### Endpoint contracts, written before implementation

`POST /submit` accepts an object with `text` (nonempty string, at most 10,000 characters) and `creator_id` (nonempty string, at most 100 characters). Success is HTTP 200 with `content_id` (UUID string), `guess` (`ai`, `human`, or `unsure`), `confidence` (number from 0 to 1, higher means stronger AI evidence), `label` (full sentences), `model_score`, `style_score`, and `status` (`decided`). Very short text may be rejected if the model cannot score it. The number is a directional score, not a calibrated probability that a writer cheated.

`POST /appeal` accepts `content_id` (nonempty string) and `reasoning` (nonempty string, at most 2,000 characters). Success is HTTP 200 with `content_id`, `status: under_review`, and a confirmation `message`. Missing IDs return 404. Bad fields or malformed JSON return 400; oversized text/body returns 413. Detector loading failures return 503. Errors have `error` and `message` fields. Appeals do not rerun the detector.

### False-positive trace

Suppose a person writes a simple, repetitive paragraph. The model returns 0.92 and style returns 0.80, making the combined score 0.884. The AI label explains that the estimate can be wrong and offers an appeal. The writer sends their content ID and explains their drafting process. The log keeps the initial decision and adds the appeal with `under_review`. This is a hypothetical trace, not a test result. Nothing in this prototype removes their work or penalizes them automatically.

### Planned scope

I declared the optional `GET /content/<id>` status endpoint in the first planning commit, before implementing it. The required features and that extension are now implemented. No third signal or verified-human credential is planned. Unit 8 attack runs and rate limiting remain next-unit work. *(Done now, see Unit 8 below.)*

## Signals and Scoring

The model signal in `detector.py::model_signal` measures contextual next-token predictability using GPT-2 perplexity. AI prose may use predictable sequences, but so can children, second-language writers, and people writing plainly. It does not verify authorship or understand a writer's intent. Only the first 400 model tokens are examined. The starter's midpoint 45 and steepness 1.6 stay unchanged.

The style signal in `stylometry.py::style_signal` measures sentence length spread (population standard deviation divided by mean), unique words divided by all words, and Unicode punctuation characters divided by all characters. Repetitive, evenly paced prose may look AI-like. The measures cannot understand meaning, distinguish quoted text, or resist deliberate edits. Vocabulary variety depends on text length, and sentence splitting is approximate.

### Combining rule, decided before coding or seeing results

The rule lives in **`scoring.py::combine_signals`**, with settings in `config.py`. Start with `0.70 * model_score + 0.30 * style_score`. If the signals differ by at least 0.50, clamp the result to [0.40, 0.60] so the label stays unsure. The larger model weight reflects its use of context; it is a design choice, not evidence of measured accuracy.

For style, use `0.50 * (1 - min(spread, 1)) + 0.30 * (1 - vocabulary_ratio) + 0.20 * (1 - min(punctuation_density / 0.12, 1))`. Fewer than 20 words or fewer than two word-containing sentences gives a neutral 0.50 because there is too little evidence. These are transparent heuristics, not a trained detector.

### Development results

These six fixtures were frozen before the first model run. Full texts and provenance are in `calibration.py`; full scores are in `results/calibration.jsonl`.

| Fixture | Model | Style | Combined | Label |
|---|---:|---:|---:|---|
| generated_conventional | 0.9146 | 0.7498 | 0.8652 | ai |
| human_literary | 0.5745 | 0.5000 | 0.5522 | unsure |
| mixed | 0.6731 | 0.2770 | 0.5543 | unsure |
| human_formal | 0.4651 | 0.5000 | 0.4756 | unsure |
| lightly_edited_ai | 0.7203 | 0.4570 | 0.6413 | unsure |
| generated_unusual | 0.0961 | 0.1625 | 0.1160 | human |

The conventional generated example scores 0.3130 higher than the human literary example (0.8652 versus 0.5522). That is a development observation, not a pass for the matched 20-piece acceptance criterion.

The lightly edited AI example exposes a split: the model leans AI at 0.7203 while style leans human at 0.4570. Their gap is below 0.50, so the ordinary weighted average gives 0.6413, which stays unsure. For a stronger constructed disagreement (0.95, 0.10), the weighted result 0.695 is capped at 0.60. This latter example tests the rule; it is not an observed text result.

The unusual generated paragraph receives a human label at 0.1160. This is a real false negative: unusual word choices and uneven sentence lengths fool both signals. The formal human passage remains unsure at 0.4756. I kept the original weights and thresholds rather than adjusting them to make these examples look better. The sentence splitter does not recognize every boundary before a closing quote, and one-sentence passages return neutral style evidence. Public-domain text may also overlap GPT-2 training data, so these examples do not estimate performance on new writing.

Sources for the human excerpts: [Carroll, chapter 1](https://www.gutenberg.org/files/11/11-0.txt) and [National Archives, Declaration transcript](https://www.archives.gov/founding-docs/declaration-transcript). Neither excerpt is my own writing.

## Label Variants

| Score range | Guess | Exact reader-facing text |
|---|---|---|
| 0.00 through 0.25, inclusive | human | We think this was probably written by a person. This estimate does not verify who wrote it. You can ask for a review if it seems wrong. |
| Greater than 0.25 and less than 0.80 | unsure | We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process. |
| 0.80 through 1.00, inclusive | ai | We think this may have been generated by AI. This estimate can be wrong and is not proof. If you wrote it, you can appeal and explain your writing process. |

The wide unsure range puts the cost of a false accusation ahead of catching every AI sample. Scores 0.51 and 0.95 deliberately produce different labels.

## Sample Run

### Milestone 3: one signal

The temporary hardcoded route returned `{"content_id":"route-check","confidence":0.5,"guess":"unsure","label":"Route check only."}` over curl before the detector was connected. `/ping` also returned `ok: true`.

Before wiring the detector, `python calibration.py --model-only` scored the frozen generated paragraph at 0.9146, the Carroll excerpt at 0.5745, and their concatenation at 0.6731. These are development fixtures with explicit provenance in `calibration.py`, not my personal writing.

```powershell
curl.exe -s -X POST http://127.0.0.1:5000/submit -H "Content-Type: application/json" --data-binary "@results/one_signal_request.json"
curl.exe -s "http://127.0.0.1:5000/log?limit=1"
```

Request:
```json
{"text": "The system is designed to help users complete their tasks efficiently. It provides a simple and effective way to manage information. The system is easy to use and provides consistent results. Users can use the system to improve their productivity. Overall, the system provides a reliable and effective solution for users.", "creator_id": "milestone3-demo"}
```

Response (confidence/label are temporary milestone placeholders):
```json
{"confidence":0.5,"content_id":"63847a7b-dbb6-4efa-9dc4-3c3c15c38fa3","guess":"unsure","label":"One-signal development check; final label not connected.","model_score":0.9146,"status":"decided","style_score":null}

```

Log response:
```json
{"count":1,"entries":[{"combined_score":0.5,"content_id":"63847a7b-dbb6-4efa-9dc4-3c3c15c38fa3","creator_id":"milestone3-demo","guess":"unsure","label":"One-signal development check; final label not connected.","model_score":0.9146,"status":"decided","style_score":null,"timestamp":"2026-11-03T03:36:24+00:00"}]}

```

### Final two-signal submission and appeal

These are real curl responses from the running service, not hand-written examples. The sample text is AI-generated; the appeal is a workflow demonstration, not a claim that I wrote that text. `verify_live.py` repeats the checks with curl and saves the complete requests and responses in `results/live_run.json`. Running it again appends new events and produces new IDs.

Start the service in one PowerShell terminal:

```powershell
.\.venv\Scripts\Activate.ps1
python app.py
```

In another terminal, from this repository:

```powershell
curl.exe -s -X POST http://127.0.0.1:5000/submit -H "Content-Type: application/json" --data-binary "@results/sample_submit.json"
```

Request:
```json
{
  "text": "The system is designed to help users complete their tasks efficiently. It provides a simple and effective way to manage information. The system is easy to use and provides consistent results. Users can use the system to improve their productivity. Overall, the system provides a reliable and effective solution for users.",
  "creator_id": "live-generated_conventional"
}
```

Response, HTTP 200:
```json
{
  "confidence": 0.8652,
  "content_id": "c2993493-ec33-4474-9212-2a220f37a75e",
  "guess": "ai",
  "label": "We think this may have been generated by AI. This estimate can be wrong and is not proof. If you wrote it, you can appeal and explain your writing process.",
  "model_score": 0.9146,
  "status": "decided",
  "style_score": 0.7498
}
```

Appeal command (replace the saved content ID with the new ID if repeating the submission):

```powershell
curl.exe -s -X POST http://127.0.0.1:5000/appeal -H "Content-Type: application/json" --data-binary "@results/sample_appeal.json"
```

Request:
```json
{
  "content_id": "c2993493-ec33-4474-9212-2a220f37a75e",
  "reasoning": "This is a workflow demonstration. Please review the source and drafting history before drawing a conclusion about authorship."
}
```

Response, HTTP 200:
```json
{
  "content_id": "c2993493-ec33-4474-9212-2a220f37a75e",
  "message": "Your appeal has been recorded. Your submission is under review.",
  "status": "under_review"
}
```

Immediately after the appeal:

```powershell
curl.exe -s "http://127.0.0.1:5000/log?limit=2"
```

Recorded response (later runs add more entries, so the most recent two will change):
```json
{
  "count": 2,
  "entries": [
    {
      "combined_score": 0.8652,
      "content_id": "c2993493-ec33-4474-9212-2a220f37a75e",
      "creator_id": "live-generated_conventional",
      "guess": "ai",
      "label": "We think this may have been generated by AI. This estimate can be wrong and is not proof. If you wrote it, you can appeal and explain your writing process.",
      "model_score": 0.9146,
      "status": "decided",
      "style_score": 0.7498,
      "timestamp": "2026-11-03T03:39:13+00:00"
    },
    {
      "content_id": "c2993493-ec33-4474-9212-2a220f37a75e",
      "creator_id": "live-generated_conventional",
      "event": "appeal",
      "reasoning": "This is a workflow demonstration. Please review the source and drafting history before drawing a conclusion about authorship.",
      "status": "under_review",
      "timestamp": "2026-11-03T03:39:13+00:00"
    }
  ]
}
```

The stretch endpoint was also checked with `curl.exe -s "http://127.0.0.1:5000/content/c2993493-ec33-4474-9212-2a220f37a75e"`. It returned `status: under_review`, the unchanged original scores and label, and the recorded appeal. Full output is in `results/live_run.json`.

### Verification and limits

- `python -m unittest -v test_service`: 12 tests passed. These use a controlled model response and temporary audit files to check endpoint behavior without modifying the evidence log. They cover 1,001 score values, the strong-disagreement grid, invalid input, unavailable models, five appeals, repeat appeals, unknown IDs, and current status.
- `python verify_live.py`: six real model submissions reached all three labels; five real appeals were recorded and visible through both `/log` and `/content/<id>`. `/health` confirmed the detector remained loaded.
- `python test.py`: the environment check passed all nine checks.
- Criterion 3 has development evidence for all three labels, and criteria 4 and 5 have workflow/contract evidence. Criteria 1 and 2 remain unevaluated: they need my own ten writing samples and a frozen matched AI set. I do not claim these development checks are the next unit's three-trial evaluation.

This is a local classroom prototype. There is no login, proof of ownership, or human-review dashboard; anyone with a content ID can request review. `under_review` records a request, not a promise that a staffed moderation team exists. The audit log stores IDs, scores, labels, and appeal reasoning, so I use demonstration data rather than private writing. Rate limiting and the supplied attack/evaluation runners belong to Unit 8. `scenarios.py` still requires my personal samples before that evaluation.

## How I Used AI

I used Codex extensively to implement the service, run checks, and draft this write-up. The code and reflections are AI-assisted. I did not conduct a breakout discussion, and I am not claiming that generated development examples are my own writing.

### Moment 1: turning the assignment into testable targets

I asked Codex to complete the assignment. When it asked me to choose five acceptance targets, I replied, “just do whats good for this assignment.” It produced five measurable draft targets covering false positives, score separation, label coverage, appeals, and invalid input, each with a reason. The resulting changes replaced the empty criteria template and recorded the targets in Git before implementation or detector results. The most important design choice was a wide unsure range and an explicit disagreement rule, because accusing a real writer costs more than missing one generated paragraph.

The assignment specifically asks students to write their own criteria. These are AI-assisted drafts, not independently written criteria. Before submitting, I need to read them, decide whether I can defend the targets, and resolve that requirement honestly. The history shows when the drafts existed; it does not establish independent authorship.

### Moment 2: implementing and checking the full workflow

My request to complete all the steps also asked Codex to build the service and write the reflections. It returned working endpoints, separate model and style scores, automated checks, and actual curl evidence. The implementation changed from starter placeholders to validated requests, saved decisions, plain-English labels, and an appeal path that preserves the original record. The tests also drove explicit handling for malformed input, oversized requests, unknown content IDs, and detector failures rather than returning a guessed answer when the model cannot run.

The most useful finding was that the unusual AI paragraph scored 0.1160 and received a human label. I kept that failure in the write-up. It shows that agreement between two imperfect signals still is not proof. The lightly edited AI paragraph also moved from the conventional example's 0.8652 to 0.6413, enough to change its label to unsure. I would use the next unit's held-out attacks to examine those weaknesses rather than claim the service is accurate from six examples.

### Solo reflection: the writer's side

These are AI-generated role-play reactions, not feedback from real classmates or writers.

For the false-positive target, a fictional writer might say: “I spent hours choosing these words. Being the one person your target allows you to accuse does not make this feel fair. How do I get someone to read my drafts?” That reaction explains why an appeal needs a stored reason and visible status, not just a reassuring message. A ceiling of one error in ten development examples still does not justify using this system to punish writers.

For the human label, the fictional writer might think, “It sounds like the site believes I wrote it, but it has not verified my identity.” For the AI label: “This sounds suspicious of my work, even with the warning. I would want to appeal and share my drafting process.” For the unsure label: “The site cannot tell. It says this is not an accusation, so I would expect my work to remain available.” These reactions are consistent with keeping labels tentative and providing a review path. This prototype does not make publication or punishment decisions.

### Running and continuing the project

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python test.py
python detector.py
python -m unittest -v test_service
python app.py
```

With the service running, use a second terminal for `python verify_live.py`. See [RUNNING.md](RUNNING.md) for the starter's longer setup guide; its descriptions of unimplemented routes refer to the original starter. The completed routes and score ranges are documented above.

Keep this same repository for the next unit. The submitted URL is intended to be https://github.com/afaheem1021/ai201-project4-provenance-guard-starter-v2026. I will submit it through the Course Portal myself. Next unit still needs my own writing samples, the supplied attack set, and the three-trial evaluation; this README does not claim those future activities are complete.

---

# Unit 8: Testing

Everything below this line is from Unit 8. The only changes to the system in this unit are the rate limiter, the rejection logging, and one improvement (Milestone 5). Nothing else in the signals, weights, thresholds or labels was touched.

## Rate Limiting

**Numbers:** 10 submissions per minute and 100 per day, per `creator_id` (it falls back to the IP address when there's no usable creator_id). These live in `config.py` and the decorator is on `submit` in `app.py`.

**Why these numbers:**

- A real writer submits a piece, maybe fixes a typo, and submits again. That's a few requests an hour. Even someone pasting in five short pieces back to back won't get close to 10 in a minute.
- A script trying to map my thresholds wants to send hundreds of small variations. At 100 a day, a 1,000-variation probe from one creator_id takes 10 days instead of 2 minutes. That's the point: make probing slow and visible in the log.
- I didn't go lower (like 3 a minute) because the first request takes a while while the model loads, and a writer who clicks submit twice shouldn't get punished for it.

**Proof it works** (`python run_attacks.py --flood 15`, saved in `results/flood_2026-11-08_1334.md`):

```
200 200 200 200 200 200 200 200 200 200 429 429 429 429 429
```

The first 10 went through and the next 5 got 429. `GET /health` reports `"rate_limiting": true` (saved in `results/health_unit8.json`).

**One honest weakness:** the limit is keyed on `creator_id`, and the client picks its own creator_id. A script can just send each request with a new one, which is exactly what `attacks.csv` does (every row is `attacker_<id>`). So this limit stops a lazy flood, not a smart one. Keying on something the user can't choose (a login, or the IP) would fix that, but this prototype has no login.

**Something I found while testing:** the limiter runs *before* my input checks. Bad requests with no creator_id all count against one address (127.0.0.1 on my laptop). When I ran my bad-input tests back to back, the later ones came back 429 instead of 400. That's not wrong exactly, but it meant I had to space my criterion 5 trials a minute apart so I was testing validation and not the limiter.

## Audit Log

Every decision writes one line to `logs/audit.jsonl` with all nine fields: `timestamp`, `content_id`, `creator_id`, `guess`, `model_score`, `style_score`, `combined_score`, `label`, `status`. Appeals add a separate line (`event: appeal`, `status: under_review`) and never overwrite the original.

New this unit: **every refused request is logged too.** The starter already logged 429s. I added `reject()` in `app.py`, so any 400/413/503 from `/submit` writes a `rejected` entry with the reason and HTTP status. A request whose body is too big to even read is logged as `creator_id: "unknown"`. I capped logged creator_ids at 120 characters so nobody can bloat the log with a giant ID.

I checked it by hand with three submissions and one request with no text (saved in `results/m1_log_check.json`). You can tell what was decided, for whom, when, and why from the log alone. The one thing you *can't* get back is the text itself, because I don't store it. That's on purpose (privacy), but it means you can't re-score an old decision from the log.

## Attack Set Results (before any fix)

I ran all 56 attacks with `python run_attacks.py --set attack_set --label before`, before changing anything. Full output: `results/attack_run_2026-11-08_1350_before.md`. My held/broke marks: `results/attack_verdicts_before.md`.

**How I decided held or broke.** I wrote one rule per family down in `tools/judge_attacks.py` so I couldn't be generous case by case:

- **evasion** (AI text trying to sneak past): broke if it came back 200 without the `ai` label.
- **false_positive** (real human writing): broke if it got the `ai` label.
- **prompt_injection**: broke if it got a `human` label, changed the label text, or crashed.
- **malformed** (junk input): broke on any 5xx, or if junk that isn't writing got a confident `human` or `ai` label. A 400/413 or an `unsure` counts as held.
- **flood_same_creator**: held if the run ends in 429s.

| Family | Attacks | Held | Broke |
|---|---|---|---|
| evasion | 10 | 1 | **9** |
| false_positive | 8 | 8 | 0 |
| prompt_injection | 6 | 6 | 0 |
| malformed (MF + RQ rows) | 20 | 17 | **3** |
| flood_same_creator | 12 | 12 | 0 |
| **Total** | **56** | **44** | **12** |

Nothing crashed. No 500s anywhere.

Every attack, what came back, and my mark:

| ID | Family | Status | Guess | Score | Model | Style | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | 200 | unsure | 0.3054 | 0.1635 | 0.6365 | BROKE |
| EV02 | evasion | 200 | unsure | 0.5074 | 0.5943 | 0.3048 | BROKE |
| EV03 | evasion | 200 | unsure | 0.6144 | 0.6662 | 0.4937 | BROKE |
| EV04 | evasion | 200 | unsure | 0.6162 | 0.6114 | 0.6274 | BROKE |
| EV05 | evasion | 200 | unsure | 0.3467 | 0.3212 | 0.4062 | BROKE |
| EV06 | evasion | 200 | unsure | 0.4771 | 0.5727 | 0.2542 | BROKE |
| EV07 | evasion | 200 | unsure | 0.5603 | 0.5862 | 0.5000 | BROKE |
| EV08 | evasion | 200 | unsure | 0.3216 | 0.2452 | 0.5000 | BROKE |
| EV09 | evasion | 200 | unsure | 0.6388 | 0.7042 | 0.4862 | BROKE |
| EV10 | evasion | 200 | ai | 0.9027 | 0.9792 | 0.7241 | HELD |
| FP01 | false_positive | 200 | unsure | 0.5947 | 0.6175 | 0.5415 | HELD |
| FP02 | false_positive | 200 | unsure | 0.7114 | 0.7387 | 0.6476 | HELD |
| FP03 | false_positive | 200 | unsure | 0.7446 | 0.8051 | 0.6033 | HELD |
| FP04 | false_positive | 200 | unsure | 0.7486 | 0.8329 | 0.5520 | HELD |
| FP05 | false_positive | 200 | unsure | 0.7577 | 0.8005 | 0.6579 | HELD |
| FP06 | false_positive | 200 | unsure | 0.7699 | 0.8814 | 0.5097 | HELD |
| FP07 | false_positive | 200 | unsure | 0.7610 | 0.8816 | 0.4796 | HELD |
| FP08 | false_positive | 200 | unsure | 0.3756 | 0.3223 | 0.5000 | HELD |
| PI01 | prompt_injection | 200 | unsure | 0.4412 | 0.4625 | 0.3915 | HELD |
| PI02 | prompt_injection | 200 | unsure | 0.2554 | 0.2044 | 0.3744 | HELD |
| PI03 | prompt_injection | 200 | unsure | 0.5803 | 0.5943 | 0.5478 | HELD |
| PI04 | prompt_injection | 200 | unsure | 0.5007 | 0.4998 | 0.5027 | HELD |
| PI05 | prompt_injection | 200 | unsure | 0.5641 | 0.6401 | 0.3868 | HELD |
| PI06 | prompt_injection | 200 | unsure | 0.5548 | 0.5583 | 0.5467 | HELD |
| MF01 | malformed | 400 | — | — | — | — | HELD |
| MF02 | malformed | 400 | — | — | — | — | HELD |
| MF03 | malformed | 200 | unsure | 0.4000 | 0.0000 | 0.5000 | HELD |
| MF04 | malformed | 200 | human | 0.1578 | 0.0112 | 0.5000 | BROKE |
| MF05 | malformed | 200 | ai | 0.8483 | 0.9976 | 0.5000 | BROKE |
| MF06 | malformed | 200 | ai | 0.8478 | 0.9969 | 0.5000 | BROKE |
| MF07 | malformed | 200 | unsure | 0.7845 | 0.9064 | 0.5000 | HELD |
| MF08 | malformed | 413 | — | — | — | — | HELD |
| RQ01–RQ12 | malformed | 400 (all 12) | — | — | — | — | HELD (12) |
| FL01_01–FL01_10 | flood_same_creator | 200 (all 10) | human | 0.1701 | 0.0287 | 0.5000 | HELD |
| FL01_11–FL01_12 | flood_same_creator | 429 (both) | — | — | — | — | HELD |

(The flood family has 12 rows in the file, even though its description says 20. The limiter cut in at row 11.)

**A control I ran before judging the evasion rows.** The evasion attacks are all edits of one AI essay about workplace communication. I sent the *unedited* essay too (`results/control_base_ai_essay.json`). It scored **0.6595, unsure** (model 0.6694, style 0.6365). So my detector never caught the original in the first place. The evasion attacks didn't have to beat anything. That changes how I read every evasion row below.

### Audit log extract

Twelve real entries from `logs/audit.jsonl` (full run in `results/audit_extract_before.json`). I picked the ones that show something, not the easy ones. Rejection entries have fewer fields because no decision was made.

```json
{"combined_score": 0.3054, "content_id": "adcdd562-e648-435c-be97-d01046d2d3fa", "creator_id": "attacker_EV01", "guess": "unsure", "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.", "model_score": 0.1635, "status": "decided", "style_score": 0.6365, "timestamp": "2026-11-08T18:50:12+00:00"}
{"combined_score": 0.9027, "content_id": "7e826b1f-9293-44f1-98cc-82ffa8bd3bf2", "creator_id": "attacker_EV10", "guess": "ai", "label": "We think this may have been generated by AI. This estimate can be wrong and is not proof. If you wrote it, you can appeal and explain your writing process.", "model_score": 0.9792, "status": "decided", "style_score": 0.7241, "timestamp": "2026-11-08T18:50:12+00:00"}
{"combined_score": 0.7446, "content_id": "2362ecb0-df9e-4710-91d7-9ab4db8eb45f", "creator_id": "attacker_FP03", "guess": "unsure", "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.", "model_score": 0.8051, "status": "decided", "style_score": 0.6033, "timestamp": "2026-11-08T18:50:12+00:00"}
{"combined_score": 0.761, "content_id": "0a79f065-0dc6-42a9-b5b3-f2f1563e5790", "creator_id": "attacker_FP07", "guess": "unsure", "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.", "model_score": 0.8816, "status": "decided", "style_score": 0.4796, "timestamp": "2026-11-08T18:50:12+00:00"}
{"combined_score": 0.2554, "content_id": "b1f8689d-adb2-4231-91c3-61b867af3e2e", "creator_id": "attacker_PI02", "guess": "unsure", "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.", "model_score": 0.2044, "status": "decided", "style_score": 0.3744, "timestamp": "2026-11-08T18:50:12+00:00"}
{"combined_score": 0.5641, "content_id": "847fbfc9-9760-40da-bb46-2c991ff4efad", "creator_id": "attacker_PI05", "guess": "unsure", "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.", "model_score": 0.6401, "status": "decided", "style_score": 0.3868, "timestamp": "2026-11-08T18:50:12+00:00"}
{"combined_score": 0.1578, "content_id": "dd6fcaaf-aba8-4b1b-8958-d29081d85fb9", "creator_id": "attacker_MF04", "guess": "human", "label": "We think this was probably written by a person. This estimate does not verify who wrote it. You can ask for a review if it seems wrong.", "model_score": 0.0112, "status": "decided", "style_score": 0.5, "timestamp": "2026-11-08T18:50:13+00:00"}
{"combined_score": 0.8483, "content_id": "360d3c5c-d071-42d8-870b-787a5f31bdd1", "creator_id": "attacker_MF05", "guess": "ai", "label": "We think this may have been generated by AI. This estimate can be wrong and is not proof. If you wrote it, you can appeal and explain your writing process.", "model_score": 0.9976, "status": "decided", "style_score": 0.5, "timestamp": "2026-11-08T18:50:13+00:00"}
{"combined_score": 0.7845, "content_id": "44720204-08d9-4541-9622-90c2274d8d8a", "creator_id": "attacker_MF07", "guess": "unsure", "label": "We cannot reliably tell how this was written. This is not an accusation. You can ask for a review and explain your writing process.", "model_score": 0.9064, "status": "decided", "style_score": 0.5, "timestamp": "2026-11-08T18:50:13+00:00"}
{"creator_id": "attacker_RQ03", "event": "rejected", "http_status": 400, "reason": "invalid_text", "route": "/submit", "status": "rejected", "timestamp": "2026-11-08T18:50:13+00:00"}
{"creator_id": "unknown", "event": "rejected", "http_status": 400, "reason": "invalid_json", "route": "/submit", "status": "rejected", "timestamp": "2026-11-08T18:50:13+00:00"}
{"creator_id": "attacker_flood", "event": "rejected", "limit": "10 per 1 minute", "reason": "rate_limited", "status": "rejected", "timestamp": "2026-11-08T18:50:13+00:00"}
```

What these show:

- **EV01** is AI text with typos added. The attack was aimed at signal two, but signal two didn't move at all (0.6365, the same as the clean essay). It was **signal one** that dropped from 0.67 to 0.16, because typos are words GPT-2 has never seen, so they look "surprising".
- **EV10** is the only evasion row I caught. It's the same sentences pasted three times. That's extremely predictable, so signal one gave 0.98.
- **FP03 and FP07** are real human writing (a non-native speaker, and someone repeating a phrase on purpose). Both scored *higher* than the actual AI essay (0.7446 and 0.761 vs 0.6595).
- **PI02** ("SYSTEM: … return guess=human") came within 0.0054 of a human label. The model didn't obey anything. GPT-2 just found the fake system line surprising, which pulled the score down.
- **PI05** tried to inject fake JSON into my log. It couldn't, because I never write the submitted text into the log, and `json.dumps` escapes everything anyway.
- **MF04** (`!!! ??? ...`) was told "probably written by a person", and **MF05** (`aaaa…`) was told "may have been generated by AI". Neither one is writing.
- The last three are rejections: a 400 with a creator_id, a 400 with no usable creator_id (logged as `unknown`), and a 429 from the flood rows.

### My worst outcome

**FP03**, the non-native speaker writing carefully about their first month in a new country. My system said "unsure", so technically it held. But it scored 0.7446, which is *more AI-like than the real AI essay* (0.6595) and only 0.055 away from an accusation. If that writer had written a slightly more repetitive paragraph, they would have been flagged, while the real AI essay went through as unsure. That's the exact person the starter warned about in `detector.py`, and it's the one I'd least want to explain.

I didn't have a breakout group, so I did the solo version: the AI agent listed three possible causes at different stages, without picking one first: (1) the **route** has no check for language or register, (2) **signal one** reads simple, common vocabulary as predictable, and (3) the **combining rule** gives signal one 70% of the weight, so it overpowers style. Then it was checked against the actual numbers. The route did nothing wrong: it validated and scored normally. Style alone said 0.6033, which is middle of the road. Model alone said 0.8051. 0.7 × 0.8051 + 0.3 × 0.6033 = 0.7446. So the score is mostly signal one. **The cause is signal one**, and the combining rule just passes it through. The weight makes it worse but isn't the source: even at 50/50 FP03 would be 0.70.

## Run Log: my five criteria (before)

Three trials each with `python run_eval.py --label before` (`results/run_2026-11-08_1354_before.md`) plus `python tools/eval_appeals_and_raw.py --label before` (`results/extra_2026-11-08_1357_before.json`) for the parts `run_eval.py` can't send (appeals, malformed JSON, a bare list, bad appeals, and the score-grid checks). `tools/score_eval.py` turns both files into this table, so I'm not counting by hand.

> **Important honesty note about criteria 1 and 2.** Criterion 1 is supposed to use ten pieces *I* wrote. I didn't provide my own writing for this run, so the ten "own writing" pieces in `scenarios.py` are **stand-ins written by an AI assistant** in a casual, everyday student style. The matched AI set for criterion 2 was also written by the AI assistant, in its normal polished style. So criteria 1 and 2 tell you how my system treats *casual-sounding text vs polished text*, not how it treats me. To do it properly I'd swap in ten real pieces and re-run one command.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Own-writing stand-ins labelled AI | ≤ 1 of 10 | 0/10 | 0/10 | 0/10 | MET |
| 2. Mean AI score minus mean human score | ≥ 0.20 | +0.1681 | +0.1681 | +0.1681 | MISSED |
| 3. All three labels reached, plus grid and disagreement checks | 3 of 3 and every check passes | 3/3, disagreement check failed | 3/3, disagreement check failed | 3/3, disagreement check failed | MISSED |
| 4. Appeals recorded, original decision kept | 5 of 5 + repeat recorded + unknown ID 404 | 5/5 | 5/5 | 5/5 | MET |
| 5. Bad input rejected before scoring | 15 of 15 with 0 decisions created | 15/15 | 15/15 | 15/15 | MET |

All three trials came out identical. That's expected: GPT-2 runs in eval mode with no sampling, and the style signal is plain arithmetic. So the repeats show the result is stable, not a one-off.

### Real output, one trial each

**Criterion 1**, from `run_eval.py::main`, scenario `own writing stand-ins`, trial 1 (first 3 of 10, label text removed to save space). The highest of all ten was 0.6561:

```json
[
  {"status": 200, "guess": "unsure", "confidence": 0.5815, "model_score": 0.6088, "style_score": 0.5179, "sent": "The 7:40 bus was late again today. I stood at the stop for twenty minu"},
  {"status": 200, "guess": "unsure", "confidence": 0.6561, "model_score": 0.7458, "style_score": 0.4468, "sent": "I tried making my mom's lentil soup last night and it did not taste li"},
  {"status": 200, "guess": "unsure", "confidence": 0.4259, "model_score": 0.4019, "style_score": 0.482, "sent": "Studied for the stats midterm at the library until it closed. I still "}
]
```

All ten stand-in scores: 0.5815, 0.6561, 0.4259, 0.3996, 0.5866, 0.6159, 0.4764, 0.4302, 0.641, 0.5824 (mean **0.5396**).

**Criterion 2**, from `run_eval.py::main`, scenario `matched AI set`, trial 1 (first 2 of 10):

```json
[
  {"status": 200, "guess": "unsure", "confidence": 0.7541, "model_score": 0.7948, "style_score": 0.6591, "sent": "Public transportation plays an important role in the daily lives of ma"},
  {"status": 200, "guess": "unsure", "confidence": 0.6777, "model_score": 0.7247, "style_score": 0.5681, "sent": "Cooking traditional family recipes is a meaningful way to stay connect"}
]
```

All ten AI scores: 0.7541, 0.6777, 0.5838, 0.7251, 0.7116, 0.7577, 0.699, 0.7069, 0.7487, 0.712 (mean **0.7077**). Gap = 0.7077 − 0.5396 = **0.1681**.

**Criterion 3**, from `run_eval.py::main`, scenario `label coverage fixtures`, trial 1 (all six):

```json
[
  {"status": 200, "guess": "ai", "confidence": 0.8652, "model_score": 0.9146, "style_score": 0.7498, "sent": "The system is designed to help users complete their tasks efficiently."},
  {"status": 200, "guess": "unsure", "confidence": 0.5522, "model_score": 0.5745, "style_score": 0.5, "sent": "Alice was beginning to get very tired of sitting by her sister on the "},
  {"status": 200, "guess": "unsure", "confidence": 0.5543, "model_score": 0.6731, "style_score": 0.277, "sent": "Alice was beginning to get very tired of sitting by her sister on the "},
  {"status": 200, "guess": "unsure", "confidence": 0.4756, "model_score": 0.4651, "style_score": 0.5, "sent": "Prudence, indeed, will dictate that Governments long established shoul"},
  {"status": 200, "guess": "unsure", "confidence": 0.6413, "model_score": 0.7203, "style_score": 0.457, "sent": "The system is designed to help users complete their tasks efficiently."},
  {"status": 200, "guess": "human", "confidence": 0.116, "model_score": 0.0961, "style_score": 0.1625, "sent": "Clunk! The marmalade-powered unicycle coughed violet confetti across m"}
]
```

And the grid half, from `tools/eval_appeals_and_raw.py::criterion_3_grid`, trial 1:

```json
{"grid_1001_all_labelled": true, "0.51_vs_0.95_differ": true, "disagreement_pairs_checked": 2652, "disagreement_all_unsure": false}
```

**Criterion 4**, from `tools/eval_appeals_and_raw.py::criterion_4`, trial 1 (first appeal of five, plus the summary):

```json
{
  "first_appeal": {
    "content_id": "30f273c2-b694-4586-9c77-cbb8dca226ff",
    "appeal_status": 200,
    "appeal_body": {"content_id": "30f273c2-b694-4586-9c77-cbb8dca226ff", "message": "Your appeal has been recorded. Your submission is under review.", "status": "under_review"},
    "appeal_entries": 1,
    "original_unchanged": true,
    "content_status": "under_review",
    "pass": true
  },
  "passed": 5,
  "repeat_appeal_recorded": true,
  "unknown_id_404_no_entry": true,
  "unknown_response": {"status": 404, "body": {"error": "content_not_found", "message": "No submission has that content ID."}}
}
```

**Criterion 5**, from `tools/eval_appeals_and_raw.py::criterion_5`, trial 1 (3 of the 15 cases, plus the summary):

```json
{
  "cases": [
    {"case": "malformed JSON", "want": 400, "got": 400, "body": {"error": "invalid_json", "message": "Send a JSON object with text and creator_id."}, "pass": true},
    {"case": "JSON list", "want": 400, "got": 400, "body": {"error": "invalid_json", "message": "Send a JSON object with text and creator_id."}, "pass": true},
    {"case": "appeal: JSON list", "want": 400, "got": 400, "body": {"error": "invalid_json", "message": "Send a JSON object with content_id and reasoning."}, "pass": true}
  ],
  "passed": 15,
  "total": 15,
  "decisions_created_by_bad_input": 0,
  "appeals_recorded_by_bad_appeals": 0
}
```

The `run_eval.py` side of criterion 5 agrees: the nine dict bodies came back `400, 400, 400, 400, 400, 400, 400, 413, 413` in every trial.

## Verdicts and Diagnosis

### Criterion 1: MET (but I think my target was too easy)

0 of 10 stand-ins got an AI label in all three trials, and the target was at most 1. So it's met. But being honest: it's met mostly because my AI label is almost impossible to reach. The highest stand-in was 0.6561, and *none* of the real AI pieces reached 0.80 either. A criterion that passes because the system barely ever says "AI" isn't telling me much. If I wrote it again, I'd tighten it to "no own-writing piece scores above 0.70", so it catches the near misses, like the attack set's FP03 at 0.7446.

### Criterion 2: MISSED, gap 0.1681 vs 0.20 in all three trials

**Stage: signal one, and signal two can't make up for it.** On these 20 texts signal one separates the groups by 0.1819 (human 0.5653, AI 0.7472). Signal two separates them by 0.1357 (0.4796 vs 0.6153). My combined score is a weighted average of the two, so the combined gap has to land between 0.1357 and 0.1819 whatever weights I pick. **No reweighting can reach 0.20.** Even 100% signal one only gets 0.1819. The mechanism: modern polished AI text isn't as predictable to GPT-2 as old-style AI text was, so its perplexity sits near the midpoint (45) and signal one only gives it about 0.75. Meanwhile casual human text full of short common words gets about 0.57. The gap is real but small.

I'm not changing this target. 0.20 is measurable and reasonable. I just missed it.

### Criterion 3: MISSED, the disagreement check fails in all three trials

All three labels were reached in every trial (ai 0.8652, unsure, human 0.116), and every one of the 1,001 grid scores maps to a label. But the target also says *any* two signal scores at least 0.50 apart must come out unsure. Four pairs don't:

| Model | Style | Real gap | What Python computes | Combined | Label |
|---|---|---|---|---|---|
| 0.95 | 0.45 | 0.50 | 0.49999999999999994 | 0.80 | **ai** |
| 0.96 | 0.46 | 0.50 | 0.49999999999999994 | 0.81 | **ai** |
| 0.07 | 0.57 | 0.50 | 0.49999999999999994 | 0.22 | human |
| 0.08 | 0.58 | 0.50 | 0.49999999999999994 | 0.23 | human |

**Stage: the combining rule (`scoring.py::combine_signals`). Mechanism: floating-point rounding.** `0.95 - 0.45` in Python is `0.49999999999999994`, which is less than 0.50, so the "strong disagreement → stay unsure" clamp gets skipped. The result is an **AI accusation for a piece the rule promises to call unsure.** My unit-7 test (`test_strong_disagreement_stays_unsure`) missed it because the test did the same float subtraction to decide which pairs to check, so it quietly skipped exactly these four. Testing my code with the same math as my code is why I never saw it.

### Criterion 4: MET, 5/5 in all three trials

Every appeal returned 200 with `under_review`, added exactly one appeal entry with the right reasoning and creator, left the original decision untouched, and showed up in `GET /content/<id>`. A repeat appeal was recorded too, and an unknown ID got a 404 with no entry. I don't think this target was low: losing even one appeal would have been a miss.

### Criterion 5: MET, 15/15 in all three trials, 0 decisions created

Every bad request got the right JSON error, and none of them created a decision or an appeal. One caveat: this only held because I spaced the trials a minute apart (see Rate Limiting). Back to back, the later ones got 429 instead of 400.

### Diagnosis of the broken attacks

**Evasion: 9 broke. Stage: signal one, with the AI threshold making it visible.** The big finding is the control: the *unedited* AI essay already scores 0.6595 (unsure). So the edits didn't need to work. And most of the edits pushed signal one down even further:

- EV01 (typos): model 0.67 → 0.16. Misspelled words are tokens GPT-2 can't predict, so perplexity jumps. The attack was aimed at signal two, but signal two didn't change at all (0.6365 → 0.6365).
- EV05 (a heavy human editing pass) and EV08 (two short sentences) dropped to 0.32 and 0.25 on signal one.
- EV02 and EV06 targeted signal two's sentence-length spread, and it worked: style fell to 0.30 and 0.25. But it didn't matter, because the text was already unsure.

The one I caught, EV10, is the same sentences repeated, which is about the only kind of AI text that gets very low perplexity.

**Junk input: 3 broke (MF04, MF05, MF06). Stage: the route, plus signal one.** My route only checks that `text` is a non-empty string. So `!!! ??? ...`, `aaaa…` and a row of emoji all reach the model. Signal one gives a single repeated character or emoji a near-perfect 0.997 (it's trivially predictable), and gives punctuation-only text 0.011. Signal two returns its neutral 0.5 because there are fewer than 20 words, so it can't pull the score back. With 70% weight on the model, junk gets a confident label.

### The pattern

**Almost every failure goes back to signal one measuring predictability, not authorship.** Typos, rare words and short text push it down (evasion). Repetition and junk push it up (EV10, MF05, MF06). Plain, careful human writing lands *above* polished AI writing (FP02–FP07 scored 0.71–0.77, the AI essay 0.66). That's the same problem behind the criterion 2 miss. Signal two can't save it, because it gets only 30% of the weight and goes neutral on short input.

That also means **moving a threshold can't fix it.** I checked using the scores I already had (no code change):

| AI threshold | Matched AI set flagged | Stand-ins flagged | Human FP attacks flagged | Base AI essay flagged |
|---|---|---|---|---|
| 0.80 (current) | 0/10 | 0/10 | 0/8 | no |
| 0.75 | 2/10 | 0/10 | 3/8 | no |
| 0.70 | 7/10 | 0/10 | 6/8 | no |
| 0.65 | 9/10 | 1/10 | 6/8 | yes |

To catch the base AI essay I'd have to accuse 6 of the 8 real human writers in the attack set first. Not a trade I'm willing to make.

The two failures I *can* fix without making something else worse are separate from that pattern: junk reaching the model (route), and the float bug (combining rule).

### Stretch I'm adding (declared before starting it)

**A second improvement, measured the same way.** Improvement 1 is the one the assignment requires. After measuring it, I'll make one more change (fixing the floating-point bug in the disagreement rule) and re-run everything again as a third result set, so each change can be compared on its own.

## Improvement: refuse text under 20 words

**What I changed (one thing):** `app.py::submit` now refuses any text with fewer than 20 words (`config.MIN_WORDS_TO_SCORE = 20`) *before* either signal runs. It returns a 400 `text_too_short` and logs the rejection. I picked 20 because that's where my style signal already gives up and returns a neutral 0.5. Below that, I only ever had one real signal. No signal, weight, threshold or label text changed.

**Why this one:** the diagnosis said the evasion and criterion 2 problems come from signal one itself, and I showed above that no weight or threshold fixes them without accusing real writers. The junk-input breaks were different. They happened because the route let non-writing reach the model, and that's fixable at the route without touching the signals.

**One mistake on the way, for honesty:** my first "after" run accidentally went to the *old* server. My stop command didn't match the process name, so the old process kept the port and the new one quietly failed to start. The numbers came back identical, which made me suspicious. I found the old process, deleted those result files, and re-ran. Those requests still show up in `logs/audit.jsonl`, because the log is append-only and I didn't want to edit it.

### Attack set, before vs after

`results/attack_verdicts_before.md` vs `results/attack_verdicts_after.md`. Same judge rules both times.

| Family | Before: held / broke | After: held / broke |
|---|---|---|
| evasion | 1 / 9 | 2 / 8 |
| false_positive | 8 / 0 | 8 / 0 |
| prompt_injection | 6 / 0 | 6 / 0 |
| malformed | 17 / 3 | **20 / 0** |
| flood_same_creator | 12 / 0 | 12 / 0 |
| **Total** | **44 / 12** | **48 / 8** |

Every row that changed:

| ID | What it is | Before | After | Verdict change |
|---|---|---|---|---|
| MF04 | only punctuation | 200, **human** 0.1578 | 400 text_too_short | BROKE → HELD |
| MF05 | one very long word | 200, **ai** 0.8483 | 400 text_too_short | BROKE → HELD |
| MF06 | only emoji | 200, **ai** 0.8478 | 400 text_too_short | BROKE → HELD |
| EV08 | 10-word AI text | 200, unsure 0.3216 | 400 text_too_short | BROKE → HELD |
| MF03 | control characters | 200, unsure 0.4000 | 400 text_too_short | held → held |
| MF07 | 17-word Arabic sentence | 200, unsure 0.7845 | 400 text_too_short | held → held |
| FP08 | real 8-word human note ("Went for a run. Legs hurt. Worth it.") | 200, unsure 0.3756 | 400 text_too_short | held → held |
| FL01_01–10 | flood rows (9-word text) | 200, human 0.1701 | 400 text_too_short | held → held (11 and 12 still 429) |

Every other attack came back with exactly the same scores.

**Did it help? Yes, for what it targeted:** all three junk breaks are fixed and nothing that used to hold now breaks. EV08 flipped too, but only because a refusal counts as held under my rule. The detector didn't get any better at spotting AI.

**What it cost:**

- **FP08**, a real person's 8-word note, now gets "please send at least 20 words" instead of a result. I think that's more honest than "unsure", but it's still a real writer we turn away.
- **MF07**, Arabic text, is now refused for being short, not for being Arabic. A *longer* Arabic piece would still get scored, and GPT-2 gave this one 0.9064. I haven't tested that, but I'd expect a longer Arabic piece to land near or over the AI line.
- Short pieces (poems, captions) can't be checked at all now.

### My five criteria, before vs after

Before: `results/run_2026-11-08_1354_before.md` + `results/extra_2026-11-08_1357_before.json`. After: `results/run_2026-11-08_1401_after.md` + `results/extra_2026-11-08_1404_after.json`.

| Criterion | Target | Before (runs 1/2/3) | Verdict | After (runs 1/2/3) | Verdict |
|---|---|---|---|---|---|
| 1. Own-writing stand-ins labelled AI | ≤ 1 of 10 | 0/10, 0/10, 0/10 | MET | 0/10, 0/10, 0/10 | MET |
| 2. Mean AI − mean human | ≥ 0.20 | +0.1681 ×3 | MISSED | +0.1681 ×3 | MISSED |
| 3. Labels reached + grid checks | 3/3 and all checks pass | 3/3, disagreement check failed ×3 | MISSED | 3/3, disagreement check failed ×3 | MISSED |
| 4. Appeals | 5/5 + repeat + 404 | 5/5 ×3 | MET | 5/5 ×3 | MET |
| 5. Bad input | 15/15, 0 decisions | 15/15 ×3 | MET | 15/15 ×3 | MET |

No change, which is what I expected: every criterion text is over 20 words, and none of the criterion 5 bad inputs got as far as the new check. So the improvement fixed attacks without moving any of my own criteria, good or bad.

## Stretch: a second improvement, measured the same way

Declared above before I started. **Change:** `scoring.py::combine_signals` now rounds the gap between the two signals to 6 decimal places before checking it against 0.50, so `0.95 - 0.45` counts as 0.50 like it should. I also fixed the unit test to compare whole hundredths instead of floats. I checked that the new test **fails** on the old code (`AssertionError: 'human' != 'unsure'`) and passes on the new code, so it would have caught this in unit 7.

Third result set, after both improvements: `results/attack_verdicts_after2.md`, `results/run_2026-11-08_1404_after2.md`, `results/extra_2026-11-08_1408_after2.json`.

| Criterion | After improvement 1 | After improvement 2 |
|---|---|---|
| 1 | 0/10 ×3, MET | 0/10 ×3, MET |
| 2 | +0.1681 ×3, MISSED | +0.1681 ×3, MISSED |
| 3 | 3/3, disagreement check failed ×3, MISSED | 3/3 and every check passes ×3, **MET** |
| 4 | 5/5 ×3, MET | 5/5 ×3, MET |
| 5 | 15/15 ×3, MET | 15/15 ×3, MET |
| Attack set | 48 held / 8 broke | 48 held / 8 broke (every score identical) |

**Did it help?** It fixed criterion 3 and changed nothing else. No real submission in any of my runs had signals exactly 0.50 apart, so no real score moved. It's a small fix, but before it, four score combinations could turn into an AI accusation that my own rule says shouldn't happen.

## What's Still Broken

**Evasion: 8 attacks still get AI text through as "unsure"** (EV01–EV07, EV09). The real problem is that even the *unedited* AI essay scores 0.6595, and plain human writing scores higher than that. To fix it I'd need a better first signal: a newer model than GPT-2, or comparing the text's perplexity under two different models instead of one. I stopped because that's replacing a signal, not tuning one. It would need its own calibration run, and it's more than the "one change" this unit allows. Lowering the threshold isn't an option: I showed it would accuse 6 of the 8 human writers in the attack set before it caught the base essay.

**Criterion 2 is still missed (0.1681 vs 0.20).** Same root cause as the evasion. No reweighting can get there, since even 100% signal one only reaches a 0.1819 gap. Same fix (a better signal one), same reason I stopped.

**Padded junk still gets labelled.** I tested this myself after the fix (`results/probe_padded_junk_after2.txt`): `"aaa "` repeated 30 times got **ai, 0.8464**, and `"🙂ok"` ×25 got **ai, 0.8429**. My check counts words but doesn't care whether they're real words or all the same word. Next I'd also refuse text where very few of the words are different (a very low type-token ratio). I stopped because I only get one change per measured round, and I found this after my round was done.

**The false-positive family "held", but only just.** FP02–FP07 are all real human writing scoring 0.71–0.77, just under my 0.80 line. FP03 (the non-native speaker) is my worst case. Nothing I changed helps them. They're safe only because my AI label is so hard to reach.

**PI02 came within 0.0054 of a human label.** Not because the model obeyed the fake "SYSTEM" line, but because GPT-2 found it surprising. Any odd-looking line pasted on top of AI text pulls the score toward human. This is the same signal-one problem.

**The rate limit can be dodged by changing creator_id**, because the client picks it. A real fix needs a login or an API key. There's no login in this prototype, so I left it.

**The limiter runs before validation**, so a burst of bad requests from one address gets 429 instead of a useful 400. I'd move the input checks in front of the limiter, or not count 400s toward the limit. I didn't, because that changes the limiter again after I'd measured it.

**The log can't replay a decision**, because it doesn't store the text. That's on purpose for privacy, but it means if a writer appeals, the reviewer needs the writer to send the text again.

**Criterion 1 hasn't really been tested on my writing.** The ten pieces are AI-written stand-ins. The honest next step is to put ten real pieces of my own into `HUMAN_STAND_INS` in `scenarios.py` and run `python run_eval.py --label mine`.

### The trade I'd make if this ran for real

I'd keep it tilted toward fewer wrong accusations, even though that means more AI text gets through as "unsure". The people who pay for that are teachers and readers who can't rely on the label, and honest students whose work sits next to AI-written work that wasn't caught. But a false accusation lands on one specific person, often someone like FP03 with the least power to argue back, and I think that's the worse harm.

## How I Used AI (Unit 8)

Same as Unit 7, I'm being upfront: I used an AI coding agent (Claude Code) for almost all of this unit. I gave it the assignment and my repo and asked it to do all six milestones. It turned on the limiter, added rejection logging, ran the attack set and my criteria, wrote the helper scripts in `tools/`, and drafted this write-up. I asked for the write-up to be in plain, simple language.

### Moment 1: the "own writing" problem

Criterion 1 needs ten pieces I wrote myself. When the agent asked me for them, I told it to just make something up. It did write ten casual paragraphs, but it refused to pass them off as mine. It labelled them as AI-written stand-ins in `scenarios.py` and in the run log, and it pointed out that criterion 1 is the exact place where AI text pretending to be human defeats the whole test. So criterion 1's "MET" is about stand-ins, not me, and swapping in my real writing is the first thing on my list.

### Moment 2: the bug my own test hid

The most useful thing in this unit was criterion 3 failing, because my unit-7 test checked the exact same thing and passed. The agent's new check compared score gaps in whole numbers instead of decimals, and four pairs failed. `0.95 - 0.45` isn't exactly 0.5 in Python. My old test used the same decimal math as my code, so it skipped exactly the cases that were broken. The lesson I'm keeping: a test that does the same math as the code it's testing can't catch a math bug.

### Moment 3: the "after" run that wasn't

The first time we re-ran after the fix, the numbers were identical to before, down to the last decimal. Instead of writing "the fix didn't help", the agent checked which process was actually on port 5000 and found the old server still running. If those identical numbers had gone into the README, the whole before/after comparison would have been wrong. I kept that story in the write-up because it's the kind of mistake that's easy to miss.

### The solo "talk this through"

I didn't have a breakout group, so I used the solo prompts. For my worst failure (FP03), the agent listed three possible causes at different pipeline stages without picking one first (the route, signal one, and the combining weight), then checked each against the real scores. It was signal one (0.8051 alone; style alone was 0.6033). I didn't run the "argue the opposite verdict" prompt as a separate step. The closest thing is in the criterion 1 verdict: "MET" is a generous reading when nothing ever reaches 0.80, so the write-up says the target was too easy and how I'd tighten it.

### What I'd still need to do myself

- Put ten pieces of my real writing into `scenarios.py` and re-run criteria 1 and 2.
- Read through every held/broke mark and every verdict and make sure I agree with them, not just the agent.

### Commands for this unit

```bash
source .venv/bin/activate
python -m unittest test_service              # 13 tests
python app.py                                # terminal 1
python run_attacks.py --flood 15             # terminal 2: rate limit check
python run_attacks.py --set attack_set --label before
python tools/judge_attacks.py results/attack_run_<stamp>_before.md results/attack_verdicts_before.md
python run_eval.py --label before
python tools/eval_appeals_and_raw.py --label before    # takes ~4 min (waits a minute between trials)
python tools/score_eval.py results/run_<stamp>_before.md results/extra_<stamp>_before.json
```


## Capstone

**What This Extends**

I extended my existing Provenance Guard service from Units 7 and 8. The starting commit was `3d4b91a`. Submission scoring, cautious labels, input validation, rate limiting, appeals, and content lookup already existed. This capstone adds a reproducible local run path, a separate request-completion log, real elapsed/CPU measurements, and a repeatable evaluator. Earlier README sections and results remain intact; the old acceptance criteria are preserved in [docs/criteria-units-7-8.md](docs/criteria-units-7-8.md).

**The Shape**

I chose **Shape A — Deploy and instrument**, using **Path B — local with logs**. The scope was the operational layer around the existing application. Model replacement, score/label changes, and a new interface or authentication system stayed out of scope. The model remains local GPT-2; I did not attempt a small free host. No stretch is claimed. The Unit 8 rate limiter, short-text rejection and floating-point fix are existing work, not capstone improvements.

**Running It**

The exact environment, setup, model download, startup command and repeat commands are in [RUNNING.md](RUNNING.md). After setup, the single PowerShell command is:

```powershell
.\.venv\Scripts\python.exe run_local.py
```

I verified clean checkouts of the same repository at `e599f4d` (before) and `e3929c0` (after), with a fresh virtual environment installed from `requirements-lock.txt`. Both manifests record an empty initial Git status. All three trials in each set started fresh processes, and every trial checked persistence through a further restart. Tests used the same launcher with an available local port and a separate log directory. Code and session response headers verified which server answered.

The environment was Python 3.12.10 on Windows x64 with 12 logical CPUs, torch 2.15.0, transformers 4.57.6, Flask 3.1.3, and Flask-Limiter 3.12. Full package versions are recorded in each manifest. The pinned GPT-2 revision is `607a30d783dfa663caf39e06633721c8d4cfcd7e`. Its seven selected files total **550,959,861 bytes**, measured from the local cache. [Setup evidence](results/capstone/setup/) includes the successful clean installation, dependency check, model-file inventory, and 17 passing regression tests before and after.

**Instrumentation**

`observability.py::install` registers request hooks before the rate limiter. `start_request` records an ID, start counters, model-loaded state, and input description. `finish_request` writes one JSONL completion record including HTTP errors; the exception signal identifies unexpected detector errors. The normal launcher disables debugging/reload and serves one request at a time.

Records include UTC time, request and service-run IDs, code revision, process ID, method, route, input byte count/hash and fixture ID, output status/selected fields/hash, elapsed milliseconds, CPU milliseconds, model-loaded-at-start, actual PyTorch thread count, and error code/stage/type. Oversized bodies are marked unread with their declared size. Full nonprivate test input and response bytes are saved in each `trial.json`, so hashes can be resolved to actual evidence. Raw submitted writing is not copied into the operational log; hashes are not an anonymity guarantee.

The new `requests.jsonl` stays separate from `audit.jsonl`, preserving the existing decision/appeal history. `/log` still reads business history. The timing hook ends before writing the completion record and sending the response; the evaluator's client timer captures the full exchange. CPU time is process-wide and is attributed to requests only because this experiment is sequential. No claim is made about logging after abrupt process termination or disk failure.

These are **ten real successful performance records plus one real malformed-input rejection**, copied without invented values from after-trial 1. Source: `observability.py::finish_request`, [normal/logs/requests.jsonl](results/capstone/after/trial_1/normal/logs/requests.jsonl). The corresponding exact inputs and responses are in [trial.json](results/capstone/after/trial_1/trial.json).

```jsonl
{"schema_version": 1, "event": "request_completed", "timestamp": "2026-11-17T03:24:12.138+00:00", "service_run_id": "3902f785-4d5d-461a-a7ae-3ef4dcdd433a", "code_revision": "e3929c01fd2e8f48c4e9122493b93e73520783a9", "pid": 16240, "request_id": "46401b3a-7352-4efc-b59c-23ea64ef4b86", "method": "POST", "route": "/submit", "input": {"content_type": "application/json", "declared_bytes": 484, "fixture_id": "performance_01", "query": "", "capture": "hashed", "bytes": 484, "sha256": "34f444d8d655e9abe20c747147f731ca0851dca2825e8c66ae2e11182c70f61c", "json_type": "dict", "fields": ["creator_id", "text"], "text_chars": 440}, "http_status": 200, "output": {"bytes": 294, "sha256": "0e3ac3ced9ba122963a0062aecaf4321e698750822879d5b3bebce9c47190d98", "content_type": "application/json", "fields": {"content_id": "564dd8c7-b44d-4777-bb9a-6fab56d04e81", "guess": "unsure", "confidence": 0.5815, "model_score": 0.6088, "style_score": 0.5179, "status": "decided"}}, "duration_ms": 429.3209, "cpu_ms": 437.5, "model_loaded_at_start": true, "torch_threads": 1, "error_code": null, "error_stage": null, "exception_type": null}
{"schema_version": 1, "event": "request_completed", "timestamp": "2026-11-17T03:24:12.591+00:00", "service_run_id": "3902f785-4d5d-461a-a7ae-3ef4dcdd433a", "code_revision": "e3929c01fd2e8f48c4e9122493b93e73520783a9", "pid": 16240, "request_id": "09ec56de-6085-4d4a-8b5e-7aa118c97380", "method": "POST", "route": "/submit", "input": {"content_type": "application/json", "declared_bytes": 465, "fixture_id": "performance_02", "query": "", "capture": "hashed", "bytes": 465, "sha256": "c9a361d9734c9e20c2c3090cd67b7b430e5ed71d1ded44700b734b935ad53ac7", "json_type": "dict", "fields": ["creator_id", "text"], "text_chars": 421}, "http_status": 200, "output": {"bytes": 294, "sha256": "1e4873d3e8224feebc65aecd81eeacef5ccc064695b3c917f9cde56d41b41a13", "content_type": "application/json", "fields": {"content_id": "51644a50-6b91-410b-8346-e3ca320f7dd3", "guess": "unsure", "confidence": 0.6561, "model_score": 0.7458, "style_score": 0.4468, "status": "decided"}}, "duration_ms": 436.1992, "cpu_ms": 421.875, "model_loaded_at_start": true, "torch_threads": 1, "error_code": null, "error_stage": null, "exception_type": null}
{"schema_version": 1, "event": "request_completed", "timestamp": "2026-11-17T03:24:13.022+00:00", "service_run_id": "3902f785-4d5d-461a-a7ae-3ef4dcdd433a", "code_revision": "e3929c01fd2e8f48c4e9122493b93e73520783a9", "pid": 16240, "request_id": "b103f078-6316-48b0-bfd2-ffbca9e65837", "method": "POST", "route": "/submit", "input": {"content_type": "application/json", "declared_bytes": 424, "fixture_id": "performance_03", "query": "", "capture": "hashed", "bytes": 424, "sha256": "aeec99a210d862e2107bad0ca7e375c43e9b2e9fc159ce358aec43ecbcaf452c", "json_type": "dict", "fields": ["creator_id", "text"], "text_chars": 380}, "http_status": 200, "output": {"bytes": 293, "sha256": "cc81ed05e3e446a68e50b66bdfbf76123890ed5a5cbb723cf32f3a632daa4210", "content_type": "application/json", "fields": {"content_id": "030f0cf2-4f43-4339-834f-e3adea3cb349", "guess": "unsure", "confidence": 0.4259, "model_score": 0.4019, "style_score": 0.482, "status": "decided"}}, "duration_ms": 412.0113, "cpu_ms": 390.625, "model_loaded_at_start": true, "torch_threads": 1, "error_code": null, "error_stage": null, "exception_type": null}
{"schema_version": 1, "event": "request_completed", "timestamp": "2026-11-17T03:24:13.419+00:00", "service_run_id": "3902f785-4d5d-461a-a7ae-3ef4dcdd433a", "code_revision": "e3929c01fd2e8f48c4e9122493b93e73520783a9", "pid": 16240, "request_id": "37f08981-8e6c-446a-ab2f-796144dac261", "method": "POST", "route": "/submit", "input": {"content_type": "application/json", "declared_bytes": 439, "fixture_id": "performance_04", "query": "", "capture": "hashed", "bytes": 439, "sha256": "c9ea0a41b86a7f3d144b2240f3b5949a0c0db40c0653ff09f7a4b889c10a8d9e", "json_type": "dict", "fields": ["creator_id", "text"], "text_chars": 395}, "http_status": 200, "output": {"bytes": 294, "sha256": "8eb97a354d11bd1470aad4894a8d564db76e57948d9fff7c6fe22c6eb16ab5c0", "content_type": "application/json", "fields": {"content_id": "b494f262-c6e8-467f-8401-631d04a803e8", "guess": "unsure", "confidence": 0.3996, "model_score": 0.2947, "style_score": 0.6443, "status": "decided"}}, "duration_ms": 373.038, "cpu_ms": 375.0, "model_loaded_at_start": true, "torch_threads": 1, "error_code": null, "error_stage": null, "exception_type": null}
{"schema_version": 1, "event": "request_completed", "timestamp": "2026-11-17T03:24:13.818+00:00", "service_run_id": "3902f785-4d5d-461a-a7ae-3ef4dcdd433a", "code_revision": "e3929c01fd2e8f48c4e9122493b93e73520783a9", "pid": 16240, "request_id": "8f8c0839-596a-4044-8dba-1d6495b0c4a3", "method": "POST", "route": "/submit", "input": {"content_type": "application/json", "declared_bytes": 420, "fixture_id": "performance_05", "query": "", "capture": "hashed", "bytes": 420, "sha256": "757e30d3418ce3612bfa9fa724c10acf93c443499958cb8af9a88c9acbadafeb", "json_type": "dict", "fields": ["creator_id", "text"], "text_chars": 376}, "http_status": 200, "output": {"bytes": 294, "sha256": "5ec927a878e63e9ca91bf29f7d433e7591cc944136500ebdd33bab1ce9415eb3", "content_type": "application/json", "fields": {"content_id": "fb33db6a-33ca-43c5-84cf-1c39feda8de0", "guess": "unsure", "confidence": 0.5866, "model_score": 0.6187, "style_score": 0.5117, "status": "decided"}}, "duration_ms": 380.9989, "cpu_ms": 375.0, "model_loaded_at_start": true, "torch_threads": 1, "error_code": null, "error_stage": null, "exception_type": null}
{"schema_version": 1, "event": "request_completed", "timestamp": "2026-11-17T03:24:14.228+00:00", "service_run_id": "3902f785-4d5d-461a-a7ae-3ef4dcdd433a", "code_revision": "e3929c01fd2e8f48c4e9122493b93e73520783a9", "pid": 16240, "request_id": "829913a6-761f-447f-a23f-9a14d8f11d62", "method": "POST", "route": "/submit", "input": {"content_type": "application/json", "declared_bytes": 428, "fixture_id": "performance_06", "query": "", "capture": "hashed", "bytes": 428, "sha256": "1ad54b600d4a0e9c8d2e99087564a5b1d66cad455d815a7906a5b070ea3a76d7", "json_type": "dict", "fields": ["creator_id", "text"], "text_chars": 384}, "http_status": 200, "output": {"bytes": 292, "sha256": "1c3d852f1ba1343bbe8cc06727e2f0a3d4fe96a744edb5e1574529e47bb5285f", "content_type": "application/json", "fields": {"content_id": "5a5614e6-6659-4525-9963-fdcd6df6db2e", "guess": "unsure", "confidence": 0.6159, "model_score": 0.6785, "style_score": 0.47, "status": "decided"}}, "duration_ms": 392.1111, "cpu_ms": 390.625, "model_loaded_at_start": true, "torch_threads": 1, "error_code": null, "error_stage": null, "exception_type": null}
{"schema_version": 1, "event": "request_completed", "timestamp": "2026-11-17T03:24:14.653+00:00", "service_run_id": "3902f785-4d5d-461a-a7ae-3ef4dcdd433a", "code_revision": "e3929c01fd2e8f48c4e9122493b93e73520783a9", "pid": 16240, "request_id": "966d0d02-8505-49b2-96bb-839ca386838c", "method": "POST", "route": "/submit", "input": {"content_type": "application/json", "declared_bytes": 479, "fixture_id": "performance_07", "query": "", "capture": "hashed", "bytes": 479, "sha256": "df47b995ae0515a7fb408e6f9e23fe804f78ffc58106253e6e9cab22131f5ade", "json_type": "dict", "fields": ["creator_id", "text"], "text_chars": 435}, "http_status": 200, "output": {"bytes": 294, "sha256": "532d232c06b619904dabca69fb8783b9a7a6f99b3c3a2ef901725605238b7890", "content_type": "application/json", "fields": {"content_id": "41f7ef03-cce2-4c72-a35e-c79cd7c7b51c", "guess": "unsure", "confidence": 0.4764, "model_score": 0.5154, "style_score": 0.3855, "status": "decided"}}, "duration_ms": 409.0624, "cpu_ms": 406.25, "model_loaded_at_start": true, "torch_threads": 1, "error_code": null, "error_stage": null, "exception_type": null}
{"schema_version": 1, "event": "request_completed", "timestamp": "2026-11-17T03:24:15.050+00:00", "service_run_id": "3902f785-4d5d-461a-a7ae-3ef4dcdd433a", "code_revision": "e3929c01fd2e8f48c4e9122493b93e73520783a9", "pid": 16240, "request_id": "ed3c38ef-f49e-4be9-a299-c26805e8c553", "method": "POST", "route": "/submit", "input": {"content_type": "application/json", "declared_bytes": 439, "fixture_id": "performance_08", "query": "", "capture": "hashed", "bytes": 439, "sha256": "ee90fc7a2904b9d594488ae2d44868dc6bbecd3add9abebcca46f68af6bd22fd", "json_type": "dict", "fields": ["creator_id", "text"], "text_chars": 395}, "http_status": 200, "output": {"bytes": 294, "sha256": "48de83687d11753ec4de6623655a13a1eadb2499fbbe27aaef5a121e4a27bd2d", "content_type": "application/json", "fields": {"content_id": "4c9f168c-e1ed-432c-86df-f93bd48a48ef", "guess": "unsure", "confidence": 0.4302, "model_score": 0.4776, "style_score": 0.3196, "status": "decided"}}, "duration_ms": 378.3548, "cpu_ms": 375.0, "model_loaded_at_start": true, "torch_threads": 1, "error_code": null, "error_stage": null, "exception_type": null}
{"schema_version": 1, "event": "request_completed", "timestamp": "2026-11-17T03:24:15.464+00:00", "service_run_id": "3902f785-4d5d-461a-a7ae-3ef4dcdd433a", "code_revision": "e3929c01fd2e8f48c4e9122493b93e73520783a9", "pid": 16240, "request_id": "8357c586-3f5d-4eac-bbf4-7e042038dc44", "method": "POST", "route": "/submit", "input": {"content_type": "application/json", "declared_bytes": 442, "fixture_id": "performance_09", "query": "", "capture": "hashed", "bytes": 442, "sha256": "878996775483f58bce092a077d2e367a83eb85cd67dfe6d0598aa1928fe21c8f", "json_type": "dict", "fields": ["creator_id", "text"], "text_chars": 398}, "http_status": 200, "output": {"bytes": 293, "sha256": "1730c9dc237e46b676bd5486b7932cc76144b1680388753640fc3c0ae27fd9a9", "content_type": "application/json", "fields": {"content_id": "77340eee-44ac-4977-af26-27512a26cec6", "guess": "unsure", "confidence": 0.641, "model_score": 0.7146, "style_score": 0.4694, "status": "decided"}}, "duration_ms": 395.2899, "cpu_ms": 390.625, "model_loaded_at_start": true, "torch_threads": 1, "error_code": null, "error_stage": null, "exception_type": null}
{"schema_version": 1, "event": "request_completed", "timestamp": "2026-11-17T03:24:15.857+00:00", "service_run_id": "3902f785-4d5d-461a-a7ae-3ef4dcdd433a", "code_revision": "e3929c01fd2e8f48c4e9122493b93e73520783a9", "pid": 16240, "request_id": "c75a8e25-3a16-40ec-b0ca-c3ae545166dd", "method": "POST", "route": "/submit", "input": {"content_type": "application/json", "declared_bytes": 410, "fixture_id": "performance_10", "query": "", "capture": "hashed", "bytes": 410, "sha256": "1ab3e7d9a083c09ce001abe26479085810da648c8c35bd23ec9786970a71a11a", "json_type": "dict", "fields": ["creator_id", "text"], "text_chars": 366}, "http_status": 200, "output": {"bytes": 294, "sha256": "054a0f5437e04d91ad73d81e5ca6dfcf31e0ad669768e830dc87567180215865", "content_type": "application/json", "fields": {"content_id": "8a674b5e-fe69-43ea-bc3d-2fc638bf278a", "guess": "unsure", "confidence": 0.5824, "model_score": 0.5968, "style_score": 0.5489, "status": "decided"}}, "duration_ms": 374.4636, "cpu_ms": 375.0, "model_loaded_at_start": true, "torch_threads": 1, "error_code": null, "error_stage": null, "exception_type": null}
{"schema_version": 1, "event": "request_completed", "timestamp": "2026-11-17T03:24:09.650+00:00", "service_run_id": "3902f785-4d5d-461a-a7ae-3ef4dcdd433a", "code_revision": "e3929c01fd2e8f48c4e9122493b93e73520783a9", "pid": 16240, "request_id": "425950bc-9198-4f76-b456-fff73121704c", "method": "POST", "route": "/submit", "input": {"content_type": "application/json", "declared_bytes": 7, "fixture_id": "malformed_json", "query": "", "capture": "hashed", "bytes": 7, "sha256": "be302461cda285db3ed2d45fb767b23e08ca8808b35a638009937df22b332d73", "json_type": "NoneType"}, "http_status": 400, "output": {"bytes": 82, "sha256": "4957d793f21310d561d0c089f480106e7d6c722a6d9146a2bb8540e06f20eae2", "content_type": "application/json", "fields": {"error": "invalid_json", "message": "Send a JSON object with text and creator_id."}}, "duration_ms": 1.2995, "cpu_ms": 0.0, "model_loaded_at_start": true, "torch_threads": 1, "error_code": "invalid_json", "error_stage": "request_handling", "exception_type": null}
```

**What It Costs**

I measured ten fixed 50–150-word submissions per trial, after a real warm-up in the same process, and repeated that three times in each result set. These are generated operational fixtures, not my own human-writing samples. No successful slow request was removed, and all 60 performance requests returned 200.

The client used `time.perf_counter()` around the HTTP exchange. The server used `time.process_time()` around request handling for CPU seconds. These clocks measure different things: simultaneous work on several CPU threads can consume more CPU seconds than elapsed seconds. See [Python's timing documentation](https://docs.python.org/3.12/library/time.html#time.process_time). Setup/download, process startup, idle time, and the first model-loading request are excluded from the warm average and identified separately. This is measured compute use, not an electricity bill or a concurrency-capacity estimate.

| Build | Trial | Successful requests | Mean elapsed seconds | Nearest-rank p95 elapsed seconds | Mean CPU seconds |
|---|---|---|---|---|---|
| before | 1 | 10 | 0.164060 | 0.175837 | 0.937500 |
| before | 2 | 10 | 0.166485 | 0.187335 | 0.918750 |
| before | 3 | 10 | 0.165251 | 0.183434 | 0.932813 |
| after | 1 | 10 | 0.401197 | 0.438961 | 0.393750 |
| after | 2 | 10 | 0.390277 | 0.422184 | 0.382812 |
| after | 3 | 10 | 0.385307 | 0.422477 | 0.370312 |

Across 30 warm requests per build, the mean changed from **0.929688 to 0.382292 CPU seconds per run**, while mean elapsed time changed from **0.165265 to 0.392260 seconds**. Each trial's ten individual timings and the calculation inputs are saved under criterion 4 in the manifests and trial evidence.

For **100 people a day, assuming one submission each to an already-warm process**: `100 people × 1 submission/person × 0.382292 CPU seconds/submission = 38.2292 CPU seconds/day`. The corresponding sum of sequential request elapsed times is `100 × 0.392260 = 39.2260 seconds/day`; that is not a throughput promise. The code makes no hosted inference API calls, but local CPU work, memory, setup and idle operation still have costs. Cold first-request times remain visible in criterion 1's tables. Cold here means a fresh server process; the disk model cache and operating-system file cache were not erased.

**Run Log and Verdicts**

The criteria were committed at `0b11575`, before implementation and capstone measurements; first results were committed at `29cf86e`. The five original capstone targets and all fixture bytes stayed unchanged for both sets. The baseline is the initial completed operational extension, not the old Unit 8 runs. `capstone_eval.py::trial` generated the results; real model scoring uses `app.py::submit` and `detector.py::model_signal`. Only the two named fault processes substitute a detector exception.

Before the improvement, tested code `e599f4d`:

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Reproducible startup | Health <=15s; first submit <=30s | 1.187s / 9.794s | 0.550s / 6.655s | 0.555s / 6.648s | MET |
| 2. Complete request traces | 22/22 complete, unique records; reads preserve audit | 22/22; audit unchanged | 22/22; audit unchanged | 22/22; audit unchanged | MET |
| 3. Visible failures | 9/9 error cases; fault processes remain alive | 9/9; alive | 9/9; alive | 9/9; alive | MET |
| 4. Warm latency and CPU budget | >=9/10 within 2s; mean CPU <=5s | 10/10; 0.9375 CPU s | 10/10; 0.9187 CPU s | 10/10; 0.9328 CPU s | MET |
| 5. Original behavior preserved | 6/6 compatible scores/labels; both appeals survive restart | 6/6; appeals + restart pass | 6/6; appeals + restart pass | 6/6; appeals + restart pass | MET |

**Verdicts and diagnosis:** All five criteria were MET in all three trials. There are no missed acceptance criteria to diagnose. The deliberate 400/404/413/429/503/500 responses are successful bad-path checks, not unreported failures. Criterion 4's budgets were generous for these short texts: every warm request was below 0.188 seconds before the improvement, versus the two-second target.

The useful operational finding was the difference between elapsed and CPU time. The baseline recorded six PyTorch threads and about 0.930 CPU seconds for a 0.165-second request. Parallel work explains why CPU time exceeds elapsed time; thread coordination was a hypothesis to test, not a measured stage breakdown. The improvement below tests a single smaller thread setting.

Actual output supporting each criterion from **before trial 1** follows. These are excerpts of saved responses/records, not hypothetical examples.

Criterion 1 — `capstone_eval.py::Server.__enter__` / `Server.send`, serving `app.py::submit`:

```json
{
  "startup": {
    "command": [
      "C:\\Users\\ahmed\\Documents\\Codex\\2026-11-16\\i-have-to-work-on-a-3\\work\\clean-venv\\Scripts\\python.exe",
      "run_local.py",
      "--port",
      "62975",
      "--log-dir",
      "C:\\Users\\ahmed\\Documents\\Codex\\2026-11-16\\i-have-to-work-on-a-3\\work\\evidence-before\\trial_1\\normal\\logs"
    ],
    "cwd": "C:\\Users\\ahmed\\Documents\\Codex\\2026-11-16\\i-have-to-work-on-a-3\\work\\clean-before",
    "seconds": 1.1868205000000671,
    "service_run_id": "0af3ca36-5e4e-41d2-ac91-ae942176d4f5"
  },
  "first_submit_client_seconds": 9.793703000000278,
  "first_submit_response": {
    "confidence": 0.1945,
    "content_id": "c222b4c9-22d9-4d04-a151-b374c7bcde70",
    "guess": "human",
    "label": "We think this was probably written by a person. This estimate does not verify who wrote it. You can ask for a review if it seems wrong.",
    "model_score": 0.0447,
    "status": "decided",
    "style_score": 0.5441
  }
}
```

Criterion 2 — `observability.py::finish_request`, the matching completion record:

```json
{
  "schema_version": 1,
  "event": "request_completed",
  "timestamp": "2026-11-17T03:21:47.952+00:00",
  "service_run_id": "0af3ca36-5e4e-41d2-ac91-ae942176d4f5",
  "code_revision": "e599f4dec7c474a3428064d68e73b9b16644a29f",
  "pid": 35380,
  "request_id": "686dad78-ba24-4e3c-9ecc-8ed013065b5f",
  "method": "POST",
  "route": "/submit",
  "input": {
    "content_type": "application/json",
    "declared_bytes": 204,
    "fixture_id": "trace_valid",
    "query": "",
    "capture": "hashed",
    "bytes": 204,
    "sha256": "c0a9903d49257db711ebbf958debb0e76d215ebf61629d8c3cf5e6f714431560",
    "json_type": "dict",
    "fields": [
      "creator_id",
      "text"
    ],
    "text_chars": 162
  },
  "http_status": 200,
  "output": {
    "bytes": 297,
    "sha256": "8faf2b1e9ff957e566eb9e073ac51c364831fe6095d88700377627dc065ef7f0",
    "content_type": "application/json",
    "fields": {
      "content_id": "c222b4c9-22d9-4d04-a151-b374c7bcde70",
      "guess": "human",
      "confidence": 0.1945,
      "model_score": 0.0447,
      "style_score": 0.5441,
      "status": "decided"
    }
  },
  "duration_ms": 9790.0291,
  "cpu_ms": 8296.875,
  "model_loaded_at_start": false,
  "torch_threads": 6,
  "error_code": null,
  "error_stage": null,
  "exception_type": null
}
```

Criterion 3 — `capstone_fault_server.py::main` deliberately raises `DetectorUnavailable`; `app.py::submit` returns 503 and the same process subsequently answers health checks:

```json
{
  "response": {
    "error": "detector_unavailable",
    "message": "The local detector could not load. Run python detector.py and try again."
  },
  "http_status": 503,
  "record": {
    "schema_version": 1,
    "event": "request_completed",
    "timestamp": "2026-11-17T03:21:54.114+00:00",
    "service_run_id": "f988914a-f423-48ea-ac19-ce3d3b342730",
    "code_revision": "e599f4dec7c474a3428064d68e73b9b16644a29f",
    "pid": 34272,
    "request_id": "856f0a28-0e8e-457a-9d6a-00abfe94ec78",
    "method": "POST",
    "route": "/submit",
    "input": {
      "content_type": "application/json",
      "declared_bytes": 204,
      "fixture_id": "unavailable",
      "query": "",
      "capture": "hashed",
      "bytes": 204,
      "sha256": "c69814e33169fad7bec866eac4806209cea235f21ce7a1a7cb0e66030de0dd18",
      "json_type": "dict",
      "fields": [
        "creator_id",
        "text"
      ],
      "text_chars": 162
    },
    "http_status": 503,
    "output": {
      "bytes": 118,
      "sha256": "663e824a6798fd4c86db6f61fe0b9dee466c0a7028a766609f6465746e60855f",
      "content_type": "application/json",
      "fields": {
        "error": "detector_unavailable",
        "message": "The local detector could not load. Run python detector.py and try again."
      }
    },
    "duration_ms": 1.4244,
    "cpu_ms": 0.0,
    "model_loaded_at_start": false,
    "torch_threads": null,
    "error_code": "detector_unavailable",
    "error_stage": "detector",
    "exception_type": null
  },
  "trial_failure_checks": {
    "met": true,
    "failures_passed": 9,
    "total": 9,
    "fault_processes_survived": true,
    "rate_block_seconds": 1.27381830000013
  }
}
```

Criterion 4 — `capstone_eval.py::trial`, real ten-request measurements:

```json
{
  "met": true,
  "under_two_seconds": 10,
  "count": 10,
  "mean_elapsed_seconds": 0.16406011000017315,
  "p95_elapsed_seconds": 0.17583680000007007,
  "mean_cpu_seconds": 0.9375,
  "elapsed_seconds": [
    0.1703458000001774,
    0.17583680000007007,
    0.1716681999996581,
    0.14847670000017388,
    0.15854940000008355,
    0.15885070000058477,
    0.1654359000003751,
    0.16432090000034805,
    0.1593603000001167,
    0.1677564000001439
  ],
  "cpu_seconds": [
    1.0,
    1.03125,
    0.921875,
    0.78125,
    0.9375,
    0.9375,
    0.9375,
    1.0,
    0.90625,
    0.921875
  ]
}
```

Criterion 5 — actual `app.py::get_content` response after the server restart, showing the preserved original decision and both appeals:

```json
{
  "appeals": [
    {
      "content_id": "c222b4c9-22d9-4d04-a151-b374c7bcde70",
      "creator_id": "trace_writer",
      "event": "appeal",
      "reasoning": "Demonstration appeal: please preserve the original decision and record this request for review.",
      "status": "under_review",
      "timestamp": "2026-11-17T03:21:47+00:00"
    },
    {
      "content_id": "c222b4c9-22d9-4d04-a151-b374c7bcde70",
      "creator_id": "trace_writer",
      "event": "appeal",
      "reasoning": "Demonstration appeal: please preserve the original decision and record this request for review.",
      "status": "under_review",
      "timestamp": "2026-11-17T03:21:52+00:00"
    }
  ],
  "combined_score": 0.1945,
  "confidence": 0.1945,
  "content_id": "c222b4c9-22d9-4d04-a151-b374c7bcde70",
  "creator_id": "trace_writer",
  "guess": "human",
  "label": "We think this was probably written by a person. This estimate does not verify who wrote it. You can ask for a review if it seems wrong.",
  "model_score": 0.0447,
  "status": "under_review",
  "style_score": 0.5441,
  "timestamp": "2026-11-17T03:21:47+00:00"
}
```

**The Improvement**

I made one operational change at `e3929c0`: `detector.py::_load` now calls `torch.set_num_threads(1)` before loading/running the model. The baseline used six intra-operation threads. PyTorch documents that this setting controls CPU intra-operation parallelism and should be applied before model work: [torch.set_num_threads](https://docs.pytorch.org/docs/2.15/generated/torch.set_num_threads.html). I changed no weights, labels, thresholds, fixture texts, acceptance targets, or dependency versions.

After the improvement, tested code `e3929c0`:

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Reproducible startup | Health <=15s; first submit <=30s | 1.163s / 6.853s | 1.161s / 7.016s | 1.146s / 6.868s | MET |
| 2. Complete request traces | 22/22 complete, unique records; reads preserve audit | 22/22; audit unchanged | 22/22; audit unchanged | 22/22; audit unchanged | MET |
| 3. Visible failures | 9/9 error cases; fault processes remain alive | 9/9; alive | 9/9; alive | 9/9; alive | MET |
| 4. Warm latency and CPU budget | >=9/10 within 2s; mean CPU <=5s | 10/10; 0.3937 CPU s | 10/10; 0.3828 CPU s | 10/10; 0.3703 CPU s | MET |
| 5. Original behavior preserved | 6/6 compatible scores/labels; both appeals survive restart | 6/6; appeals + restart pass | 6/6; appeals + restart pass | 6/6; appeals + restart pass | MET |

| Measurement across 30 warm requests | Before: 6 threads | After: 1 thread | Observed effect |
|---|---|---|---|
| Mean CPU seconds/run | 0.929688 | 0.382292 | **58.9% less CPU work** |
| Mean elapsed seconds/run | 0.165265 | 0.392260 | **137.4% slower** |
| Performance responses within 2 seconds | 30/30 | 30/30 | Both meet the original target |
| Complete matrix records | 66/66 | 66/66 | No missing or duplicate request records |
| Deliberate failure cases handled | 27/27 | 27/27 | Both sets preserve business history |
| Six-fixture compatibility checks | 18/18 | 18/18 | Original scoring behavior preserved |

**Did it help?** It reduced aggregate CPU work, at the cost of slower replies. I kept the one-thread setting because the mean reply is still under 0.4 seconds and every measured reply remains within the original two-second budget. It is not a latency improvement. This is evidence from one laptop and one small sequential workload, not a claim that one thread is best for every machine, input length, or load. I did not try several thread counts and select a favorable result; this was the one declared change followed by one complete after-evaluation.

Real compatibility scores from trial 1 in each set (all three trials passed):

| Original fixture | Before guess / combined score | After guess / combined score |
|---|---|---|
| generated_conventional | ai / 0.8652 | ai / 0.8652 |
| human_literary | unsure / 0.5522 | unsure / 0.5522 |
| mixed | unsure / 0.5543 | unsure / 0.5543 |
| human_formal | unsure / 0.4756 | unsure / 0.4756 |
| lightly_edited_ai | unsure / 0.6413 | unsure / 0.6413 |
| generated_unusual | human / 0.1160 | human / 0.1160 |

**What's Still Broken**

No capstone criterion remains missed. The target I would tighten in a future, separately committed evaluation is **criterion 4**: require **all ten** warm requests within **0.5 seconds**, and mean CPU time no more than **0.5 CPU seconds**. I did not retroactively substitute this tighter target for the frozen two-second/five-CPU-second targets.

The CPU improvement made latency worse, even though it stayed within budget. The experiment covers short texts, one local sequential server, and a cached model; it does not establish performance on long inputs, concurrent users, another operating system, or an empty model cache. I stopped after the one measured change to keep the comparison attributable and the unit bounded.

The original detector's limitations also remain: its predictability score is not proof of authorship, unusual generated writing can receive a human label, and the older own-writing evaluation used generated stand-ins. My capstone fixtures are labeled honestly and do not resolve that accuracy gap. The client-selected creator ID can evade rate limits, in-memory counters reset on restart, and there is no login or staffed review workflow. Disk exhaustion, killed processes, and long-term log rotation are outside the measured scope. I did not expand into model replacement, authentication, or storage redesign during this operational extension.

If I had another unit before treating this as a real authorship product, I would first replace the old stand-ins with documented human-authored writing and evaluate false accusations across writing styles. Better operational measurements cannot establish that the detector's judgments are valid.

**How I Used AI**

**Moment 1 — scope and criteria.** I asked Codex to read the assignment and my existing application carefully, then complete the capstone under my direction and review. It identified missing request timing, unlogged appeal failures, stale setup instructions, and the limits of the existing test runner. I used that review to focus the work on Shape A and a separate request log that preserves business history. Criteria drafting was part of this assistance; the commit order establishes that targets preceded results, but does not establish the assignment's requested unaided authorship.

**Moment 2 — measurement and the tradeoff.** I used Codex to implement the instrumentation and evaluator, execute automated checks, and assemble the actual outputs while I directed and reviewed the work in chat. The first measurements showed six model threads and substantially more CPU seconds than elapsed seconds. The resulting change used one model thread; the full rerun showed lower CPU work and slower replies. I kept both numbers, the original targets, and the unchanged scores in the report. The Git commits use my configured name and email; no agent author or agent co-author line is added.
