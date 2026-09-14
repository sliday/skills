#!/usr/bin/env python3
"""Local PII redaction. Never emits raw spans or reverse mappings."""
import argparse
import json
import os
import re
import sys
from pathlib import Path

os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')
CATEGORIES = {'account_number', 'private_address', 'private_email', 'private_person',
              'private_phone', 'private_url', 'private_date', 'secret'}
PATTERNS = [
    r'(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',
    r'(?<!\w)\+?\d[\d ()-]{7,}\d(?!\w)',
    r'https?://[^\s<>]+',
    r'(?i)\b(?:password|passwd|api[_ -]?key|token|secret)\s*(?:[:=]|\bis\b)\s*["\']?[^\s"\',;]+',
    r'\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]){11,30}\b',
]


def merge_spans(text, spans):
    checked = []
    for start, end in spans:
        if not (isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(text)):
            raise ValueError('Invalid detector offsets; no output written')
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        if start < end:
            checked.append((start, end))
    result = []
    for start, end in sorted(checked):
        if result and (start <= result[-1][1] or text[result[-1][1]:start].isspace()):
            result[-1] = (result[-1][0], max(end, result[-1][1]))
        else:
            result.append((start, end))
    return result


def pattern_spans(text, literals=()):
    spans = [(m.start(), m.end()) for pattern in PATTERNS for m in re.finditer(pattern, text)]
    for value in literals:
        if not isinstance(value, str) or not value.strip():
            raise ValueError('Extra literals must be nonempty strings')
        spans.extend((m.start(), m.end()) for m in re.finditer(re.escape(value), text, re.IGNORECASE))
    return spans


def model_spans(text, offline=False):
    from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
    name = 'openai/privacy-filter'
    tokenizer = AutoTokenizer.from_pretrained(name, local_files_only=offline)
    model = AutoModelForTokenClassification.from_pretrained(name, local_files_only=offline)
    classifier = pipeline('token-classification', model=model, tokenizer=tokenizer, device=-1)
    offsets = tokenizer(text, return_offsets_mapping=True, add_special_tokens=False)['offset_mapping']
    spans = []
    # Bounded overlapping windows; never silently truncate the tail of a document.
    for i in range(0, len(offsets), 896):
        batch = offsets[i:i + 1024]
        start, end = batch[0][0], batch[-1][1]
        for entity in classifier(text[start:end], aggregation_strategy='none'):
            label = entity['entity']
            if label == 'O':
                continue
            category = label.split('-', 1)[-1]
            if category not in CATEGORIES:
                raise ValueError('Unrecognized model label; no output written')
            a, b = int(entity['start']), int(entity['end'])
            if b > a:
                spans.append((start + a, start + b))
    return spans


def redact(text, spans):
    merged = merge_spans(text, spans)
    out, previous = [], 0
    for start, end in merged:
        out.extend([text[previous:start], '[REDACTED]'])
        previous = end
    out.append(text[previous:])
    return ''.join(out), len(merged)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--extra-literals', type=Path, help='Private JSON array of exact strings to remove')
    parser.add_argument('--engine', choices=['privacy-filter', 'patterns'], default='privacy-filter')
    parser.add_argument('--offline', action='store_true', help='Require cached weights; no model downloads')
    args = parser.parse_args()
    if args.output.exists() or args.input.resolve() == args.output.resolve():
        parser.error('Output must be a new file distinct from input')
    try:
        text = args.input.read_text(encoding='utf-8')
        if len(text) > 2_000_000:
            raise ValueError('Input exceeds local safety limit; split into reviewed documents')
        literals = json.loads(args.extra_literals.read_text()) if args.extra_literals else []
        if not isinstance(literals, list):
            raise ValueError('Extra literals must be a JSON array')
        spans = pattern_spans(text, literals)
        from secret_scan import secret_spans
        spans += secret_spans(text)
        if args.engine == 'privacy-filter' and text:
            spans += model_spans(text, args.offline)
        output, count = redact(text, spans)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(output)
        print(json.dumps({'engine': args.engine, 'redactions': count, 'review_required': True,
                          'limited_pattern_only': args.engine == 'patterns'}))
    except Exception as exc:
        # Third-party error strings may include input. Report type, not raw exception.
        print('Redaction failed (' + type(exc).__name__ + '); do not share an unreviewed output.', file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
