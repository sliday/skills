#!/usr/bin/env python3
"""Run isolated local discovery acceptance checks with Python's standard library."""
import argparse
import importlib.util
import json
import pathlib
import secrets
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

options = argparse.ArgumentParser(add_help=False)
options.add_argument('--tool', type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[2] / 'prototyper/scripts/discovery.py')
arguments, remaining = options.parse_known_args()
sys.argv = [sys.argv[0], *remaining]
SOURCE = arguments.tool.resolve()
spec = importlib.util.spec_from_file_location('discovery_under_test', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DiscoveryAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sliday-discovery-check-')
        self.directory = pathlib.Path(self.temp.name)
        self.store = module.Store(self.directory / 'data')
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), module.Handler)
        self.server.store = self.store
        self.server.token = secrets.token_urlsafe(32)
        self.base = 'http://127.0.0.1:' + str(self.server.server_port)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, path, payload=None, headers=None, raw=None):
        body = raw if raw is not None else (json.dumps(payload).encode() if payload is not None else None)
        defaults = {'Content-Type': 'application/json', 'X-CSRF-Token': self.server.token}
        defaults.update(headers or {})
        request = urllib.request.Request(self.base + path, data=body, headers=defaults)
        try:
            response = urllib.request.urlopen(request, timeout=3)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, response.read().decode(), response.headers

    def create(self, name):
        status, body, _ = self.request('/api/projects', {'name': name})
        self.assertEqual(status, 201, body)
        return json.loads(body)['project']['id']

    def save(self, identifier, qid, answer, status='answered', cursor=0):
        code, body, _ = self.request('/api/projects/' + identifier + '/answer',
                                   {'question_id': qid, 'answer': answer, 'status': status, 'cursor': cursor})
        self.assertEqual(code, 200, body)
        return json.loads(body)

    def test_complete_website_app_service_and_cli_export(self):
        for medium in ('Website', 'App', 'Service'):
            with self.subTest(medium=medium):
                identifier = self.create(medium + ' Łódź')
                state = self.save(identifier, 'medium', medium)
                expected = medium.lower() + '-'
                self.assertTrue(state['questions'][1]['id'].startswith(expected))
                for position, question in enumerate(state['questions'][1:], 1):
                    text = 'Zażółć gęślą\n<script>alert("test")</script> ' + question['id']
                    if question['id'] == 'stack':
                        text = 'Existing vanilla HTML/CSS/JS' if medium != 'Service' else 'Manual service, no software required'
                    self.save(identifier, question['id'], text, cursor=position)
                code, brief, _ = self.request('/api/projects/' + identifier + '/export/PRD.md')
                self.assertEqual(code, 200)
                self.assertIn('Zażółć gęślą', brief)
                self.assertIn('No unanswered questions', brief)
                self.assertIn('Manual service' if medium == 'Service' else 'Existing vanilla', brief)
                output = self.directory / ('export-' + medium)
                result = subprocess.run([sys.executable, str(SOURCE), '--data-dir', str(self.store.directory),
                                         '--export', identifier, '--output-dir', str(output)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                record = json.loads((output / 'discovery.json').read_text())
                self.assertEqual(record['project']['id'], identifier)
                self.assertEqual((output / 'PRD.md').read_text(), brief)
                self.assertTrue((output / 'BAR.md').is_file())

    def test_resume_edit_skip_branch_and_delete(self):
        identifier = self.create('Interrupted app')
        survivor = self.create('Keep this project')
        self.save(identifier, 'medium', 'App')
        self.save(identifier, 'user', 'draft text', 'draft', 4)
        resumed = module.Store(self.store.directory).project(identifier)
        self.assertEqual(resumed['answers']['user']['answer'], 'draft text')
        self.assertEqual(resumed['project']['cursor'], 4)
        self.save(identifier, 'user', 'Updated owner')
        self.save(identifier, 'constraints', '', 'skipped')
        self.save(identifier, 'app-context', 'Only phone')
        state = self.save(identifier, 'medium', 'Service')
        self.assertTrue(state['questions'][1]['id'].startswith('service-'))
        brief = self.store.export(identifier)['PRD.md']
        self.assertIn('Updated owner', brief)
        self.assertNotIn('Only phone', brief)
        self.assertIn('Unknown. Discuss this before implementation.', brief)
        self.assertEqual(state['answers']['constraints']['status'], 'skipped')
        self.assertEqual(self.request('/api/projects/' + identifier + '/delete', {})[0], 200)
        self.assertEqual(self.request('/api/projects/' + identifier)[0], 404)
        self.assertEqual(self.request('/api/projects/' + survivor)[0], 200)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM answers WHERE project_id=?', (identifier,)).fetchone()[0], 0)

    def test_origin_host_csrf_and_malformed_requests(self):
        self.assertEqual(self.server.server_address[0], '127.0.0.1')
        self.assertEqual(self.store.path.stat().st_mode & 0o777, 0o600)
        for headers in ({'Origin': 'https://evil.example'}, {'Host': 'evil.example:' + str(self.server.server_port)},
                        {'X-CSRF-Token': ''}, {'X-CSRF-Token': 'wrong'}):
            self.assertEqual(self.request('/api/projects', {'name': 'blocked'}, headers)[0], 403)
        for raw in (b'{', b'[]', b'null', b'\xff'):
            self.assertEqual(self.request('/api/projects', raw=raw)[0], 400)
        self.assertEqual(self.request('/api/projects', {'name': ''})[0], 400)
        identifier = self.create('Safe project')
        self.save(identifier, 'user', 'Retained answer')
        self.assertEqual(self.request('/api/projects/' + identifier + '/answer', {'question_id': 'user', 'answer': '', 'status': 'answered'})[0], 400)
        self.assertEqual(self.store.project(identifier)['answers']['user']['answer'], 'Retained answer')
        self.assertEqual(self.request('/api/projects/' + identifier + '/drop', {})[0], 404)
        code, _, headers = self.request('/')
        self.assertEqual(code, 200)
        self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])
        self.assertEqual(headers['Cache-Control'], 'no-store')


if __name__ == '__main__':
    unittest.main(verbosity=2)
