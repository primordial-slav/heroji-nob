"""
The entries of books across units that build_ostali_borci.py leaves out because they are the same man as an entry a
unit's record holds (a census line and a village book's entry of one man, of which the record took one): each goes to
the records that hold its man, as a reference (2026-10-31; before, such an entry showed nowhere: Komnenović Dušan's
Popovo polje entry, whose census line the 14. hercegovačka's record holds).

The builder writes the list on each --write (data-extraction/.cache/ostali_on_site.json: the entry, its book, the
entries on the site it goes with). A record gets the entry unless it holds an entry of that book already, or another
record of its unit holds this entry.

    python scripts/attach_left_out.py                   # dry run: counts and samples
    python scripts/attach_left_out.py --write START     # append the references from correction id START
Then run apply_corrections.py --apply.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from name_utils import BRIGADE_CONFIGS, OSTALI_CODES  # noqa: E402
from cleanup_text_fields import live_json_files       # noqa: E402

ON_SITE = ROOT / 'data-extraction' / '.cache' / 'ostali_on_site.json'
CORRECTIONS = ROOT / 'corrections.json'


def main():
    start = int(sys.argv[sys.argv.index('--write') + 1]) if '--write' in sys.argv else None
    left = json.loads(ON_SITE.read_text(encoding='utf-8'))
    corr = json.loads(CORRECTIONS.read_text(encoding='utf-8'))
    live = live_json_files()
    records = set()
    for code, cfg in BRIGADE_CONFIGS.items():
        if code not in OSTALI_CODES and cfg['json_file'] in live:
            records |= {s['soldier_id'] for s in json.loads((ROOT / 'website' / 'public' / cfg['json_file'])
                                                            .read_text(encoding='utf-8'))}
    holders = defaultdict(set)              # entry -> the records that hold it
    books_of = defaultdict(set)             # record -> the books it holds an entry of
    units_of = defaultdict(set)             # entry -> the units whose records hold it
    for c in corr:
        if c['action'] == 'reference':
            holders[c['ref_id']].add(c['soldier_id'])
            books_of[c['soldier_id']].add(c['ref_book'])
            units_of[c['ref_id']].add(c['soldier_id'][:4])
    add, why = [], Counter()
    for e in left:
        recs = sorted({r for w in e['with'] for r in holders[w] if r in records})
        if not recs:
            why['no record holds his entry'] += 1
            continue
        for r in recs:
            if e['book'] in books_of[r]:
                why['record holds an entry of the book'] += 1
            elif r[:4] in units_of[e['entry']]:
                why['another record of the unit holds it'] += 1
            else:
                add.append({'record': r, 'entry': e['entry'], 'book': e['book'], 'name': e['name'], 'with': e['with']})
                books_of[r].add(e['book'])
                units_of[e['entry']].add(r[:4])
    print(f'{len(left)} entries left out; {len(add)} references to write; {dict(why)}')
    for a in add[:12]:
        print('  ', a)
    if start is not None and add:
        taken = {c['id'] for c in corr}
        new = [{'id': start + i, 'action': 'reference', 'soldier_id': a['record'], 'ref_book': a['book'],
                'ref_id': a['entry'], 'ref_name': a['name'],
                'reason': f"the same man as {', '.join(a['with'])} on this record (build_ostali_borci.py joins the "
                          f"entries); the entry had shown nowhere"} for i, a in enumerate(add)]
        if any(c['id'] in taken for c in new):
            sys.exit(f'--write {start}: ids from there are taken')
        CORRECTIONS.write_text(json.dumps(corr + new, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'Appended {len(new)} reference corrections from id {start}')


if __name__ == '__main__':
    main()
