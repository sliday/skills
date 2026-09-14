import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from PIL import Image
import sys

SCRIPT = Path(__file__).parents[1] / 'scripts/replicate_finish.py'

class CloudGateTests(unittest.TestCase):
    def test_dry_run_and_consent_gate(self):
        with tempfile.TemporaryDirectory() as d:
            source, output = Path(d) / 'redacted.png', Path(d) / 'out.png'
            Image.new('RGB', (64, 64), 'black').save(source)
            cmd = [sys.executable, str(SCRIPT), '--input', str(source), '--output', str(output)]
            env = dict(os.environ)
            env.pop('REPLICATE_API_TOKEN', None)
            p = subprocess.run(cmd + ['--dry-run'], capture_output=True, text=True, env=env)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn('"network_request": false', p.stdout)
            self.assertFalse(output.exists())
            for flags in [[], ['--approve-cloud-upload'], ['--confirm-reviewed-redacted']]:
                p = subprocess.run(cmd + flags, capture_output=True, text=True, env=env)
                self.assertNotEqual(p.returncode, 0)
                self.assertIn('Both explicit cloud approval', p.stderr)
                self.assertFalse(output.exists())
    def test_overwrite_refused(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / 'redacted.png'
            Image.new('RGB', (64, 64), 'black').save(source)
            p = subprocess.run([sys.executable, str(SCRIPT), '--input', str(source), '--output', str(source), '--dry-run'], capture_output=True)
            self.assertNotEqual(p.returncode, 0)

if __name__ == '__main__':
    unittest.main()
