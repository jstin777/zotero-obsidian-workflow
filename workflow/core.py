"""Local, deterministic reading workflow. Zotero remains the source of imported text."""
from __future__ import annotations
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo
import yaml
from markdownify import markdownify

LOCAL = '<!-- zotero-local-review -->'
COLORS = {'#aaaaaa': ('Gray', 'Context'), '#ffd400': ('Yellow', 'Claims, results, supporting evidence'),
 '#2ea8e5': ('Blue', 'Definitions, theory, models, background'), '#5fb236': ('Green', 'Methods, operational definitions, analysis'),
 '#ff6666': ('Red', 'Limitations, contradictions, uncertainty, questions'), '#a28ae5': ('Purple', 'Ideas, connections, interpretations'),
 '#f19837': ('Orange', 'Follow-up actions and reading'), '#e56eee': ('Magenta', 'Recall and possible flashcards')}
READING = {'reading/unread': 'unread', '⏳': 'reading', '✅': 'read'}
ORIGINS = {'🌱 origin/personal': 'personal', '👤 origin/recommended': 'recommended', '🔎 origin/literature-search': 'literature-search'}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''): h.update(part)
    return h.hexdigest()


def read_json(path, default=None):
    return json.loads(Path(path).read_text()) if Path(path).exists() else default


def atomic(path, text):
    path = Path(path)
    if path.exists() and path.read_text() == text: return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(text); f.flush(); os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)


