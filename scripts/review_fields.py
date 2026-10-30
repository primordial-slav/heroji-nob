"""
A small local page for the cases scripts/check_fields.py finds that need a person: each record with its field, the
check's note, the entry's text and the scan of its book page cut around it, and the answers fix (with the new value),
keep (the field is right as it is), delete (no record: the deserters' rule), merge (the same man twice in one unit),
not sure. Every answer goes at once to field_decisions.json (in git), so a case answered is not raised again while
what it answered is unchanged; --write turns the answers 'fix', 'delete' and 'merge' into corrections.

Usage:
    python scripts/apply_corrections.py --apply      # or python scripts/check_fields.py: writes the cases
    python scripts/review_fields.py                  # then open http://localhost:8766
    python scripts/review_fields.py --answer KEY delete --note "prešao u četnike" --by claude
    python scripts/review_fields.py --answer KEY fix --fields '{"first_name": "Dragutin"}' --by claude
    python scripts/review_fields.py --write [--start 290061]   # then apply_corrections.py --apply
Keys on the page: Enter fix, K keep, X delete, M merge, U not sure, Z take back, arrows to move.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'data-extraction'))
import check_fields as CF  # noqa: E402

PAGE = Path(__file__).with_name('review_fields.html')
CORRECTIONS = ROOT / 'corrections.json'
ANSWERS = ('fix', 'keep', 'delete', 'merge', 'unsure')
EDITABLE = ('last_name', 'middle_name', 'fathers_name', 'first_name', 'birth_year', 'birth_place', 'death_type',
            'death_date', 'death_place', 'unit_detail', 'additional_info')


def report_rows() -> list[dict]:
    if not CF.REPORT.exists():
        return []
    return json.loads(CF.REPORT.read_text(encoding='utf-8')).get('problems', [])


def save_answer(key: str, answer: str, by: str, note: str = '', fields: dict | None = None) -> dict:
    """Keep one answer (the last given for a case wins), with what the case answered (the field's value or the note)
    so it holds only while that is unchanged. The file is re-read right before writing."""
    if answer not in ANSWERS and answer != 'clear':
        raise ValueError(answer)
    row = next((r for r in report_rows() if r.get('key') == key), None)
    decisions = CF.load_decisions()
    if answer == 'clear':
        decisions.pop(key, None)
        d = {'key': key, 'answer': None}
    else:
        if row is None and key not in decisions:
            raise ValueError(f'no such case: {key}')
        old = decisions.get(key, {})
        base = row or old
        if answer == 'fix' and not fields:
            raise ValueError('a fix needs the new values (fields)')
        if fields and set(fields) - set(EDITABLE):
            raise ValueError(f'not a field a fix may set: {sorted(set(fields) - set(EDITABLE))}')
        if answer == 'merge' and not (base.get('twin') or old.get('twin_id')):
            raise ValueError('merge is for a record that is the same entry twice')
        d = {'key': key, 'check': base['check'], 'kind': base['kind'], 'soldier_id': base['soldier_id'],
             'field': base['field'], 'name': base.get('name', ''), 'value': base.get('value', ''), 'answer': answer,
             **({'fields': fields} if answer == 'fix' else {}),
             **({'twin_id': (base.get('twin') or {}).get('soldier_id') or old.get('twin_id')} if answer == 'merge' else {}),
             'by': by, 'date': datetime.date.today().isoformat(), **({'note': note} if note else {})}
        decisions[key] = d
    tmp = CF.DECISIONS.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(sorted(decisions.values(), key=lambda x: x['key']), ensure_ascii=False, indent=1) + '\n',
                   encoding='utf-8')
    os.replace(tmp, CF.DECISIONS)
    return d


def write(start: int | None) -> None:
    """the answers fix, delete and merge not written yet, as corrections; each answer keeps the id it was written as"""
    decisions = CF.load_decisions()
    todo = [d for d in decisions.values() if d.get('answer') in ('fix', 'delete', 'merge') and not d.get('written')]
    if not todo:
        print('nothing to write')
        return
    text = CORRECTIONS.read_text(encoding='utf-8')
    corrections = json.loads(text)
    taken = {c['id'] for c in corrections}
    next_id = start or max(i for i in taken if 290061 <= i <= 293060 or i == 290060) + 1
    out = []
    for d in sorted(todo, key=lambda x: x['key']):
        while next_id in taken:
            next_id += 1
        why = f"{d['check']}/{d['kind']} ({d.get('value', '')[:120]}): {d.get('note') or 'read on the page'}; " \
              f"answered by {d['by']} {d['date']} (scripts/review_fields.py)"
        if d['answer'] == 'fix':
            c = {'id': next_id, 'action': 'edit', 'soldier_id': d['soldier_id'], 'fields': d['fields'], 'reason': why}
        elif d['answer'] == 'delete':
            c = {'id': next_id, 'action': 'delete', 'soldier_id': d['soldier_id'],
                 'reason': f"{d.get('name', '')}: {why}; deserters and traitors are left out (the user's rule of 2026-10-14)"
                 if d['check'] == 'deserter' else f"{d.get('name', '')}: {why}"}
        else:
            c = {'id': next_id, 'action': 'merge', 'soldier_id': d['twin_id'], 'merge_id': d['soldier_id'],
                 'merge_name': d.get('name', ''), 'reason': f'the same entry twice in the unit; {why}'}
        out.append(c)
        taken.add(next_id)
        d['written'] = next_id
        next_id += 1
    corrections.extend(out)
    CORRECTIONS.write_text(json.dumps(corrections, ensure_ascii=False, indent=2) + ('\n' if text.endswith('\n') else ''),
                           encoding='utf-8')
    tmp = CF.DECISIONS.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(sorted(decisions.values(), key=lambda x: x['key']), ensure_ascii=False, indent=1) + '\n',
                   encoding='utf-8')
    os.replace(tmp, CF.DECISIONS)
    kinds = {}
    for c in out:
        kinds[c['action']] = kinds.get(c['action'], 0) + 1
    print(f"written {len(out)} corrections ({out[0]['id']}-{out[-1]['id']}): {kinds}; now run apply_corrections.py --apply")


class Handler(BaseHTTPRequestHandler):
    by = 'Boris'

    def log_message(self, *args):
        pass

    def send(self, body: bytes, kind: str, code: int = 200):
        self.send_response(code)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store' if kind.startswith(('application/json', 'text/html')) else 'max-age=86400')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(url.query)
        try:
            if url.path == '/':
                return self.send(PAGE.read_bytes(), 'text/html; charset=utf-8')
            if url.path == '/api/queue':
                decisions = CF.load_decisions()
                rows = report_rows()
                # an answer holds while the case is unchanged; another's 'not sure' is no answer for this reviewer
                answers = {r['key']: decisions[r['key']]['answer'] for r in rows
                           if r.get('key') in decisions and decisions[r['key']].get('value') == r.get('value')
                           and not (decisions[r['key']]['answer'] == 'unsure' and decisions[r['key']].get('by') != self.by)}
                body = {'rows': rows, 'answers': answers, 'by': self.by}
                return self.send(json.dumps(body, ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8')
            if url.path == '/crop':
                import review_identities as RI
                box = [float(v) for v in q['box'][0].split(',')]
                rects = json.loads(q['rects'][0]) if q.get('rects') else None
                return self.send(RI.crop(q['file'][0], int(q['page'][0]), box, rects), 'image/png')
        except Exception as e:                                              # noqa: BLE001
            return self.send(f'{type(e).__name__}: {e}'.encode('utf-8'), 'text/plain; charset=utf-8', 500)
        self.send(b'not found', 'text/plain', 404)

    def do_POST(self):
        if self.path != '/api/answer':
            return self.send(b'not found', 'text/plain', 404)
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])).decode('utf-8'))
        try:
            d = save_answer(body['key'], body['answer'], body.get('by') or self.by, body.get('note', ''), body.get('fields'))
        except (ValueError, KeyError) as e:
            return self.send(json.dumps({'error': str(e)}).encode('utf-8'), 'application/json', 400)
        self.send(json.dumps(d, ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--port', type=int, default=8766)
    ap.add_argument('--by', default='Boris', help='whose answers these are (kept with each)')
    ap.add_argument('--answer', nargs=2, metavar=('KEY', 'ANSWER'))
    ap.add_argument('--fields', help='a fix\'s new values, as JSON')
    ap.add_argument('--note', default='')
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--start', type=int)
    args = ap.parse_args()
    if args.answer:
        d = save_answer(args.answer[0], args.answer[1], args.by, args.note, json.loads(args.fields) if args.fields else None)
        print(json.dumps(d, ensure_ascii=False))
        return
    if args.write:
        write(args.start)
        return
    Handler.by = args.by
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'http://localhost:{args.port}  (answers go to {CF.DECISIONS.name}; Ctrl+C to stop)')
    server.serve_forever()


if __name__ == '__main__':
    main()
