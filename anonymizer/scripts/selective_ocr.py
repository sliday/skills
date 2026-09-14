"""Local hOCR character alignment: redact detected PII, not whole screenshots."""
import io
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET


def _bbox(title, key, size):
    match = re.search(r'(?:^|;\s*)' + key + r' (\d+) (\d+) (\d+) (\d+)(?:;|$)', title)
    if not match:
        raise ValueError('Missing OCR coordinates')
    x1, y1, x2, y2 = map(int, match.groups())
    if not (0 <= x1 < x2 <= size[0] and 0 <= y1 < y2 <= size[1]):
        raise ValueError('Invalid OCR coordinates')
    return (x1, y1, x2, y2)


def parse_hocr(data, size):
    """Return text plus Unicode-offset word/character geometry. Never persist it."""
    root = ET.fromstring(data)
    parts, words, cursor = [], [], 0
    for line in root.iter():
        if line.attrib.get('class') not in ('ocr_line', 'ocrx_line', 'ocr_header'):
            continue
        line_words = [node for node in line.iter() if node.attrib.get('class') == 'ocrx_word']
        for node in line_words:
            char_nodes = [c for c in node.iter() if c.attrib.get('class') == 'ocrx_cinfo']
            if not char_nodes:
                raise ValueError('OCR did not return character boxes')
            if parts and not parts[-1].endswith('\n'):
                parts.append(' ')
                cursor += 1
            start = cursor
            chars = []
            for char in char_nodes:
                value = ''.join(char.itertext())
                if not value:
                    continue
                box = _bbox(char.attrib.get('title', ''), 'x_bboxes', size)
                chars.append({'start': cursor, 'end': cursor + len(value), 'box': box})
                parts.append(value)
                cursor += len(value)
            if cursor > start:
                words.append({'start': start, 'end': cursor,
                              'box': _bbox(node.attrib.get('title', ''), 'bbox', size), 'chars': chars})
        if line_words:
            parts.append('\n')
            cursor += 1
    return ''.join(parts), words


def ocr_document(image, tesseract='tesseract', scale=2):
    if scale not in (1, 2):
        raise ValueError('OCR scale must be 1 or 2')
    executable = shutil.which(tesseract)
    if not executable:
        raise RuntimeError('Local OCR unavailable')
    buffer = io.BytesIO()
    from PIL import Image
    # Upscaling improves small screenshot text; all output geometry returns to
    # original pixels. Bound memory for very large source images.
    if image.width * image.height > 8_000_000:
        scale = 1
    scanned = image.resize((image.width * scale, image.height * scale), Image.Resampling.LANCZOS) if scale != 1 else image
    scanned.save(buffer, format='PNG')
    proc = subprocess.run([executable, 'stdin', 'stdout', '--psm', '11', '-c', 'hocr_char_boxes=1', 'hocr'],
                          input=buffer.getvalue(), capture_output=True, timeout=120)
    if proc.returncode:
        raise RuntimeError('Local OCR failed')
    text, words = parse_hocr(proc.stdout, scanned.size)
    if scale != 1:
        def original_box(box):
            a, b, c, d = box
            return (a // scale, b // scale, min(image.width, (c + scale - 1) // scale),
                    min(image.height, (d + scale - 1) // scale))
        for word in words:
            word['box'] = original_box(word['box'])
            for char in word['chars']:
                char['box'] = original_box(char['box'])
    return text, words


def boxes_for_spans(text, words, spans, size, padding=1):
    if type(padding) is not int or padding < 0:
        raise ValueError('Invalid padding')
    for a, b in spans:
        if not (type(a) is int and type(b) is int and 0 <= a < b <= len(text)):
            raise ValueError('Invalid detector offsets')
    boxes = []
    for word in words:
        for start, end in spans:
            if word['end'] <= start or word['start'] >= end:
                continue
            selected = [c['box'] for c in word['chars'] if c['start'] < end and c['end'] > start]
            if not selected:
                raise ValueError('Unmappable OCR span')
            boxes.append({'x1': max(0, min(b[0] for b in selected) - padding),
                          'y1': max(0, min(b[1] for b in selected) - padding),
                          'x2': min(size[0], max(b[2] for b in selected) + padding),
                          'y2': min(size[1], max(b[3] for b in selected) + padding)})
    # Stable deduplication, without ever recording detected text.
    return [dict(zip(('x1', 'y1', 'x2', 'y2'), b)) for b in dict.fromkeys(tuple(b.values()) for b in boxes)]


def selective_boxes(image, level='low', offline=False, engine='privacy-filter', literals=(), padding=1, tesseract='tesseract'):
    from text_redact import detect_spans
    text, words = ocr_document(image, tesseract)
    if not words:
        raise ValueError('No OCR words found; manual review required')
    spans = detect_spans(text, level=level, offline=offline, engine=engine, literals=literals)
    return boxes_for_spans(text, words, spans, image.size, padding)
