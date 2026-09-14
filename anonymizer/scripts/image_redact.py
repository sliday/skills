#!/usr/bin/env python3
"""Local-only irreversible image masking. Requires Pillow; OCR requires tesseract.

Boxes are integer pixel coordinates in the EXIF-oriented image, half-open:
[x1, x2) by [y1, y2). All boxes must fit the image. OCR masks every detected
word, NOT every actual word: detection can miss text. Review output and add
manual boxes for missed text, faces, codes, avatars, or other identifiers.
No face/QR detector is included. --full-image is the fail-safe blanket mask.
Existing outputs are refused. Input bytes remain untouched. Only fresh RGB PNG
pixels are saved, without source metadata, alpha, hidden frames, or layers.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import warnings

from PIL import Image, ImageOps


class RedactionError(ValueError):
    """Messages must be static and contain no image contents or paths."""


def validate_boxes(boxes, size):
    if not isinstance(boxes, list):
        raise RedactionError("Boxes must be a JSON array.")
    width, height = size
    result = []
    for box in boxes:
        if not isinstance(box, dict) or set(box) != {"x1", "y1", "x2", "y2"}:
            raise RedactionError("Each box must contain exactly x1, y1, x2, y2.")
        coords = tuple(box[key] for key in ("x1", "y1", "x2", "y2"))
        if any(type(value) is not int for value in coords):
            raise RedactionError("Box coordinates must be integers.")
        x1, y1, x2, y2 = coords
        if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
            raise RedactionError("Boxes must have positive area and fit the oriented image.")
        result.append(coords)
    return result


def load_rgb(path):
    # Treat oversized inputs as failures rather than emitting potentially identifying warnings.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with Image.open(path) as source:
            if getattr(source, "n_frames", 1) != 1:
                raise RedactionError("Multi-frame images are not supported; export one frame first.")
            oriented = ImageOps.exif_transpose(source)
            rgba = oriented.convert("RGBA")
            white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            flattened = Image.alpha_composite(white, rgba).convert("RGB")
            # Explicit fresh buffer: no info, EXIF, ICC, XMP, thumbnails, or PNG text.
            return Image.frombytes("RGB", flattened.size, flattened.tobytes())


def ocr_boxes(image, padding=4, tesseract="tesseract"):
    if type(padding) is not int or padding < 0:
        raise RedactionError("OCR padding must be a nonnegative integer.")
    executable = shutil.which(tesseract)
    if not executable:
        raise RedactionError("Local tesseract is unavailable; no output written.")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    try:
        proc = subprocess.run(
            [executable, "stdin", "stdout", "--psm", "11", "tsv"],
            input=buffer.getvalue(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=120, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise RedactionError("Local OCR failed; no output written.") from None
    if proc.returncode:
        raise RedactionError("Local OCR failed; no output written.")
    try:
        reader = csv.DictReader(io.StringIO(proc.stdout.decode("utf-8")), delimiter="\t", quoting=csv.QUOTE_NONE)
        if not {"level", "left", "top", "width", "height", "text"}.issubset(reader.fieldnames or []):
            raise ValueError
        boxes = []
        width, height = image.size
        for row in reader:
            if row["level"] != "5" or not row["text"].strip():
                continue
            left, top, w, h = (int(row[key]) for key in ("left", "top", "width", "height"))
            if not (0 <= left < left + w <= width and 0 <= top < top + h <= height):
                raise ValueError
            boxes.append({"x1": max(0, left - padding), "y1": max(0, top - padding),
                          "x2": min(width, left + w + padding), "y2": min(height, top + h + padding)})
        return boxes
    except (ValueError, TypeError, KeyError, AttributeError, csv.Error):
        raise RedactionError("Invalid local OCR result; no output written.") from None


def redact_image(input_path, output_path, boxes=None, *, all_text=False,
                 full_image=False, padding=4, tesseract="tesseract"):
    source, target = Path(input_path), Path(output_path)
    if source.resolve() == target.resolve():
        raise RedactionError("Input and output must be different files.")
    # Refuse even dangling symlinks and hard-link aliases; never clobber any existing file.
    if os.path.lexists(target):
        raise RedactionError("Output already exists; choose a new file.")
    if target.suffix.lower() != ".png":
        raise RedactionError("Output must use the .png extension.")
    if type(padding) is not int or padding < 0:
        raise RedactionError("OCR padding must be a nonnegative integer.")
    image = load_rgb(source)
    rectangles = validate_boxes([] if boxes is None else boxes, image.size)
    if all_text and not full_image:
        rectangles.extend(validate_boxes(ocr_boxes(image, padding, tesseract), image.size))
    if full_image:
        rectangles = [(0, 0, *image.size)]
    if not rectangles:
        raise RedactionError("No regions to mask; add boxes or use --full-image.")
    for rectangle in rectangles:
        image.paste((0, 0, 0), rectangle)
    # Stage only redacted pixels, mode 0600; publish atomically without overwriting.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".redacted-", suffix=".png", delete=False) as handle:
            temporary = Path(handle.name)
            image.save(handle, format="PNG")
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return {"masked_regions": len(rectangles), "width": image.width, "height": image.height}


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "error: Invalid command arguments; use --help.\n")


def main(argv=None):
    parser = SafeParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--boxes", help="Local JSON file of half-open oriented pixel rectangles")
    parser.add_argument("--all-text", action="store_true", help="Mask words detected by local OCR (may miss text)")
    parser.add_argument("--full-image", action="store_true", help="Mask the entire image")
    parser.add_argument("--padding", type=int, default=4, help="OCR padding in pixels (default: 4)")
    parser.add_argument("--tesseract", default="tesseract", help="Local tesseract executable")
    args = parser.parse_args(argv)
    try:
        boxes = None
        if args.boxes:
            with open(args.boxes, encoding="utf-8") as handle:
                boxes = json.load(handle)
        result = redact_image(args.input, args.output, boxes, all_text=args.all_text,
                              full_image=args.full_image, padding=args.padding, tesseract=args.tesseract)
    except RedactionError as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 2
    except Exception:
        # Decoder/OS/subprocess errors can contain paths or sensitive metadata. Never echo them.
        print("error: Image redaction failed; no successful output confirmed.", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
