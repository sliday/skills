#!/usr/bin/env python3
"""Local progress board: Python standard library HTTP and SQLite.

Run from the client project. --apply FILE merges task work without erasing client
answers; --export FILE writes a portable snapshot; --demo seeds synthetic tasks.
"""
import argparse
from contextlib import contextmanager
import datetime
import html
import json
import os
import pathlib
import re
import secrets
import sqlite3
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

SCHEMA_VERSION = 1
MAX_BODY = 65536
MAX_IMPORT = 2 * 1024 * 1024
MAX_TASKS = 1000
MAX_DEPTH = 64
ASSETS = pathlib.Path(__file__).resolve().parent / 'board-assets'
IDENTIFIER = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z')
STATUSES = ('planned', 'building', 'ready', 'done')


class BoardError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='microseconds')


def empty_board():
    return {'schema_version': SCHEMA_VERSION, 'revision': 0, 'updated_at': None,
            'project': {'name': 'Your prototype', 'summary': 'No development tasks yet.',
                        'demo': False, 'prototype_url': None}, 'tasks': []}


def fields(value, required, optional, label):
    if not isinstance(value, dict):
        raise BoardError(f'{label} must be a JSON object')
    missing = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    if missing:
        raise BoardError(f'{label} needs these fields: {", ".join(sorted(missing))}')
    if extra:
        raise BoardError(f'{label} has unknown fields: {", ".join(sorted(extra))}')


def text_value(value, label, limit, required=False):
    if not isinstance(value, str) or len(value) > limit:
        raise BoardError(f'{label} must be text of at most {limit} characters')
    if required and not value.strip():
        raise BoardError(f'{label} needs some text')
    try:
        value.encode('utf-8')
    except UnicodeEncodeError:
        raise BoardError(f'{label} contains invalid text') from None
    if any(ord(character) < 32 and character not in '\n\r\t' for character in value):
        raise BoardError(f'{label} contains a control character')
    return value


def identifier(value, label):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise BoardError(f'{label} needs 1 to 80 letters, digits, underscores or hyphens, starting with a letter or digit')
    return value


def timestamp(value, label, nullable=False):
    if value is None and nullable:
        return None
    if not isinstance(value, str) or len(value) > 64:
        raise BoardError(f'{label} needs an ISO date and time with a timezone')
    try:
        parsed = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.utcoffset() is None:
            raise ValueError()
    except ValueError:
        raise BoardError(f'{label} needs an ISO date and time with a timezone') from None
    return value


def validate_answer(value, choices, label):
    if value is None:
        return None
    fields(value, ('choice_id', 'comment', 'submitted_at'), (), label)
    choice = value['choice_id']
    if choice is not None:
        identifier(choice, f'{label} choice ID')
    if choice is not None and choice not in {item['id'] for item in choices}:
        raise BoardError(f'{label} must use one of the listed choices')
    comment = text_value(value['comment'], f'{label} comment', 12000)
    if choice is None and not comment.strip():
        raise BoardError(f'{label} needs a choice or a comment')
    return {'choice_id': choice, 'comment': comment,
            'submitted_at': timestamp(value['submitted_at'], f'{label} time')}


def validate_feedback(value, label, history=False):
    if value is None and not history:
        return None
    fields(value, ('question', 'why', 'choices', 'answer'), ('archived_at',) if history else (), label)
    question = text_value(value['question'], f'{label} question', 2000, True)
    why = text_value(value['why'], f'{label} explanation', 4000)
    raw_choices = value['choices']
    if not isinstance(raw_choices, list) or len(raw_choices) > 20:
        raise BoardError(f'{label} needs at most 20 choices')
    choices, seen = [], set()
    for raw in raw_choices:
        fields(raw, ('id', 'label'), (), f'{label} choice')
        choice_id = identifier(raw['id'], f'{label} choice ID')
        if choice_id in seen:
            raise BoardError(f'{label} has duplicate choice IDs')
        seen.add(choice_id)
        choices.append({'id': choice_id, 'label': text_value(raw['label'], f'{label} choice label', 200, True)})
    result = {'question': question, 'why': why, 'choices': choices,
              'answer': validate_answer(value['answer'], choices, f'{label} answer')}
    if history:
        if 'archived_at' not in value:
            raise BoardError(f'{label} needs an archived_at time')
        result['archived_at'] = timestamp(value['archived_at'], f'{label} archive time')
    return result


