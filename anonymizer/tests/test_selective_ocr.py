"""Preservation and Unicode alignment regressions; no private fixtures."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import selective_ocr as s
import image_redact as m


def aligned(text):
    chars = [{'start': i, 'end': i + 1, 'box': (i * 10, 0, i * 10 + 8, 10)} for i in range(len(text))]
    return [{'start': 0, 'end': len(text), 'box': (0, 0, len(text) * 10, 10), 'chars': chars}]

class SelectiveTests(unittest.TestCase):
    def test_only_username_not_entire_path(self):
        text = '/Users/alice/project/README.md'
        box = s.boxes_for_spans(text, aligned(text), [(7, 12)], (400, 30), padding=0)
        self.assertEqual(box, [{'x1': 70, 'y1': 0, 'x2': 118, 'y2': 10}])
    def test_unicode_offsets(self):
        text = 'Привет:Анна!'
        box = s.boxes_for_spans(text, aligned(text), [(7, 11)], (200, 30), padding=0)
        self.assertEqual(box[0]['x1'], 70)
        self.assertEqual(box[0]['x2'], 108)
    def test_invalid_offsets_fail(self):
        with self.assertRaises(ValueError):
            s.boxes_for_spans('abc', aligned('abc'), [(-1, 3)], (100, 30))
    def test_hocr_entity_and_line_offsets(self):
        data = '''<html><body><span class="ocr_line"><span class="ocrx_word" title="bbox 0 0 10 10"><span class="ocrx_cinfo" title="x_bboxes 0 0 10 10">é</span></span><span class="ocrx_word" title="bbox 20 0 30 10"><span class="ocrx_cinfo" title="x_bboxes 20 0 30 10">&amp;</span></span></span></body></html>'''
        text, words = s.parse_hocr(data, (100, 20))
        self.assertEqual(text, 'é &\n')
        self.assertEqual(words[1]['start'], 2)
        self.assertEqual(words[1]['end'], 3)
    def test_low_preserves_unselected_pixels(self):
        with tempfile.TemporaryDirectory() as d:
            source, output = Path(d) / 'in.png', Path(d) / 'out.png'
            Image.new('RGB', (100, 30), 'white').save(source)
            box = {'x1': 10, 'y1': 5, 'x2': 20, 'y2': 15}
            with patch.object(s, 'selective_boxes', return_value=[box]) as detected:
                result = m.redact_image(source, output, level='low', padding=1)
            detected.assert_called_once()
            image = Image.open(output)
            self.assertEqual(image.getpixel((30, 10)), (255, 255, 255))
            self.assertEqual(image.getpixel((15, 10)), (0, 0, 0))
            self.assertEqual(result['level'], 'low')
    def test_medium_uses_selective_detector(self):
        with tempfile.TemporaryDirectory() as d:
            source, output = Path(d) / 'in.png', Path(d) / 'out.png'
            Image.new('RGB', (100, 30), 'white').save(source)
            with patch.object(s, 'selective_boxes', return_value=[{'x1':0,'y1':0,'x2':2,'y2':2}]) as detect:
                m.redact_image(source, output, level='medium')
                self.assertEqual(detect.call_args.kwargs['level'], 'medium')
    def test_real_hocr_character_boxes(self):
        image = Image.new('RGB', (800, 100), 'white')
        fontpath = Path('/System/Library/Fonts/Supplemental/Arial.ttf')
        font = ImageFont.truetype(str(fontpath), 32) if fontpath.exists() else ImageFont.load_default(size=32)
        ImageDraw.Draw(image).text((20,20), 'Email: alex@example.test', fill='black', font=font)
        text, words = s.ocr_document(image)
        self.assertIn('alex@example.test', text)
        start = text.index('alex@example.test')
        boxes = s.boxes_for_spans(text, words, [(start,start+len('alex@example.test'))], image.size)
        self.assertTrue(boxes)
        self.assertTrue(all(b['x1'] > 90 for b in boxes))

if __name__ == '__main__':
    unittest.main()
