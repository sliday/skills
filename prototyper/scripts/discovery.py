#!/usr/bin/env python3
"""Local discovery: Python stdlib HTTP + SQLite, with no external requests.

Run from the client project: python3 /path/to/skill/scripts/discovery.py
Use --data-dir PATH for a different database directory; --port defaults to 0.
Use --list or --export PROJECT_ID --output-dir PATH for agent access without UI.
"""
import argparse
from contextlib import contextmanager
import datetime
import html
import ipaddress
import json
import pathlib
import secrets
import sqlite3
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

VERSION = '1.0.0'
MAX_BODY = 65536
ASSETS = pathlib.Path(__file__).resolve().parent / 'assets'
QUESTIONS = [
    ('medium', 'What kind of solution are you considering?', 'Choose the closest fit. You can change it later.', ['Website', 'App', 'Service', 'Unsure']),
    ('user', 'Who will use this?', 'Name a specific person or role. Describe them without sharing personal information.'),
    ('situation', 'When will they need it?', 'Describe the situation that starts the task.'),
    ('job', 'What will they try to accomplish?', 'Describe the result they want in their own terms.'),
    ('workaround', 'How do they handle this today?', 'Name the current workaround and where it causes trouble.'),
    ('flow', 'What is the one flow your prototype should demonstrate?', 'Write a start, the main action and a finish. Keep the first version small.'),
    ('constraints', 'What limits do we need to respect?', 'Consider time, budget, access, accessibility, policy and existing systems.'),
    ('data', 'What data will the prototype need?', 'Describe sources, who may access them and whether mock data will work. Do not paste secrets or personal records.'),
    ('assumption', 'What is the riskiest assumption?', 'Name one thing that must be true for the idea to help its user.'),
    ('non-goals', 'What should we leave out of this version?', 'Name features, users or situations that can wait.'),
    ('failure', 'What should happen when the main flow fails?', 'Think about missing data, mistakes, unavailable services and ways to recover.'),
    ('style', 'What should the experience look and feel like?', 'Describe references, tone, readability and accessibility needs. A URL is a reference, we will not fetch it.'),
    ('stack', 'What technology or integration choices matter?', 'Name existing tools or preferences. Write “unknown” if you want the team to decide.'),
    ('acceptance', 'How will you judge whether this prototype works?', 'Give observable checks for the main flow, failure states and usability. Separate machine checks from human review.'),
    ('evidence', 'How will you test the assumption with a user?', 'Describe who should try it, what you will observe and what would change your mind.'),
    ('handoff', 'What will your design and development team need next?', 'Name setup information, decisions, open questions and ownership they need to continue.'),
]
BRANCHES = {
    'website': [('website-purpose', 'What should a visit to the website achieve?', 'Choose one useful outcome rather than a list of pages.'), ('website-entry', 'How will a visitor arrive and find their next action?', 'Describe the entry page, discovery route and any account requirements.')],
    'app': [('app-context', 'On which devices and in what context will the app run?', 'Mention desktop, mobile, browser or offline use if it matters.'), ('app-access', 'How will someone start using the app?', 'Describe installation, sign-in and permissions, or say these are unnecessary.')],
    'service': [('service-touchpoint', 'Where will the user interact with the service?', 'Consider conversation, forms, email, an existing tool or an in-person step.'), ('service-delivery', 'Which steps need a person, and which could software handle?', 'Describe the service boundary and the person responsible for delivery.')],
    'unsure': [('unsure-form', 'What would help you choose a form for this solution?', 'Name access, device, frequency or operational factors that matter.'), ('unsure-test', 'What is the simplest way to test the main task?', 'A sketch, conversation or manual service can be enough before software.')],
}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


def question(row, parent=None):
    return {'id': row[0], 'prompt': row[1], 'help': row[2], 'options': row[3] if len(row) > 3 else [], 'parent': parent, 'pack_version': VERSION}


