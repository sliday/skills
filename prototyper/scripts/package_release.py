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


def package(output, revision='HEAD'):
    dirty = subprocess.check_output(['git', '-C', str(REPO), 'status', '--porcelain', '--', ROOT.name], text=True)
    if dirty.strip():
        raise SystemExit('Commit Prototyper changes before creating the release')
    commit = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', '--verify', revision + '^{commit}'], text=True).strip()
    tree = subprocess.check_output(['git', '-C', str(REPO), 'ls-tree', '-rz', commit, '--', ROOT.name + '/'])
    blobs = {}
    for entry in tree.split(b'\0'):
        if not entry:
            continue
        metadata, path = entry.split(b'\t', 1)
        mode, kind, object_id = metadata.decode().split()
        name = path.decode().removeprefix(ROOT.name + '/')
        if kind == 'blob' and mode in ('100644', '100755'):
            blobs[name] = object_id
    def committed(name):
        if name not in blobs:
            raise SystemExit('Required committed resource missing: ' + name)
        return subprocess.check_output(['git', '-C', str(REPO), 'cat-file', 'blob', blobs[name]])
    required = ('SKILL.md', 'LICENSE', '.claude-plugin/plugin.json', 'scripts/discovery.py', 'scripts/board.py')
    records = {name: committed(name) for name in required}
    folders = ('references', 'assets', 'scripts/assets', 'scripts/board-assets', 'tests', 'evals')
    for name in sorted(blobs):
        path = pathlib.PurePosixPath(name)
        if any(name.startswith(folder + '/') for folder in folders) and '__pycache__' not in path.parts and path.suffix in ('.md', '.json', '.py', '.js', '.css', '.html', '.txt', '.cjs'):
            records[name] = committed(name)
    records['README.md'] = re.sub(r'(\]\()\.\./', r'\1', committed('pack/README.md').decode()).replace('](extensions.md)', '](pack/extensions.md)').encode()
    records['pack/extensions.md'] = committed('pack/extensions.md')
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
    parser.add_argument('--commit', default='HEAD', help='Git commit to package (default: HEAD)')
    args = parser.parse_args()
    package(args.output.resolve(), args.commit)
