**Provenance Guard: classroom speech and demonstration guide**

**How to use this document**

Read the speech in your own voice. Use the bold section titles to keep your place; you do not need to say them aloud. The italic directions in square brackets tell you what to show or when to pause; do not read them aloud. The speech is a suggested presentation, not an additional course requirement. Allow roughly 8–10 minutes for speaking and another 2–3 minutes for the live demonstration; shorten it to fit your instructor's time limit. The supplied brief asks for a short scope explanation and text evidence in the repository, not a slide deck.

Keep the repository's Capstone README section open beside two PowerShell terminals. This application is a backend service, so its demonstration consists of requests, responses, and logs. The runnable commands and backup plan follow the speech.

**Read-aloud speech**

**1. What the project does**

Hi everyone. My capstone is an extension of Provenance Guard, my writing-analysis application.

The application accepts a piece of writing and returns a cautious estimate: human, AI, or unsure. It combines two signals. A local language model called GPT-2 measures how predictable the text is, and a separate style signal looks at features such as sentence length and repetition.

Those signals cannot prove who wrote something. That is why the labels include a warning, and why the application lets a writer appeal. An appeal preserves the original decision and changes the submission's status to “under review.”

For this capstone, I focused on making that existing system easier to run, observe, and evaluate.

*[Show the beginning of the README's Capstone section.]*

**2. The scope I chose**

I chose Shape A: deploy and instrument. I used Path B: local with logs, which the assignment accepts on the same basis as hosting.

That fits this application because its model runs on my computer. The selected model files occupy about 551 megabytes on disk, and the running application needs additional memory. The local path also lets the demonstration run without a hosted inference API.

I kept the scope focused. I did not replace the model, change the scoring rules, or build a new interface. The new contribution was the operational layer: a repeatable startup process, complete request records, and measured runtime cost.

**3. What needed to improve**

The existing application already saved decisions and appeals. However, those records did not tell me how long a request took or how much CPU work it used. Some error paths, including invalid appeals, also returned a response without leaving an audit record.

The setup instructions needed attention too. Parts still described unfinished starter code even though the endpoints had been implemented.

I updated those instructions, recorded exact package versions, pinned the model revision, and checked the application from fresh checkouts. After setup, one documented command starts the service.

Then I added a separate request log. Each request gets a unique ID, and its record includes the time, route, input description, response status, output description, elapsed time, and CPU time.

Keeping this separate from the original audit log matters. Request measurements should not interfere with the history used to reconstruct a decision or an appeal.

*[Point to one request record. Explain the request ID, status, and timing fields; do not read the entire record.]*

**4. How I evaluated the work**

The five acceptance criteria were committed before the capstone measurements. Four concerned the new operational layer, and one checked that the original behavior stayed intact.

The first criterion covered startup: the service had to answer a health check within 15 seconds, and its first valid submission had to finish within 30 seconds.

The second required a complete, unique log record for every request in a fixed set of 22 requests.

The third covered nine failure cases. These included missing input, malformed data, oversized requests, unknown IDs, rate limiting, and two deliberately simulated detector failures. A failure had to leave a record without creating a false decision or appeal. The service also had to remain responsive after each simulated detector fault.

The fourth measured performance after the model was loaded. At least nine of ten valid requests had to finish within two seconds, and their average CPU time had to be at most five CPU seconds.

The fifth checked the original workflow. Six existing examples had to retain their labels and nearly identical scores, and both an appeal and a repeated appeal had to survive a restart without changing the original decision.

I ran three trials before the improvement and three afterward, using the same criteria and inputs. Here, “before” means the first completed version of the capstone extension. The performance evaluation used the actual local model. The two simulated failures were used only to test error handling.

**5. What the results showed**

All five criteria were met in all three before trials and all three after trials. Every trial accounted for all 22 traced requests and handled all nine expected failure cases. Scoring stayed compatible, and the appeal history survived restarts. The 17 automated regression checks passed too.

Passing everything did not mean there was nothing to learn. The performance targets were generous for these short inputs, and the measurements revealed a useful tradeoff.

*[Show the before-and-after comparison table. Pause before explaining the numbers.]*

**6. The improvement and its tradeoff**

There are two different kinds of time here. Elapsed time is how long the user waits. CPU time measures the processor work used during the request. When several CPU threads work at once, their total CPU time can be greater than the time on a stopwatch.

Before the improvement, the model used six CPU threads. A warm request took about 0.165 seconds for the user, but consumed about 0.930 CPU seconds.

I made one change: limit the model to one CPU thread. I then repeated the complete evaluation.

Average CPU time fell to about 0.382 seconds per submission, a reduction of approximately 59 percent. Average elapsed time increased to about 0.392 seconds. The replies became slower, while the amount of CPU work decreased.

I kept the change because every measured warm request still met the original two-second limit. For this small local workload, I accepted a longer wait in exchange for lower CPU use. That does not prove one thread is the best setting for every computer or workload.

These numbers describe a warmed-up model. The first scored request after starting the improved service took about seven seconds because it also loaded the model. I measured that separately.

**7. What it costs to run**

There is no hosted inference API charge in this application, but local processing still uses resources.

Using the measured average, 100 people making one submission each to an already-warm service would use about 38.23 CPU seconds of request-processing work. That is 100 multiplied by approximately 0.3823 CPU seconds per submission.

This calculation excludes installation, model loading, and idle operation. It is a compute measurement, not an electricity bill or a claim about how many people can use the service at once.

**8. What I learned and what remains**

The most useful lesson was that measurements make design choices easier to explain. I can point to the saved results and show exactly what the thread change improved and what it made worse.

I also learned that a passing result needs context. These were short inputs on one laptop, with requests handled one at a time. In a future evaluation, I would tighten the warm-request target to all ten finishing within half a second and average CPU use no more than half a CPU second. I kept the original targets unchanged for this comparison.

Detection accuracy remains a limitation. One unusual generated example still receives a human label. Preserving that result confirms that the operational change left the scoring behavior intact; it does not make the label correct. The generated performance fixtures also cannot stand in for a test of my own human writing.

If I had another unit, I would first evaluate documented human-authored samples across writing styles, with particular attention to false accusations.

I used Codex for assistance with implementation, criteria drafting, automated execution, and documentation while I directed and reviewed the work. That assistance is documented in the README.

The capstone leaves me with a service that can be started consistently, a record of what happened on both successful and failed requests, and evidence for the tradeoff I chose. I can show how it behaved and be clear about what the experiment does not establish.

Thank you. I’ll now demonstrate a submission, an appeal, and the records they create.

---

**Presentation checklist and live demonstration**

**Before class**

- Open this speech and the README's Capstone section. Keep the before-and-after comparison table easy to reach.
- Confirm setup is complete using RUNNING.md. Packages and model files should be downloaded before the presentation.
- Use two terminals in the project root. Start a fresh demonstration server so its in-memory rate-limit counters are clear.
- If you want the live submission to be warm, rehearse one submission after starting the server and leave that same process running. Downloading the model in another process does not warm this server.
- Use the provided demonstration text. Do not describe it as your own human-authored writing.
- Keep the committed logs and response examples open as a backup. Do not rerun the complete evaluator during class or overwrite the before/after evidence.

**Terminal 1 — start the application**

From the repository root:

```powershell
.\.venv\Scripts\python.exe run_local.py --port 5051 --log-dir logs\classroom-demo
```

Leave this terminal running. If port 5051 is occupied, choose another unused port and change the URL in Terminal 2 to match. Stop only your own demonstration process with Ctrl+C when finished.

**Terminal 2, step 1 — check the service**

```powershell
$baseUrl = 'http://127.0.0.1:5051'
Invoke-RestMethod -Uri "$baseUrl/health" | ConvertTo-Json
```

Say: “This confirms the service is responding. The `detector_loaded` field tells me whether this process has loaded the model yet.”

**Step 2 — send a submission and retain its current ID**

```powershell
$payload = Get-Content '.\results\sample_submit.json' -Raw | ConvertFrom-Json
$payload.creator_id = 'class-demo-' + [guid]::NewGuid().ToString('N').Substring(0, 8)
$submitResponse = Invoke-WebRequest -UseBasicParsing -Uri "$baseUrl/submit" -Method Post -ContentType 'application/json' -Body ($payload | ConvertTo-Json)
$submission = $submitResponse.Content | ConvertFrom-Json
$requestId = [string]($submitResponse.Headers['X-Request-ID'] | Select-Object -First 1)
$submission | ConvertTo-Json
$requestId
```

Say: “This is the returned label and its explanation. The content ID identifies the submission, while the request ID connects this particular HTTP response to its timing record. The score is a directional estimate, not a calibrated probability that someone cheated.”

Read the label actually returned. If this is the first submission since startup, explain the model-loading delay instead of presenting it as warm-request performance.

**Step 3 — demonstrate an appeal**

```powershell
$appealBody = @{
    content_id = $submission.content_id
    reasoning = 'Classroom demonstration: please record this request for review.'
} | ConvertTo-Json
Invoke-RestMethod -Uri "$baseUrl/appeal" -Method Post -ContentType 'application/json' -Body $appealBody | ConvertTo-Json
Invoke-RestMethod -Uri "$baseUrl/content/$($submission.content_id)" | ConvertTo-Json -Depth 6
```

Say: “The status is now under review. The original score and decision are still present, and the appeal has been added beside them. This records a request for review; it does not mean a human reviewer has already made a decision.”

Use the newly returned content ID in these commands. The old sample appeal file contains a historical ID and is not the right request for a new demonstration.

**Step 4 — show a deliberate input failure**

```powershell
curl.exe -s -i -X POST "$baseUrl/submit" -H "Content-Type: application/json" --data-binary "{}"
```

Say: “I sent a JSON object without the required text. The expected response is HTTP 400, meaning the request was rejected. That is the correct outcome for this test; it should not create a scored decision.”

The displayed body should contain `invalid_text`. A fresh demonstration process keeps repeated earlier bad requests from using up the address-based rate-limit allowance. If you get a different response, describe what actually happened and use the saved evidence rather than calling it the expected result.

**Step 5 — inspect the records**

```powershell
$requestLog = Get-Content '.\logs\classroom-demo\requests.jsonl' | ForEach-Object { $_ | ConvertFrom-Json }
$requestLog | Select-Object -Last 5 timestamp, route, http_status, duration_ms, cpu_ms | Format-Table -AutoSize
$requestLog | Where-Object { $_.request_id -eq $requestId } | ConvertTo-Json -Depth 6
```

Say: “These records include the successful submission, the appeal, the lookup, and the rejected input. This full record matches the request ID returned earlier. I can inspect the response status and timing without changing the code to reproduce the event.”

The operational log stores input fingerprints and descriptions, not full submitted writing. Exact nonprivate evaluation inputs are preserved separately with the committed trial evidence. A fingerprint connects records; it does not anonymize the underlying text or prove authorship.

**Step 6 — finish with the measured comparison**

Return to the README's comparison table. Point to both rows: CPU time decreased, while elapsed response time increased. Then point to the unchanged scoring results and the before/after verdict tables.

Say: “The live demo shows the workflow. The committed experiment supplies the repeated measurements. My conclusion is lower CPU work with slower replies that remained within the original target.”

**If the live demonstration fails**

Pause and state the actual problem. Use these saved sources, identifying them as recorded evaluation evidence rather than a live response:

| What to show | Where it is |
|---|---|
| Exact startup and setup instructions | RUNNING.md |
| Ten successful records and one real rejection | README.md → Capstone → Instrumentation |
| Submission, failure, and persisted appeal responses | README.md → Capstone → Run Log and Verdicts |
| Both five-criterion result tables and the tradeoff | README.md → Capstone → The Improvement |
| All individual timings and environment details | results/capstone/before/manifest.json and results/capstone/after/manifest.json |
| Exact calculations behind the comparison | results/capstone/comparison.json |

Do not spend the presentation debugging a download or trying to recreate the entire evaluation. The saved evidence is part of the assignment and is a valid way to explain what was measured.

---

**Questions classmates may ask**

**Why did you choose local deployment?**

“The assignment accepts local deployment with logs, and my model runs locally. I focused on a documented startup command, an exact environment, and real records from fresh checkouts. A public URL was not needed for this path.”

**Why make an improvement when all five criteria already passed?**

“Passing the original targets did not mean the implementation was optimal. The measurements showed a chance to reduce CPU work. I tested one change and reported its benefit and cost without changing the targets.”

**Does 59 percent less CPU mean the application is 59 percent faster?**

“No. CPU work decreased by about 59 percent, but elapsed time increased from about 0.165 to 0.392 seconds. The result is lower measured CPU use with slower replies.”

**How can CPU seconds be greater than elapsed seconds?**

“Several CPU threads can work during the same interval. CPU time counts their processing work, while elapsed time counts the wait from start to finish. Those are different measurements.”

**Were the errors real?**

“The malformed, oversized, unknown-ID, and rate-limit requests exercised the actual service. The unavailable-model and unexpected-exception cases used deliberate faults in separate test processes. Those controlled faults tested the response and logging behavior; they did not contribute to model-performance measurements.”

**Why does a 500 response appear in a passing test?**

“That test deliberately makes the detector raise an unexpected exception. The expected result is an error response, a matching log record, no invented authorship decision, and a service that can still answer its health check.”

**Does passing the five criteria prove the detector is accurate?**

“No. Four criteria concern operation and measurement, and the fifth checks compatibility with existing scores and appeals. The unusual generated example still gets a human label. That limitation stays visible.”

**Did you test on your own writing?**

“The performance set contains generated operational examples, clearly labeled as such. It measures runtime, not accuracy on my writing. The six compatibility examples retain their original documented sources. A proper own-writing accuracy evaluation still requires authentic writing samples.”

**Why were repeated trials useful if the scores were identical?**

“The model runs without sampling, so repeated scores can be stable. Fresh request IDs and process records verify that requests were actually rerun. Repetition also exposes differences in startup, runtime, logging, and persistence.”

**How much would 100 users cost?**

“Under the stated assumption of one submission per user to a warm service, the measured request-processing work is about 38.23 CPU seconds. This is not a dollar estimate, an electricity measurement, or a claim about 100 simultaneous users.”

**What would you change next?**

“I would first evaluate documented human-authored samples across writing styles, especially for false accusations. I would also set stricter operational targets before a future evaluation. The original targets remain unchanged in this submission.”

**How did you use AI?**

“I used Codex for implementation assistance, criteria drafting, automated execution, and documentation, under my direction and review. The README records that use. The history proves that the criteria came before the results; it does not establish unaided authorship of those criteria.”

---

**Two-sentence version for a short scope standup**

“I extended Provenance Guard through Shape A using the local-with-logs path, adding reproducible startup and complete request measurements around the existing scoring and appeal workflow. The measured improvement reduced CPU work by about 59 percent while increasing average warm-response time from 0.165 to 0.392 seconds, with all five criteria still met.”

**Memory card**

- Existing system: writing estimate plus an appeal path.
- New work: repeatable startup, complete request logs, and measured cost.
- Shape A; Path B; same repository and preserved history.
- Five criteria; three trials before and three after; all met.
- Each trial: 22 trace requests and nine expected failure cases.
- Real performance sample: ten requests per trial, 60 across both builds.
- CPU work: about 0.930 → 0.382 seconds, or 59% less.
- User wait: about 0.165 → 0.392 seconds, so replies became slower.
- Cost assumption: 100 people × one warm request ≈ 38.23 CPU seconds.
- Main limit: operational success does not establish authorship accuracy.

**Evidence sources for these notes**

The speech summarizes the committed criteria, README, RUNNING.md, and before/after evaluation records. The numerical comparison comes from `results/capstone/comparison.json`; individual measurements and actual responses remain in `results/capstone/`. Adding these speaking notes does not change the frozen criteria, application code, or recorded evaluation results.
