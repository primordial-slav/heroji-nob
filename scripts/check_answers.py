"""
Your answers kept: every answer given on the two review pages (field_decisions.json from scripts/review_fields.py,
identity_decisions.json from scripts/review_identities.py) checked against the data as it stands, so a reader, a rule
or a matcher that undoes one is caught the run it happens (the user's wish of 2026-11-08, after Karpathy's "give it
success criteria": a reader once filled back a death an answer had left empty).

It changes nothing. An answer holds when the data still says what it decided:
  fix        the record has the values the answer gave (in a form the field rules may have changed: "14. 2. 1943" is
             14.02.1943), unless a later correction sets that field otherwise;
  keep       the field still holds the value the answer kept, or a correction changed it on purpose; a record kept
             (a deserter's case answered no) is still on the site;
  delete     the record is gone; merge: the record is in its twin's;
  same       the two are one record, linked, or the record holds the book's entry;
  different  they are none of these.
An answer not written as corrections yet is 'pending', not broken; one whose record now bears another name (a re-parse
gave the id to someone else) is 'stale'. apply_corrections.py runs it last; alone it loads every unit:
    python scripts/check_answers.py [--sample 10] [--strict]       # --strict: exit 1 if an answer is broken
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = Path(__file__).resolve().parent.parent
FIELD_DECISIONS = ROOT / 'field_decisions.json'
IDENTITY_DECISIONS = ROOT / 'identity_decisions.json'
REPORT = ROOT / 'data-extraction' / '.cache' / 'answer_checks.json'
BROKEN = 'broken'


def fold(s) -> str:
    s = str(s or '').replace('đ', 'dj').replace('Đ', 'Dj')
    return ''.join(c for c in unicodedata.normalize('NFD', s) if not unicodedata.combining(c)).lower()


def same_value(a, b) -> bool:
    """one value in two forms: spaces, full stops, a day's leading zero ("14. 2. 1943" and 14.02.1943)"""
    a, b = str(a or '').strip(), str(b or '').strip()
    if a == b:
        return True
    norm = lambda t: re.sub(r'[\W_]+', '', re.sub(r'(?<!\d)0+(?=\d)', '', t.lower()))
    return norm(a) == norm(b)


def surname(name: str) -> str:
    return fold(re.split(r'[\s(]', (name or '').strip(), maxsplit=1)[0]).replace('-', '')


def same_man(record: dict, name: str) -> bool:
    """the id still names the man the answer was about: his surname then and now share their first letters (a name
    mended since keeps them; a re-parse giving the id to another man doesn't)"""
    a, b = surname(record.get('full_name') or f"{record.get('last_name', '')} {record.get('first_name', '')}"), surname(name)
    return not a or not b or a[:3] == b[:3] or a in b or b in a


class Index:
    def __init__(self, units: dict):
        self.rec, self.holder = {}, {}
        self.merged_in = collections.defaultdict(set)   # an id -> the records holding it as a merged entry
        self.linked = collections.defaultdict(set)
        self.refs = collections.defaultdict(set)
        for soldiers in units.values():
            for s in soldiers:
                self.rec[s['soldier_id']] = s
                self.holder[s['soldier_id']] = s['soldier_id']
        for soldiers in units.values():
            for s in soldiers:
                sid = s['soldier_id']
                for o in s.get('other_sources') or []:
                    oid = o.get('soldier_id')
                    if not oid:
                        continue
                    if o.get('ref_book'):
                        self.refs[sid].add((o['ref_book'], oid))
                    elif o.get('unit_file'):
                        self.linked[sid].add(oid)
                    else:
                        self.merged_in[oid].add(sid)
                        self.holder.setdefault(oid, sid)
        # one id, two men: a record's own id that another record also holds as a merged entry (an `add` given an id
        # an older merge had freed)
        self.twice = sorted(i for i in self.merged_in if i in self.rec)

    def holders(self, i: str) -> set:
        return ({i} if i in self.rec else set()) | self.merged_in.get(i, set())

    def joined(self, kind: str, a: str, b: str, book: str | None) -> str | None:
        """how the data joins the two ('' when it doesn't), None when one of them is not on the site"""
        ha = self.holders(a)
        if kind == 'reference':
            if not ha:
                return None
            via = [h for h in ha if (book, b) in self.refs[h]]
            return ('' if not via else 'the record holds the entry' if via == [a]
                    else f"{a} is merged into {via[0]}, which holds the entry")
        hb = self.holders(b)
        if not ha or not hb:
            return None
        if ha & hb:
            h = next(iter(ha & hb))
            return 'one record' if h in (a, b) else f"both merged into {h}"
        for x in ha:
            if hb & self.linked[x] or b in self.linked[x]:
                return f"linked ({x} holds {b}'s entries)"
        for y in hb:
            if ha & self.linked[y] or a in self.linked[y]:
                return f"linked ({y} holds {a}'s entries)"
        return ''


