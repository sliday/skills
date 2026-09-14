#!/usr/bin/env python3
"""Optional cloud cosmetic edit of an already-redacted PNG. Not a privacy filter."""
import argparse
import base64
import io
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from PIL import Image

MODEL = 'openai/gpt-image-2.5-sunburst'
PROMPT = ('This is an already-redacted image. Preserve the layout and all opaque redaction blocks exactly. '
          'Make only minor cosmetic improvements to non-redacted areas. Never reconstruct, infer, reveal, '
          'or invent identifying text, faces, numbers, signatures, QR codes, or barcodes. '
          'Do not change dimensions or move content. Do not add text.')


def request(url, token, payload=None):
    if not url.startswith('https://api.replicate.com/v1/'):
        raise ValueError('Unexpected API URL')
    req = urllib.request.Request(url, data=json.dumps(payload).encode() if payload else None,
                                 headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=90) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--approve-cloud-upload', action='store_true')
    parser.add_argument('--confirm-reviewed-redacted', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--resume-id', help='Resume a previously created prediction; never repeat a paid POST')
    args = parser.parse_args()
    if args.output.exists() or args.input.resolve() == args.output.resolve():
        parser.error('Output must be a new file distinct from input')
    if not args.dry_run and not (args.approve_cloud_upload and args.confirm_reviewed_redacted):
        parser.error('Both explicit cloud approval and reviewed-redaction confirmation are required')
    image = Image.open(args.input)
    if image.format != 'PNG' or getattr(image, 'n_frames', 1) != 1:
        parser.error('Input must be a flattened redacted PNG')
    # Fresh pixels only: never upload source metadata or original container bytes.
    clean = Image.new('RGB', image.size, 'white')
    rgba = image.convert('RGBA')
    clean.paste(rgba, mask=rgba.getchannel('A'))
    buf = io.BytesIO()
    clean.save(buf, format='PNG')
    if args.dry_run:
        print(json.dumps({'model': MODEL, 'network_request': False, 'review_required': True,
                          'image_size': list(clean.size), 'prompt': PROMPT}))
        return 0
    token = os.environ.get('REPLICATE_API_TOKEN')
    if not token:
        parser.error('Set REPLICATE_API_TOKEN in the environment; never pass a token on the command line')
    if args.resume_id:
        import re
        if not re.fullmatch(r'[a-zA-Z0-9]+', args.resume_id):
            parser.error('Invalid prediction ID')
        result = request('https://api.replicate.com/v1/predictions/' + args.resume_id, token)
    else:
        result = request('https://api.replicate.com/v1/models/' + MODEL + '/predictions', token,
                         {'input': {'prompt': PROMPT, 'input_images': ['data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()],
                                    'number_of_images': 1, 'quality': 'high', 'output_format': 'png', 'aspect_ratio': 'auto'}})
    prediction_id = result['id']
    # ID contains no source data. Read-back exact prediction before claiming success.
    print('prediction_id=' + prediction_id, flush=True)
    deadline = time.monotonic() + 600
    while True:
        result = request('https://api.replicate.com/v1/predictions/' + prediction_id, token)
        if result['status'] in ('succeeded', 'failed', 'canceled'):
            break
        if time.monotonic() >= deadline:
            raise TimeoutError('Resume with prediction ID; do not resubmit')
        time.sleep(3)
    if result['status'] != 'succeeded':
        raise RuntimeError('Prediction did not succeed')
    url = result['output'][0]
    if not url.startswith('https://'):
        raise ValueError('Unexpected output URL')
    with urllib.request.urlopen(url, timeout=90) as response:
        data = response.read(80_000_001)
    if len(data) > 80_000_000:
        raise ValueError('Output exceeds download limit')
    with Image.open(io.BytesIO(data)) as generated:
        final = Image.new('RGB', generated.size, 'white')
        rgba = generated.convert('RGBA')
        final.paste(rgba, mask=rgba.getchannel('A'))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as f:
            final.save(f, format='PNG')
    print(json.dumps({'prediction_id': prediction_id, 'status': 'succeeded', 'review_required': True,
                      'warning': 'Cosmetic draft only; rescan and deterministically re-redact before sharing'}))
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('Cloud edit failed (' + type(exc).__name__ + '). Resume any printed prediction ID; do not blindly resubmit.', file=sys.stderr)
        sys.exit(1)
