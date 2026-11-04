"""Take a merge, a link or a reference back when two men turn out to be on one record.

A merge moved the other book's entry into the keeper's other_sources and removed its record, and the unit files are state,
so taking the correction off is not enough: this puts the record back beside its keeper and forgets what the keeper read
from the entry. A link or reference is only taken off; what it lent goes on the next run. Each pair is answered 'different'
in identity_decisions.json, so no matcher takes it again.

    python scripts/undo_merges.py TABLE.json [--write]      # then apply_corrections.py --apply --brigade <the units>

TABLE: {"merges": [{"id": correction id, "last_name": ..., "first_name": ..., "middle_name": ..., "fathers_name": ...,
                    "note": why}],
        "links": [{"id": ..., "note": ...}], "references": [{"id": ..., "note": ...}],
        "blank": [{"soldier_id": ..., "fields": [what an old copy left that no entry of his prints]}],
        "new": [correction without an id, e.g. the two entries put back merged into each other]}
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.stdout.reconfigure(encoding='utf-8')
from name_utils import BRIGADE_CONFIGS, extract_birth_info  # noqa: E402
import find_identities as FI  # noqa: E402
import extract_structured_fields as structured  # noqa: E402

CORRECTIONS = ROOT / 'corrections.json'
# what a record's fields may hold from an entry taken off it: read again from what is left (a correction sets its own again)
FORGET = tuple(structured.FIELDS) + ('birth_date', 'variants', 'borrowed')


def path_of(code: int) -> Path:
    return ROOT / 'website' / 'public' / BRIGADE_CONFIGS[code]['json_file']


def write_json(path: Path, data) -> None:
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    for _ in range(8):
        try:
            os.replace(tmp, path)
            return
        except OSError:
            import time
            time.sleep(2)
    raise SystemExit(f'could not write {path}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('table')
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    table = json.loads(Path(args.table).read_text(encoding='utf-8'))
    corr = json.loads(CORRECTIONS.read_text(encoding='utf-8'))
    by_cid = {c['id']: c for c in corr}
    units, drop, touched, answers = {}, set(), set(), []

    def unit(code):
        if code not in units:
            units[code] = json.loads(path_of(code).read_text(encoding='utf-8'))
        return units[code]

    def record(sid):
        return next((s for s in unit(int(sid[:4])) if s['soldier_id'] == sid), None)

    from apply_corrections import SOURCE_FIELDS, rebuild_computed_fields
    for m in table.get('merges', ()):
        c = by_cid[m['id']]
        keep_id, mid = c['soldier_id'], c['merge_id']
        code = int(keep_id[:4])
        soldiers = unit(code)
        keep = next((s for s in soldiers if any(o.get('soldier_id') == mid and not o.get('unit_file') and not o.get('ref_book')
                                                for o in s.get('other_sources', ()))), None)
        if keep is None:
            sys.exit(f'{mid}: no record holds it')
        entry = next(o for o in keep['other_sources'] if o.get('soldier_id') == mid)
        keep['other_sources'] = [o for o in keep['other_sources'] if o is not entry]
        if not keep['other_sources']:
            del keep['other_sources']
        rec = {'soldier_id': mid, 'last_name': m['last_name'], 'middle_name': m.get('middle_name', ''),
               'first_name': m['first_name'], 'fathers_name': m.get('fathers_name', ''),
               'additional_info': entry.get('additional_info', '')}
        rec.update({k: entry[k] for k in SOURCE_FIELDS if entry.get(k) not in (None, '')})
        rec['birth_year'] = extract_birth_info(rec['additional_info'])[1] or ''
        rebuild_computed_fields(rec, skip_birth_year=True)
        for k in FORGET:
            keep.pop(k, None)
        soldiers.insert(soldiers.index(keep) + 1, rec)
        drop.add(c['id'])
        touched.add(code)
        answers.append((FI.key('merge', keep_id, mid), keep.get('full_name'), rec['full_name'], m.get('note', '')))
        print(f"  merge {c['id']}: {mid} {rec['full_name']} back beside {keep_id} {keep.get('full_name')}")
    for x in table.get('links', ()):
        c = by_cid[x['id']]
        drop.add(c['id'])
        for sid in (c['soldier_id'], c['link_id']):
            touched.add(int(sid[:4]))
            s = record(sid)
            if s is not None and x.get('forget'):
                for k in x['forget']:
                    s.pop(k, None)
        answers.append((FI.key('link', c['soldier_id'], c['link_id']), (record(c['soldier_id']) or {}).get('full_name', ''),
                        (record(c['link_id']) or {}).get('full_name', ''), x.get('note', '')))
        print(f"  link {c['id']}: {c['soldier_id']} / {c['link_id']} off")
    for x in table.get('references', ()):
        c = by_cid[x['id']]
        drop.add(c['id'])
        touched.add(int(c['soldier_id'][:4]))
        answers.append((FI.key('reference', c['soldier_id'], c['ref_id'], c['ref_book']),
                        (record(c['soldier_id']) or {}).get('full_name', ''), c.get('ref_name', ''), x.get('note', '')))
        print(f"  reference {c['id']}: {c['ref_id']} off {c['soldier_id']}")
    for x in table.get('blank', ()):
        s = record(x['soldier_id'])
        touched.add(int(x['soldier_id'][:4]))
        for k in x['fields']:
            s.pop(k, None)
    start = max(c['id'] for c in corr) + 1
    new = [{'id': start + i, **c} for i, c in enumerate(table.get('new', ()))]
    for c in new:
        touched.add(int(c['soldier_id'][:4]))
    print(f'{len(drop)} corrections off, {len(new)} new from {start}; units {sorted(touched)}')
    if not args.write:
        print('dry run')
        return
    write_json(CORRECTIONS, [c for c in corr if c['id'] not in drop] + new)
    for code in touched:
        if code in units:
            write_json(path_of(code), units[code])
    for k, a_name, b_name, note in answers:
        FI.save_answer(k, 'different', a_name or '', b_name or '', 'claude', note)
    print(' '.join(str(c) for c in sorted(touched)))


if __name__ == '__main__':
    main()
