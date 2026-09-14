"""Synthetic-only image redaction tests; real OCR test skips if unavailable."""
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "image_redact.py"
spec = importlib.util.spec_from_file_location("image_redact", SCRIPT)
assert spec is not None and spec.loader is not None
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def screenshot():
    image = Image.new("RGB", (720, 240), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 32) if Path("/System/Library/Fonts/Supplemental/Arial.ttf").exists() else ImageFont.load_default(size=32)
    draw.text((30, 30), "SYNTHETIC DEMO", font=font, fill="black")
    draw.text((30, 100), "Alex Example", font=font, fill="black")
    draw.text((30, 165), "alex@example.test", font=font, fill="black")
    return image


class ImageRedactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "source.png"
        self.output = self.root / "output.png"
        Image.new("RGB", (20, 12), (60, 120, 180)).save(self.source)

    def tearDown(self):
        self.tmp.cleanup()

    def test_exact_opaque_half_open_mask_and_original_preserved(self):
        original = self.source.read_bytes()
        m.redact_image(self.source, self.output, [{"x1": 2, "y1": 3, "x2": 8, "y2": 9}])
        with Image.open(self.output) as image:
            self.assertEqual(image.mode, "RGB")
            for y in range(12):
                for x in range(20):
                    self.assertEqual(image.getpixel((x, y)), (0, 0, 0) if 2 <= x < 8 and 3 <= y < 9 else (60, 120, 180))
        self.assertEqual(original, self.source.read_bytes())

    def test_alpha_white_and_all_metadata_removed(self):
        image = Image.new("RGBA", (20, 12), (255, 0, 0, 0))
        image.putpixel((10, 5), (255, 0, 0, 128))
        meta = PngImagePlugin.PngInfo()
        meta.add_text("private", "synthetic-secret")
        exif = Image.Exif()
        exif[315] = "synthetic-author"
        image.save(self.source, pnginfo=meta, exif=exif, icc_profile=b"synthetic-icc", dpi=(72, 72))
        m.redact_image(self.source, self.output, [{"x1": 0, "y1": 0, "x2": 1, "y2": 1}])
        with Image.open(self.output) as out:
            self.assertEqual(out.mode, "RGB")
            self.assertEqual(out.info, {})
            self.assertFalse(out.getexif())
            self.assertEqual(out.getpixel((2, 2)), (255, 255, 255))
            self.assertEqual(out.getpixel((10, 5)), (255, 127, 127))
        self.assertNotIn(b"synthetic", self.output.read_bytes())

    def test_exif_orientation_precedes_boxes(self):
        image = Image.new("RGB", (20, 12), "red")
        image.putpixel((0, 0), (0, 255, 0))
        exif = Image.Exif()
        exif[274] = 6
        image.save(self.source, exif=exif)
        m.redact_image(self.source, self.output, [{"x1": 0, "y1": 18, "x2": 12, "y2": 20}])
        with Image.open(self.output) as out:
            self.assertEqual(out.size, (12, 20))
            self.assertEqual(out.getpixel((11, 0)), (0, 255, 0))
            self.assertEqual(out.getpixel((11, 19)), (0, 0, 0))
            self.assertFalse(out.getexif())

    def test_empty_fails_closed(self):
        for boxes in (None, []):
            with self.assertRaises(m.RedactionError):
                m.redact_image(self.source, self.output, boxes)
            self.assertFalse(self.output.exists())

    def test_full_image(self):
        m.redact_image(self.source, self.output, [], full_image=True)
        with Image.open(self.output) as out:
            self.assertEqual(out.getextrema(), ((0, 0),) * 3)

    def test_validation(self):
        cases = [{}, [None], [{"x1": 0}], [{"x1": False, "y1": 0, "x2": 2, "y2": 2}],
                 [{"x1": 0.5, "y1": 0, "x2": 2, "y2": 2}],
                 [{"x1": -1, "y1": 0, "x2": 2, "y2": 2}],
                 [{"x1": 0, "y1": 0, "x2": 21, "y2": 2}],
                 [{"x1": 2, "y1": 0, "x2": 2, "y2": 2}]]
        for boxes in cases:
            with self.subTest(boxes=boxes), self.assertRaises(m.RedactionError):
                m.redact_image(self.source, self.output, boxes)
        self.assertFalse(self.output.exists())

    def test_same_file_alias_and_existing_outputs_refused(self):
        original = self.source.read_bytes()
        with self.assertRaises(m.RedactionError):
            m.redact_image(self.source, self.source, full_image=True)
        self.output.symlink_to(self.source)
        with self.assertRaises(m.RedactionError):
            m.redact_image(self.source, self.output, full_image=True)
        self.output.unlink()
        os.link(self.source, self.output)
        with self.assertRaises(m.RedactionError):
            m.redact_image(self.source, self.output, full_image=True)
        self.assertEqual(self.source.read_bytes(), original)

    def test_animation_rejected(self):
        source = self.root / "animated.gif"
        Image.new("RGB", (20, 12), "red").save(source, save_all=True, append_images=[Image.new("RGB", (20, 12), "blue")])
        with self.assertRaises(m.RedactionError):
            m.redact_image(source, self.output, full_image=True)
        self.assertFalse(self.output.exists())

    def test_ocr_masks_low_confidence_words_with_padding(self):
        tsv = b"level\tleft\ttop\twidth\theight\tconf\ttext\n5\t2\t3\t4\t5\t0\tSYNTHETIC\n"
        with patch.object(m.shutil, "which", return_value="tesseract"), patch.object(m.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, tsv, b"")):
            boxes = m.ocr_boxes(m.load_rgb(self.source), padding=4)
        self.assertEqual(boxes, [{"x1": 0, "y1": 0, "x2": 10, "y2": 12}])

    def test_ocr_failure_and_empty_never_write(self):
        with patch.object(m.shutil, "which", return_value=None), self.assertRaises(m.RedactionError):
            m.redact_image(self.source, self.output, all_text=True)
        with patch.object(m, "ocr_boxes", return_value=[]), self.assertRaises(m.RedactionError):
            m.redact_image(self.source, self.output, all_text=True)
        self.assertFalse(self.output.exists())

    def test_cli_errors_do_not_log_paths_or_json_content(self):
        secret = self.root / "SYNTHETIC_PRIVATE_IDENTIFIER.json"
        secret.write_text("SYNTHETIC_PRIVATE_VALUE", encoding="utf-8")
        proc = subprocess.run([sys.executable, str(SCRIPT), "--input", str(self.source), "--output", str(self.output), "--boxes", str(secret)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn("SYNTHETIC_PRIVATE", proc.stdout + proc.stderr)
        self.assertFalse(self.output.exists())

    @unittest.skipUnless(shutil.which("tesseract"), "local tesseract unavailable")
    def test_real_tesseract_cli_and_mask_pixels(self):
        screenshot().save(self.source)
        detected = m.ocr_boxes(m.load_rgb(self.source))
        self.assertGreaterEqual(len(detected), 4)
        proc = subprocess.run([sys.executable, str(SCRIPT), "--input", str(self.source), "--output", str(self.output), "--all-text"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertGreaterEqual(json.loads(proc.stdout)["masked_regions"], 4)
        self.assertNotIn("Example", proc.stdout + proc.stderr)
        with Image.open(self.output) as out:
            for box in detected:
                self.assertEqual(out.crop(tuple(box[k] for k in ("x1", "y1", "x2", "y2"))).getextrema(), ((0, 0),) * 3)
            self.assertEqual(out.info, {})


if __name__ == "__main__":
    unittest.main()
