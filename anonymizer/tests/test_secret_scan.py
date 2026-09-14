import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from unittest.mock import patch
from secret_scan import secret_spans
from text_redact import redact, detect_spans, LEVELS

# Entirely synthetic, constructed examples. Never validate against provider APIs.
PAYLOAD = 'A1b2C3d4E5f6G7h8I9j0K1l2M3n4P5q6'
CASES = {
    'openai_project': 'sk-' + 'proj-' + PAYLOAD * 3,
    'anthropic': 'sk-' + 'ant-api03-' + PAYLOAD * 3,
    'replicate': 'r8_' + PAYLOAD + 'ABCDE123',
    'huggingface': 'hf_' + PAYLOAD,
    'github_classic': 'ghp_' + PAYLOAD + 'A1b2',
    'github_finegrained': 'github_' + 'pat_' + PAYLOAD * 2,
    'google': 'AIza' + PAYLOAD + 'A1b',
    'aws_access': 'AKIA' + 'QWERTYUIOPASDFGH',
    'stripe': 'sk_' + 'live_' + PAYLOAD,
    'slack': 'xoxb-' + '123456789012-123456789012-' + PAYLOAD[:24],
    'sendgrid': 'SG.' + PAYLOAD[:22] + '.' + (PAYLOAD * 2)[:43],
    'npm': 'npm_' + PAYLOAD + 'A1b2',
    'bearer': 'Bearer ' + PAYLOAD,
    'named_short': 'CUSTOM_API_KEY="short-but-private"',
    'named_spaces': 'client_secret="private value with spaces"',
    'natural_password': 'My password is SomethingPrivate123',
    'private_key': '-----BEGIN RSA PRIVATE KEY-----\n' + PAYLOAD * 3 + '\n-----END RSA PRIVATE KEY-----',
}

class SecretTests(unittest.TestCase):
    def test_provider_and_generic_secrets(self):
        text = '\n'.join(CASES.values())
        output, count = redact(text, secret_spans(text))
        for name, value in CASES.items():
            with self.subTest(provider=name):
                # All substantive credential material must disappear, not only prefix.
                check = value.split('=', 1)[-1].strip('"') if '=' in value else value
                if name == 'natural_password':
                    check = 'SomethingPrivate123'
                elif name == 'private_key':
                    check = PAYLOAD * 3
                self.assertNotIn(check, output)
        self.assertNotIn(PAYLOAD, output)
    def test_suppression_comment_ignored(self):
        token = CASES['google']
        result, _ = redact(token + ' # gitleaks:allow', secret_spans(token + ' # gitleaks:allow'))
        self.assertNotIn(token, result)
    def test_unicode_repeated(self):
        token = CASES['replicate']
        text = 'Привет 🌿 ' + token + '\nAgain ' + token
        result, _ = redact(text, secret_spans(text))
        self.assertNotIn(token, result)
        self.assertIn('Привет 🌿', result)
    def test_plain_text(self):
        self.assertEqual(secret_spans('Enjoy a sunny picnic by the lake.'), [])
    def test_cli_does_not_log_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / 'in.txt', Path(directory) / 'out.txt'
            source.write_text('\n'.join(CASES.values()))
            p = subprocess.run([sys.executable, str(ROOT / 'scripts/text_redact.py'), '--input', str(source), '--output', str(output), '--engine', 'patterns'], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertNotIn(PAYLOAD, p.stdout + p.stderr + output.read_text())
            self.assertTrue(json.loads(p.stdout)['review_required'])

    def test_value_only_with_punctuation_all_levels(self):
        examples = [
            ('API key: "short-but-private".', 'API key: "[REDACTED]".'),
            ("client_secret='private value with spaces';", "client_secret='[REDACTED]';"),
            ('My password is SomethingPrivate123.', 'My password is [REDACTED].'),
            ('CUSTOM_API_KEY="short-but-private"', 'CUSTOM_API_KEY="[REDACTED]"'),
            ('Authorization: Bearer ' + PAYLOAD + '.', 'Authorization: Bearer [REDACTED].'),
            ('Authorization: "Basic ' + PAYLOAD + '";', 'Authorization: "Basic [REDACTED]";'),
            ('{"password": "punctuated!secret?"}', '{"password": "[REDACTED]"}'),
        ]
        for level in LEVELS:
            for text, expected in examples:
                with self.subTest(level=level, text=text[:20]):
                    self.assertEqual(redact(text, detect_spans(text, level, engine='patterns'))[0], expected)

    def test_unicode_offsets_exact(self):
        token = CASES['replicate']
        text = '🌿 Анна: "' + token + '"; again ' + token
        spans = detect_spans(text, engine='patterns')
        first = text.index(token)
        last = text.rindex(token)
        self.assertEqual(spans, [(first, first + len(token)), (last, last + len(token))])

    def test_scanner_missing_fails(self):
        with patch('secret_scan.shutil.which', return_value=None):
            with self.assertRaises(RuntimeError):
                secret_spans('password=secret')

    def test_scanner_failure_fails(self):
        with patch('secret_scan.subprocess.run', return_value=subprocess.CompletedProcess([], 2, b'', b'')):
            with self.assertRaises(RuntimeError):
                secret_spans('hello')

    def test_cli_defaults_low_and_explicit_levels(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'in.txt'
            source.write_text('Read https://docs.python.org/3/ on 2026-09-14. password="private-value"')
            for level in [None, 'medium', 'high']:
                output = Path(directory) / (str(level) + '.txt')
                command = [sys.executable, str(ROOT / 'scripts/text_redact.py'), '--input', str(source),
                           '--output', str(output), '--engine', 'patterns']
                if level:
                    command += ['--level', level]
                proc = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(json.loads(proc.stdout)['level'], level or 'low')
                result = output.read_text()
                self.assertNotIn('private-value', result)
                self.assertIn('password="[REDACTED]"', result)
                self.assertEqual('https://docs.python.org/3/' in result, level != 'high')

if __name__ == '__main__':
    unittest.main()
