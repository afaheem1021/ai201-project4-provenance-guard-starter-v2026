# Provenance Guard

Repository: https://github.com/afaheem1021/ai201-project4-provenance-guard-starter-v2026

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

I declared the optional `GET /content/<id>` status endpoint in the first planning commit, before implementing it. The required features and that extension are now implemented. No third signal or verified-human credential is planned. Unit 8 attack runs and rate limiting remain next-unit work.

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