class Corrections:
    """what the corrections say about each record: which field each sets (id, value), which pairs they join"""

    def __init__(self, corrections: list):
        self.sets = collections.defaultdict(list)
        self.gone = {}
        self.pairs = set()
        for c in corrections:
            a = c['action']
            if a == 'edit':
                for k, v in c.get('fields', {}).items():
                    self.sets[c['soldier_id'], k].append((c['id'], v))
            elif a == 'add':
                for k, v in c.get('record', {}).items():
                    self.sets[c['new_id'], k].append((c['id'], v))
            elif a == 'delete':
                self.gone[c['soldier_id']] = c['id']
            elif a == 'merge':
                self.gone[c['merge_id']] = c['id']
                self.pairs.add(frozenset((c['soldier_id'], c['merge_id'])))
            elif a == 'link':
                self.pairs.add(frozenset((c['soldier_id'], c['link_id'])))
            elif a == 'reference':
                self.pairs.add(frozenset((c['soldier_id'], c['ref_id'])))
            elif a == 'split':
                self.gone[c['soldier_id']] = c['id']

    def set_on_purpose(self, sid: str, field: str, value, after: int = 0) -> int | None:
        """a correction after `after` that sets this field to this value: the change was meant"""
        for cid, v in self.sets.get((sid, field), []):
            if cid > after and same_value(v, value):
                return cid
        return None


def load(path: Path) -> list:
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else []


def check_fields(ix: Index, cs: Corrections, decisions: list) -> list[dict]:
    out = []

    def add(d, status, why):
        out.append({'page': 'fields', 'key': d['key'], 'answer': d['answer'], 'by': d.get('by'), 'name': d.get('name'),
                    'soldier_id': d['soldier_id'], 'status': status, 'why': why})

    for d in decisions:
        ans, sid, field = d.get('answer'), d['soldier_id'], d.get('field')
        if ans in (None, 'unsure'):
            continue
        s = ix.rec.get(sid)
        # a name the answer itself mended, or a correction mended since, is the same man's
        if (s is not None and not same_man(s, d.get('name', ''))
                and not same_value(s.get('last_name'), d.get('fields', {}).get('last_name'))
                and not cs.set_on_purpose(sid, 'last_name', s.get('last_name'))):
            add(d, 'stale', f"the id now names {s.get('full_name')}")
            continue
        if ans in ('delete', 'merge'):
            if not d.get('written'):
                add(d, 'pending', 'answered, not written as a correction yet (review_fields.py --write)')
            elif ans == 'delete' and s is not None:
                add(d, BROKEN, 'answered delete, but the record is still on the site')
            elif ans == 'merge' and not (ix.holders(sid) & ix.holders(d.get('twin_id', ''))):
                add(d, BROKEN, f"answered merge with {d.get('twin_id')}, but they are two records")
            continue
        if ans == 'fix':
            if not d.get('written'):
                add(d, 'pending', 'answered, not written as a correction yet (review_fields.py --write)')
                continue
            if s is None:
                if sid not in cs.gone and sid not in ix.holder:
                    add(d, BROKEN, 'the record the answer mended is gone, and no correction took it off')
                continue
            for k, v in d.get('fields', {}).items():
                cur = s.get(k) or ''
                if same_value(cur, v) or cs.set_on_purpose(sid, k, cur, after=d['written']):
                    continue
                lent = ' (lent by another book or a linked record: record_sources.py)' if k in (s.get('borrowed') or ()) else ''
                add(d, BROKEN, f"{k}: answered {v!r}, the record holds {cur!r}{lent}")
            continue
        # keep
        if field == 'record':
            if s is None and sid not in cs.gone and sid not in ix.holder:
                add(d, BROKEN, 'kept, but the record is gone and no correction took it off')
            continue
        if s is None:
            continue
        cur = str(s.get(field) or '')
        if same_value(cur, d.get('value', '')) or cs.set_on_purpose(sid, field, cur):
            continue
        add(d, BROKEN, f"{field}: kept {d.get('value')!r} as right, the record now holds {cur!r}")
    return out


