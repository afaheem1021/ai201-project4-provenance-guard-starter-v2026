# Capstone acceptance criteria — Provenance Guard

These five targets are frozen before capstone implementation or measurements. Earlier criteria are preserved in `docs/criteria-units-7-8.md`. The extension is Shape A, using Path B. The same five criteria and inputs are evaluated in three separate trials before and after one improvement. A criterion is MET only if its complete target holds in all three trials. No results are claimed here.

## 1. Reproduce the local startup (extension)

From a clean Git checkout with the documented Python environment and the pinned GPT-2 files already downloaded, start the service with the single command in RUNNING.md. In each of three fresh-process trials, `/health` must respond HTTP 200 within 15 seconds of process launch, and the first valid `/submit` must return HTTP 200 within 30 seconds of sending it. Save the command, code commit, environment, service-run ID, and both measured times. Installation and first download are prerequisites, timed separately if measured; neither is silently included in a warm request.

**Why this target:** A classmate should be able to start and demonstrate the service without editing its code. Fifteen seconds allows Python startup on this laptop, and thirty seconds allows cold model loading without accepting an indefinite wait. These are local demonstration budgets, not public-host service guarantees.

## 2. Trace every request exactly once (extension)

For the fixed 22-request trace matrix defined below, each trial must produce exactly one parseable completion record for every response's request ID (22/22, no duplicates). Each record must have a UTC timestamp, service-run ID, method and route, input description, HTTP status, output description, and nonnegative elapsed milliseconds and server CPU milliseconds. The record's status and output SHA-256 must match the actual response. Normal input bodies must have a matching SHA-256 and byte count; an oversized body may instead explicitly record that it was not read, with its declared length and rejection reason. Saved request bytes in the trial evidence must make every input inspectable. Reading existing audit history must not add request records to that business history.

**Why this target:** A missing error is invisible after the session, and duplicate records make counts and cost totals misleading. Exact accounting is feasible for a small, sequential local run. Full private writing need not be copied into the operational log because public test fixtures and saved trial requests supply the input evidence.

## 3. Keep failures visible without corrupting history (extension; bad path)

All nine failure cases in the trace matrix must return their specified status, have a matching completion record with a nonempty error code, and create no decision or appeal event: missing text (400), malformed JSON (400), body over 100,000 bytes (413), unknown appeal ID (404), unknown content ID (404), unknown route (404), the eleventh same-creator submission in one rate-limit window (429), controlled detector unavailability (503), and a controlled unexpected detector exception (500). After each controlled detector fault, `/health` must still answer 200 from that same process. Faults are injected only by the test harness, never exposed as a public endpoint or production setting. All nine must pass in each trial.

**Why this target:** Validation errors, refusal, and operational failure must be distinguishable from an actual authorship decision. A deliberate 500 is expected for the injected unexpected failure; losing the process or creating a false decision is not. This does not claim recovery from machine shutdown, disk exhaustion, or a killed process.

## 4. Measure a usable warm-request budget (extension)

After one real successful warm-up request in the same server process, submit the ten fixed 50–150-word performance fixtures sequentially. In each trial, at least 9 of 10 successful HTTP 200 responses must arrive within 2.0 seconds end to end, and mean server CPU time must be at most 5.0 CPU seconds per submission. Save all ten individual elapsed and CPU measurements, their means, and the nearest-rank p95 elapsed time. Exclude no slow successful request. An error or missing timing fails the trial; a rejected request cannot count as cheap inference. The startup/cold measurement stays separate.

**Why this target:** Two seconds is a useful interactive budget for a short classroom text, while the nine-of-ten allowance admits an occasional scheduling delay. Five CPU seconds per request bounds local processing work even when several CPU threads run at once. Both numbers are hypotheses to test on the documented laptop, not measurements or promised production capacity.

## 5. Preserve the original scoring and appeal workflow (regression)

In each trial, submit all six original `calibration.FIXTURES` through the real model. Each must retain its previously recorded guess and its combined score within 0.001 of `results/calibration.jsonl`. For the trace matrix's valid submission, submit an appeal and then a repeated appeal. Each must return 200 and add exactly one appeal with the unchanged reasoning and original creator ID. The original decision must remain identical, and `/content/<id>` must show `under_review` with both appeals, including after a service restart using the same audit file. Every check must pass in every trial. The six fixtures test compatibility, not human/AI accuracy.

**Why this target:** Operational instrumentation must not silently alter an authorship estimate or lose a writer's challenge. The small numeric tolerance allows harmless floating-point variation while catching a material scoring change. Restarting verifies that the appeal is persisted, not merely retained in memory.

## Frozen trace matrix and trial conditions

The 22 requests are: one valid submission; one valid appeal; one existing-content lookup; the six ordinary invalid requests listed in criterion 3 (missing text through unknown route); eleven submissions using one fresh creator ID (ten accepted, then one rate-limited); and the two controlled detector faults in separate test processes. This is 20 requests to the normal service and two to fault processes. Health probes, extra performance requests, six calibration requests, the repeated appeal, and restart checks are saved too but are outside the 22-request accounting matrix.

Each trial uses new service processes and its own log directory. Rate limiting remains on at 10/minute and 100/day. The rate-limit block must complete within one minute; its measured time is saved, and a block exceeding the window is reported as an invalid attempt, not silently scored as a limiter failure. Non-rate-limit workloads use distinct fixture identities. The model revision and test texts remain fixed before and after; any operational change is disclosed. The initial extension and later improvement get separate commits and separate result files. Existing generated stand-ins are never represented as the student's own writing.

## Revisions

None. If a target proves unmeasurable, its original text and a reasoned revision must both remain here. Missing a measurable target is not a reason to lower it.
