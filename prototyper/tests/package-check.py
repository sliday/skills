#!/usr/bin/env python3
"""Check committed archive provenance in an isolated synthetic Git repository."""
import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

options = argparse.ArgumentParser(add_help=False)
options.add_argument('--tool', type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1] / 'scripts/package_release.py')
arguments, remaining = options.parse_known_args()
sys.argv = [sys.argv[0], *remaining]
SOURCE = arguments.tool.resolve()


class PackageAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='prototyper-package-check-')
        self.addCleanup(self.temp.cleanup)
        self.repo = pathlib.Path(self.temp.name) / 'repo'
        self.root = self.repo / 'prototyper'
        shutil.copytree(SOURCE.parents[1], self.root, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        self.git('init', '-q')
        (self.repo / '.gitignore').write_text('prototyper/tests/private-local.py\nprototyper/tests/private-link.py\n')
        self.git('add', '.')
        self.git('-c', 'user.name=Eval', '-c', 'user.email=eval@example.invalid', 'commit', '-qm', 'Synthetic eval source')
        self.commit = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True)

    def package(self, name, commit=None):
        output = pathlib.Path(self.temp.name) / name
        command = [sys.executable, str(self.root / 'scripts/package_release.py'), '--output', str(output)]
        if commit:
            command += ['--commit', commit]
        result = subprocess.run(command, capture_output=True, text=True)
        return output, result

    def test_ignored_local_files_excluded_and_archive_deterministic(self):
        (self.root / 'tests/private-local.py').write_text('PRIVATE_SYNTHETIC_SENTINEL = True\n')
        (self.root / 'tests/private-link.py').symlink_to(self.root / 'tests/private-local.py')
        self.assertEqual(self.git('status', '--porcelain'), '')
        output, result = self.package('first.zip')
        self.assertEqual(result.returncode, 0, result.stderr)
        second, result = self.package('second.zip')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_bytes(), second.read_bytes())
        with zipfile.ZipFile(output) as archive:
            source = json.loads(archive.read('prototyper/SOURCE.json'))
            self.assertEqual(source['commit'], self.commit)
            self.assertNotIn('tests/private-local.py', source['files'])
            self.assertNotIn('tests/private-link.py', source['files'])
            self.assertNotIn('prototyper/tests/private-local.py', archive.namelist())
            self.assertNotIn('prototyper/tests/private-link.py', archive.namelist())
            self.assertEqual(set(archive.namelist()), {'prototyper/' + name for name in source['files']} | {'prototyper/SOURCE.json'})
            for name, digest in source['files'].items():
                self.assertEqual(hashlib.sha256(archive.read('prototyper/' + name)).hexdigest(), digest)
            self.assertIn('prototyper/scripts/board-assets/DAUB-LICENSE.txt', archive.namelist())

    def test_selected_commit_bytes_and_dirty_guard(self):
        original = (self.root / 'pack/README.md').read_bytes()
        (self.root / 'pack/README.md').write_text('Synthetic later README\n')
        output, result = self.package('dirty.zip')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Commit Prototyper changes', result.stderr)
        self.assertFalse(output.exists())
        self.git('add', 'prototyper/pack/README.md')
        self.git('-c', 'user.name=Eval', '-c', 'user.email=eval@example.invalid', 'commit', '-qm', 'Later synthetic source')
        output, result = self.package('selected.zip', self.commit)
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(output) as archive:
            source = json.loads(archive.read('prototyper/SOURCE.json'))
            self.assertEqual(source['commit'], self.commit)
            readme = archive.read('prototyper/README.md').decode()
            self.assertNotIn('Synthetic later README', readme)
            self.assertIn(original.decode().splitlines()[0], readme)


if __name__ == '__main__':
    unittest.main(verbosity=2)
