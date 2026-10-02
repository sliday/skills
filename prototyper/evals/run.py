#!/usr/bin/env python3
"""Run isolated, standard-library Prototyper behaviour evals and retain results."""
import argparse
import datetime
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=('all', 'discovery', 'board', 'package'), default='all')
    parser.add_argument('--output-dir', type=pathlib.Path)
    args = parser.parse_args()
    output = args.output_dir or pathlib.Path(tempfile.mkdtemp(prefix='prototyper-evals-'))
    output.mkdir(parents=True, exist_ok=True)
    suites = {
        'discovery': ROOT / 'tests/discovery-check.py',
        'board': ROOT / 'evals/board-check.py',
        'package': ROOT / 'tests/package-check.py',
    }
    results = []
    for name, script in suites.items():
        if args.suite not in ('all', name):
            continue
        command = [sys.executable, '-W', 'error::ResourceWarning', str(script),
                   '--tool', str(ROOT / 'scripts' / ('package_release.py' if name == 'package' else name + '.py'))]
        try:
            run = subprocess.run(command, capture_output=True, text=True, timeout=120)
            code, log = run.returncode, run.stdout + run.stderr
        except (OSError, subprocess.TimeoutExpired) as error:
            code, log = 1, str(error)
        (output / (name + '.log')).write_text(log, encoding='utf-8')
        results.append({'suite': name, 'exit_code': code, 'status': 'pass' if code == 0 else 'fail',
                        'command': command, 'log': name + '.log'})
        print(f'{name}: {"PASS" if code == 0 else "FAIL"}', flush=True)
        if code:
            print(log, file=sys.stderr)
    report = {'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'results': results, 'browser': 'untested by this runner; run the browser eval separately'}
    (output / 'results.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'Evidence: {output.resolve()}')
    print('Browser interaction and screenshots require the separate browser eval.')
    return 1 if any(result['exit_code'] for result in results) else 0


if __name__ == '__main__':
    sys.exit(main())
