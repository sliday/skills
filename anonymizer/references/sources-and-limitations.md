# Verified upstream contracts

- https://openai.com/index/introducing-openai-privacy-filter/
- https://huggingface.co/openai/privacy-filter
- https://huggingface.co/openai/privacy-filter/raw/main/config.json
- https://replicate.com/openai/gpt-image-2.5-sunburst/llms.txt

OpenAI describes Privacy Filter as a 1.5B-total/50M-active parameter token classifier, with eight categories: private_person, private_address, private_email, private_phone, private_url, private_date, account_number, secret. It is explicitly not an anonymization/compliance guarantee. Local inference is supported through Transformers. The released model supports long context, but this helper uses bounded overlapping windows to constrain local memory; do not equate it to the reference inference implementation or transfer benchmark claims.

The current Replicate Sunburst docs expose `prompt`, `input_images`, `quality`, `aspect_ratio`, `number_of_images`, and `output_format`; outputs are an array of image URLs. The helper uses a fixed privacy-conscious cosmetic prompt, uploads fresh raster pixels only, and defaults to no network unless both consent flags are passed. Its initial verification is a dry run, not a paid live generation.

## Lessons embodied in this implementation

- Add supplemental credential patterns and explicit literals: a real local test missed “My password is ExampleSecret123” even though it detected the accompanying name, street address, email, and phone. The regression now covers that phrasing. Other phrasings can still be missed.
- Merge adjacent BIOES token spans instead of treating each token as a whole entity; the pipeline can return separate name and email fragments.
- Trim span-edge whitespace to preserve readable prose without restoring sensitive characters.
- Treat cloud cosmetics as a new untrusted artifact; generation can relocate or invent details. Reinspect and apply irreversible redaction again.
- Keep low-signal logs and neutral filenames. No entity reverse map, raw OCR text, or raw provider errors should escape by default.

## Selective defaults and preservation lessons

- Default to low, selective removal. Do not treat whole panels or all OCR text as personal data; high/all-text is explicit opt-in.
- Assemble complete BIOES entities before confidence gating. Redacting only high-scoring sub-tokens can expose a suffix of a name or credential.
- Preserve field labels, punctuation and non-user path components. Credentials and explicit literals override preservation so secrets embedded in paths are still masked.
- Map to hOCR character boxes rather than whole OCR words; this preserves most of a filename/path when only its username segment is sensitive.
- Upscale small screenshot text for local OCR and transform boxes back to original pixels with conservative rounding. Review remains necessary: small UI names can be missed even at 2×.
- Level selection must change category policy, not only confidence thresholds. A live Q2 email test classified both a launch date and a project file identifier as privacy categories at near-certain confidence. Low excludes private dates/URLs but still masks model-classified account numbers; document this semantic false positive rather than overfit an exception.
- Compare removal AND preservation. A screenshot with all text hidden does not demonstrate a successful selective default.

## Safe rule vendoring

Keep raw upstream config in memory only. Gitleaks allowlists embed example credential values that GitHub secret scanning can flag even though they are unused by this project. Publish only the stripped-down redaction rules, upstream license, source URL/revision and checksum. Never vendor raw allowlists or suppress GitHub scanning to hide this class of problem. The updater regression test verifies that allowlist values never reach published files.

## Non-goals

No compliance certification, face recognition, guaranteed multilingual recall, secure erasure of originals, automatic folder scans, PDF redaction, stable pseudonyms, or automatic publication. No guarantees against background/contextual re-identification. Manual region selection is required for faces, plates, signatures, QR/barcodes, and visual details not captured by OCR.
