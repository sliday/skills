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

## Non-goals

No compliance certification, face recognition, automatic contextual image PII selection, guaranteed multilingual recall, secure erasure of originals, automatic folder scans, PDF redaction, stable pseudonyms, or automatic publication. No guarantees against background/contextual re-identification. Manual region selection is required for faces, plates, signatures, QR/barcodes, and visual details not captured by OCR.
