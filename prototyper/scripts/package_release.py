#!/usr/bin/env python3
"""Create the deterministic book download from a committed Prototyper source."""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent


def package(output):
    dirty = subprocess.check_output(['git', '-C', str(REPO), 'status', '--porcelain', '--', ROOT.name], text=True)
    if dirty.strip():
        raise SystemExit('Commit Prototyper changes before creating the release')
    commit = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip()
    files = [ROOT / name for name in ('SKILL.md', 'LICENSE', '.claude-plugin/plugin.json', 'scripts/discovery.py')]
    for folder in ('references', 'assets', 'scripts/assets'):
        files += sorted((ROOT / folder).rglob('*'))
    files = [file for file in files if file.is_file() and '__pycache__' not in file.parts and file.suffix in ('.md', '.json', '.py', '.js', '.css', '.html') or file.name == 'LICENSE']
    records = {file.relative_to(ROOT).as_posix(): file.read_bytes() for file in files}
    records['README.md'] = re.sub(r'(\]\()\.\./', r'\1', (ROOT / 'pack/README.md').read_text()).replace('](extensions.md)', '](pack/extensions.md)').encode()
    records['pack/extensions.md'] = (ROOT / 'pack/extensions.md').read_bytes()
    provenance = {'repository': 'https://github.com/sliday/skills', 'source_path': 'prototyper', 'commit': commit,
                  'version': json.loads(records['.claude-plugin/plugin.json'])['version'],
                  'files': {name: hashlib.sha256(data).hexdigest() for name, data in sorted(records.items())}}
    records['SOURCE.json'] = (json.dumps(provenance, indent=2) + '\n').encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(records.items()):
            entry = zipfile.ZipInfo('prototyper/' + name, (2026, 10, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, content)
    summary = {'source': provenance['repository'], 'commit': commit, 'archive_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}
    output.with_suffix('.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=pathlib.Path, required=True)
    package(parser.parse_args().output.resolve())
