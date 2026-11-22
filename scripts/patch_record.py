"""One man's fix in Borci drugih jedinica (122) or a census part (131-138), in seconds (2026-11-22, the user: "If one
soldier changes, we should just change that entry ... It should be a 5 second job").

These records are made by data-extraction/build_ostali_borci.py from the books' entries, so a fix can't be a correction
on the record (the record is made anew on every full run). It is kept by entry instead, in
data-extraction/ostali_overrides.json, which the builder applies to the record it assembles (apply_overrides); this
script writes the override and changes the record in place the way the full chain would: the field in its one form, the
places in the nominative, the books' other versions ("ili"), the record's life events. The fields it sets are marked in
the record's manual_fields, so no later step (the normalizer, the field reader, the places, the one form) reads them
otherwise.

    python scripts/patch_record.py 0122961304 death_date="1945 ili 1946" --reason "family form 2026-11-21" [--by Boris]
    python scripts/patch_record.py 0122961304 death_place=          # blank a field (and keep it blank)
    python scripts/patch_record.py 0122961304 --remove death_place  # take a field's override away: the record keeps
                                                                    # the value until the next full run reads it anew
    python scripts/patch_record.py 0122961304 --dry                 # show, write nothing

What it leaves to the next full run (the chain in docs/claude/ostali-borci.md): the field checks' review file, the
women's names list (name-genders.json) and "zvana", the places index (build_relations.py), the war events, and the
search data (a build). A unit's record is fixed with an edit correction (scripts/apply_corrections.py --brigade N).
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'data-extraction'))
from name_utils import BRIGADE_CONFIGS, CENSUS_VOLUMES, OSTALI_CODES  # noqa: E402
from safe_write import write_text  # noqa: E402

OVERRIDES = ROOT / 'data-extraction' / 'ostali_overrides.json'
IDS = ROOT / 'data-extraction' / 'ostali_borci_ids.json'
LIFE_EVENTS = ROOT / 'website' / 'data' / 'life-events'
# as build_ostali_borci.OVERRIDE_REFUSED: the entry's text stays as printed, a role is a decision, the rest is the builder's
REFUSED = {'soldier_id', 'additional_info', 'role', 'other_sources', 'from_columns', 'manual_fields', 'former_ids',
           'full_name'}
NAMES = ('last_name', 'middle_name', 'first_name')
CENSUS_CODES = set(CENSUS_VOLUMES.values())
FAMILY = ROOT / 'data-extraction' / 'porodica' / 'porodicna-arhiva-entries.json'
MOVED = ROOT / 'website' / 'data' / 'moved-ids.json'


def family_fields(rid: str) -> dict:
    """The fields a family's papers set for the record (Porodična arhiva: the builder puts them over the books, and the
    user's rule is that the family's report wins on the card)"""
    if not FAMILY.exists():
        return {}
    mine = {e for e, r in json.loads(IDS.read_text(encoding='utf-8')).items() if r == rid}
    out = {}
    for e in json.loads(FAMILY.read_text(encoding='utf-8')):
        if e.get('soldier_id') in mine:
            out.update(e.get('fields') or {})
    return out


def entry_of(rid: str, rec: dict) -> str:
    """The entry the override is kept by: a census record's own census entry (its ID is the part's code + the entry's
    number), else the record's lead entry in the registry (ostali_borci_ids.json: entry -> record)"""
    code = int(rid[:4])
    if code in CENSUS_CODES:
        prefix = {c: i for i, c in enumerate(sorted(CENSUS_VOLUMES.values()))}[code]
        return f'90{20 + prefix:02d}{rid[4:]}'
    merged = {o.get('soldier_id') for o in rec.get('other_sources') or ()}
    mine = sorted(e for e, r in json.loads(IDS.read_text(encoding='utf-8')).items() if r == rid)
    if not mine:
        raise SystemExit(f'{rid}: no entry of the registry names this record')
    return next((e for e in mine if e not in merged), mine[0])


