#!/usr/bin/env python3
"""Explicit maintenance action: fetch, pin and harden current upstream Gitleaks regexes."""
import datetime
import hashlib
import json
import urllib.request
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def harden(source):
    data = tomllib.loads(source)
    lines = ['# Generated from pinned Gitleaks rules; see gitleaks-provenance.json.',
             'title = "Anonymizer conservative secret regexes"', 'minVersion = "v8.25.0"']
    count = 0
    for rule in data['rules']:
        if not rule.get('regex'):
            continue
        lines.append('\n[[rules]]')
        for key in ('id', 'description', 'regex', 'secretGroup'):
            if key in rule:
                lines.append(key + ' = ' + json.dumps(rule[key], ensure_ascii=True))
        # Intentional: no entropy gates, allowlists, keyword prefilters, paths or
        # dependency checks. Redaction favors recall over repository-scan precision.
        count += 1
    result = '\n'.join(lines) + '\n'
    tomllib.loads(result)
    return result, count


def main():
    api = 'https://api.github.com/repos/gitleaks/gitleaks'
    def get_json(url):
        with urllib.request.urlopen(url, timeout=60) as response:
            return json.load(response)
    repository = get_json(api)
    branch = repository['default_branch']
    from urllib.parse import quote
    head = get_json(api + '/commits/' + quote(branch, safe=''))
    release = get_json(api + '/releases/latest')
    sha = head['sha']
    base = 'https://raw.githubusercontent.com/gitleaks/gitleaks/' + sha
    with urllib.request.urlopen(base + '/config/gitleaks.toml', timeout=60) as response:
        raw = response.read()
    with urllib.request.urlopen(base + '/LICENSE', timeout=60) as response:
        license_text = response.read().decode()
    hardened, count = harden(raw.decode())
    refs = ROOT / 'references'
    refs.mkdir(exist_ok=True)
    # Raw upstream contains allowlisted example credentials. Keep it in memory
    # only: publishing it creates secret-scanning alerts. Provenance retains its
    # source URL and SHA-256 without distributing the credential examples.
    (refs / 'gitleaks-redaction.toml').write_text(hardened)
    (refs / 'GITLEAKS-LICENSE').write_text(license_text)
    provenance = {'repository': 'https://github.com/gitleaks/gitleaks', 'commit': sha,
                  'default_branch': branch, 'head_date': head['commit']['committer']['date'],
                  'latest_release': release['tag_name'], 'latest_release_url': release['html_url'],
                  'source_url': base + '/config/gitleaks.toml',
                  'fetched_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'sha256': hashlib.sha256(raw).hexdigest(), 'regex_rules': count,
                  'policy': 'No allowlists, entropy gates, keyword prefilters, paths, or dependent-rule restrictions'}
    (refs / 'gitleaks-provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps(provenance))

if __name__ == '__main__':
    main()
