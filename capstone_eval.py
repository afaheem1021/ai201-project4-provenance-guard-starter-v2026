"""Three real local-service trials of the five frozen capstone criteria."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import socket
import statistics
import subprocess
import sys
import time

import requests

ROOT = Path(__file__).resolve().parent


def sha(body):
    return hashlib.sha256(body).hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def lines(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()] if path.exists() else []


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


class Server:
    def __init__(self, folder, name, fault=None):
        self.folder = folder
        self.name = name
        self.fault = fault
        self.process = None
        self.log_dir = folder / 'logs'

    def __enter__(self):
        self.folder.mkdir(parents=True, exist_ok=True)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        self.url = f'http://127.0.0.1:{port}'
        script = 'capstone_fault_server.py' if self.fault else 'run_local.py'
        self.command = [sys.executable, script, '--port', str(port), '--log-dir', str(self.log_dir)]
        if self.fault:
            self.command += ['--fault', self.fault]
        env = dict(os.environ, AI201_MODEL_OFFLINE='1', HF_HUB_OFFLINE='1', AI201_RATE_LIMITS='1',
                   AI201_DETECTOR_MODEL='gpt2', AI201_DETECTOR_REVISION='607a30d783dfa663caf39e06633721c8d4cfcd7e')
        self.stream = (self.folder / f'{self.name}_server.txt').open('w', encoding='utf-8')
        started = time.perf_counter()
        self.process = subprocess.Popen(self.command, cwd=ROOT, env=env, stdout=self.stream, stderr=subprocess.STDOUT,
                                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        try:
            while time.perf_counter() - started < 45:
                if self.process.poll() is not None:
                    raise RuntimeError(f'Server exited: {self.folder}')
                try:
                    health = requests.get(self.url+'/health', timeout=1)
                    if health.status_code == 200 and health.headers.get('X-Code-Revision') == git('rev-parse', 'HEAD'):
                        self.startup_seconds = time.perf_counter()-started
                        self.run_id = health.headers['X-Service-Run-ID']
                        return self
                except requests.RequestException:
                    pass
                time.sleep(0.1)
            raise TimeoutError('No verified service response within 45 seconds')
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *unused):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=10)
        self.stream.close()

    def events(self):
        return lines(self.log_dir / 'audit.jsonl')

    def send(self, name, method, route, payload=None, raw=None, expected=200):
        body = raw if raw is not None else (json.dumps(payload, ensure_ascii=False).encode() if payload is not None else b'')
        before_events = self.events()
        headers = {'Content-Type': 'application/json', 'X-Fixture-ID': name}
        started = time.perf_counter()
        response = requests.request(method, self.url+route, data=body, headers=headers, timeout=90)
        elapsed = time.perf_counter()-started
        request_id = response.headers.get('X-Request-ID')
        records = [r for r in lines(self.log_dir / 'requests.jsonl') if r['request_id'] == request_id]
        try:
            parsed = response.json()
        except ValueError:
            parsed = None
        delta = self.events()[len(before_events):]
        item = {
            'case': name, 'method': method, 'route': route, 'expected_status': expected,
            'request': {'body_utf8': body.decode('utf-8'), 'sha256': sha(body), 'bytes': len(body), 'headers': headers},
            'response': {'status': response.status_code, 'body_utf8': response.text, 'json': parsed,
                         'sha256': sha(response.content), 'request_id': request_id,
                         'service_run_id': response.headers.get('X-Service-Run-ID')},
            'client_seconds': elapsed, 'completion_records': records,
            'new_business_events': [e for e in delta if e.get('status') == 'decided' or e.get('event') == 'appeal'],
        }
        return item


def trace_ok(item):
    records = item['completion_records']
    if len(records) != 1:
        return False
    record = records[0]
    stamp = datetime.fromisoformat(record['timestamp'])
    normal_input = record['input']['capture'] == 'hashed'
    input_ok = (record['input']['sha256'] == item['request']['sha256'] and record['input']['bytes'] == item['request']['bytes']) if normal_input else (
        item['request']['bytes'] > 100000 and record['input']['capture'] == 'not_read_oversized'
        and record['input']['declared_bytes'] == item['request']['bytes'] and record['input']['reason'] == 'request_too_large')
    return bool(stamp.utcoffset().total_seconds() == 0 and record['service_run_id'] == item['response']['service_run_id']
                and record['request_id'] == item['response']['request_id'] and record['method'] == item['method']
                and record['route'] == item['route'] and record['http_status'] == item['response']['status']
                and record['output']['sha256'] == item['response']['sha256'] and input_ok
                and all(isinstance(record[key], (float, int)) and math.isfinite(record[key]) and record[key] >= 0
                        for key in ['duration_ms', 'cpu_ms']))


def failure_ok(item):
    return (trace_ok(item) and item['response']['status'] == item['expected_status']
            and bool(item['completion_records'][0]['error_code']) and not item['new_business_events'])


def trial(number, out, fixtures, golden):
    folder = out / f'trial_{number}'
    folder.mkdir(parents=True, exist_ok=True)
    matrix, extra, failures = [], [], []
    text, reason = fixtures['trace_text'], fixtures['appeal_reason']
    normal_folder = folder / 'normal'
    with Server(normal_folder, 'initial') as server:
        startup = {'command': server.command, 'cwd': str(ROOT), 'seconds': server.startup_seconds, 'service_run_id': server.run_id}
        first = server.send('trace_valid', 'POST', '/submit', {'text': text, 'creator_id': 'trace_writer'})
        matrix.append(first)
        cid = first['response']['json']['content_id']
        original = next(e.copy() for e in server.events() if e.get('content_id') == cid and e.get('status') == 'decided')
        matrix.append(server.send('trace_appeal', 'POST', '/appeal', {'content_id': cid, 'reasoning': reason}))
        matrix.append(server.send('trace_content', 'GET', '/content/'+cid))
        invalid = [
            ('missing_text', 'POST', '/submit', {'creator_id': 'bad_missing'}, None, 400),
            ('malformed_json', 'POST', '/submit', None, b'{broken', 400),
            ('oversized', 'POST', '/submit', None, b'x'*100001, 413),
            ('unknown_appeal', 'POST', '/appeal', {'content_id': 'no-such-content', 'reasoning': reason}, None, 404),
            ('unknown_content', 'GET', '/content/no-such-content', None, None, 404),
            ('unknown_route', 'GET', '/no-such-route', None, None, 404),
        ]
        for name, method, route, payload, raw, status in invalid:
            item = server.send(name, method, route, payload, raw, status)
            matrix.append(item)
            failures.append(item)
        block_start = time.perf_counter()
        for i in range(11):
            item = server.send(f'rate_{i+1:02}', 'POST', '/submit', {'text': text, 'creator_id': 'rate_writer'}, expected=200 if i < 10 else 429)
            matrix.append(item)
            if i == 10:
                failures.append(item)
        rate_seconds = time.perf_counter()-block_start
        perf = [server.send(fixture['id'], 'POST', '/submit', {'text': fixture['text'], 'creator_id': fixture['id']}) for fixture in fixtures['performance']]
        extra.extend(perf)
        calibration = []
        for fixture in fixtures['calibration']:
            item = server.send('calibration_'+fixture['name'], 'POST', '/submit', {'text': fixture['text'], 'creator_id': 'cal_'+fixture['name']})
            actual = item['response']['json'] or {}
            expected = golden[fixture['name']]
            calibration.append({'name': fixture['name'], 'expected': expected, 'actual': actual,
                                'passed': item['response']['status'] == 200 and actual.get('guess') == expected['guess']
                                and abs(actual.get('confidence', -10)-expected['combined_score']) <= .001})
            extra.append(item)
        repeat = server.send('repeat_appeal', 'POST', '/appeal', {'content_id': cid, 'reasoning': reason})
        extra.append(repeat)
        before_read = server.events()
        lookup = server.send('content_after_repeat', 'GET', '/content/'+cid)
        log_read = server.send('read_business_log', 'GET', '/log')
        extra.extend([lookup, log_read])
        audit_unchanged_by_reads = before_read == server.events()
        current = lookup['response']['json']
        original_after = next(e for e in server.events() if e.get('content_id') == cid and e.get('status') == 'decided')
        appeals = [e for e in server.events() if e.get('content_id') == cid and e.get('event') == 'appeal']
        workflow = (original == original_after and len(appeals) == 2 and current['status'] == 'under_review'
                    and len(current['appeals']) == 2 and repeat['response']['status'] == 200
                    and len(repeat['new_business_events']) == 1 and len(matrix[1]['new_business_events']) == 1
                    and all(e['reasoning'] == reason and e['creator_id'] == 'trace_writer' for e in appeals))
    with Server(normal_folder, 'restart') as restarted:
        persisted = restarted.send('persisted_after_restart', 'GET', '/content/'+cid)
        extra.append(persisted)
        workflow = workflow and persisted['response']['json'] == current
    fault_health = []
    for fault, expected in [('unavailable', 503), ('unexpected', 500)]:
        with Server(folder/fault, fault, fault=fault) as fault_server:
            item = fault_server.send(fault, 'POST', '/submit', {'text': text, 'creator_id': 'fault_writer'}, expected=expected)
            matrix.append(item)
            failures.append(item)
            health = fault_server.send(fault+'_health_after', 'GET', '/health')
            extra.append(health)
            fault_health.append(health['response']['status'] == 200 and health['response']['service_run_id'] == item['response']['service_run_id'])
    elapsed = [item['client_seconds'] for item in perf]
    cpu = [item['completion_records'][0]['cpu_ms']/1000 if len(item['completion_records']) == 1 else None for item in perf]
    timing_valid = all(item['response']['status'] == 200 and trace_ok(item) for item in perf)
    mean_cpu = statistics.mean(cpu) if all(value is not None for value in cpu) else None
    criteria = {
        '1': {'met': startup['seconds'] <= 15 and first['response']['status'] == 200 and first['client_seconds'] <= 30,
              'startup_seconds': startup['seconds'], 'cold_submit_seconds': first['client_seconds']},
        '2': {'met': len(matrix) == 22 and all(trace_ok(item) for item in matrix)
              and len(set(item['response']['request_id'] for item in matrix)) == 22 and audit_unchanged_by_reads,
              'complete_records': sum(trace_ok(item) for item in matrix), 'total': len(matrix), 'audit_unchanged_by_reads': audit_unchanged_by_reads},
        '3': {'met': len(failures) == 9 and all(failure_ok(item) for item in failures) and all(fault_health) and rate_seconds < 60
              and all(item['response']['status'] == 200 for item in matrix[9:19]),
              'failures_passed': sum(failure_ok(item) for item in failures), 'total': len(failures),
              'fault_processes_survived': all(fault_health), 'rate_block_seconds': rate_seconds},
        '4': {'met': timing_valid and sum(value <= 2 for value in elapsed) >= 9 and mean_cpu is not None and mean_cpu <= 5,
              'under_two_seconds': sum(value <= 2 for value in elapsed), 'count': len(perf),
              'mean_elapsed_seconds': statistics.mean(elapsed), 'p95_elapsed_seconds': sorted(elapsed)[math.ceil(.95*len(elapsed))-1],
              'mean_cpu_seconds': mean_cpu, 'elapsed_seconds': elapsed, 'cpu_seconds': cpu},
        '5': {'met': all(item['passed'] for item in calibration) and workflow,
              'calibration_passed': sum(item['passed'] for item in calibration), 'total': len(calibration),
              'appeals_and_restart_preserved': bool(workflow)},
    }
    result = {'trial': number, 'produced_by': 'capstone_eval.py::trial', 'startup': startup,
              'criteria': criteria, 'trace_matrix': matrix, 'other_requests': extra, 'calibration': calibration}
    write_json(folder/'trial.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit('Use a new empty output folder; existing evidence is never overwritten.')
    out.mkdir(parents=True, exist_ok=True)
    fixtures = json.loads((ROOT/'data/capstone_fixtures.json').read_text(encoding='utf-8'))
    old = lines(ROOT/'results/calibration.jsonl')
    golden = {row['name']: row for row in old}
    from prepare_model import manifest
    environment = {'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
                   'processor': platform.processor(), 'logical_cpus': os.cpu_count(),
                   'packages': {dist.metadata['Name']: dist.version for dist in importlib.metadata.distributions()},
                   'model': manifest(local_only=True), 'cpu_threads_override': os.getenv('AI201_CPU_THREADS')}
    run = {'label': args.label, 'timestamp': datetime.now(timezone.utc).isoformat(), 'code_revision': git('rev-parse', 'HEAD'),
           'criteria_sha256': sha((ROOT/'criteria.md').read_bytes()), 'fixtures_sha256': sha((ROOT/'data/capstone_fixtures.json').read_bytes()),
           'initial_git_status': git('status', '--porcelain'), 'environment': environment, 'trials': []}
    write_json(out/'manifest.json', run)
    for number in range(1, 4):
        print(f'{args.label}: starting trial {number}', flush=True)
        try:
            result = trial(number, out, fixtures, golden)
        except Exception as exc:
            write_json(out/f'trial_{number}'/'fatal_error.json', {'type': type(exc).__name__, 'message': str(exc)})
            raise
        summary = {'trial': number, 'criteria': result['criteria']}
        run['trials'].append(summary)
        write_json(out/'manifest.json', run)
        print(json.dumps(summary), flush=True)
    run['verdicts'] = {str(i): 'MET' if all(t['criteria'][str(i)]['met'] for t in run['trials']) else 'MISSED' for i in range(1, 6)}
    write_json(out/'manifest.json', run)
    print(json.dumps(run['verdicts']), flush=True)


if __name__ == '__main__':
    main()
