#!/usr/bin/env python3
"""Run pinned Gitleaks regexes locally; secrets stay in memory, never reports/logs."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

CONFIG = Path(__file__).resolve().parents[1] / 'references/gitleaks-redaction.toml'
# Conservative supplements for modern AI/provider prefixes, bearer headers,
# complete PEM key blocks, and short named assignments not covered by upstream.
SUPPLEMENTAL = [
    r'(?<![\w-])(?:sk-(?:proj-|svcacct-|ant-[A-Za-z0-9_-]*?)?|r8_|hf_|github_pat_|gh[pousr]_)[A-Za-z0-9_-]{16,}',
    r'(?i)\b(?:authorization\s*[:=]\s*["\']?\s*)?(?:bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}',
    r'-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z0-9]+ )*PRIVATE KEY-----',
    r'''(?ix)\b(?:[a-z0-9]+[_-])*(?:api[_-]?key|access[_-]?key|access[_-]?token|refresh[_-]?token|auth[_-]?token|client[_-]?secret|password|passwd|secret|token)\b["']?\s*(?::|=|\bis\b)\s*(?:"[^"\r\n]+"|'[^'\r\n]+'|[^\s,;\]}]+)''',
]


def secret_spans(text):
    executable = shutil.which('gitleaks')
    if not executable:
        raise RuntimeError('Gitleaks is required; no silent fallback')
    spans = [(m.start(), m.end()) for pattern in SUPPLEMENTAL for m in re.finditer(pattern, text)]
    # Prevent ambient .gitleaksignore files/configuration and suppression comments
    # inside the untrusted text from disabling detection. No raw data on disk.
    with tempfile.TemporaryDirectory(prefix='anonymizer-scan-') as directory:
        env = {k: v for k, v in os.environ.items() if not k.startswith('GITLEAKS_')}
        proc = subprocess.run(
            [executable, 'stdin', '--config', str(CONFIG), '--report-format', 'json',
             '--report-path', '-', '--no-banner', '--no-color', '--log-level', 'fatal',
             '--ignore-gitleaks-allow', '--gitleaks-ignore-path', directory,
             '--max-decode-depth', '0', '--timeout', '60'],
            input=text.encode('utf-8'), capture_output=True, cwd=directory, env=env, timeout=70)
    if proc.returncode not in (0, 1):
        raise RuntimeError('Local secret scanner failed')
    findings = json.loads(proc.stdout or b'[]')
    if not isinstance(findings, list):
        raise ValueError('Invalid scanner result')
    for finding in findings:
        value = finding.get('Secret')
        if not isinstance(value, str) or not value:
            raise ValueError('Missing secret offsets')
        # Match all occurrences, using Unicode character offsets instead of
        # Gitleaks byte-column offsets. Decoding is disabled to avoid unmappable spans.
        matches = list(re.finditer(re.escape(value), text))
        if not matches:
            raise ValueError('Unmappable secret finding')
        spans.extend((m.start(), m.end()) for m in matches)
    return spans