def validate_board(value):
    fields(value, ('schema_version', 'project', 'tasks'), ('revision', 'updated_at'), 'Board')
    if type(value['schema_version']) is not int or value['schema_version'] != SCHEMA_VERSION:
        raise BoardError('Use board schema_version 1')
    revision = value.get('revision', 0)
    if type(revision) is not int or revision < 0:
        raise BoardError('Board revision must be a nonnegative whole number')
    updated_at = timestamp(value.get('updated_at'), 'Board update time', True)
    project = value['project']
    fields(project, ('name', 'summary', 'demo', 'prototype_url'), (), 'Project')
    if type(project['demo']) is not bool:
        raise BoardError('Project demo must be true or false')
    prototype_url = project['prototype_url']
    if prototype_url is not None:
        text_value(prototype_url, 'Prototype link', 2048, True)
        try:
            parsed = urlparse(prototype_url)
            if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError()
            parsed.port
        except ValueError:
            raise BoardError('Prototype link must be an HTTP or HTTPS URL without credentials') from None
        if project['demo']:
            raise BoardError('A demonstration board cannot claim a live prototype link')
    clean_project = {'name': text_value(project['name'], 'Project name', 120, True),
                     'summary': text_value(project['summary'], 'Project summary', 4000),
                     'demo': project['demo'], 'prototype_url': prototype_url}
    raw_tasks = value['tasks']
    if not isinstance(raw_tasks, list) or len(raw_tasks) > MAX_TASKS:
        raise BoardError(f'Board tasks must be a list of at most {MAX_TASKS} tasks')
    tasks, parents = [], {}
    for raw in raw_tasks:
        fields(raw, ('id', 'parent_id', 'title', 'description', 'status', 'evidence', 'feedback'), ('feedback_history',), 'Task')
        task_id = identifier(raw['id'], 'Task ID')
        if task_id in parents:
            raise BoardError(f'Task ID {task_id} appears more than once')
        parent_id = raw['parent_id']
        if parent_id is not None:
            identifier(parent_id, f'Parent ID for {task_id}')
        status = raw['status']
        if not isinstance(status, str) or status not in STATUSES:
            raise BoardError(f'Task {task_id} status must be planned, building, ready or done')
        evidence = raw['evidence']
        if not isinstance(evidence, list) or len(evidence) > 64:
            raise BoardError(f'Task {task_id} needs at most 64 evidence notes')
        task = {'id': task_id, 'parent_id': parent_id,
                'title': text_value(raw['title'], f'Task {task_id} title', 200, True),
                'description': text_value(raw['description'], f'Task {task_id} description', 12000),
                'status': status,
                'evidence': [text_value(item, f'Task {task_id} evidence', 4000, True) for item in evidence],
                'feedback': validate_feedback(raw['feedback'], f'Task {task_id} feedback')}
        history = raw.get('feedback_history', [])
        if not isinstance(history, list):
            raise BoardError(f'Task {task_id} prior feedback requests must be a list')
        if history:
            task['feedback_history'] = [validate_feedback(item, f'Task {task_id} prior feedback', True) for item in history]
        tasks.append(task)
        parents[task_id] = parent_id
    for task_id, parent_id in parents.items():
        if parent_id is not None and parent_id not in parents:
            raise BoardError(f'Task {task_id} names a missing parent: {parent_id}')
        seen, cursor = set(), task_id
        while cursor is not None:
            if cursor in seen:
                raise BoardError(f'Task {task_id} belongs to a parent cycle')
            seen.add(cursor)
            if len(seen) > MAX_DEPTH:
                raise BoardError(f'Task {task_id} exceeds {MAX_DEPTH} nesting levels')
            cursor = parents[cursor]
    return {'schema_version': SCHEMA_VERSION, 'revision': revision, 'updated_at': updated_at,
            'project': clean_project, 'tasks': tasks}


