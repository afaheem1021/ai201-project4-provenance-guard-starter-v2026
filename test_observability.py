"""Checks for request evidence; controlled model responses never count as performance evidence."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app as service
import audit
import config
import detector

TEXT = 'This paragraph has enough words to be a valid submission. It exists to check the request log and preserve the original decision history.'


class ObservabilityTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        for name, value in [('LOG_DIR', self.root), ('AUDIT_LOG', self.root / 'audit.jsonl')]:
            p = patch.object(config, name, value)
            p.start()
            self.addCleanup(p.stop)
        if hasattr(service.limiter, 'enabled'):
            previous = service.limiter.enabled
            service.limiter.enabled = False
            self.addCleanup(setattr, service.limiter, 'enabled', previous)
        p = patch.object(detector, 'model_signal', return_value=0.92)
        self.model = p.start()
        self.addCleanup(p.stop)
        self.client = service.app.test_client()

    def records(self):
        return [json.loads(line) for line in (self.root / 'requests.jsonl').read_text(encoding='utf-8').splitlines()]

    def assert_record(self, response):
        matches = [r for r in self.records() if r['request_id'] == response.headers['X-Request-ID']]
        self.assertEqual(len(matches), 1)
        record = matches[0]
        self.assertEqual(record['http_status'], response.status_code)
        self.assertEqual(record['output']['sha256'], hashlib.sha256(response.data).hexdigest())
        self.assertGreaterEqual(record['duration_ms'], 0)
        self.assertGreaterEqual(record['cpu_ms'], 0)
        return record

    def test_success_and_reads_leave_business_history_unchanged(self):
        body = json.dumps({'text': TEXT, 'creator_id': 'fixture'}).encode()
        response = self.client.post('/submit', data=body, content_type='application/json')
        record = self.assert_record(response)
        self.assertEqual(record['input']['sha256'], hashlib.sha256(body).hexdigest())
        self.assertNotIn(TEXT, json.dumps(record))
        before = audit.read_entries()
        self.assert_record(self.client.get('/log'))
        self.assertEqual(audit.read_entries(), before)

    def test_invalid_appeal_and_unknown_route_are_traced(self):
        for response in [self.client.post('/appeal', json={}), self.client.get('/missing')]:
            self.assertTrue(self.assert_record(response)['error_code'])
        self.assertEqual(audit.read_entries(), [])

    def test_oversized_body_is_not_copied_or_parsed(self):
        response = self.client.post('/submit', data=b'x' * 100001, content_type='application/json')
        self.assertEqual(response.status_code, 413)
        self.assertEqual(self.assert_record(response)['input']['capture'], 'not_read_oversized')
        self.model.assert_not_called()

    def test_unexpected_exception_is_recorded_once_and_service_survives(self):
        self.model.side_effect = RuntimeError('controlled failure')
        with patch.dict(service.app.config, {'TESTING': False, 'PROPAGATE_EXCEPTIONS': False}):
            response = self.client.post('/submit', json={'text': TEXT, 'creator_id': 'fault'})
        self.assertEqual(response.status_code, 500)
        record = self.assert_record(response)
        self.assertEqual(record['exception_type'], 'RuntimeError')
        self.assertEqual(record['error_stage'], 'detector')
        self.assertEqual(audit.read_entries(), [])
        self.assertEqual(self.client.get('/health').status_code, 200)


if __name__ == '__main__':
    unittest.main()
