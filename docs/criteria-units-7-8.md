# Acceptance criteria — Provenance Guard

These targets were recorded before implementation and before collecting detector results. They are AI-assisted drafts: I asked Codex to choose suitable targets. The assignment asks for personally written criteria, so I need to review and take responsibility for these choices before submitting. I have not independently authored them.

For the next unit, freeze the evaluation texts before running them and repeat each criterion in three trials. A target must hold in every trial. Do not lower targets after seeing results. Calibration fixtures are development checks, not a substitute for personal writing.

## 1. Limit false accusations

On 10 distinct, unedited pieces I actually wrote myself, each 50–150 words, at most 1 may receive `guess: ai` in each trial. Include at least 3 pieces written in plain, everyday language. Record the exact texts and their provenance before evaluation; do not use AI-generated stand-ins.

**Why this target:** A wrong accusation can damage a writer's trust. One out of ten is a small-sample development ceiling, not an acceptable production guarantee; a miss deserves investigation rather than a quieter label change.

## 2. Separate scores without demanding perfect detection

For the same 10 human pieces and 10 AI-generated pieces matched by topic and approximately by length (50–150 words), the mean AI confidence score must exceed the mean human score by at least 0.20 in each trial. Freeze both groups before scoring and report both means, the difference, and individual scores.

**Why this target:** A detector that returns nearly the same number for everything is not useful. A 0.20 gap demands a visible difference without pretending every individual piece can be identified correctly.

## 3. Cover every label and handle disagreement

In a frozen set of 6 development texts, at least one actual submission must reach each of `human`, `unsure`, and `ai`. Separately, all 1,001 scores from 0.000 to 1.000 in steps of 0.001 must map to exactly one nonempty label. Scores 0.51 and 0.95 must map to different labels. Any two valid signal scores differing by at least 0.50 must combine to the unsure range, including (0.95, 0.10) and (0.10, 0.95).

**Why this target:** Ranges on paper are not enough; real requests need to reach them. When the signals strongly disagree, an unsure answer is more defensible than a confident accusation.

## 4. Preserve every appeal and the original decision

For 5 successful submissions, send one valid appeal per content ID. All 5 must return HTTP 200 with `status: under_review`; each must add exactly one appeal entry containing the submitted reasoning and matching creator ID. The original decision must remain unchanged, and `GET /content/<id>` must show `under_review`. A repeated valid appeal must also be recorded. An unknown ID must return 404 and must not create an appeal entry.

**Why this target:** The appeal path is a writer's way to challenge an error. Losing even one valid appeal or overwriting the original decision makes that path unreliable.

## 5. Reject bad input before scoring

Every request in this fixed invalid-input set must return JSON with `error` and `message`, without calling the detector or creating a decision: malformed JSON, a JSON list, missing text, null text, numeric text, whitespace-only text, missing creator ID, blank creator ID, a 101-character creator ID, and 10,001-character text. Use HTTP 400 for the first 9 and HTTP 413 for oversized text. A request body over 100,000 bytes must also return JSON/413. Invalid appeals (missing/blank reasoning, reasoning over 2,000 characters, and non-object JSON) must return 400 without recording an appeal.

**Why this target:** Input errors should not crash the service or waste a model call. The limits keep a local classroom service usable and produce clear responses a client can handle.

## Evaluation status

Criteria 1 and 2 require my own writing and a frozen, matched comparison set. They cannot honestly be reported as passed using generated examples. The current unit builds the service; the next unit evaluates the targets against the required evidence.