def one_form(rec: dict, field: str, value: str) -> str:
    """The value as the one form gives it (standardize_fields), so the full run and this script start from the same"""
    import standardize_fields
    tmp = copy.deepcopy(rec)
    tmp.pop('manual_fields', None)
    tmp[field] = value
    standardize_fields.apply([tmp])
    return tmp.get(field, value)


def per_record_steps(rec: dict, code: int, json_file: str) -> None:
    """The steps the chain runs over the record after the builder (apply_corrections.py), on this record alone"""
    import extract_structured_fields as structured
    import record_sources
    import resolved_places
    import standardize_fields
    from apply_corrections import fix_names
    rid = rec['soldier_id']
    if structured._EXTRACTOR is None:
        # the kept vocabulary, not learned anew from every unit (minutes): one record reads the same
        structured._EXTRACTOR = structured.any_kept_extractor()
        if structured._EXTRACTOR is None:
            print('  (no kept vocabulary yet: learning it from every unit, a few minutes, once)')
    manual = set(rec.get('manual_fields') or ())
    by_manual = {rid: manual & set(structured.FIELDS)}
    for _ in range(3 if code in CENSUS_CODES else 1):     # the census parts want two runs ("Lima, Sarajevo")
        before = json.dumps(rec, sort_keys=True)
        resolved_places.apply(json_file, [rec], by_manual)
        if code not in CENSUS_CODES:                      # their places of death stay in a case ("Beogradu")
            v = rec.get('death_place')
            if v and 'death_place' not in manual:
                new = structured.tidy_death_place(v)
                if new:
                    rec['death_place'] = new
                else:
                    rec.pop('death_place')
        standardize_fields.apply([rec], by_manual)
        if json.dumps(rec, sort_keys=True) == before:
            break
    record_sources.apply([rec], {rid: (code, rec)}, {rid: manual}, {})
    rec.update(fix_names(rec))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('record')
    ap.add_argument('fields', nargs='*', help='field=value (an empty value blanks the field)')
    ap.add_argument('--remove', nargs='+', default=[], metavar='FIELD', help="take these fields' override away")
    ap.add_argument('--reason', default='')
    ap.add_argument('--by', default='claude')
    ap.add_argument('--dry', action='store_true')
    args = ap.parse_args()
    t0 = time.time()
    rid, code = args.record, int(args.record[:4])
    if code not in OSTALI_CODES:
        raise SystemExit(f'{rid} is a unit\'s record: fix it with an edit correction in corrections.json, then '
                         f'python scripts/apply_corrections.py --apply --brigade {code}')
    sets = {}
    for f in args.fields:
        k, eq, v = f.partition('=')
        if not eq:
            raise SystemExit(f'{f!r}: write field=value')
        if k in REFUSED:
            raise SystemExit(f'{k} may not be set by hand (the entry stays as printed; a role is a decision)')
        sets[k] = v.strip()
    if not sets and not args.remove:
        raise SystemExit('nothing to change')

    json_file = BRIGADE_CONFIGS[code]['json_file']
    path = ROOT / 'website' / 'public' / json_file
    soldiers = json.loads(path.read_text(encoding='utf-8'))
    at = next((i for i, s in enumerate(soldiers) if s['soldier_id'] == rid), None)
    if at is None:
        now = json.loads(MOVED.read_text(encoding='utf-8')).get(rid) if MOVED.exists() else None
        if now:
            raise SystemExit(f'{rid} is now {now}' + ('' if int(now[:4]) in OSTALI_CODES else
                             f' in a unit: fix it with an edit correction, then apply_corrections.py --apply --brigade {int(now[:4])}')
                             + ('' if int(now[:4]) not in OSTALI_CODES else f': run this again with {now}'))
        raise SystemExit(f'{rid} is not in {json_file}')
    rec = soldiers[at]
    before = copy.deepcopy(rec)
    entry = entry_of(rid, rec)

    overrides = json.loads(OVERRIDES.read_text(encoding='utf-8')) if OVERRIDES.exists() else {}
    o = overrides.get(entry) or {'for': rid, 'fields': {}}
    if o.get('for') != rid:
        print(f'  note: the override of entry {entry} was written for {o.get("for")}; it is now {rid}')
        o['for'] = rid
    family = family_fields(rid)
    clash = {k: family[k] for k, v in sets.items() if k in family and family[k] != v}
    if clash:
        raise SystemExit(f"{rid}: the family's papers set {clash}; the family's report wins (the user's rule). Change it in "
                         f"the family's entry ({FAMILY.relative_to(ROOT)}), with the user's OK and a case in the ops repo")
    manual = set(rec.get('manual_fields') or ())
    for k, v in sets.items():
        v = one_form(rec, k, v) if v else ''
        o['fields'][k] = v
        if v:
            rec[k] = v
        else:
            rec.pop(k, None)
        manual.add(k)
    for k in args.remove:
        o['fields'].pop(k, None)
        manual.discard(k)
        if k == 'fathers_name':
            rec['fathers_name'] = ''      # chosen_fathers keeps a father it finds: the full run reads him anew
    if manual:
        rec['manual_fields'] = sorted(manual)
    else:
        rec.pop('manual_fields', None)
    cols = [k for k in rec.get('from_columns') or () if k not in manual]
    if cols:
        rec['from_columns'] = cols
    else:
        rec.pop('from_columns', None)
    if set(sets) & set(NAMES):
        rec['full_name'] = ' '.join(p for p in (rec.get(n) for n in NAMES) if p)

    per_record_steps(rec, code, json_file)

    if set(sets) & set(NAMES):               # the part is sorted by name (build_ostali_borci.by_name)
        from match_references import fold
        soldiers.sort(key=lambda r: (fold(r['last_name']), fold(r['first_name']), fold(r['middle_name']), r['soldier_id']))

    changed = {k for k in set(before) | set(rec) if before.get(k) != rec.get(k)}
    print(f"{rid} {rec.get('full_name')} ({json_file}), override by entry {entry}:")
    for k in sorted(changed):
        print(f'  {k}: {before.get(k)!r} -> {rec.get(k)!r}')
    if not changed:
        print('  nothing changes on the record')

    # the record's life events (the dialog's line), in the file's order
    import extract_life_events
    ev_path = LIFE_EVENTS / json_file
    events = json.loads(ev_path.read_text(encoding='utf-8')) if ev_path.exists() else {}
    mine = extract_life_events.unit_events(code, [rec])
    had = events.get(rid)
    if mine.get(rid) != had:
        if rid in mine:
            events[rid] = mine[rid]
        else:
            events.pop(rid, None)
        order = {s['soldier_id']: i for i, s in enumerate(soldiers)}
        events = dict(sorted(events.items(), key=lambda kv: order.get(kv[0], 1 << 30)))
        print('  life events:', 'changed' if had and rid in mine else 'added' if rid in mine else 'removed')

    if args.dry:
        print(f'dry run, nothing written ({time.time() - t0:.1f} s)')
        return
    if o['fields']:
        o.update({'reason': args.reason or o.get('reason', ''), 'by': args.by, 'date': date.today().isoformat()})
        overrides[entry] = o
    else:
        overrides.pop(entry, None)
    write_text(OVERRIDES, json.dumps(dict(sorted(overrides.items())), ensure_ascii=False, indent=1) + '\n')
    write_text(path, json.dumps(soldiers, ensure_ascii=False, indent=2))
    if mine.get(rid) != had:
        write_text(ev_path, json.dumps(events, ensure_ascii=False, separators=(',', ':')))
    print(f'written: {path.name}, {OVERRIDES.name}' + (f', life-events/{json_file}' if mine.get(rid) != had else '')
          + f' ({time.time() - t0:.1f} s)')


if __name__ == '__main__':
    main()
