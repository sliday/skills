"""Regression: upstream allowlist credentials must never be written to disk."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
import update_secret_rules as updater

class UpdateSafetyTests(unittest.TestCase):
    def test_update_publishes_rules_not_raw_allowlist(self):
        marker = 'UPSTREAM-EXAMPLE-MUST-NOT-BE-PUBLISHED'
        raw = ('title = "fixture"\n[[rules]]\nid="fixture"\ndescription="test"\n'
               'regex="token_[a-z]+"\n[[rules.allowlists]]\nregexes=["' + marker + '"]\n')
        def response(url, **kwargs):
            if url.endswith('/config/gitleaks.toml'):
                data = raw.encode()
            elif url.endswith('/LICENSE'):
                data = b'Synthetic test license'
            elif url.endswith('/commits/main'):
                data = json.dumps({'sha':'a'*40,'commit':{'committer':{'date':'2026-01-01'}}}).encode()
            elif url.endswith('/releases/latest'):
                data = json.dumps({'tag_name':'test','html_url':'https://example.com/release'}).encode()
            else:
                data = b'{"default_branch":"main"}'
            return io.BytesIO(data)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(updater, 'ROOT', root), patch.object(updater.urllib.request, 'urlopen', side_effect=response), contextlib.redirect_stdout(io.StringIO()):
                updater.main()
            self.assertFalse((root/'references/gitleaks-upstream.toml').exists())
            published = list((root/'references').iterdir())
            self.assertEqual(len(published), 3)
            for file in published:
                self.assertNotIn(marker, file.read_text())
            self.assertIn('token_[a-z]+', (root/'references/gitleaks-redaction.toml').read_text())

if __name__ == '__main__':
    unittest.main()