def save(path, value): atomic(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def safe_part(value):
    value = re.sub(r'[\\/:*?"<>|\x00-\x1f\[\]#^]', '-', value).strip(' .')
    return value or '_unnamed'


def frontmatter(meta, body):
    return '---\n' + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + '---\n\n' + body


def split_note(text):
    if text.count(LOCAL) != 1: raise ValueError('Missing or duplicate local-review marker; preserve the file for review')
    return text.split(LOCAL, 1)


class Zotero:
    def __init__(self, config, root):
        self.base = config.get('zotero_api', 'http://127.0.0.1:23119/api').rstrip('/')
        if self.base not in ('http://localhost:23119/api', 'http://127.0.0.1:23119/api'):
            raise ValueError('Use the loopback Zotero API; remote endpoints are not supported')
        self.fixture = read_json(root / config['fixture']) if config.get('fixture') else None
        self.root = root
        self.server = None

    def request(self, endpoint):
        headers = {'Zotero-API-Version': '3'}
        if self.server: headers['Zotero-Server-ID'] = self.server
        req = urllib.request.Request(self.base + '/' + endpoint, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            server = response.headers.get('Zotero-Server-ID')
            if self.server and server != self.server: raise ValueError('Zotero database changed during sync')
            self.server = server or self.server
            return json.load(response)

    def all(self, kind):
        if self.fixture:
            self.server = 'synthetic-demo'
            return self.fixture[kind]
        output = []
        while True:
            page = self.request(f'users/0/{kind}?limit=100&start={len(output)}')
            if not isinstance(page, list): raise ValueError('Unexpected Zotero response')
            output.extend(page)
            if len(page) < 100: return output

    def pdf_path(self, attachment):
        if self.fixture:
            return (self.root / self.fixture['files'][attachment]).resolve()
        req = urllib.request.Request(self.base + f'/users/0/items/{attachment}/file/view/url',
            headers={'Zotero-API-Version': '3', **({'Zotero-Server-ID': self.server} if self.server else {})})
        with urllib.request.urlopen(req, timeout=30) as response: value = response.read().decode().strip()
        parsed = urllib.parse.urlparse(value)
        if parsed.scheme != 'file' or parsed.netloc not in ('', 'localhost'):
            raise ValueError('Zotero did not return a local attachment path; download the PDF in Zotero')
        return Path(urllib.parse.unquote(parsed.path))


class Vault:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.private = self.root / '.workflow'
        self.config_path = self.root / 'config.local.json'
        self.config = read_json(self.config_path)
        if not self.config: raise ValueError('Run init first; see docs/setup.md')
        if self.config.get('version') != 1: raise ValueError('Unsupported configuration version')
        ZoneInfo(self.config['timezone'])
        if self.config.get('scheduler', {}).get('mode', 'convert') not in ('convert', 'summary'): raise ValueError('scheduler.mode must be convert or summary')
        interval = self.config.get('scheduler', {}).get('interval_seconds', 3600)
        if type(interval) != int or interval < 60: raise ValueError('Scheduler interval must be an integer of at least 60 seconds')
        self.api = Zotero(self.config, self.root)

    def path(self, relative):
        path = (self.root / relative).resolve()
        if path == self.root or self.root not in path.parents: raise ValueError('Path escapes the vault')
        return path

    @contextlib.contextmanager
    def lock(self):
        self.private.mkdir(exist_ok=True)
        with (self.private / 'coordinator.lock').open('a') as f:
            try: fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError: raise RuntimeError('Workflow busy; retry after the current operation completes')
            try: yield
            finally: fcntl.flock(f, fcntl.LOCK_UN)

    def collections(self):
        return {c['key']: c['data'] for c in self.api.all('collections')}

    def scope(self, collections):
        selected = set(self.config['collection_keys'])
        if not selected or not selected <= collections.keys(): raise ValueError('Select existing collection keys with init')
        if self.config.get('include_children', True):
            while True:
                expanded = selected | {k for k, c in collections.items() if c.get('parentCollection') in selected}
                if expanded == selected: break
                selected = expanded
        return selected

    def tree_path(self, key, collections):
        parts, seen = [], set()
        roots = set(self.config['collection_keys'])
        while key and key not in roots:
            if key in seen or key not in collections: raise ValueError('Invalid collection tree')
            seen.add(key); parts.append(safe_part(collections[key]['name']))
            key = collections[key].get('parentCollection')
        return '/'.join(reversed(parts))

    def route(self, item, collections, scope):
        override = self.config.get('routes', {}).get(item['key'])
        if override is not None:
            if Path(override).is_absolute() or '..' in Path(override).parts: raise ValueError('Unsafe route override')
            self.path('zotero-notes/' + override + '/note.md')
            return override.strip('/')
        paths = sorted({self.tree_path(k, collections) for k in item['data'].get('collections', []) if k in scope})
        leaves = [p for p in paths if not any(q != p and (not p or q.startswith(p + '/')) for q in paths)]
        return leaves[0] if len(leaves) == 1 else '_unfiled'

    def owned(self): return read_json(self.private / 'ownership.json', {})

    def recover(self):
        for path in sorted((self.private / 'pending').glob('*.json')):
            self.commit(read_json(path), path)

    def commit(self, tx, journal):
        """Recoverable note replacement; local review is read immediately before writing."""
        dest = self.path(tx['path']); old = self.path(tx['before']['path']) if tx['before'] else dest
        new_hash = sha(tx['generated'])
        local = '\n## Local review and processing\n\nWrite your review here. This section survives sync.\n'
        old_exists = old.exists()
        if tx['before'] and not old_exists and not dest.exists(): raise ValueError('Recovery source missing; restore the matching backup')
        redirect_at_dest = f'---\ntype: redirect\n---\n\nMoved to [[{Path(tx["before"]["path"]).with_suffix("").as_posix()}]].\n' if tx['before'] else None
        destination_is_redirect = dest.exists() and redirect_at_dest and dest.read_text() == redirect_at_dest
        if old_exists:
            old_text = old.read_text()
            redirect = f'---\ntype: redirect\n---\n\nMoved to [[{Path(tx["path"]).with_suffix("").as_posix()}]].\n'
            if old != dest and old_text == redirect:
                old_exists = False
            else:
                generated, local = split_note(old_text)
                allowed = {new_hash} if old == dest else set()
                if tx['before']: allowed.add(tx['before']['hash'])
                if sha(generated) not in allowed: raise ValueError('Imported region changed; preserved ' + str(old.relative_to(self.root)))
        if dest.exists() and old != dest and not destination_is_redirect:
            current, dest_local = split_note(dest.read_text())
            if sha(current) != new_hash: raise ValueError('Destination conflict; both files preserved')
            if old_exists and dest_local != local: raise ValueError('Local review differs at both paths; preserve and reconcile')
            local = dest_local
        elif dest.exists() and not tx['before']:
            current, local = split_note(dest.read_text())
            if sha(current) != new_hash: raise ValueError('Unmanaged destination preserved')
        atomic(dest, tx['generated'] + LOCAL + local)
        if old != dest:
            atomic(old, f'---\ntype: redirect\n---\n\nMoved to [[{Path(tx["path"]).with_suffix("").as_posix()}]].\n')
        owned = self.owned()
        owned[tx['id']] = {'path': tx['path'], 'hash': new_hash}
        save(self.private / 'ownership.json', owned)
        journal.unlink(missing_ok=True)

    def write_note(self, identifier, relative, generated, dry_run=False):
        generated = generated.replace(LOCAL, '&lt;!-- zotero-local-review --&gt;')
        before = self.owned().get(identifier)
        target = self.path(relative)
        if before:
            old = self.path(before['path'])
            if not old.exists(): raise ValueError('Managed note missing; restore it or review ownership: ' + before['path'])
            current, _ = split_note(old.read_text())
            if sha(current) != before['hash']: raise ValueError('Imported region edited; preserved ' + before['path'])
            if before['path'] == relative and sha(generated) == before['hash']: return 'unchanged'
        if target.exists() and (not before or relative != before['path']):
            redirect = f'---\ntype: redirect\n---\n\nMoved to [[{Path(before["path"]).with_suffix("").as_posix()}]].\n' if before else None
            if not redirect or target.read_text() != redirect:
                raise ValueError('Destination already exists; preserved ' + relative)
        result = 'moved' if before and before['path'] != relative else 'updated' if before else 'created'
        if not dry_run:
            tx = {'id': identifier, 'path': relative, 'before': before, 'generated': generated}
            journal = self.private / 'pending' / (sha(identifier) + '.json')
            save(journal, tx); self.commit(tx, journal)
        return result

    def observe(self, items, dry_run=False):
        history = read_json(self.private / 'reading-history.json', {'version': 1, 'items': {}})
        if history.get('version') != 1: raise ValueError('Unsupported history; preserve it')
        stamp = now(); day = dt.datetime.fromisoformat(stamp).astimezone(ZoneInfo(self.config['timezone'])).date().isoformat()
        for item in items:
            marks = sorted(set(t['tag'] for t in item['data'].get('tags', [])) & READING.keys())
            status = 'conflict' if len(marks) > 1 else READING[marks[0]] if marks else 'unknown'
            previous = history['items'].get(item['key'])
            if previous is None:
                history['items'][item['key']] = {'marks': marks, 'reading_status': status, 'read_on': None,
                    'reading_started_on': None, 'read_date_basis': 'unknown', 'observed_at': stamp,
                    'events': [{'kind': 'baseline', 'marks': marks, 'observed_at': stamp}]}
            elif marks != previous['marks']:
                added = set(marks) - set(previous['marks'])
                previous['events'].append({'kind': 'tag-change', 'before': previous['marks'], 'marks': marks, 'observed_at': stamp})
                previous.update(marks=marks, reading_status=status, observed_at=stamp)
                if '✅' in added: previous.update(read_on=day, read_date_basis='observed-tag-change')
                if '⏳' in added: previous['reading_started_on'] = day
        if not dry_run: save(self.private / 'reading-history.json', history)
        return history

    def sync(self, dry_run=False):
        if not dry_run: self.recover()
        collections = self.collections(); scope = self.scope(collections)
        records = self.api.all('items')
        previous_catalog = read_json(self.private / 'catalog.json', {})
        server = self.api.server or 'legacy-local-api'
        if previous_catalog and previous_catalog.get('server') != server:
            raise ValueError('Different Zotero database detected; use a separate vault or restore its matching state')
        parents = [i for i in records if i['data']['itemType'] not in ('note', 'annotation', 'attachment')
            and scope.intersection(i['data'].get('collections', [])) and not i['data'].get('deleted')]
        history = self.observe(parents, dry_run)
        report = {'created': 0, 'updated': 0, 'moved': 0, 'unchanged': 0, 'issues': [], 'papers': len(parents), 'dry_run': dry_run}
        by_key = {i['key']: i for i in records}
        keys = {}
        for i in parents:
            cite = self.config.get('citekey_overrides', {}).get(i['key']) or i['data'].get('citationKey')
            keys.setdefault(cite, []).append(i['key'])
        catalog = {'version': 1, 'server': server, 'items': {}}
        for item in parents:
            key = item['key']; data = item['data']
            cite = self.config.get('citekey_overrides', {}).get(key) or data.get('citationKey')
            try:
                if not cite or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', cite): raise ValueError('Missing/unsafe citation key; install Better BibTeX or configure citekey_overrides')
                if len(keys[cite]) != 1: raise ValueError('Duplicate citation key: ' + cite)
                attachments = [i for i in records if i['data'].get('parentItem') == key and i['data']['itemType'] == 'attachment']
                attachment_keys = {i['key'] for i in attachments}
                notes = [i for i in records if i['data']['itemType'] == 'note' and i['data'].get('parentItem') in {key, *attachment_keys}]
                annotations = [i for i in records if i['data']['itemType'] == 'annotation' and i['data'].get('parentItem') in attachment_keys]
                tags = [t['tag'] for t in data.get('tags', [])]
                reading = history['items'][key]
                old = previous_catalog.get('items', {}).get(key, {})
                meta = {'type': 'paper', 'ai_generated': False, 'title': data.get('title', ''), 'citekey': cite, 'zotero_item_key': key,
                    'authors': [c.get('name') or ' '.join(filter(None, [c.get('firstName'), c.get('lastName')])) for c in data.get('creators', [])],
                    'date': data.get('date', ''), 'doi': data.get('DOI', ''), 'journal': data.get('publicationTitle', ''), 'url': data.get('url', ''),
                    'zotero_item': f'zotero://select/library/items/{key}', 'zotero_tags': tags, 'tags': [],
                    'reading_status': reading['reading_status'], 'read_on': reading['read_on'], 'read_date_basis': reading['read_date_basis'],
                    'reading_started_on': reading['reading_started_on'], 'origins': [v for t, v in ORIGINS.items() if t in tags],
                    'read_next': '📌 reading/next' in tags, 'important': '⭐️' in tags, 'not_useful': '👎' in tags,
                    'selection_status': 'selected' if '📥 status/selected' in tags else 'candidate' if 'status/candidate' in tags else 'unknown',
                    'zotero_modified': data.get('dateModified')}
                # Existing filenames survive citation-key changes; identity is the Zotero key.
                stem = old.get('stem', cite)
                folder = self.route(item, collections, scope)
                annotation_path = str(Path('zotero-notes') / folder / (stem + '.md'))
                paper_path = f'papers/{stem}.md'
                paper_body = f'# {meta["title"]}\n\n[Open in Zotero]({meta["zotero_item"]})\n\nReading: **{meta["reading_status"]}**\n\n'
                if annotations or notes or self.owned().get(key + ':annotations'):
                    paper_body += f'Annotations: [[{Path(annotation_path).with_suffix("").as_posix()}]]\n\n'
                    rendered = render_annotations(item, meta, notes, annotations, self.config)
                    report[self.write_note(key + ':annotations', annotation_path, rendered, dry_run)] += 1
                paper_body += '## Attachments\n\n' + '\n'.join(f'- [{a["data"].get("title", "Attachment")}](zotero://open-pdf/library/items/{a["key"]})' for a in attachments) + '\n\n'
                report[self.write_note(key + ':paper', paper_path, frontmatter(meta, paper_body), dry_run)] += 1
                catalog['items'][key] = {'key': key, 'citekey': cite, 'stem': stem, 'metadata': meta, 'attachments': attachments,
                    'paper_path': paper_path, 'annotation_path': annotation_path if notes or annotations else None,
                    'first_seen': old.get('first_seen', now()), 'deferred': old.get('deferred', not bool(previous_catalog)),
                    'active': True}
            except (ValueError, OSError) as e:
                report['issues'].append(f'{key}: {e}')
        for key, item in previous_catalog.get('items', {}).items():
            if key not in catalog['items']:
                catalog['items'][key] = dict(item, active=False)
        if not dry_run:
            save(self.private / 'catalog.json', catalog)
            save(self.private / 'last-sync.json', dict(report, checked_at=now()))
        return report

    def item(self, value):
        matches = [p for p in read_json(self.private / 'catalog.json', {}).get('items', {}).values()
                   if p['active'] and value in (p['key'], p['citekey'])]
        if len(matches) != 1: raise ValueError('Paper absent or ambiguous; sync and check status')
        return matches[0]


def render_annotations(item, meta, notes, annotations, config):
    meta = dict(meta, type='zotero-notes', imported_by='deterministic-zotero-sync')
    modified = [r['data'].get('dateModified') for r in [item, *notes, *annotations] if r['data'].get('dateModified')]
    if modified: meta['zotero_modified'] = max(modified)
    body = f'# {meta["title"]}\n\n[Open in Zotero]({meta["zotero_item"]})\n\n'
    def child_text(note):
        return f'<!-- zotero-note:{note["key"]} -->\n\n' + markdownify(note['data'].get('note', ''), heading_style='ATX') + '\n'
    body += '## Why I read this / what it is useful for\n\n'
    body += '\n'.join(child_text(n) for n in notes if n['data'].get('parentItem') == item['key']) or '*No paper-level child notes.*\n'
    body += '\n> Edit imported text in Zotero. Write in the Local review section below.\n\n'
    for sticky, heading in [(True, 'Sticky notes — my summaries and interpretations'), (False, 'In-text highlights and other annotations')]:
        body += '## ' + heading + '\n\n'
        groups = {}
        for a in sorted(annotations, key=lambda a: (a['data']['parentItem'], a['data'].get('annotationSortIndex', ''), a['key'])):
            if (a['data'].get('annotationType') == 'note') != sticky: continue
            groups.setdefault(a['data'].get('annotationColor', '').lower(), []).append(a)
        for color in sorted(groups, key=lambda c: list(COLORS).index(c) if c in COLORS else len(COLORS)):
            name, meaning = COLORS.get(color, ('Other (' + color + ')', 'Other annotations'))
            meaning = config.get('colors', {}).get(name, meaning)
            body += f'### {meaning} ({name})\n\n'
            for a in groups[color]:
                d = a['data']; body += f'<!-- zotero-annotation:{a["key"]} -->\n\n'
                if d.get('annotationText'): body += '\n'.join('> ' + line for line in d['annotationText'].splitlines()) + '\n\n'
                if d.get('annotationComment'): body += '**My Zotero comment:**\n\n' + d['annotationComment'] + '\n\n'
                if d.get('annotationType') in ('image', 'ink'): body += '*View image/ink annotation in Zotero.*\n\n'
                tags = [t['tag'] for t in d.get('tags', [])]
                if tags: body += 'Tags: ' + ' '.join('#' + t.lstrip('#') if re.fullmatch(r'#?[\w/-]+', t) else '`' + t.replace('`','') + '`' for t in tags) + '\n\n'
                try:
                    page = json.loads(d.get('annotationPosition', '{}'))['pageIndex'] + 1
                    if type(page) != int or page < 1: raise ValueError()
                    url = f'zotero://open-pdf/library/items/{d["parentItem"]}?page={page}&annotation={a["key"]}'
                except (ValueError, KeyError, TypeError):
                    url = f'zotero://open-pdf/library/items/{d["parentItem"]}?annotation={a["key"]}'
                body += f'[Page {d.get("annotationPageLabel", "unknown")} · exact annotation]({url})\n\n---\n\n'
    body += '## Attachment child notes\n\n' + '\n'.join(child_text(n) for n in notes if n['data'].get('parentItem') != item['key']) + '\n'
    return frontmatter(meta, body)


def run_child(vault, command, log, timeout, cwd=None):
    """Retain child identity across coordinator crashes; never overlap unknown work."""
    import signal
    import subprocess
    guard = vault.private / 'child-process.json'
    previous = read_json(guard)
    if previous:
        result = subprocess.run(['/bin/ps', '-p', str(previous['pid']), '-o', 'lstart=,command='], capture_output=True, text=True)
        if result.returncode not in (0, 1): raise ValueError('Cannot verify previous child; preserve process guard')
        if result.returncode == 0 and (not previous.get('identity') or result.stdout.strip() == previous['identity']):
            raise ValueError('Previous worker may still be running; inspect .workflow/child-process.json before retrying')
        guard.unlink()
    proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, cwd=cwd, start_new_session=True)
    identity = subprocess.run(['/bin/ps','-p',str(proc.pid),'-o','lstart=,command='],capture_output=True,text=True)
    save(guard, {'pid':proc.pid,'identity':identity.stdout.strip() if identity.returncode==0 else None,'started':now()})
    try:
        code = proc.wait(timeout=timeout)
        if code: raise subprocess.CalledProcessError(code,command)
    finally:
        if proc.poll() is None:
            try: os.killpg(proc.pid,signal.SIGTERM);proc.wait(timeout=10)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                if proc.poll() is None: os.killpg(proc.pid,signal.SIGKILL)
                proc.wait()
        guard.unlink(missing_ok=True)
