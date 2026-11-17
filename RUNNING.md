# Running Provenance Guard — capstone Path B

This is the completed local Flask service, including submission, appeals, content lookup, rate limiting, and persistent request measurements. No hosted model API or API key is used. The capstone extends the same repository and history used in Units 7–8.

## Environment

- Tested target: Windows x64, **Python 3.12.10**. Use Python 3.12 for the exact lock file; do not substitute Python 3.14.
- Install exact direct and transitive versions from `requirements-lock.txt`. The earlier `requirements.txt` remains the broad course compatibility specification.
- Model: `gpt2`, revision `607a30d783dfa663caf39e06633721c8d4cfcd7e`.
- The seven selected model files total **550,959,861 bytes** (about 525.44 MiB) in the existing cache. `prepare_model.py` reports actual sizes on each machine; model weights alone are 548,105,171 bytes. Python packages and runtime memory are additional.
- Model files live in the Hugging Face user cache, not Git. Internet access is needed for dependency installation and the first model download. After setup, normal scoring runs from that cache with model-network access disabled by default.
- This is a local, sequential demonstration server. The Flask development server is intentionally bound to `127.0.0.1`, with debugging, automatic reload, and concurrent request handling disabled by `run_local.py`. It is not a public production deployment.

## Clean-checkout setup (PowerShell)

Clone this same repository into an empty directory. Use the branch containing the capstone, or main after it has been merged.

```powershell
git clone https://github.com/afaheem1021/ai201-project4-provenance-guard-starter-v2026.git
Set-Location ai201-project4-provenance-guard-starter-v2026
git switch capstone-observability
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe prepare_model.py
```

If `py` is not available, use the full path to your installed Python 3.12 interpreter for the venv command. Activation is unnecessary: using `.venv\Scripts\python.exe` explicitly avoids PowerShell activation-policy problems.

## Single startup command

After setup, from the repository root:

```powershell
.\.venv\Scripts\python.exe run_local.py
```

The completed capstone uses one PyTorch inference thread to reduce measured CPU work. The service listens on `http://127.0.0.1:5000`. Stop it with Ctrl+C. It prints the source commit and a new service-run ID, and returns those identifiers in response headers. A first scored request loads the model into this process; running the download command in a separate process does not warm the server.

Optional overrides keep the same startup entry point:

```powershell
.\.venv\Scripts\python.exe run_local.py --port 5050 --log-dir logs\demo-session
```

The documented evaluation invokes this command with an available local port and a new log directory per trial. Reusing a log directory preserves decisions and appeals across restarts. Rate-limit counters are in memory and reset at restart; this is a known prototype limit.

## Send a demonstration request

In another PowerShell terminal:

```powershell
curl.exe -s http://127.0.0.1:5000/health
curl.exe -s -D - -X POST http://127.0.0.1:5000/submit -H "Content-Type: application/json" --data-binary "@results/sample_submit.json"
```

Use the returned `content_id` in an appeal body with a nonempty `reasoning` string. Send it to `POST /appeal`; `GET /content/<id>` then shows `under_review`. An appeal records a request for review, not an actual human adjudication.

| Route | Behavior |
|---|---|
| `POST /ping` | Control route |
| `GET /health` | Process health, detector-loaded state, rate limiting, business-log count |
| `POST /submit` | Validate, score using both signals, persist the decision |
| `POST /appeal` | Append an appeal without overwriting the original |
| `GET /content/<id>` | Original decision plus current appeal status/history |
| `GET /log` | Decision, appeal, and rejection audit history |

Text must contain at least 20 words and at most 10,000 characters. The request limit is 100,000 bytes. Existing submit limits remain 10/minute and 100/day per supplied creator ID (or address fallback). Changing a client-selected ID can evade this prototype limiter.

## Logs and measurement boundaries

- `logs/audit.jsonl`: original business history. Request tracing does not add entries here.
- `logs/requests.jsonl`: one structured completion record per handled HTTP request, including errors and health probes.
- Each response includes `X-Request-ID`, `X-Service-Run-ID`, and `X-Code-Revision` to match it to its record and the tested build.
- Input records contain body SHA-256, byte count, field names and a fixture identifier, rather than raw writing. Oversized bodies are explicitly marked unread; their declared length is recorded. Hashes are identifiers, not an anonymity guarantee.
- Output records contain selected response fields, byte count and SHA-256. Actual request/response bodies are preserved in the nonprivate capstone trial evidence. A hash alone is not a replayable input.
- `duration_ms` covers Flask request handling from the initial hook through response construction, before the completion-log write and network send. `cpu_ms` is process-wide CPU usage over the same boundary. `client_seconds` in trial output measures the complete HTTP exchange, including log-write and transport overhead.
- CPU attribution is meaningful here because requests are sequential. It is not per-request attribution under concurrent traffic. Abrupt process termination and a full/unwritable disk are outside this experiment.

## Repeat the checks and evaluation

Commit criteria before collecting new measurements. Unit tests use controlled responses; the evaluator below uses the actual pinned GPT-2 model except for its two explicitly identified fault processes.

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_service test_observability
.\.venv\Scripts\python.exe capstone_eval.py --label before --output results\capstone\before
```

The evaluator starts and stops only its own server processes. It runs all five criteria three times, saves exact inputs and outputs plus logs, and writes `manifest.json` with settings, environment, model sizes, measurements, and verdicts. The ten performance inputs are generated fixtures, not the student's own writing. Compatibility fixtures retain their original provenance.

After the single diagnosed improvement:

```powershell
.\.venv\Scripts\python.exe capstone_eval.py --label after --output results\capstone\after
```

Existing evidence is never overwritten. To repeat later, choose a new output folder and label, such as `results\capstone\repeat-1`. The committed `before` and `after` folders document the actual capstone sessions. The special `capstone_fault_server.py` is used only by the evaluator and injects detector failures without adding a production fault endpoint.

## Troubleshooting

- A 503 `detector_unavailable` means model loading failed. Run `prepare_model.py` in this same environment, then retry. Model downloads are setup, not warm inference.
- Port already in use: stop your earlier server or choose `--port 5050`. Do not silently measure a different process; check its code-revision and service-run headers.
- A 429 is a rate-limit refusal, not a model result. Separate validation/performance identities from the deliberate same-creator rate-limit block.
- `/health` being 200 means the service can respond; inspect `detector_loaded` to distinguish a running process from a warm model.
- Native Windows uses this local launcher; the old Gunicorn hosting example is not the capstone start command.
