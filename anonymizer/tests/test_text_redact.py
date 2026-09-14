import importlib.util
import unittest
from pathlib import Path
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

if __name__ == '__main__':
    unittest.main()
