import importlib.util
import unittest
from unittest.mock import patch
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
spec = importlib.util.spec_from_file_location('text_redact', Path(__file__).parents[1] / 'scripts/text_redact.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class TextTests(unittest.TestCase):
    def test_patterns_and_literals(self):
        text = 'Alice Smith: alice@example.com; +1 202 555 0198; password=not-a-real-secret'
        output, count = m.redact(text, m.pattern_spans(text, ['Alice Smith']))
        for private in ['Alice Smith', 'alice@example.com', '202', 'not-a-real-secret']:
            self.assertNotIn(private, output)
        self.assertGreater(count, 0)
    def test_unicode(self):
        text = 'Привет, Анна. café@example.org'
        output, _ = m.redact(text, m.pattern_spans(text, ['Анна']))
        self.assertEqual(output, 'Привет, [REDACTED]. [REDACTED]')
    def test_overlap(self):
        self.assertEqual(m.redact('abcdef', [(1,4),(2,5)])[0], 'a[REDACTED]f')
    def test_invalid_offsets(self):
        for spans in [[(-1,2)],[(1,20)],[(2,1)]]:
            with self.assertRaises(ValueError):
                m.redact('abc', spans)
    def test_natural_language_password(self):
        output, _ = m.redact('My password is ExampleSecret123.', m.pattern_spans('My password is ExampleSecret123.'))
        self.assertNotIn('ExampleSecret123', output)
    def test_clean(self):
        self.assertEqual(m.redact('A sunny day.', []), ('A sunny day.', 0))
    def test_no_mapping(self):
        self.assertEqual(m.redact('Alice Alice', [(0,5),(6,11)]), ('[REDACTED]', 1))

    def test_project_file_id_is_not_a_pattern_phone(self):
        text = ('The project file is 4829-1037-5581. Launch September 18, 2026. '
                'Call +1 (415) 555-0124.')
        output, _ = m.redact(text, m.detect_spans(text, engine='patterns'))
        self.assertIn('4829-1037-5581', output)
        self.assertIn('September 18, 2026', output)
        self.assertNotIn('+1 (415) 555-0124', output)
        # Account predictions are not blanket-suppressed just because their
        # numeric formatting also occurs in public project IDs.
        self.assertEqual(m.entity_spans([dict(entity='S-account_number', start=0,
                                             end=14, score=.99)]), [(0, 14)])

    def test_level_preservation(self):
        text = ('OpenAI project Aurora ships on 2026-09-14 with 42 examples. '
                'Read https://docs.python.org/3/. Contact café@example.org.')
        for level in m.LEVELS:
            output, _ = m.redact(text, m.detect_spans(text, level, engine='patterns'))
            self.assertIn('OpenAI project Aurora ships on', output)
            self.assertNotIn('café@example.org', output)
            if level == 'high':
                self.assertNotIn('https://docs.python.org/3/', output)
                self.assertNotIn('42', output)
            else:
                self.assertIn('2026-09-14 with 42 examples', output)
                self.assertIn('https://docs.python.org/3/.', output)

    def test_exact_unicode_offsets_and_local_paths(self):
        text = ('🌿 Привет café@example.org; /Users/Анна/Documents/report.txt; '
                '/home/alice/project/readme.md; C:\\Users\\Zoë\\project\\readme.md')
        expected = ['café@example.org', 'Анна', 'alice', 'Zoë']
        spans = m.detect_spans(text, engine='patterns')
        self.assertEqual(spans, [(text.index(v), text.index(v) + len(v)) for v in expected])
        output, _ = m.redact(text, spans)
        self.assertIn('/Users/[REDACTED]/Documents/report.txt', output)
        self.assertIn('/home/[REDACTED]/project/readme.md', output)
        self.assertIn('C:\\Users\\[REDACTED]\\project\\readme.md', output)

    def test_bioes_expansion_before_threshold(self):
        entities = [
            dict(entity='B-private_person', start=0, end=5, score=.97),
            dict(entity='E-private_person', start=6, end=11, score=.2),
            dict(entity='B-private_email', start=13, end=16, score=.3),
            dict(entity='I-private_email', start=16, end=20, score=.99),
            dict(entity='E-private_email', start=20, end=25, score=.4),
        ]
        self.assertEqual(m.entity_spans(entities), [(0, 11), (13, 25)])

    def test_model_categories_and_confidence_levels(self):
        entities = [dict(entity='S-' + category, start=i * 10, end=i * 10 + 5, score=score)
                    for i, (category, score) in enumerate([
                        ('private_person', .9), ('private_person', .6),
                        ('private_date', .9), ('private_url', .8), ('private_address', .2)])]
        self.assertEqual(m.entity_spans(entities, 'low'), [(0, 5)])
        self.assertEqual(m.entity_spans(entities, 'medium'), [(0, 5), (10, 15), (20, 25), (30, 35)])
        self.assertEqual(m.entity_spans(entities, 'high'), [(i * 10, i * 10 + 5) for i in range(5)])

    def test_o_and_new_b_break_entities(self):
        entities = [dict(entity=label, start=i * 2, end=i * 2 + 1, score=score)
                    for i, (label, score) in enumerate([
                        ('B-private_person', .99), ('O', .99),
                        ('E-private_person', .1), ('B-private_person', .1),
                        ('E-private_person', .2)])]
        self.assertEqual(m.entity_spans(entities), [(0, 1)])

    def test_detect_forwards_level_and_requires_scanner(self):
        with patch.object(m, 'model_spans', return_value=[(0, 5)]) as model:
            self.assertEqual(m.detect_spans('Alice works.', 'medium', True), [(0, 5)])
            model.assert_called_once_with('Alice works.', True, 'medium')
        with patch('secret_scan.shutil.which', return_value=None):
            for level in m.LEVELS:
                with self.assertRaises(RuntimeError):
                    m.detect_spans('No secrets.', level, engine='patterns')
        with self.assertRaises(ValueError):
            m.detect_spans('x', level='extreme')
        with self.assertRaises(ValueError):
            m.detect_spans('x', engine='hosted')

    def test_model_cannot_swallow_secret_labels_or_path_syntax(self):
        examples = [('API key: "private-value".', 'API key: "[REDACTED]".'),
                    ('Bearer AbcDef1234567890.', 'Bearer [REDACTED].'),
                    ('/Users/alice/Documents/2026.txt', '/Users/[REDACTED]/Documents/2026.txt')]
        for text, expected in examples:
            with patch.object(m, 'model_spans', return_value=[(0, len(text))]):
                for level in m.LEVELS:
                    self.assertEqual(m.redact(text, m.detect_spans(text, level))[0], expected)

    def test_window_tail_is_not_truncated(self):
        class Tokenizer:
            def __call__(self, text, **kwargs):
                return {'offset_mapping': [(i, i + 1) for i in range(len(text))]}
        calls = []
        def classifier(text, **kwargs):
            calls.append(len(text))
            start = text.find('Alice')
            return [] if start < 0 else [dict(entity='S-private_person', start=start, end=start + 5, score=.99)]
        text = '.' * 1900 + 'Alice'
        with patch.object(m, '_classifier', return_value=(Tokenizer(), classifier)):
            self.assertIn((1900, 1905), m.model_spans(text, offline=True))
        self.assertGreater(len(calls), 1)
        self.assertLessEqual(max(calls), 1024)

    @unittest.skipUnless(os.environ.get('ANONYMIZER_MODEL_TEST') == '1', 'opt-in cached local model inference')
    def test_cached_model_fixture(self):
        text = ('🌿 Hello, my name is Alice Smith. Email: alice@example.com. '
                'OpenAI project Aurora launches on 2026-09-14. '
                'Read https://docs.python.org/3/. My birthday is June 5, 1990. '
                'API key: "short-but-private". My password is ExampleSecret123. '
                'File: /Users/alice/Documents/report.txt')
        results = {level: m.redact(text, m.detect_spans(text, level, offline=True))[0]
                   for level in m.LEVELS}
        for output in results.values():
            self.assertNotIn('Alice Smith', output)
            self.assertNotIn('alice@example.com', output)
            self.assertNotIn('short-but-private', output)
            self.assertNotIn('ExampleSecret123', output)
            self.assertIn('OpenAI project Aurora launches on', output)
            self.assertIn('API key: "[REDACTED]".', output)
            self.assertIn('My password is [REDACTED].', output)
            self.assertIn('/Users/[REDACTED]/Documents/report.txt', output)
        self.assertIn('2026-09-14.', results['low'])
        self.assertIn('June 5, 1990.', results['low'])
        self.assertNotIn('June 5, 1990', results['medium'])
        self.assertIn('https://docs.python.org/3/.', results['low'])
        self.assertNotIn('https://docs.python.org/3/', results['high'])

if __name__ == '__main__':
    unittest.main()
