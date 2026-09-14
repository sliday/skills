import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from secret_scan import secret_spans
from text_redact import redact

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

if __name__ == '__main__':
    unittest.main()
