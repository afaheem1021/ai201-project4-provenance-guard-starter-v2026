"""Request completion records, separate from the decision/appeal audit history."""

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone

from flask import g, got_request_exception, request

import config
import detector

_write_lock = threading.Lock()


def code_revision():
    try:
        return subprocess.check_output(
            ['git', '-C', str(config.ROOT), 'rev-parse', 'HEAD'],
            stderr=subprocess.DEVNULL, text=True, timeout=5,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return 'unknown'


def install(app):
    """Install before initializing the rate limiter so rejected requests are timed."""
    service_run_id = str(uuid.uuid4())
    build = code_revision()
    app.config['SERVICE_RUN_ID'] = service_run_id
    app.config['CODE_REVISION'] = build

    @app.before_request
    def start_request():
        g.trace_started = time.perf_counter()
        g.trace_cpu_started = time.process_time()
        g.trace_request_id = str(uuid.uuid4())
        g.trace_model_loaded = detector._model is not None
        g.trace_exception = None
        g.trace_input = {
            'content_type': request.content_type,
            'declared_bytes': request.content_length,
            'fixture_id': request.headers.get('X-Fixture-ID', '')[:120],
            'query': request.query_string.decode('utf-8', errors='replace')[:512],
        }
        if request.content_length is not None and request.content_length > config.MAX_REQUEST_BYTES:
            g.trace_input.update(capture='not_read_oversized', bytes=request.content_length,
                                 sha256=None, reason='request_too_large')
            return
        body = request.get_data(cache=True)
        g.trace_input.update(capture='hashed', bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        try:
            payload = json.loads(body)
        except (ValueError, UnicodeError):
            payload = None
        g.trace_input['json_type'] = type(payload).__name__
        if isinstance(payload, dict):
            g.trace_input['fields'] = sorted(str(key)[:80] for key in payload)[:30]
            text = payload.get('text')
            if isinstance(text, str):
                g.trace_input['text_chars'] = len(text)

    def remember_exception(sender, exception, **extra):
        g.trace_exception = type(exception).__name__

    got_request_exception.connect(remember_exception, sender=app, weak=False)

    @app.after_request
    def finish_request(response):
        if not hasattr(g, 'trace_request_id'):
            return response
        body = response.get_data()
        payload = response.get_json(silent=True)
        public_fields = ('content_id', 'guess', 'confidence', 'model_score', 'style_score',
                         'status', 'error', 'message', 'limit', 'ok', 'detector_loaded')
        output = {'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest(),
                  'content_type': response.content_type}
        if isinstance(payload, dict):
            output['fields'] = {key: payload[key] for key in public_fields if key in payload}
            if isinstance(payload.get('appeals'), list):
                output['appeal_count'] = len(payload['appeals'])
        code = payload.get('error') if isinstance(payload, dict) else None
        if response.status_code >= 400 and not code:
            code = 'internal_server_error' if response.status_code == 500 else f'http_{response.status_code}'
        error_stage = None
        if code:
            error_stage = ('detector' if code == 'detector_unavailable' or g.trace_exception else
                           'rate_limiter' if code == 'rate_limited' else 'request_handling')
        entry = {
            'schema_version': 1, 'event': 'request_completed',
            'timestamp': datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
            'service_run_id': service_run_id, 'code_revision': build, 'pid': os.getpid(),
            'request_id': g.trace_request_id, 'method': request.method, 'route': request.path,
            'input': g.trace_input, 'http_status': response.status_code, 'output': output,
            'duration_ms': round((time.perf_counter() - g.trace_started) * 1000, 6),
            'cpu_ms': round((time.process_time() - g.trace_cpu_started) * 1000, 6),
            'model_loaded_at_start': g.trace_model_loaded,
            'torch_threads': sys.modules['torch'].get_num_threads() if 'torch' in sys.modules else None,
            'error_code': code, 'error_stage': error_stage, 'exception_type': g.trace_exception,
        }
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        with _write_lock:
            with (config.LOG_DIR / 'requests.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(entry, ensure_ascii=False, allow_nan=False) + '\n')
        response.headers['X-Request-ID'] = g.trace_request_id
        response.headers['X-Service-Run-ID'] = service_run_id
        response.headers['X-Code-Revision'] = build
        return response
