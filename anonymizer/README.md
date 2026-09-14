# Anonymizer

A local-first agent skill for removing personal details and credentials from text and single-frame raster images. Optional Replicate GPT Image 2.5 Sunburst cosmetic editing is consent-gated and never treated as proof of privacy.

## Location and use

The skill entry point is [SKILL.md](SKILL.md). In this checkout it lives at `~/Playground/skills/anonymizer`. It is not automatically registered in a separate agent profile. Ask an agent to load this file, or install the skill using your agent's normal skill installer.

```bash
cd ~/Playground/skills/anonymizer
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
brew install gitleaks tesseract  # macOS; use equivalent packages on other systems

# First run permits model-weight downloads, not remote input inference.
.venv/bin/python scripts/text_redact.py --input input.txt --output redacted.txt
# Subsequent runs can add --offline.

# Local OCR: hide every recognized word; add --boxes boxes.json for visual details.
.venv/bin/python scripts/image_redact.py --input input.png --output redacted.png --all-text

# Full blanket mask if no details should remain:
.venv/bin/python scripts/image_redact.py --input input.png --output covered.png --full-image

.venv/bin/python -m unittest discover -s tests -v
```

Commands refuse existing output files. Keep private inputs/output outside the repository. No reverse mapping is stored. The `.venv` and dependencies/model cache are not part of the skill distribution. Python 3.12 and Gitleaks 8.30.1 were used for verification.

## Before and after

Synthetic data only. This example uses local `--all-text` OCR masking: it intentionally removes every recognized word, including the heading. Selective removal uses reviewed boxes instead.

![Synthetic screenshot before and after local OCR redaction](examples/before-after.png)

Actual text fixture input and local-model output are in [`examples/synthetic.txt`](examples/synthetic.txt) and [`examples/synthetic.redacted.txt`](examples/synthetic.redacted.txt).

## What is included

- `scripts/text_redact.py`: local OpenAI Privacy Filter inference, supplemental PII patterns, dedicated secret scanning, Unicode character-span merging, explicit-literal removal, safe separate output.
- `scripts/secret_scan.py`: pinned Gitleaks/RE2 credential rules plus conservative supplements. No key verification API calls or secret report files.
- `scripts/update_secret_rules.py`: explicit upstream rules refresh with revision/checksum provenance and preserved license.
- `scripts/image_redact.py`: all-text local OCR or manual opaque boxes; metadata stripping, EXIF orientation, alpha flattening, and multi-frame rejection.
- `scripts/replicate_finish.py`: optional reviewed-redacted-input upload to GPT Image 2.5 Sunburst, explicit consent flags, dry run, prediction resumption, immediate local download. Cosmetic results require another review/redaction pass.
- `tests/`: local regression suite. All fixtures are synthetic.
- `examples/`: synthetic text and screenshot before/after artifacts.

## Verification performed

- **26 tests passed**: text replacement, Unicode/overlap, representative provider credentials, suppression-comment resistance, no secret logging, image pixel/metadata/orientation/alpha checks, real Tesseract OCR, no-overwrite behavior, and cloud consent gates.
- **Real local OpenAI model inference completed**. Model + patterns + Gitleaks removed the seeded name, address, email, phone, and password while retaining the picnic sentence. The first model-only test missed a natural-language password, which motivated a tested supplemental rule.
- Synthetic screenshot output was opened and visually inspected: opaque black masks, no remaining readable text. Pixel/metadata assertions passed.
- Upstream Gitleaks config fetched and pinned: **221 regex rules**; see `references/gitleaks-provenance.json` for exact revision/checksum. Derived redaction rules omit entropy/allowlist suppression to favor recall.
- Replicate **dry-run and consent gates tested only**; no paid image generation performed. Live API schema documentation was checked. Do not label this as live cloud-generation verification.
- Repository skill frontmatter lint passed. This pack uses root README discovery and `.github/scripts/check-skills.py`; it has no manifest/resolver or GBrain conformance test to update.

## Limits

Not guaranteed anonymization or compliance certification. Regexes/model/OCR can miss secrets or personal details; combinations of retained facts can identify people. No automatic face/QR/plate detector or selective contextual image-Pll mapping. No PDF, hidden-document-layer, or multi-frame processing. No recursive encoded-secret decoding. Images containing API keys need full-field review even after OCR. Never upload original private images by default. Rotate already-exposed credentials.

Sources and implementation lessons: [references/sources-and-limitations.md](references/sources-and-limitations.md).
