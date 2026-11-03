"""Contract and regression checks; no model downloads or real audit mutations."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app as service
import audit
import config
import detector
import scoring
import stylometry


class ScoringTests(unittest.TestCase):
    def test_every_label_boundary_and_grid(self):
        for i in range(1001):
            score = i / 1000
            guess, label = scoring.score_to_label(score)
            expected = 'human' if score <= .25 else 'ai' if score >= .80 else 'unsure'
            self.assertEqual(guess, expected)
            self.assertTrue(label)
        self.assertNotEqual(scoring.score_to_label(.51), scoring.score_to_label(.95))

    def test_strong_disagreement_stays_unsure(self):
        for a in range(101):
            for b in range(101):
                x, y = a/100, b/100
                score = scoring.combine_signals(x, y)
                self.assertTrue(0 <= score <= 1)
                if abs(x-y) >= .50:
                    self.assertEqual(scoring.score_to_label(score)[0], 'unsure')

    def test_weighting_and_invalid_numbers(self):
        self.assertAlmostEqual(scoring.combine_signals(.92, .8), .884)
        for value in (-.1, 1.1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                scoring.combine_signals(value, .5)
            with self.assertRaises(ValueError):
                scoring.score_to_label(value)

    def test_style_measures_have_known_values(self):
        self.assertAlmostEqual(stylometry.sentence_length_spread('One two. Three four five six.'), 1/3)
        self.assertEqual(stylometry.type_token_ratio('Cat cat dog DOG'), .5)
        self.assertEqual(stylometry.punctuation_density('Hi!'), 1/3)
        self.assertEqual(stylometry.words('Café naïve café'), ['café', 'naïve', 'café'])
        self.assertEqual(stylometry.punctuation_density('—'), 1)

    def test_style_empty_short_and_varied(self):
        for text in ('', '!', 'One sentence only.', '猫'):
            self.assertEqual(stylometry.style_signal(text), .5)
        from calibration import AI_TEXT, ODD_AI
        self.assertGreater(stylometry.style_signal(AI_TEXT), stylometry.style_signal(ODD_AI))


class EndpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        for name, value in [('LOG_DIR', root), ('AUDIT_LOG', root/'audit.jsonl')]:
            patcher = patch.object(config, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.client = service.app.test_client()
        self.model_patch = patch.object(detector, 'model_signal', return_value=.92)
        self.model = self.model_patch.start()
        self.addCleanup(self.model_patch.stop)

    def submit(self):
        response = self.client.post('/submit', json={'text': 'A sample with enough words to score.', 'creator_id': 'test-writer'})
        self.assertEqual(response.status_code, 200)
        return response.get_json()

    def test_submission_and_persistent_status(self):
        from uuid import UUID
        first, second = self.submit(), self.submit()
        UUID(first['content_id'])
        self.assertNotEqual(first['content_id'], second['content_id'])
        self.assertEqual(len(audit.read_entries()), 2)
        log = audit.read_entries()[0]
        self.assertEqual(log['combined_score'], first['confidence'])
        for field in ('model_score', 'style_score', 'guess', 'label', 'status'):
            self.assertEqual(log[field], first[field])
        self.assertIn('timestamp', log)
        self.assertEqual(service.app.test_client().get('/content/'+first['content_id']).get_json()['status'], 'decided')

    def test_bad_submission_matrix_never_calls_model(self):
        cases = [[], {}, {'text': None, 'creator_id': 'x'}, {'text': 12, 'creator_id': 'x'},
                 {'text': '  ', 'creator_id': 'x'}, {'text': 'abc'},
                 {'text': 'abc', 'creator_id': ''}, {'text': 'abc', 'creator_id': 'x'*101}]
        for body in cases:
            with self.subTest(body=body):
                response = self.client.post('/submit', json=body)
                self.assertEqual(response.status_code, 400)
                self.assertIn('error', response.get_json())
                self.assertIn('message', response.get_json())
        response = self.client.post('/submit', data='{broken', content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.model.assert_not_called()
        self.assertEqual(audit.read_entries(), [])

    def test_size_limits_and_boundary(self):
        response = self.client.post('/submit', json={'text': 'x'*10001, 'creator_id': 'x'})
        self.assertEqual(response.status_code, 413)
        response = self.client.post('/submit', data='x'*100001, content_type='application/json')
        self.assertEqual(response.status_code, 413)
        self.assertIn('message', response.get_json())
        self.model.assert_not_called()
        response = self.client.post('/submit', json={'text': 'x'*10000, 'creator_id': 'x'*100})
        self.assertEqual(response.status_code, 200)

    def test_detector_failure_is_json_not_a_fake_decision(self):
        for exc, status in [(detector.DetectorUnavailable('offline'), 503), (ValueError('short'), 400)]:
            self.model.side_effect = exc
            response = self.client.post('/submit', json={'text': 'x', 'creator_id': 'x'})
            self.assertEqual(response.status_code, status)
            self.assertIn('error', response.get_json())
        self.assertEqual(audit.read_entries(), [])

    def test_five_appeals_preserve_decisions_and_reasoning(self):
        for _ in range(5):
            content = self.submit()
            before = audit.entries_for(content['content_id'])[0].copy()
            count = len(audit.read_entries())
            self.model.reset_mock()
            response = self.client.post('/appeal', json={'content_id': content['content_id'], 'reasoning': '  My draft history explains my process.  '})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()['status'], 'under_review')
            self.model.assert_not_called()
            self.assertEqual(len(audit.read_entries()), count+1)
            entries = audit.entries_for(content['content_id'])
            self.assertEqual(entries[0], before)
            self.assertEqual(entries[1]['reasoning'], '  My draft history explains my process.  ')
            self.assertEqual(entries[1]['creator_id'], 'test-writer')
            self.assertEqual(self.client.get('/content/'+content['content_id']).get_json()['status'], 'under_review')
        response = self.client.post('/appeal', json={'content_id': content['content_id'], 'reasoning': 'More context.'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(audit.entries_for(content['content_id'])), 3)

    def test_invalid_appeals_do_not_mutate_history(self):
        content = self.submit()
        before = audit.read_entries()
        for payload in ([], {}, {'content_id': content['content_id']},
                        {'content_id': content['content_id'], 'reasoning': ' '},
                        {'content_id': content['content_id'], 'reasoning': 'x'*2001},
                        {'content_id': 5, 'reasoning': 'Reason'}):
            self.assertEqual(self.client.post('/appeal', json=payload).status_code, 400)
        self.assertEqual(self.client.post('/appeal', json={'content_id': 'missing', 'reasoning': 'Reason'}).status_code, 404)
        self.assertEqual(self.client.get('/content/missing').status_code, 404)
        self.assertEqual(audit.read_entries(), before)

    def test_ping_health_log(self):
        self.assertTrue(self.client.post('/ping', json={'message':'hello'}).get_json()['ok'])
        self.assertTrue(self.client.get('/health').get_json()['ok'])
        self.submit()
        self.assertEqual(self.client.get('/log?limit=1').get_json()['count'], 1)


if __name__ == '__main__':
    unittest.main()