def check_identities(ix: Index, cs: Corrections, decisions: list) -> list[dict]:
    out = []

    def add(d, status, why):
        out.append({'page': 'identities', 'key': d['key'], 'answer': d['answer'], 'by': d.get('by'),
                    'name': f"{d.get('a_name')} / {d.get('b_name')}", 'soldier_id': d['a'], 'other': d['b'],
                    'status': status, 'why': why})

    for d in decisions:
        ans, kind, a, b = d.get('answer'), d.get('kind'), d.get('a'), d.get('b')
        if ans not in ('same', 'different') or not a or not b:
            continue
        ra = ix.rec.get(ix.holder.get(a) or '')
        if (ra is not None and ix.holder.get(a) == a and not same_man(ra, d.get('a_name', ''))
                and not cs.set_on_purpose(a, 'last_name', ra.get('last_name'))):
            add(d, 'stale', f"{a} now names {ra.get('full_name')}")
            continue
        j = ix.joined(kind, a, b, d.get('book'))
        if j is None:
            if ans == 'same' and kind != 'reference' and a not in cs.gone and b not in cs.gone:
                add(d, 'gone', 'one of the two records is no longer on the site')
            continue
        if ans == 'same' and not j:
            if frozenset((a, b)) in cs.pairs:
                add(d, BROKEN, f"answered same and written as a correction, but the data doesn't join them ({kind})")
            else:
                add(d, 'pending', 'answered same, not written yet (find_identities.py --write)')
        elif ans == 'different' and j:
            add(d, BROKEN, f"answered different, but the data joins them: {j}")
    return out


def check_consistency(ix: Index, decisions: list) -> list[dict]:
    """the answers among themselves: two men answered 'different' that a chain of answers 'same' makes one (A same B,
    B same C, A different C). find_identities.py --write takes an answer 'same' not made yet, so such a chain would
    join them again (the pairs undone on 2026-11-04 left answers 'same' on the men they parted)"""
    same = collections.defaultdict(set)
    names = {}
    for d in decisions:
        if d.get('answer') == 'same' and d.get('a') and d.get('b'):
            same[d['a']].add((d['b'], d['key']))
            same[d['b']].add((d['a'], d['key']))
        for k in ('a', 'b'):
            if d.get(k):
                names.setdefault(d[k], d.get(f'{k}_name', ''))

    def chain(a: str, b: str) -> list[tuple[str, str]] | None:
        seen, queue = {a: None}, collections.deque([a])
        while queue:
            x = queue.popleft()
            if x == b:
                path, y = [], b
                while seen[y]:
                    prev, key = seen[y]
                    path.append((y, key))
                    y = prev
                return path[::-1]
            for y, key in same[x]:
                if y not in seen:
                    seen[y] = (x, key)
                    queue.append(y)
        return None

    out = []
    for d in decisions:
        if d.get('answer') != 'different' or not d.get('a') or not d.get('b'):
            continue
        path = chain(d['a'], d['b'])
        if path:
            steps = ' = '.join([f"{d['a']} {names.get(d['a'], '')}"] + [f"{y} {names.get(y, '')}" for y, _ in path])
            out.append({'page': 'identities', 'key': d['key'], 'answer': 'different', 'by': d.get('by'),
                        'name': f"{d.get('a_name')} / {d.get('b_name')}", 'soldier_id': d['a'], 'other': d['b'],
                        'status': BROKEN, 'chain': [k for _, k in path],
                        'why': f"answered different, but answers 'same' make them one: {steps}"})
    return out


