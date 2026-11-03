"""Capture real curl requests against python app.py; appends to the audit log."""

import json
import subprocess
from pathlib import Path

from calibration import FIXTURES

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results'
BASE = 'http://127.0.0.1:5000'


def call(method, path, body=None):
    command = ['curl.exe', '--silent', '--show-error', '--max-time', '120',
               '--request', method, BASE+path, '--write-out', '\n%{http_code}']
    kwargs = {}
    if body is not None:
        command += ['--header', 'Content-Type: application/json', '--data-binary', '@-']
        kwargs['input'] = json.dumps(body).encode('utf-8')
    output = subprocess.run(command, capture_output=True, check=True, **kwargs).stdout.decode('utf-8')
    raw, status = output.rsplit('\n', 1)
    return {'method': method, 'path': path, 'request': body,
            'status_code': int(status), 'response': json.loads(raw)}


def save(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def main():
    OUT.mkdir(exist_ok=True)
    assert call('POST', '/ping', {'message': 'hello'})['response']['ok']
    runs = []
    for index, fixture in enumerate(FIXTURES):
        submit = call('POST', '/submit', {'text': fixture['text'], 'creator_id': 'live-'+fixture['name']})
        assert submit['status_code'] == 200, submit
        content_id = submit['response']['content_id']
        record = {'fixture': fixture['name'], 'origin': fixture['origin'], 'submit': submit}
        if index < 5:
            reasoning = 'This is a workflow demonstration. Please review the source and drafting history before drawing a conclusion about authorship.'
            appeal = call('POST', '/appeal', {'content_id': content_id, 'reasoning': reasoning})
            assert appeal['status_code'] == 200
            assert appeal['response']['status'] == 'under_review'
            content = call('GET', '/content/'+content_id)
            assert content['response']['status'] == 'under_review'
            assert content['response']['appeals'][0]['reasoning'] == reasoning
            assert content['response']['guess'] == submit['response']['guess']
            log = call('GET', '/log?limit=2')
            assert log['response']['entries'][0]['status'] == 'decided'
            assert log['response']['entries'][1]['status'] == 'under_review'
            record.update(appeal=appeal, content=content, log=log)
        runs.append(record)
        print(f"{fixture['name']}: {submit['response']['guess']} {submit['response']['confidence']}", flush=True)
    assert {r['submit']['response']['guess'] for r in runs} == {'ai','human','unsure'}
    first = runs[0]
    save('sample_submit.json', first['submit']['request'])
    save('sample_appeal.json', first['appeal']['request'])
    save('live_run.json', runs)
    health = call('GET', '/health')
    assert health['response']['detector_loaded'] is True
    save('health.json', health)
    print('Live checks passed: six submissions, all three labels, five recorded appeals, current status, original decisions, and cached model.')


if __name__ == '__main__':
    main()
