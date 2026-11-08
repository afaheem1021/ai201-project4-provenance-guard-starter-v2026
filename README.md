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

I didn't have a breakout group, so I did the solo version. I asked the AI assistant for three possible causes at different stages without saying which was most likely. It gave me: (1) the **route** has no check for language or register, (2) **signal one** reads simple, common vocabulary as predictable, and (3) the **combining rule** gives signal one 70% of the weight, so it overpowers style. I checked the numbers myself. The route did nothing wrong: it validated and scored normally. Style alone said 0.6033, which is middle of the road. Model alone said 0.8051. 0.7 × 0.8051 + 0.3 × 0.6033 = 0.7446. So the score is mostly signal one. **The cause is signal one**, and the combining rule just passes it through. The weight makes it worse but isn't the source: even at 50/50 FP03 would be 0.70.

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
