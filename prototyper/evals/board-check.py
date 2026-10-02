#!/usr/bin/env python3
"""Exercise the board CLI and HTTP API with isolated synthetic projects."""
import argparse
import concurrent.futures
from contextlib import closing
import copy
import hashlib
import http.client
import json
from pathlib import Path
import queue
import re
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def task(task_id, parent=None, feedback=None):
    return {'id': task_id, 'parent_id': parent, 'title': 'Synthetic ' + task_id,
            'description': 'Isolated critic fixture.', 'status': 'building',
            'evidence': ['Critic fixture, no product verification claimed.'], 'feedback': feedback}


def question(label='Choose a delivery format?', choices=None):
    return {'question': label, 'why': 'Critic decision fixture.',
            'choices': choices or [{'id': 'link', 'label': 'A link'}, {'id': 'file', 'label': 'A file'}], 'answer': None}


def fixture():
    return {'schema_version': 1, 'project': {'name': 'Synthetic critic project',
            'summary': 'No client data.', 'demo': False, 'prototype_url': None},
            'tasks': [task('root'), task('child', 'root'), task('leaf', 'child', question()),
                      task('comment', None, question('Write a note?')), task('race', None, question('Choose once?'))]}


class Server:
    def __init__(self, tool, data):
        self.tool, self.data = tool, data
        self.process = None
        self.reader = None
        self.lines = []

    def start(self):
        self.process = subprocess.Popen([sys.executable, str(self.tool), '--data-dir', str(self.data), '--port', '0'],
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        output = queue.Queue()

        def read():
            try:
                with self.process.stdout as stream:
                    for line in stream:
                        self.lines.append(line.rstrip())
                        output.put(line)
            finally:
                output.put(None)

        self.reader = threading.Thread(target=read, daemon=True)
        self.reader.start()
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            try:
                line = output.get(timeout=max(0.01, deadline - time.monotonic()))
            except queue.Empty:
                break
            if line is None:
                break
            match = re.search(r'Open http://127\.0\.0\.1:(\d+)/', line)
            if match:
                self.port = int(match.group(1))
                self.origin = 'http://127.0.0.1:' + str(self.port)
                try:
                    status, _, html = self.request('GET', '/')
                    if status != 200:
                        raise AssertionError('Page startup returned ' + str(status))
                    token = re.search(r'<meta name="csrf-token" content="([^"]+)"', html.decode())
                    if token is None:
                        raise AssertionError('Page lacks CSRF token')
                    self.token = token.group(1)
                    return self
                except BaseException:
                    self.stop()
                    raise
        self.stop()
        raise RuntimeError('Board did not launch: ' + '\n'.join(self.lines))

    def request(self, method, path, payload=None, headers=None, raw=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=12)
        body = raw if raw is not None else (json.dumps(payload).encode() if payload is not None else b'')
        pairs = [('Host', '127.0.0.1:' + str(self.port))]
        if method == 'POST':
            pairs += [('Origin', self.origin), ('X-CSRF-Token', getattr(self, 'token', '')),
                      ('Content-Type', 'application/json'), ('Content-Length', str(len(body)))]
        if headers:
            remove, extra = headers
            pairs = [(key, value) for key, value in pairs if key.lower() not in remove]
            pairs += extra
        try:
            conn.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
            for key, value in pairs:
                conn.putheader(key, value)
            conn.endheaders(body)
            response = conn.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            conn.close()

    def board(self):
        status, _, body = self.request('GET', '/api/board')
        if status != 200:
            raise AssertionError('GET /api/board returned ' + str(status))
        return json.loads(body)

    def answer(self, task_id, choice='link', comment='Critic answer', feedback=None, **extra):
        payload = {'choice_id': choice, 'comment': comment}
        if feedback:
            payload.update(expected_question=feedback['question'], expected_choices=feedback['choices'], expected_why=feedback['why'])
        payload.update(extra)
        return self.request('POST', '/api/tasks/' + task_id + '/feedback', payload)

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)
        if self.reader:
            self.reader.join(timeout=3)
            if self.reader.is_alive():
                raise RuntimeError('Board output reader did not stop')
        if self.process and self.process.stdout:
            self.process.stdout.close()