class Store:
    def __init__(self, directory):
        self.directory = directory.resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / 'discovery.sqlite3'
        self.lock = threading.Lock()
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL, cursor INTEGER NOT NULL DEFAULT 0, pack_version TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS answers (
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    question_id TEXT NOT NULL, prompt TEXT NOT NULL, help TEXT NOT NULL,
                    parent TEXT, answer TEXT NOT NULL, status TEXT NOT NULL,
                    pack_version TEXT NOT NULL, updated_at TEXT NOT NULL,
                    PRIMARY KEY(project_id, question_id)
                );
            ''')
        try:
            self.directory.chmod(0o700)
            self.path.chmod(0o600)
        except OSError:
            pass

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        try:
            db.row_factory = sqlite3.Row
            db.execute('PRAGMA foreign_keys=ON')
            with db:
                yield db
        finally:
            db.close()

    def projects(self):
        with self.connect() as db:
            return [dict(row) for row in db.execute('SELECT * FROM projects ORDER BY updated_at DESC')]

    def project(self, identifier):
        with self.connect() as db:
            project = db.execute('SELECT * FROM projects WHERE id=?', (identifier,)).fetchone()
            if project is None:
                raise ValueError('Project not found')
            answers = {row['question_id']: dict(row) for row in db.execute('SELECT * FROM answers WHERE project_id=?', (identifier,))}
        medium = answers.get('medium', {}).get('answer', 'unsure').strip().lower()
        branch = BRANCHES.get(medium, BRANCHES['unsure'])
        questions = [question(QUESTIONS[0])] + [question(row, 'medium') for row in branch] + [question(row) for row in QUESTIONS[1:]]
        return {'project': dict(project), 'questions': questions, 'answers': answers, 'data_dir': str(self.directory)}

    def create(self, name):
        if not isinstance(name, str) or not name.strip() or len(name) > 120:
            raise ValueError('Use a project name between 1 and 120 characters')
        identifier = str(uuid.uuid4())
        stamp = now()
        with self.lock, self.connect() as db:
            db.execute('INSERT INTO projects(id,name,created_at,updated_at,pack_version) VALUES(?,?,?,?,?)', (identifier, name.strip(), stamp, stamp, VERSION))
        return self.project(identifier)

    def save(self, identifier, payload):
        state = self.project(identifier)
        if set(payload) - {'question_id', 'answer', 'status', 'cursor'}:
            raise ValueError('Unknown answer fields')
        q = next((item for item in state['questions'] if item['id'] == payload.get('question_id')), None)
        answer, status = payload.get('answer'), payload.get('status')
        cursor = payload.get('cursor', state['project']['cursor'])
        if q is None or not isinstance(answer, str) or len(answer) > 12000 or status not in ('draft', 'answered', 'skipped'):
            raise ValueError('Invalid answer')
        if q['id'] == 'medium' and status == 'answered' and answer.strip().lower() not in BRANCHES:
            raise ValueError('Choose Website, App, Service or Unsure')
        if status == 'answered' and not answer.strip():
            raise ValueError('Write an answer or skip this question')
        if not isinstance(cursor, int) or isinstance(cursor, bool) or not 0 <= cursor < len(state['questions']):
            raise ValueError('Invalid question position')
        stamp = now()
        with self.lock, self.connect() as db:
            db.execute('''INSERT INTO answers VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(project_id,question_id) DO UPDATE SET prompt=excluded.prompt,
                help=excluded.help,parent=excluded.parent,answer=excluded.answer,status=excluded.status,
                pack_version=excluded.pack_version,updated_at=excluded.updated_at''',
                (identifier, q['id'], q['prompt'], q['help'], q['parent'], answer, status, VERSION, stamp))
            db.execute('UPDATE projects SET cursor=?,updated_at=? WHERE id=?', (cursor, stamp, identifier))
        return self.project(identifier)

    def delete(self, identifier):
        with self.lock, self.connect() as db:
            result = db.execute('DELETE FROM projects WHERE id=?', (identifier,))
            if result.rowcount == 0:
                raise ValueError('Project not found')

    def export(self, identifier):
        state = self.project(identifier)
        active = state['questions']
        active_ids = {item['id'] for item in active}
        completed = {qid: row['answer'].strip() for qid, row in state['answers'].items() if qid in active_ids and row['status'] == 'answered'}
        unknowns = [item['prompt'] for item in active if item['id'] not in completed]
        value = lambda key: completed.get(key, 'Unknown. Discuss this before implementation.')
        project_name = state['project']['name'].replace('\n', ' ')
        lines = [f'# {project_name}', '', '## Prototype goal', value('job'), '', '## User and situation', value('user'), '', value('situation'), '', '## Current workaround', value('workaround'), '', '## Solution form', value('medium')]
        for item in active[1:3]:
            lines += ['', '### ' + item['prompt'], value(item['id'])]
        for heading, key in [('One flow to build', 'flow'), ('Constraints', 'constraints'), ('Data and access', 'data'), ('Riskiest assumption', 'assumption'), ('Leave out of this version', 'non-goals'), ('Failure states and recovery', 'failure'), ('Design constraints', 'style'), ('Technology and integrations', 'stack'), ('Acceptance checks', 'acceptance'), ('User feedback and evidence', 'evidence'), ('Handoff', 'handoff')]:
            lines += ['', '## ' + heading, value(key)]
        lines += ['', '## Unknowns and skipped questions'] + ['- ' + prompt for prompt in unknowns]
        if not unknowns:
            lines += ['No unanswered questions. Treat untested claims as assumptions.']
        lines += ['', '## Working boundary', 'Build the one flow above. Keep the cuts and unresolved questions visible. Use mock data unless this brief authorizes a specific source. Confirm setup and verification steps with the team. Do not treat a working prototype as evidence of user demand.', '']
        bar = [f'# Acceptance bar: {project_name}', '', 'Keep this bar fixed while you review the prototype. Revise it only when the owner changes the goal.', '', '## User-provided acceptance checks', value('acceptance'), '', '## Machine-verifiable proof', '- [ ] Add an executable proof for the one flow and record its command and exit code.', '- [ ] Check the documented setup from a clean start.', '- [ ] Check the specified failure states and recovery paths.', '- [ ] Confirm the cuts remain outside the prototype.', '', '## Human review and evidence', '- [ ] Observe the intended user attempting the task.', '- [ ] Record the outcome against the riskiest assumption.', '- [ ] Inspect accessibility and the design constraints in the intended context.', '', '### Assumption to test', value('assumption'), '', '### Feedback plan', value('evidence'), '', '## Review report', 'VERDICT: pass or fail', 'GAP: the largest remaining gap', 'EVIDENCE: what you inspected, with commands, observations or file paths', '', 'Do not mark a check complete without its evidence. Unknowns need an owner before production work.', '']
        provenance = {'pack_version': VERSION, 'exported_at': now(), 'project': state['project'], 'active_questions': active,
                      'answers': list(state['answers'].values()), 'unknowns': unknowns,
                      'note': 'Inactive branch answers remain in this local record for edit history; the PRD uses only the active branch.'}
        return {'discovery.json': json.dumps(provenance, indent=2, ensure_ascii=False) + '\n', 'PRD.md': '\n'.join(lines), 'BAR.md': '\n'.join(bar)}


class Handler(BaseHTTPRequestHandler):
    server_version = 'PrototypeDiscovery/1'

    def log_message(self, format, *args):
        pass

    def loopback(self, value, origin=False):
        try:
            parsed = urlparse(value if origin else 'http://' + value)
            hostname = parsed.hostname
            local = hostname == 'localhost' or ipaddress.ip_address(hostname).is_loopback
            return local and parsed.port == self.server.server_port and parsed.scheme == 'http' and not parsed.username and not parsed.password
        except (ValueError, TypeError):
            return False

    def allowed(self, write=False):
        if not self.loopback(self.headers.get('Host', '')):
            self.send_json({'error': 'Use this server’s loopback address'}, 403)
            return False
        origin = self.headers.get('Origin')
        if origin and not self.loopback(origin, True):
            self.send_json({'error': 'Third-party origins cannot access discovery'}, 403)
            return False
        if write and not secrets.compare_digest(self.headers.get('X-CSRF-Token', ''), self.server.token):
            self.send_json({'error': 'Refresh this local page before saving'}, 403)
            return False
        return True

    def send(self, data, content_type, status=200, filename=None):
        data = data.encode('utf-8') if isinstance(data, str) else data
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        if filename:
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, value, status=200):
        self.send(json.dumps(value, ensure_ascii=False), 'application/json; charset=utf-8', status)

    def do_GET(self):
        if not self.allowed():
            return
        path = urlparse(self.path).path
        try:
            if path == '/health':
                self.send_json({'ok': True, 'pack_version': VERSION, 'data_dir': str(self.server.store.directory)})
            elif path == '/api/projects':
                self.send_json({'projects': self.server.store.projects(), 'data_dir': str(self.server.store.directory), 'pack_version': VERSION})
            elif path.startswith('/api/projects/'):
                pieces = path.strip('/').split('/')
                identifier = pieces[2]
                if len(pieces) == 3:
                    self.send_json(self.server.store.project(identifier))
                elif len(pieces) == 5 and pieces[3] == 'export' and pieces[4] in ('discovery.json', 'PRD.md', 'BAR.md'):
                    name = pieces[4]
                    self.send(self.server.store.export(identifier)[name], 'application/json; charset=utf-8' if name.endswith('.json') else 'text/markdown; charset=utf-8', filename=name)
                else:
                    self.send_json({'error': 'Route not found'}, 404)
            elif path in ('/', '/index.html'):
                page = (ASSETS / 'index.html').read_text().replace('__CSRF__', html.escape(self.server.token, quote=True))
                self.send(page, 'text/html; charset=utf-8')
            elif path in ('/app.js', '/style.css'):
                self.send((ASSETS / path[1:]).read_bytes(), 'text/javascript; charset=utf-8' if path.endswith('.js') else 'text/css; charset=utf-8')
            else:
                self.send_json({'error': 'Route not found'}, 404)
        except ValueError as error:
            self.send_json({'error': str(error)}, 404)

    def do_POST(self):
        if not self.allowed(write=True):
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= MAX_BODY:
                raise ValueError('Request size must be between 1 and 65536 bytes')
            if self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json':
                raise ValueError('Send JSON data')
            payload = json.loads(self.rfile.read(length).decode('utf-8'))
            if not isinstance(payload, dict):
                raise ValueError('Send a JSON object')
            path = urlparse(self.path).path
            if path == '/api/projects':
                if set(payload) != {'name'}:
                    raise ValueError('Use only a project name')
                self.send_json(self.server.store.create(payload['name']), 201)
            else:
                pieces = path.strip('/').split('/')
                if len(pieces) != 4 or pieces[:2] != ['api', 'projects']:
                    self.send_json({'error': 'Route not found'}, 404)
                    return
                if pieces[3] == 'answer':
                    self.send_json(self.server.store.save(pieces[2], payload))
                elif pieces[3] == 'delete' and payload == {}:
                    self.server.store.delete(pieces[2])
                    self.send_json({'ok': True})
                else:
                    self.send_json({'error': 'Route not found'}, 404)
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
            self.send_json({'error': str(error)}, 400)
        except sqlite3.Error:
            self.send_json({'error': 'Could not save to SQLite. Check the data directory and try again.'}, 500)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=pathlib.Path, default=pathlib.Path.cwd() / '.prototype-discovery')
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--export', metavar='PROJECT_ID')
    parser.add_argument('--output-dir', type=pathlib.Path)
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('Port must be between 0 and 65535')
    store = Store(args.data_dir)
    if args.list:
        print(json.dumps(store.projects(), indent=2, ensure_ascii=False))
        return
    if args.export:
        if not args.output_dir:
            parser.error('--export requires --output-dir')
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, content in store.export(args.export).items():
            (args.output_dir / name).write_text(content)
        print(str(args.output_dir.resolve()), flush=True)
        return
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.store, server.token = store, secrets.token_urlsafe(32)
    print(f'Open http://127.0.0.1:{server.server_port}/', flush=True)
    print(f'Local data: {store.path}', flush=True)
    print('Press Ctrl+C to stop. Nothing uploads.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
