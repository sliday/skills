#!/usr/bin/env python3
"""Local selective PII redaction. Review required; detection is not perfect recall."""
import argparse
from functools import lru_cache
import json
import os
import re
import sys
from pathlib import Path

os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')
CATEGORIES = {'account_number', 'private_address', 'private_email', 'private_person',
              'private_phone', 'private_url', 'private_date', 'secret'}
LEVELS = ('low', 'medium', 'high')
THRESHOLDS = {'low': .85, 'medium': .5, 'high': 0.0}
PATTERNS = [
    r'(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',
    r'\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]){11,30}\b',
    r'(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)',  # US SSN
]
URL_PATTERN = r'https?://[^\s<>"\']+'
PATH_PATTERN = r'(?:/(?:Users|home)/|[A-Za-z]:\\Users\\)(?P<username>[^/\\\s]+)(?=[/\\])'
PHONE_PATTERN = r'(?<![\w])\+?\d[\d ()-]{7,}\d(?!\w)'


def _validate_level(level):
    if level not in LEVELS:
        raise ValueError('Unknown redaction level')


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


def pattern_spans(text, literals=(), level='low'):
    """Direct identifiers at low/medium; high also removes URLs and numbers."""
    from secret_scan import supplemental_spans
    _validate_level(level)
    spans = [m.span() for pattern in PATTERNS for m in re.finditer(pattern, text)]
    spans += supplemental_spans(text)
    spans += [m.span('username') for m in re.finditer(PATH_PATTERN, text)]
    for match in re.finditer(PHONE_PATTERN, text):
        value = match.group()
        # Avoid mundane dates and eight-digit date-like counters at low/medium.
        if re.fullmatch(r'\d{4}[- /]\d{1,2}[- /]\d{1,2}|\d{1,2}[- /]\d{1,2}[- /]\d{4}', value):
            continue
        phone_shape = (value.startswith('+') or
                       re.fullmatch(r'(?:1[ -]?)?\(?\d{3}\)?[ -]\d{3}[ -]\d{4}', value) or
                       re.fullmatch(r'\d{10}', value))
        if phone_shape and 10 <= sum(c.isdigit() for c in value) <= 15:
            spans.append(match.span())
    if level == 'high':
        for match in re.finditer(URL_PATTERN, text, re.IGNORECASE):
            spans.append((match.start(), match.start() + len(match.group().rstrip('.,;:!?)]}'))))
        spans += [m.span() for m in re.finditer(r'\d+(?:[.,]\d+)*', text)]
    for value in literals:
        if not isinstance(value, str) or not value.strip():
            raise ValueError('Extra literals must be nonempty strings')
        spans.extend(m.span() for m in re.finditer(re.escape(value), text, re.IGNORECASE))
    return spans


@lru_cache(maxsize=2)
def _classifier(offline):
    from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
    name = 'openai/privacy-filter'
    tokenizer = AutoTokenizer.from_pretrained(name, local_files_only=offline)
    model = AutoModelForTokenClassification.from_pretrained(name, local_files_only=offline)
    return tokenizer, pipeline('token-classification', model=model, tokenizer=tokenizer, device=-1)


def entity_spans(entities, level='low'):
    """Assemble full BIOES entities BEFORE applying a peak-token confidence gate.

    One confident token accepts the whole entity, including weaker boundary tokens.
    O tokens and new B/S labels terminate entities; malformed orphan I/E tokens are
    kept as conservative partial entities, never joined across an O token.
    """
    _validate_level(level)
    allowed = CATEGORIES if level != 'low' else CATEGORIES - {'private_date', 'private_url'}
    pending = None
    result = []

    def flush():
        if pending and pending[0] in allowed and pending[3] >= THRESHOLDS[level]:
            result.append((pending[1], pending[2]))

    for entity in entities:
        label = entity['entity']
        if label == 'O':
            flush()
            pending = None
            continue
        prefix, separator, category = label.partition('-')
        if not separator or prefix not in {'B', 'I', 'E', 'S'} or category not in CATEGORIES:
            raise ValueError('Unrecognized model label; no output written')
        start, end = int(entity['start']), int(entity['end'])
        score = float(entity['score'])
        if end <= start:
            continue
        if pending and prefix in {'I', 'E'} and category == pending[0]:
            pending = (category, pending[1], end, max(score, pending[3]))
        else:
            flush()
            pending = (category, start, end, score)
        if prefix in {'E', 'S'}:
            flush()
            pending = None
    flush()
    return result