def question_key(feedback):
    return json.dumps({'question': feedback['question'], 'why': feedback['why'], 'choices': feedback['choices']},
                      ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def export_bytes(state):
    content = (json.dumps(state, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    if len(content) > MAX_IMPORT:
        raise BoardError(f'Board snapshot exceeds {MAX_IMPORT} bytes. Export decisions before splitting this project into separate boards')
    return content


def decode_json(data):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise BoardError(f'JSON repeats the field {key}')
            result[key] = value
        return result
    try:
        return json.loads(data.decode('utf-8'), object_pairs_hook=unique_keys,
                          parse_constant=lambda value: (_ for _ in ()).throw(BoardError('JSON cannot contain NaN or Infinity')))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        raise BoardError('Use valid UTF-8 JSON') from None


class Store:
    def __init__(self, directory):
        self.directory = pathlib.Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / 'board.sqlite3'
        self.lock = threading.Lock()
        with self.connect() as db:
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0, SCHEMA_VERSION):
                raise BoardError('This board database uses a newer format. Use its matching board tool')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS board (id INTEGER PRIMARY KEY CHECK (id=1), state TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS feedback_records (
                    task_id TEXT NOT NULL, question_key TEXT NOT NULL, feedback TEXT NOT NULL,
                    archived_at TEXT, PRIMARY KEY (task_id, question_key)
                );
                PRAGMA user_version=1;
            ''')
            for record in db.execute('SELECT rowid,task_id,question_key,feedback,archived_at FROM feedback_records').fetchall():
                key = question_key(json.loads(record['feedback']))
                if record['archived_at'] is not None:
                    key += ':archive:' + str(record['rowid'])
                if key != record['question_key']:
                    db.execute('UPDATE feedback_records SET question_key=? WHERE task_id=? AND question_key=?',
                               (key, record['task_id'], record['question_key']))
        self.directory.chmod(0o700)
        self.path.chmod(0o600)

    @contextmanager
    def connect(self, write=False):
        db = sqlite3.connect(self.path, timeout=5)
        try:
            db.row_factory = sqlite3.Row
            db.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
            with db:
                yield db
        finally:
            db.close()

    def _board(self, db):
        row = db.execute('SELECT state FROM board WHERE id=1').fetchone()
        state = json.loads(row['state']) if row else empty_board()
        records = {}
        for record in db.execute('SELECT * FROM feedback_records ORDER BY archived_at, rowid'):
            records.setdefault(record['task_id'], []).append(record)
        for task in state['tasks']:
            active_key = question_key(task['feedback']) if task['feedback'] else None
            history = []
            for record in records.get(task['id'], []):
                feedback = json.loads(record['feedback'])
                if record['archived_at']:
                    feedback['archived_at'] = record['archived_at']
                    history.append(feedback)
                elif record['question_key'] == active_key:
                    task['feedback']['answer'] = feedback['answer']
            if history:
                task['feedback_history'] = history
        return state

    def board(self):
        with self.connect() as db:
            return self._board(db)

    def _put_feedback(self, db, task_id, feedback, archived_at, occurrence=1):
        clean = {key: feedback[key] for key in ('question', 'why', 'choices', 'answer')}
        key = question_key(clean)
        if archived_at is not None:
            count = db.execute('SELECT COUNT(*) FROM feedback_records WHERE task_id=? AND feedback=? AND archived_at=?',
                               (task_id, json.dumps(clean, ensure_ascii=False), archived_at)).fetchone()[0]
            if count >= occurrence:
                return clean
            key += ':archive:' + secrets.token_hex(16)
        else:
            existing = db.execute('SELECT feedback FROM feedback_records WHERE task_id=? AND question_key=?', (task_id, key)).fetchone()
            if existing:
                clean['answer'] = json.loads(existing['feedback'])['answer']
        db.execute('''INSERT INTO feedback_records(task_id,question_key,feedback,archived_at) VALUES(?,?,?,?)
            ON CONFLICT(task_id,question_key) DO UPDATE SET feedback=excluded.feedback,archived_at=excluded.archived_at''',
                   (task_id, key, json.dumps(clean, ensure_ascii=False), archived_at))
        return clean

    def apply(self, value, seed=False):
        state = validate_board(value)
        with self.lock, self.connect(write=True) as db:
            existing = db.execute('SELECT state FROM board WHERE id=1').fetchone()
            if seed and existing:
                return self._board(db), False
            previous = self._board(db)
            previous_requests = {task['id']: question_key(task['feedback']) if task['feedback'] else None for task in previous['tasks']}
            stamp = now()
            active = {task['id']: question_key(task['feedback']) for task in state['tasks'] if task['feedback']}
            for record in db.execute('SELECT rowid,task_id,question_key FROM feedback_records WHERE archived_at IS NULL').fetchall():
                if active.get(record['task_id']) != record['question_key']:
                    db.execute('UPDATE feedback_records SET archived_at=?,question_key=? WHERE task_id=? AND question_key=?',
                               (stamp, record['question_key'] + ':archive:' + str(record['rowid']), record['task_id'], record['question_key']))
            for task in state['tasks']:
                if task['feedback'] and task['id'] in previous_requests and active[task['id']] != previous_requests[task['id']]:
                    task['feedback']['answer'] = None
                occurrences = {}
                for item in task.pop('feedback_history', []):
                    fingerprint = json.dumps(item, ensure_ascii=False, sort_keys=True)
                    occurrences[fingerprint] = occurrences.get(fingerprint, 0) + 1
                    self._put_feedback(db, task['id'], item, item['archived_at'], occurrences[fingerprint])
                if task['feedback']:
                    task['feedback'] = self._put_feedback(db, task['id'], task['feedback'], None)
            state['revision'] = previous['revision'] + 1
            state['updated_at'] = stamp
            db.execute('INSERT INTO board(id,state) VALUES(1,?) ON CONFLICT(id) DO UPDATE SET state=excluded.state',
                       (json.dumps(state, ensure_ascii=False),))
            result = self._board(db)
            export_bytes(result)
            return result, True

    def answer(self, task_id, payload):
        fields(payload, ('choice_id', 'comment'), ('expected_question', 'expected_choices', 'expected_why'), 'Response')
        comment = text_value(payload['comment'], 'Response comment', 12000)
        choice_id = payload['choice_id']
        if choice_id is not None:
            identifier(choice_id, 'Response choice ID')
        if choice_id is None and not comment.strip():
            raise BoardError('Choose an option or write a comment')
        if 'expected_question' in payload:
            text_value(payload['expected_question'], 'Expected question', 2000, True)
        if 'expected_why' in payload:
            text_value(payload['expected_why'], 'Expected explanation', 4000)
        if 'expected_choices' in payload:
            validate_feedback({'question': 'Expected question', 'why': '', 'choices': payload['expected_choices'], 'answer': None}, 'Expected choices')
        with self.lock, self.connect(write=True) as db:
            state = self._board(db)
            task = next((item for item in state['tasks'] if item['id'] == task_id), None)
            if task is None:
                raise BoardError('This task no longer exists. Reload the board', 404)
            feedback = task['feedback']
            if feedback is None:
                raise BoardError('This task has no current feedback request. Reload the board', 409)
            if 'expected_question' in payload and payload['expected_question'] != feedback['question']:
                raise BoardError('The team changed this question. Review the new question before sending your draft', 409)
            if 'expected_choices' in payload and payload['expected_choices'] != feedback['choices']:
                raise BoardError('The team changed these options. Review the new options before sending your draft', 409)
            if 'expected_why' in payload and payload['expected_why'] != feedback['why']:
                raise BoardError('The team changed the conditions. Review the new explanation before sending your draft', 409)
            if choice_id is not None and choice_id not in {item['id'] for item in feedback['choices']}:
                raise BoardError('Choose one of the current options or send a comment')
            if feedback['answer']:
                answer = feedback['answer']
                if answer['choice_id'] == choice_id and answer['comment'] == comment:
                    return state
                raise BoardError('You have answered this question. Reload the board to see your saved response', 409)
            stamp = now()
            feedback['answer'] = {'choice_id': choice_id, 'comment': comment, 'submitted_at': stamp}
            db.execute('UPDATE feedback_records SET feedback=? WHERE task_id=? AND question_key=?',
                       (json.dumps(feedback, ensure_ascii=False), task_id, question_key(feedback)))
            for item in state['tasks']:
                item.pop('feedback_history', None)
            state['revision'] += 1
            state['updated_at'] = stamp
            db.execute('UPDATE board SET state=? WHERE id=1', (json.dumps(state, ensure_ascii=False),))
            result = self._board(db)
            export_bytes(result)
            return result


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(10)
        return connection, address


class Handler(BaseHTTPRequestHandler):
    server_version = 'PrototypeProgress/1'

    def log_message(self, format, *args):
        pass

    def loopback(self, value, origin=False):
        try:
            parsed = urlparse(value if origin else 'http://' + value)
            return (parsed.hostname in ('127.0.0.1', 'localhost') and parsed.port == self.server.server_port
                    and parsed.scheme == 'http' and not parsed.username and not parsed.password
                    and not parsed.path and not parsed.query and not parsed.fragment)
        except (ValueError, TypeError):
            return False

    def allowed(self, write=False):
        hosts = self.headers.get_all('Host', [])
        if len(hosts) != 1 or not self.loopback(hosts[0]):
            self.send_json({'error': 'Use this server\u2019s local address'}, 403)
            return False
        origins = self.headers.get_all('Origin', [])
        if len(origins) > 1 or (origins and not self.loopback(origins[0], True)) or self.headers.get('Sec-Fetch-Site') == 'cross-site':
            self.send_json({'error': 'Open this board from its local address'}, 403)
            return False
        tokens = self.headers.get_all('X-CSRF-Token', [])
        if write and (len(tokens) != 1 or not secrets.compare_digest(tokens[0].encode('utf-8'), self.server.token.encode('ascii'))):
            self.send_json({'error': 'Refresh this local page before saving'}, 403)
            return False
        return True

    def send(self, data, content_type, status=200):
        data = data.encode('utf-8') if isinstance(data, str) else data
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, value, status=200):
        self.send(json.dumps(value, ensure_ascii=False), 'application/json; charset=utf-8', status)

    def do_GET(self):
        if not self.allowed():
            return
        path = urlparse(self.path).path
        try:
            if path == '/api/board':
                self.send_json(self.server.store.board())
            elif path == '/health':
                self.send_json({'ok': True, 'schema_version': SCHEMA_VERSION})
            elif path in ('/', '/index.html'):
                page = (ASSETS / 'index.html').read_text(encoding='utf-8').replace('__CSRF__', html.escape(self.server.token, quote=True))
                self.send(page, 'text/html; charset=utf-8')
            elif path in ('/app.js', '/style.css', '/daub.css', '/assets/app.js', '/assets/style.css', '/assets/daub.css'):
                self.send((ASSETS / path.rsplit('/', 1)[1]).read_bytes(), 'text/javascript; charset=utf-8' if path.endswith('.js') else 'text/css; charset=utf-8')
            else:
                self.send_json({'error': 'Route not found'}, 404)
        except (sqlite3.Error, ValueError, KeyError, TypeError):
            self.send_json({'error': 'Could not read the local board. Check the data directory'}, 500)
        except OSError:
            self.send_json({'error': 'Could not read the local page files. Check the installed skill files'}, 500)

    def do_POST(self):
        if not self.allowed(write=True):
            return
        try:
            lengths = self.headers.get_all('Content-Length', [])
            if len(lengths) != 1 or not re.fullmatch(r'[0-9]{1,10}', lengths[0]) or self.headers.get('Transfer-Encoding'):
                raise BoardError('Send a JSON body with one Content-Length header')
            length = int(lengths[0])
            if not 0 < length <= MAX_BODY:
                raise BoardError(f'Request size must be between 1 and {MAX_BODY} bytes')
            if self.headers.get('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
                raise BoardError('Send JSON data')
            data = self.rfile.read(length)
            if len(data) != length:
                raise BoardError('The request ended before its JSON body arrived')
            payload = decode_json(data)
            path = urlparse(self.path).path
            pieces = path.strip('/').split('/')
            if len(pieces) != 4 or pieces[:2] != ['api', 'tasks'] or pieces[3] != 'feedback':
                raise BoardError('Route not found', 404)
            identifier(pieces[2], 'Task ID')
            self.send_json(self.server.store.answer(pieces[2], payload))
        except BoardError as error:
            self.send_json({'error': str(error)}, error.status)
        except (OSError, sqlite3.Error):
            self.send_json({'error': 'Could not save your response. Check the data directory and try again'}, 500)

    def do_OPTIONS(self):
        if self.allowed():
            self.send_json({'error': 'Use GET to read this board or POST to answer a question'}, 405)

    do_PUT = do_DELETE = do_PATCH = do_OPTIONS


def demo_board():
    def task(task_id, parent, title, status, description, feedback=None, evidence=None):
        return {'id': task_id, 'parent_id': parent, 'title': title, 'description': description,
                'status': status, 'evidence': evidence or [], 'feedback': feedback}
    return {'schema_version': SCHEMA_VERSION,
            'project': {'name': 'Quote helper demonstration',
                        'summary': 'Synthetic tasks show how you can follow work and answer team questions. No live prototype exists in this example.',
                        'demo': True, 'prototype_url': None},
            'tasks': [
                task('quote-flow', None, 'Create a quote (demo)', 'building',
                     'Synthetic work: add an item, check the price and choose a delivery format.',
                     {'question': 'How should a customer receive the quote?', 'why': 'Your sample answer changes the delivery step in this demonstration.',
                      'choices': [{'id': 'link', 'label': 'Shareable link'}, {'id': 'file', 'label': 'PDF attachment'}], 'answer': None}),
                task('quote-items', 'quote-flow', 'Add work items (demo)', 'building', 'Synthetic child board for entering the work and its price.'),
                task('quote-price', 'quote-items', 'Check the item total (demo)', 'planned', 'Synthetic third level: review how a quantity affects the total.',
                     {'question': 'Should the customer see the hourly rate?', 'why': 'This sample decision affects the price display.',
                      'choices': [{'id': 'visible', 'label': 'Show the rate'}, {'id': 'total', 'label': 'Show the total only'}], 'answer': None}),
                task('sample-preview', None, 'Review a sample preview (demo)', 'ready', 'This card demonstrates Ready to try. The example contains no working quote prototype.',
                     evidence=['Simulated evidence: a sample user adds an item and sees the total. This illustrates an evidence note; the team has not tested a live quote prototype.']),
                task('quote-copy', None, 'Name the first action (demo)', 'done', 'Synthetic completed task used to demonstrate the Done column.',
                     evidence=['Simulated decision: the sample first action reads Create a quote.']),
                task('quote-delivery', None, 'Prepare delivery (demo)', 'planned', 'Synthetic next step that depends on your sample delivery answer.')
            ]}


def write_export(path, state, store):
    path = pathlib.Path(path).resolve()
    if path == store.path or path.name in {store.path.name + '-wal', store.path.name + '-shm', store.path.name + '-journal'} and path.parent == store.directory:
        raise BoardError('Choose an export file outside the board database files')
    content = export_bytes(state)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.' + path.name + '.', dir=path.parent, delete=False) as output:
            temporary = pathlib.Path(output.name)
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=pathlib.Path, default=pathlib.Path.cwd() / '.prototype-progress')
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--apply', type=pathlib.Path, metavar='FILE')
    parser.add_argument('--export', type=pathlib.Path, metavar='FILE')
    parser.add_argument('--demo', action='store_true')
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('Port must be between 0 and 65535')
    if args.apply and args.demo:
        parser.error('Choose --apply or --demo for this run')
    try:
        incoming = None
        if args.apply:
            with args.apply.open('rb') as source:
                data = source.read(MAX_IMPORT + 1)
            if len(data) > MAX_IMPORT:
                raise BoardError(f'Board file must be at most {MAX_IMPORT} bytes')
            incoming = validate_board(decode_json(data))
        store = Store(args.data_dir)
        if incoming is not None:
            state, _ = store.apply(incoming)
            print(f'Applied {len(state["tasks"])} tasks. Board revision {state["revision"]}. Client responses retained.', flush=True)
        if args.demo:
            _, seeded = store.apply(demo_board(), seed=True)
            print('Seeded synthetic demonstration tasks. No live prototype exists.' if seeded else 'Kept the existing board. Demonstration data did not replace it.', flush=True)
        if args.export:
            write_export(args.export, store.board(), store)
            print(f'Exported board to {args.export.resolve()}', flush=True)
        if args.apply or args.export:
            return 0
        server = LocalServer(('127.0.0.1', args.port), Handler)
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
        return 0
    except (BoardError, OSError, sqlite3.Error) as error:
        detail = str(error) if isinstance(error, BoardError) else 'Check the file paths, directory permissions and available disk space'
        print(f'Board error: {detail}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