def check_ids(ix: Index) -> list[dict]:
    return [{'page': 'data', 'key': f'twice:{i}', 'answer': '', 'by': '', 'name': ix.rec[i].get('full_name'),
             'soldier_id': i, 'status': BROKEN,
             'why': f"one id, two men: a record of its own and an entry merged into {', '.join(sorted(ix.merged_in[i]))}"}
            for i in ix.twice]


def run(units: dict, corrections: list) -> list[dict]:
    """units: any keys -> each unit's records (every unit on the site); corrections: all of corrections.json"""
    ix, cs = Index(units), Corrections(corrections)
    identities = load(IDENTITY_DECISIONS)
    found = (check_fields(ix, cs, load(FIELD_DECISIONS)) + check_identities(ix, cs, identities)
             + check_consistency(ix, identities) + check_ids(ix))
    # an answer 'same' not made yet that a contradiction runs through is no plain 'pending': --write would take it
    risky = {k for f in found for k in f.get('chain', ())}
    for f in found:
        if f['status'] == 'pending' and f['key'] in risky:
            f['status'] = BROKEN
            f['why'] = "answered same, not written, and a chain of answers 'same' through it contradicts an answer " \
                       "'different': find_identities.py --write would join men answered different"
    return found


def describe(found: list[dict]) -> str:
    n = collections.Counter(f['status'] for f in found)
    total = len(load(FIELD_DECISIONS)) + len(load(IDENTITY_DECISIONS))
    broken = n.get(BROKEN, 0)
    head = f"{broken} broken" if broken else 'all hold'
    rest = ', '.join(f"{v} {k}" for k, v in sorted(n.items()) if k != BROKEN)
    return f"{head} of {total} answers" + (f" ({rest})" if rest else '')


def write_report(found: list[dict]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({'answers': found}, ensure_ascii=False, indent=1), encoding='utf-8')


def show(found: list[dict], sample: int) -> None:
    by = collections.defaultdict(list)
    for f in found:
        by[f['status'], f['page'], f['answer']].append(f)
    for (status, page, ans), rows in sorted(by.items(), key=lambda x: (x[0][0] != BROKEN, x[0])):
        print(f"  {status:8} {page:10} {ans:9} {len(rows)}")
        if status == BROKEN or sample > 3:
            for f in rows[:sample]:
                print(f"      {f['soldier_id']} {f['name']}: {f['why']} [{f['by']}]")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sample', type=int, default=10)
    ap.add_argument('--strict', action='store_true', help='exit 1 if an answer is broken')
    args = ap.parse_args()
    sys.path.insert(0, str(ROOT / 'scripts'))
    from name_utils import BRIGADE_CONFIGS
    public = ROOT / 'website' / 'public'
    units = {code: json.loads((public / cfg['json_file']).read_text(encoding='utf-8'))
             for code, cfg in BRIGADE_CONFIGS.items() if (public / cfg['json_file']).exists()}
    found = run(units, load(ROOT / 'corrections.json'))
    write_report(found)
    print(f"Your answers: {describe(found)}  (list in {REPORT.relative_to(ROOT)})")
    show(found, args.sample)
    if args.strict and any(f['status'] == BROKEN for f in found):
        sys.exit(1)


if __name__ == '__main__':
    main()