class Checks:
    def __init__(self, tool, work):
        self.tool, self.work = tool, work
        self.data = work / 'project' / '.prototype-progress'
        self.results = []
        self.number = 0

    def check(self, name, operation):
        try:
            detail = operation()
            self.results.append({'name': name, 'passed': True, 'evidence': detail})
            print('PASS ' + name, flush=True)
        except Exception as error:
            self.results.append({'name': name, 'passed': False, 'error': type(error).__name__ + ': ' + str(error)})
            print('FAIL ' + name + ': ' + str(error), flush=True)

    def cli(self, *args, expected=0):
        self.number += 1
        cmd = [sys.executable, str(self.tool), '--data-dir', str(self.data), *map(str, args)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        (self.work / ('cli-%03d.log' % self.number)).write_text(json.dumps({'command': cmd,
            'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}, indent=2))
        assert result.returncode == expected, (result.returncode, result.stdout, result.stderr)
        return result

    def apply(self, state, expected=0):
        path = self.work / ('import-%03d.json' % (self.number + 1))
        path.write_text(json.dumps(state, ensure_ascii=True))
        return self.cli('--apply', path, expected=expected)

    def export(self):
        path = self.work / ('export-%03d.json' % (self.number + 1))
        self.cli('--export', path)
        return json.loads(path.read_text())

    def rejected_import(self, state):
        prior = self.export()
        result = self.apply(state, expected=2)
        assert 'Board error:' in result.stderr, result.stderr
        assert self.export() == prior, 'Failed import changed saved state'
        return result.stderr.strip()


def require(value, detail):
    assert value, detail
    return detail


def run(checks):
    c = checks
    base = fixture()
    c.check('K1 empty project exports zero tasks without demo or work timestamp',
            lambda: require((lambda state: state['tasks'] == [] and not state['project']['demo'] and state['updated_at'] is None)(c.export()), 'Empty board is honest'))
    c.check('K8 CLI imports and exports three hierarchy levels',
            lambda: (c.apply(base), require([t['parent_id'] for t in c.export()['tasks'][:3]] == [None, 'root', 'child'], 'Hierarchy retained'))[-1])
    invalid = copy.deepcopy(base)
    invalid['tasks'][0]['parent_id'] = 'leaf'
    c.check('K2 reject parent cycle and preserve prior state', lambda: c.rejected_import(invalid))
    invalid = copy.deepcopy(base)
    invalid['tasks'][1]['parent_id'] = 'missing'
    c.check('K2 reject missing parent and preserve prior state', lambda: c.rejected_import(invalid))
    invalid = copy.deepcopy(base)
    invalid['tasks'].append(copy.deepcopy(invalid['tasks'][0]))
    c.check('K2 reject duplicate task IDs and preserve prior state', lambda: c.rejected_import(invalid))
    for name, modify in [
        ('unknown status', lambda state: state['tasks'][0].update(status='complete')),
        ('oversize task title', lambda state: state['tasks'][0].update(title='x' * 201)),
        ('duplicate choice IDs', lambda state: state['tasks'][2]['feedback']['choices'].append({'id': 'link', 'label': 'Repeat'})),
        ('script prototype URL', lambda state: state['project'].update(prototype_url='javascript:alert(1)')),
        ('credential prototype URL', lambda state: state['project'].update(prototype_url='https://name:secret@example.test/')),
        ('demo live prototype claim', lambda state: state['project'].update(demo=True, prototype_url='https://example.test/')),
        ('invalid control character', lambda state: state['tasks'][0].update(title='bad\x00title')),
        ('invalid Unicode surrogate', lambda state: state['tasks'][0].update(title='bad\ud800title')),
        ('more than 1000 tasks', lambda state: state.update(tasks=[task('task' + str(i)) for i in range(1001)])),
        ('more than 64 nesting levels', lambda state: state.update(tasks=[task('level' + str(i), 'level' + str(i - 1) if i else None) for i in range(65)])),
    ]:
        invalid = copy.deepcopy(base)
        modify(invalid)
        c.check('K7 import rejects ' + name + ' without state loss', lambda state=invalid: c.rejected_import(state))
    for name, body in [('malformed JSON', b'{'), ('duplicate JSON key', b'{"schema_version":1,"schema_version":1}'),
                       ('nonfinite JSON number', b'{"schema_version":NaN}'), ('oversize file', b' ' * (2097152 + 1))]:
        def bad_file(body=body):
            before = c.export()
            path = c.work / ('bad-%03d.json' % (c.number + 1))
            path.write_bytes(body)
            result = c.cli('--apply', path, expected=2)
            assert c.export() == before, 'Invalid bytes changed state'
            return result.stderr.strip()
        c.check('K7 import rejects ' + name + ' without state loss', bad_file)
    c.check('K7 local directory and database limit access to owner',
            lambda: require((c.data.stat().st_mode & 0o777) == 0o700 and ((c.data / 'board.sqlite3').stat().st_mode & 0o777) == 0o600, 'Directory 0700 and database 0600'))
    server = Server(c.tool, c.data).start()
    try:
        c.check('K7 server launches on an assigned loopback port', lambda: require(server.port > 0, '\n'.join(server.lines)))
        def nonloopback():
            route = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                route.connect(('192.0.2.1', 9))
                address = route.getsockname()[0]
            finally:
                route.close()
            assert not address.startswith('127.'), 'No nonloopback interface available to test bind'
            try:
                connection = socket.create_connection((address, server.port), timeout=1)
            except ConnectionRefusedError as error:
                return 'Nonloopback connection to ' + address + ':' + str(server.port) + ' gets ' + str(error)
            connection.close()
            raise AssertionError('Board accepts connections on ' + address)
        c.check('K7 nonloopback interface cannot reach board', nonloopback)
        def served_assets():
            for path, kind in [('/', 'text/html'), ('/assets/app.js', 'text/javascript'), ('/assets/style.css', 'text/css'), ('/assets/daub.css', 'text/css')]:
                status, headers, body = server.request('GET', path)
                assert status == 200 and headers['Content-Type'].startswith(kind) and len(body) > 0, path
                assert headers['X-Content-Type-Options'] == 'nosniff', path
                assert "connect-src 'self'" in headers['Content-Security-Policy'], path
                assert 'Access-Control-Allow-Origin' not in headers, path
            return 'HTML, JavaScript and both stylesheets return 200 with local CSP and nosniff'
        c.check('K7 installed assets serve with CSP and no cross-origin API grant', served_assets)
        security_cases = [
            ('external Host', 'GET', ['host'], [('Host', 'evil.example:' + str(server.port))]),
            ('wrong-port Host', 'GET', ['host'], [('Host', '127.0.0.1:1')]),
            ('duplicate Host', 'GET', [], [('Host', '127.0.0.1:' + str(server.port))]),
            ('external Origin', 'POST', ['origin'], [('Origin', 'https://evil.example')]),
            ('wrong-port Origin', 'POST', ['origin'], [('Origin', 'http://127.0.0.1:1')]),
            ('duplicate Origin', 'POST', [], [('Origin', server.origin)]),
            ('cross-site fetch', 'POST', [], [('Sec-Fetch-Site', 'cross-site')]),
            ('missing CSRF', 'POST', ['x-csrf-token'], []),
            ('wrong CSRF', 'POST', ['x-csrf-token'], [('X-CSRF-Token', 'wrong')]),
            ('non-ASCII CSRF', 'POST', ['x-csrf-token'], [('X-CSRF-Token', 'café')]),
            ('duplicate CSRF', 'POST', [], [('X-CSRF-Token', server.token)]),
        ]
        def denied(method, remove, extra):
            before = server.board()
            status, _, body = server.request(method, '/api/tasks/leaf/feedback' if method == 'POST' else '/api/board',
                                             {'choice_id': 'link', 'comment': 'Forbidden mutation'} if method == 'POST' else None,
                                             headers=(remove, extra))
            assert status == 403 and json.loads(body).get('error'), (status, body)
            assert server.board() == before, 'Rejected origin/CSRF changed state'
            return '403 with a clear error and unchanged state'
        for name, method, remove, extra in security_cases:
            c.check('K7 reject ' + name, lambda method=method, remove=remove, extra=extra: denied(method, remove, extra))
        bad_requests = [
            ('empty response', {}, None, None),
            ('unknown choice', {'choice_id': 'unknown', 'comment': ''}, None, None),
            ('blank comment without choice', {'choice_id': None, 'comment': '  '}, None, None),
            ('oversize comment', {'choice_id': None, 'comment': 'x' * 12001}, None, None),
            ('client status change', {'choice_id': 'link', 'comment': 'Try mutation', 'status': 'done'}, None, None),
            ('client evidence change', {'choice_id': 'link', 'comment': 'Try mutation', 'evidence': ['invented']}, None, None),
            ('malformed JSON', None, b'{', None),
            ('duplicate JSON response key', None, b'{"choice_id":"link","choice_id":"file","comment":""}', None),
            ('nonfinite response JSON', None, b'{"choice_id":NaN,"comment":""}', None),
            ('oversize body', None, b' ' * 65537, None),
            ('zero Content-Length', None, b'', None),
            ('duplicate Content-Length', {'choice_id': 'link', 'comment': 'a'}, None, ([], [('Content-Length', '0')])),
            ('wrong content type', {'choice_id': 'link', 'comment': 'a'}, None, (['content-type'], [('Content-Type', 'text/plain')])),
            ('transfer encoding', {'choice_id': 'link', 'comment': 'a'}, None, ([], [('Transfer-Encoding', 'chunked')])),
        ]
        def invalid_request(payload, raw, headers):
            before = server.board()
            status, _, body = server.request('POST', '/api/tasks/leaf/feedback', payload, raw=raw, headers=headers)
            assert status == 400 and json.loads(body).get('error'), (status, body)
            assert server.board() == before, 'Invalid request changed state'
            return '400 with a clear error and unchanged state'
        for name, payload, raw, headers in bad_requests:
            criterion = 'K5' if name.startswith('client ') else 'K7'
            c.check(criterion + ' reject ' + name, lambda payload=payload, raw=raw, headers=headers: invalid_request(payload, raw, headers))
        for method in ('PUT', 'PATCH', 'DELETE'):
            c.check('K5 ' + method + ' cannot update board status',
                    lambda method=method: require(server.request(method, '/api/board')[0] == 405, method + ' returns 405'))
        c.check('K7 unknown feedback task gets clear 404',
                lambda: require(server.answer('missing')[0] == 404, 'Missing task returns 404'))
        c.check('K7 task without feedback gets clear 409',
                lambda: require(server.answer('root')[0] == 409, 'Task without request returns 409'))
        prior = server.board()
        def save_choice():
            status, _, body = server.answer('leaf', feedback=base['tasks'][2]['feedback'])
            state = json.loads(body)
            assert status == 200, body
            saved = next(t for t in state['tasks'] if t['id'] == 'leaf')
            assert saved['feedback']['answer']['choice_id'] == 'link'
            assert saved['status'] == prior['tasks'][2]['status'] and saved['evidence'] == prior['tasks'][2]['evidence']
            assert saved['feedback']['answer']['submitted_at'] and state['revision'] > prior['revision']
            return '200 persists choice, comment and timestamp without status or evidence changes'
        c.check('K4 K5 answer choice saves without marking task complete', save_choice)
        def save_comment():
            status, _, body = server.answer('comment', choice=None, comment='Comment-only client answer', feedback=base['tasks'][3]['feedback'])
            assert status == 200, body
            answer = next(t for t in server.board()['tasks'] if t['id'] == 'comment')['feedback']['answer']
            assert answer['choice_id'] is None and answer['comment'] == 'Comment-only client answer'
            return 'Comment-only response survives GET reload'
        c.check('K4 comment-only answer persists on reload', save_comment)
        saved = server.board()
        c.check('K4 GET reload preserves saved answer', lambda: require(server.board() == saved, 'GET state matches saved response'))
        c.check('K4 duplicate identical response is idempotent',
                lambda: require(server.answer('leaf', feedback=base['tasks'][2]['feedback'])[0] == 200 and server.board() == saved, 'Repeat response returns same revision'))
        c.check('K4 conflicting second response fails without data loss',
                lambda: require(server.answer('leaf', choice='file', comment='Conflicting answer')[0] == 409 and server.board() == saved, '409 preserves first answer'))
        def race():
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(server.answer, 'race', choice, 'Concurrent ' + choice) for choice in ('link', 'file')]
                statuses = sorted(f.result()[0] for f in futures)
            assert statuses == [200, 409], statuses
            answer = next(t for t in server.board()['tasks'] if t['id'] == 'race')['feedback']['answer']
            assert answer['choice_id'] in ('link', 'file')
            return 'Two simultaneous different responses return 200 and 409'
        c.check('K4 concurrent conflicts preserve one answer', race)
        saved = server.board()
        old_token = server.token
        server.stop()
        with closing(sqlite3.connect(c.data / 'board.sqlite3')) as db, db:
            records = db.execute('SELECT task_id,question_key,feedback FROM feedback_records').fetchall()
            for task_id, key, value in records:
                feedback = json.loads(value)
                legacy_key = json.dumps({'question': feedback['question'], 'choices': feedback['choices']}, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
                db.execute('UPDATE feedback_records SET question_key=? WHERE task_id=? AND question_key=?', (legacy_key, task_id, key))
        server = Server(c.tool, c.data).start()
        c.check('K4 server restart migrates legacy request keys and preserves client responses', lambda: require(server.board() == saved, 'Restart state matches saved responses'))
        c.check('K7 old process CSRF token cannot save after restart',
                lambda: require(server.request('POST', '/api/tasks/leaf/feedback', {'choice_id': 'link', 'comment': 'Critic answer'},
                               headers=(['x-csrf-token'], [('X-CSRF-Token', old_token)]))[0] == 403, 'Old token returns 403'))
        def stale_apply():
            c.apply(base)
            state = server.board()
            for task_id in ('leaf', 'comment', 'race'):
                assert next(t for t in state['tasks'] if t['id'] == task_id)['feedback']['answer'] == next(t for t in saved['tasks'] if t['id'] == task_id)['feedback']['answer'], task_id
            return 'CLI applies original unanswered snapshot without erasing three saved answers'
        c.check('K4 stale CLI apply cannot erase client responses', stale_apply)
        forged = copy.deepcopy(base)
        forged['tasks'][2]['feedback']['answer'] = {'choice_id': 'file', 'comment': 'Agent tries overwrite', 'submitted_at': '2026-10-01T00:00:00+00:00'}
        c.check('K4 imported conflicting answer cannot overwrite client response',
                lambda: (c.apply(forged), require(server.board()['tasks'][2]['feedback']['answer'] == saved['tasks'][2]['feedback']['answer'], 'Saved client answer wins'))[-1])
        why_changed = copy.deepcopy(base)
        why_changed['tasks'][2]['feedback']['why'] = 'Agent clarified the reason.'
        def changed_conditions():
            c.apply(why_changed)
            leaf = server.board()['tasks'][2]
            assert leaf['feedback']['answer'] is None
            assert len(leaf['feedback_history']) == 1
            assert leaf['feedback_history'][0]['answer'] == saved['tasks'][2]['feedback']['answer']
            before = server.board()
            assert server.answer('leaf', feedback=base['tasks'][2]['feedback'])[0] == 409
            assert server.board() == before
            assert server.answer('leaf', comment='Accepted revised conditions', feedback=why_changed['tasks'][2]['feedback'])[0] == 200
            return 'Changed rationale archives prior approval, rejects stale expected_why and accepts reviewed conditions'
        c.check('K4 changed conditions require a new client decision', changed_conditions)
        changed = c.export()
        changed['tasks'][2]['feedback']['question'] = 'Choose the revised delivery format?'
        c.apply(changed)
        def changed_question():
            leaf = server.board()['tasks'][2]
            assert leaf['feedback']['answer'] is None
            history = leaf['feedback_history']
            assert len(history) == 2 and history[0]['question'] == base['tasks'][2]['feedback']['question']
            assert history[0]['answer'] == saved['tasks'][2]['feedback']['answer'] and history[0]['archived_at']
            before = server.board()
            assert server.answer('leaf', feedback=base['tasks'][2]['feedback'])[0] == 409
            assert server.board() == before
            return 'Changed question archives original answer and rejects stale expected_question'
        c.check('K4 question history survives update and stale draft conflicts', changed_question)
        c.check('K4 revised question accepts its own response',
                lambda: require(server.answer('leaf', choice='file', comment='Revised response', feedback=changed['tasks'][2]['feedback'])[0] == 200, 'Revised request accepts 200'))
        changed_choices = copy.deepcopy(changed)
        changed_choices['tasks'][2]['feedback']['choices'][0]['label'] = 'Secure link'
        c.apply(changed_choices)
        def choice_history():
            leaf = server.board()['tasks'][2]
            assert leaf['feedback']['answer'] is None and len(leaf['feedback_history']) == 3, leaf
            assert any(h['answer'] and h['answer']['comment'] == 'Revised response' for h in leaf['feedback_history'])
            before = server.board()
            assert server.answer('leaf', feedback=changed['tasks'][2]['feedback'])[0] == 409
            assert server.board() == before
            exported = c.export()
            restored = c.work / 'portable-copy'
            path = c.work / 'portable-history.json'
            path.write_text(json.dumps(exported))
            result = subprocess.run([sys.executable, str(c.tool), '--data-dir', str(restored), '--apply', str(path), '--export', str(c.work / 'portable-export.json')], capture_output=True, text=True, timeout=15)
            assert result.returncode == 0, result.stderr
            imported = json.loads((c.work / 'portable-export.json').read_text())
            assert imported['tasks'][2]['feedback_history'] == exported['tasks'][2]['feedback_history']
            return 'Choice-label change archives response, rejects stale options and exports/imports three history entries'
        c.check('K4 choice history and portable snapshot retain earlier answers', choice_history)
        xss = copy.deepcopy(changed_choices)
        hostile = '<img src=x onerror=alert(1)></script><script>alert(2)</script>'
        xss['project']['name'] = hostile
        xss['tasks'][2]['title'] = hostile
        xss['tasks'][2]['description'] = hostile
        xss['tasks'][2]['evidence'] = [hostile]
        xss['tasks'][2]['feedback']['question'] = hostile
        xss['tasks'][2]['feedback']['choices'][0]['label'] = hostile
        c.apply(xss)
        def safe_fields():
            status, headers, body = server.request('GET', '/api/board')
            data = json.loads(body)
            assert status == 200 and headers['Content-Type'].startswith('application/json')
            assert data['project']['name'] == hostile and data['tasks'][2]['title'] == hostile
            assert headers['X-Content-Type-Options'] == 'nosniff'
            status, headers, body = server.request('GET', '/')
            assert hostile.encode() not in body
            assert "script-src 'self'" in headers['Content-Security-Policy']
            return 'Untrusted markup stays in JSON text fields; HTML page contains no injected task text'
        c.check('K7 HTTP returns hostile text in JSON fields with HTML isolation', safe_fields)
        def failed_save():
            before = server.board()
            with closing(sqlite3.connect(c.data / 'board.sqlite3')) as db, db:
                db.execute("CREATE TRIGGER critic_fail_save BEFORE UPDATE ON feedback_records BEGIN SELECT RAISE(ABORT, 'critic fault'); END")
            try:
                status, _, body = server.answer('leaf', choice='link', comment='Save under injected DB fault', feedback=xss['tasks'][2]['feedback'])
                assert status == 500 and 'Could not save' in json.loads(body)['error'], (status, body)
                assert server.board() == before, 'Failed save changed state'
            finally:
                with closing(sqlite3.connect(c.data / 'board.sqlite3')) as db, db:
                    db.execute('DROP TRIGGER critic_fail_save')
            assert server.answer('leaf', choice='link', comment='Save after DB fault', feedback=xss['tasks'][2]['feedback'])[0] == 200
            return 'Injected SQLite write abort returns clear 500, preserves state and permits retry'
        c.check('K7 failed client save preserves state and allows recovery', failed_save)
        def failed_import():
            before = server.board()
            with closing(sqlite3.connect(c.data / 'board.sqlite3')) as db, db:
                db.execute("CREATE TRIGGER critic_fail_import BEFORE UPDATE ON board BEGIN SELECT RAISE(ABORT, 'critic fault'); END")
            try:
                c.apply(base, expected=2)
                assert server.board() == before, 'Failed CLI import lost answers or history'
            finally:
                with closing(sqlite3.connect(c.data / 'board.sqlite3')) as db, db:
                    db.execute('DROP TRIGGER critic_fail_import')
            return 'Injected SQLite transaction abort preserves active answer, archived history and board revision'
        c.check('K7 failed import transaction rolls back without state loss', failed_import)
        def failed_export():
            before = server.board()
            c.cli('--export', c.data / 'board.sqlite3', expected=2)
            c.cli('--export', c.work / 'absent-dir' / 'export.json', expected=2)
            assert server.board() == before
            return 'Export refuses database overwrite and missing directory without state loss'
        c.check('K7 failed export preserves local state', failed_export)
        history_saved = server.board()
        server.stop()
        server = Server(c.tool, c.data).start()
        c.check('K4 active and archived answers survive final server restart',
                lambda: require(server.board() == history_saved, 'Final restart preserves answer and three archived requests'))
        def recurring_conditions():
            cycle = Checks(c.tool, c.work / 'recurring-conditions')
            cycle.work.mkdir()
            state = fixture()
            state['tasks'] = [task('cycle', feedback=question())]
            state['tasks'][0]['feedback']['why'] = 'Condition A'
            cycle.apply(state)
            local = Server(c.tool, cycle.data).start()
            try:
                assert local.answer('cycle', comment='Approved A', feedback=state['tasks'][0]['feedback'])[0] == 200
                state['tasks'][0]['feedback']['why'] = 'Condition B'
                cycle.apply(state)
                assert local.answer('cycle', comment='Approved B', feedback=state['tasks'][0]['feedback'])[0] == 200
                state['tasks'][0]['feedback']['why'] = 'Condition A'
                cycle.apply(state)
                restored_a = cycle.export()
                leaf = restored_a['tasks'][0]
                assert leaf['feedback']['answer'] is None and len(leaf['feedback_history']) == 2, leaf
                assert [h['answer']['comment'] for h in leaf['feedback_history']] == ['Approved A', 'Approved B']
                assert local.answer('cycle', comment='Approved A again', feedback=state['tasks'][0]['feedback'])[0] == 200
                cycle.apply(restored_a)
                assert local.board()['tasks'][0]['feedback']['answer']['comment'] == 'Approved A again'
                for condition in ('Condition B', 'Condition A'):
                    state['tasks'][0]['feedback']['why'] = condition
                    cycle.apply(state)
                exported = cycle.export()
                assert exported['tasks'][0]['feedback']['answer'] is None
                assert len(exported['tasks'][0]['feedback_history']) == 4
                fresh = Checks(c.tool, cycle.work / 'fresh')
                fresh.work.mkdir()
                fresh.apply(exported)
                assert fresh.export()['tasks'][0]['feedback_history'] == exported['tasks'][0]['feedback_history']
                duplicate = copy.deepcopy(exported)
                duplicate['tasks'][0]['feedback_history'].append(copy.deepcopy(duplicate['tasks'][0]['feedback_history'][0]))
                fresh.apply(duplicate)
                imported = fresh.export()
                assert len(imported['tasks'][0]['feedback_history']) == 5
                fresh.apply(imported)
                assert fresh.export()['tasks'][0]['feedback_history'] == imported['tasks'][0]['feedback_history']
                return 'A/B/A/B/A keeps four prior occurrences, restores A unanswered, preserves identical-active saved answer and round-trips duplicate same-time history without growth'
            finally:
                local.stop()
        c.check('K4 recurring conditions preserve history and need renewed approval', recurring_conditions)
        def long_history():
            history_work = Checks(c.tool, c.work / 'long-history')
            history_work.work.mkdir()
            state = fixture()
            state['tasks'] = [task('history', feedback=question('Request 0?'))]
            for index in range(102):
                state['tasks'][0]['feedback']['question'] = f'Request {index}?'
                history_work.apply(state)
            exported = history_work.export()
            assert len(exported['tasks'][0]['feedback_history']) == 101
            path = history_work.work / 'restore.json'
            path.write_text(json.dumps(exported, indent=2, ensure_ascii=False) + '\n')
            restored = history_work.work / 'restored'
            output = history_work.work / 'restored.json'
            result = subprocess.run([sys.executable, str(c.tool), '--data-dir', str(restored), '--apply', str(path), '--export', str(output)], capture_output=True, text=True, timeout=15)
            assert result.returncode == 0, result.stderr
            assert json.loads(output.read_text())['tasks'][0]['feedback_history'] == exported['tasks'][0]['feedback_history']
            return '102 distinct CLI requests retain 101 prior decisions and reimport their own portable export'
        c.check('K4 more than 100 prior requests survive export and reimport', long_history)
        def snapshot_bound():
            oversized = fixture()
            oversized['tasks'] = [task(f'bounded-{index}') for index in range(1000)]
            for item in oversized['tasks']:
                item['description'] = 'x' * 1850
            compact = json.dumps(oversized, ensure_ascii=True).encode()
            pretty = (json.dumps(oversized, indent=2, ensure_ascii=False) + '\n').encode()
            assert len(compact) < 2 * 1024 * 1024 < len(pretty), (len(compact), len(pretty))
            result = c.rejected_import(oversized)
            assert 'snapshot exceeds' in result, result
            return 'Compact import fits 2 MiB, oversized portable snapshot fails and transaction keeps prior decisions'
        c.check('K7 portable size limit rolls back oversized merged state', snapshot_bound)
        def bounded_answer():
            bounded = Checks(c.tool, c.work / 'bounded-answer')
            bounded.work.mkdir()
            state = fixture()
            state['tasks'] = [task(f'bounded-{index}') for index in range(1000)]
            for item in state['tasks']:
                item['description'] = 'x' * 1820
            state['tasks'][0]['feedback'] = question()
            bounded.apply(state)
            local = Server(c.tool, bounded.data).start()
            try:
                before = local.board()
                status, _, body = local.answer('bounded-0', comment='x' * 12000, feedback=state['tasks'][0]['feedback'])
                assert status == 400 and 'snapshot exceeds' in json.loads(body)['error'], (status, body)
                assert local.board() == before, 'Oversized response changed answer or revision'
                assert local.answer('bounded-0', comment='Short reply', feedback=state['tasks'][0]['feedback'])[0] == 200
                return 'Response exceeding portable capacity rolls back; shorter response saves without losing decisions'
            finally:
                local.stop()
        c.check('K7 portable size limit rolls back oversized answer and permits retry', bounded_answer)
        c.check('K1 --demo cannot overwrite an existing project',
                lambda: (c.cli('--demo', '--export', c.work / 'demo-export.json'), require(server.board() == history_saved, 'Demo seed leaves existing project intact'))[-1])
    finally:
        server.stop()
        (c.work / 'server-startup.json').write_text(json.dumps(server.lines, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool', type=Path, default=Path(__file__).resolve().parent.parent / 'scripts' / 'board.py')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--work-dir', type=Path)
    args = parser.parse_args()
    tool = args.tool.resolve()
    if args.work_dir:
        args.work_dir.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix='run-', dir=args.work_dir))
    else:
        work = Path(tempfile.mkdtemp(prefix='prototyper-board-critic-'))
    report = args.report or work / 'results.json'
    before_hash = digest(tool)
    checks = Checks(tool, work)
    fatal = None
    try:
        run(checks)
    except Exception as error:
        fatal = type(error).__name__ + ': ' + str(error)
        print('HARNESS STOP ' + fatal, flush=True)
    failures = [r for r in checks.results if not r['passed']]
    result = {'tool': str(tool), 'source_sha256_before': before_hash, 'source_sha256_after': digest(tool),
              'work_dir': str(work), 'passed': len(checks.results) - len(failures), 'failed': len(failures),
              'fatal': fatal, 'checks': checks.results,
              'scope': 'CLI and HTTP backend behavior. Browser rendering and screenshots require a separate UI critic.'}
    report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'passed': result['passed'], 'failed': result['failed'], 'fatal': fatal, 'report': str(report), 'work_dir': str(work)}), flush=True)
    return 1 if failures or fatal else 0


if __name__ == '__main__':
    sys.exit(main())
