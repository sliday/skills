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
    r'(?i)\b(?:bearer|basic)\s+(?P<value>[A-Za-z0-9._~+/=-]{8,})',
    r'-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z0-9]+ )*PRIVATE KEY-----',
    r'''(?ix)\b(?:[a-z0-9]+[_-])*(?:api[_ -]?key|access[_ -]?key|access[_ -]?token|refresh[_ -]?token|auth[_ -]?token|client[_ -]?secret|password|passwd|secret|token)\b["']?\s*(?::|=|\bis\b)\s*(?:"(?P<double>[^"\r\n]+)"|'(?P<single>[^'\r\n]+)'|(?P<bare>[^\s,"';\]}]+))''',
]


def supplemental_spans(text, *, syntax=False):
    """Value-only matches, or their label/quote delimiters when syntax=True."""
    spans = []
    for pattern in SUPPLEMENTAL:
        for match in re.finditer(pattern, text):
            group = next((key for key, value in match.groupdict().items()
                          if value is not None), 0)
            start, end = match.span(group)
            if group in ('bare', 'value'):
                # Sentence delimiters, not the punctuation inside a quoted password.
                while end > start and text[end - 1] in '.,;:!?)]}':
                    end -= 1
            if syntax:
                spans.extend((a, b) for a, b in ((match.start(), start), (end, match.end())) if a < b)
            elif start < end:
                spans.append((start, end))
    return spans


def secret_spans(text):
    executable = shutil.which('gitleaks')
    if not executable:
        raise RuntimeError('Gitleaks is required; no silent fallback')
    spans = supplemental_spans(text)
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
        for match in matches:
            start, end = match.span()
            # Some upstream rules (e.g. hashicorp-tf-password) include enclosing
            # quotes in Secret. Keep syntax, while retaining every value byte.
            if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
                start += 1
                end -= 1
            if start < end:
                spans.append((start, end))
    return spans