def model_spans(text, offline=False, level='low'):
    _validate_level(level)
    tokenizer, classifier = _classifier(offline)
    offsets = tokenizer(text, return_offsets_mapping=True, add_special_tokens=False)['offset_mapping']
    spans = []
    # Overlapping windows cover the tail and allow entities at a boundary to
    # complete in a neighboring window. Confidence gating happens after assembly.
    for i in range(0, len(offsets), 896):
        batch = offsets[i:i + 1024]
        start, end = batch[0][0], batch[-1][1]
        entities = classifier(text[start:end], aggregation_strategy='none', ignore_labels=[])
        spans += [(start + a, start + b) for a, b in entity_spans(entities, level)]
    return spans


def _subtract_spans(spans, preserved):
    """Remove known syntax/public path segments from heuristic/model selections."""
    for left, right in preserved:
        pieces = []
        for start, end in spans:
            if right <= start or left >= end:
                pieces.append((start, end))
            else:
                if start < left:
                    pieces.append((start, left))
                if end > right:
                    pieces.append((right, end))
        spans = pieces
    return spans


def _path_syntax(text):
    preserved = []
    for match in re.finditer(PATH_PATTERN, text):
        tail = re.match(r'[^\s<>"\']*', text[match.end():]).group()
        preserved += [(match.start(), match.start('username')),
                      (match.end('username'), match.end() + len(tail))]
    return preserved


def detect_spans(text: str, level='low', offline=False, engine='privacy-filter', literals=()) -> list[tuple[int, int]]:
    """Return merged Unicode character offsets. Secrets use Gitleaks at EVERY level.

    Offline requires cached model files. Inference is local even when downloads
    are allowed. Pattern-only mode has no contextual person/address detection.
    """
    from secret_scan import secret_spans, supplemental_spans
    _validate_level(level)
    if engine not in ('privacy-filter', 'patterns'):
        raise ValueError('Unknown redaction engine')
    literals = tuple(literals)
    spans = pattern_spans(text, literals, level)
    credentials = secret_spans(text)
    if engine == 'privacy-filter' and text:
        modeled = []
        for start, end in model_spans(text, offline, level):
            if not 0 <= start < end <= len(text):
                raise ValueError('Invalid model offsets')
            while start < end and text[start] in ' \t\r\n\"\'([{':
                start += 1
            while start < end and text[end - 1] in ' \t\r\n\"\'.,;:!?)]}':
                end -= 1
            if start < end:
                modeled.append((start, end))
        spans += _subtract_spans(modeled, supplemental_spans(text, syntax=True))
    spans = _subtract_spans(spans, _path_syntax(text))
    # Explicit literals and credential scanner findings override preservation.
    spans += [match.span() for value in literals
              for match in re.finditer(re.escape(value), text, re.IGNORECASE)]
    spans += credentials
    return merge_spans(text, spans)


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
    parser.add_argument('--level', choices=LEVELS, default='low')
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
        spans = detect_spans(text, args.level, args.offline, args.engine, literals)
        output, count = redact(text, spans)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(output)
        print(json.dumps({'engine': args.engine, 'level': args.level, 'redactions': count, 'review_required': True,
                          'limited_pattern_only': args.engine == 'patterns'}))
    except Exception as exc:
        # Third-party error strings may include input. Report type, not raw exception.
        print('Redaction failed (' + type(exc).__name__ + '); do not share an unreviewed output.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
