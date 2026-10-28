"""
The birthplaces and places of death resolved to one place: data-extraction/places/resolved.json, written from
GeoNames (geonames.org, CC BY 4.0) by our local places tool (quality/places/gazetteer.py --site), only where
something narrows a printed name to one place: the only place of the name, the printed municipality, the unit's
own region, a town far bigger than the rest, a well-known mountain, river or region. A field it doesn't list is
unresolved (several places of the name, or none GeoNames knows) and is left alone.

    place_id(unit_file, field, text)   the GeoNames id of a stored birth_place / death_place, or None
                                       (scripts/build_relations.py groups the "Saborci i zemljaci" tree by it)
    apply(unit_file, soldiers, manual) a field whose village resolved through a case gets it in the nominative
                                       ("Gradcu, Virovitica" -> "Gradac, Virovitica", "Romaniji" -> "Romanija"),
                                       spelled as the place is named. A form that is plainly a case changes
                                       anywhere ("Užicu", "Tugarima", "Bosanskom Petrovcu"); one that could be a
                                       nominative too ("Kuli" of Kula, but "Radenkovići") only where the entry
                                       prints a preposition before it ("u Kuli"). Fields set by corrections stay.
    case_nominative(text)              a place stored in a case that GeoNames left unresolved (a name of several
                                       places, or of none it knows), from data-extraction/places/case_forms.json:
                                       "na Sutjesci" -> "Sutjeska", "u s. Bazje, Šid" -> "Bazje, Šid"; apply()
                                       uses it where the resolved places have nothing, after the table's
                                       births: a record's birthplace whose form is a case there and a village's
                                       own name elsewhere ("Marini, Trogir" -> "Marina, Trogir", not the
                                       Marini by Prijedor), soldier_id -> [the field as read, the new field]

    remember()                         the case forms of the Ostali borci files (122, 131-138) kept in
                                       data-extraction/places/ostali_cases.json: the gazetteer keys a field as it
                                       finds it, so once apply() has put "Podgrađu, Omiš" in the nominative its next
                                       run keys "Podgrađe, Omiš" alone, and build_ostali_borci.py, which writes those
                                       files anew, reads "u Podgrađu" again. _value() falls back to the kept forms
                                       there, resolved.json's own decision first; apply_corrections.py runs it first

scripts/apply_corrections.py runs apply() on every unit it writes. The entries' text is never touched.

Usage:
    python scripts/resolved_places.py              # how many fields each unit would change, with samples
    python scripts/resolved_places.py --apply      # write them (outside apply_corrections.py)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESOLVED = ROOT / 'data-extraction' / 'places' / 'resolved.json'
CASES = ROOT / 'data-extraction' / 'places' / 'case_forms.json'
KEPT = ROOT / 'data-extraction' / 'places' / 'ostali_cases.json'
REBUILT = 'ostali-borci'                # the files build_ostali_borci.py writes anew: ostali-borci.json, ostali-borci-*.json
FIELDS = ('birth_place', 'death_place')
PREP = r'(?:u|iz|kod|na|pri|v|od|do|blizu|ispod|iznad|pod|nad|prema|kraj|oko)'
# what a place in a case is stored after: a preposition the nominative drops, then the village's own word
# ("u s. Bazje", "u selu Dinjevcu"); "kod", "pod", "pri" stay ("kod Bihaća" is near it)
CASE_LEAD = re.compile(r'(?:(u|na|v)\s+)?(?:(s\.|selu|selo)\s*)?')


@lru_cache(maxsize=1)
def load() -> dict:
    try:
        return json.loads(RESOLVED.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return {'units': {}, 'places': {}}


@lru_cache(maxsize=1)
def case_forms() -> dict:
    """the reviewed table of places in a case (quality/places/case_forms.py writes it): forms -> nominative, and
    the forms that may change with no preposition before them"""
    try:
        t = json.loads(CASES.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return {'forms': {}, 'bare': set(), 'births': {}, 'direct': set()}
    return {'forms': t['forms'], 'bare': set(t['bare']), 'births': t.get('births', {}), 'direct': set(t.get('direct', []))}


def case_nominative(text: str, s: dict | None = None) -> str | None:
    """'na Sutjesci' -> 'Sutjeska', 'u s. Bazje, Šid' -> 'Bazje, Šid', the census's 'Pločama' -> 'Ploče' (a bare
    form where the table says it can only be a case, or where the record's entry prints "u" before it: a birthplace
    "Ripnju, Beograd" of "rođen 1923. u Ripnju - Beograd"); None where the table has nothing"""
    first, sep, rest = (text or '').partition(',')
    first = first.strip()
    m = CASE_LEAD.match(first)
    form = first[m.end():].strip()
    t = case_forms()
    new = t['forms'].get(form)
    if new is None:
        return None
    if form in t['direct']:
        # a form that is a village's own name somewhere ("Peći", "Brezovici"): only right after "u", never after
        # "u selu" ("u selu Peći" is the village Peći of Bosansko Grahovo)
        if m.group(2):
            return None
        printed = re.compile(rf'(?<![\w])(?:u|na|v)\s+{re.escape(form)}(?![\w])')
        if not m.group(1) and (s is None or not any(printed.search(x) for x in _texts(s))):
            return None
    elif not (m.group(1) or m.group(2) or form in t['bare']):
        printed = re.compile(rf'(?<![\w])(?:u|na|v)\s+(?:s\.\s*|selu\s+)?{re.escape(form)}(?![\w])')
        if s is None or not any(printed.search(x) for x in _texts(s)):
            return None
    return new + sep + rest


@lru_cache(maxsize=1)
def kept() -> dict:
    try:
        return json.loads(KEPT.read_text(encoding='utf-8'))['units']
    except FileNotFoundError:
        return {}


def remember() -> int:
    """add resolved.json's case forms of the rebuilt files (a field -> [id, the nominative, plain]) to the kept ones;
    returns how many were new"""
    units, added = json.loads(json.dumps(kept())), 0
    for unit, fields in load()['units'].items():
        if not unit.startswith(REBUILT):
            continue
        for field, m in fields.items():
            for text, v in m.items():
                if isinstance(v, list) and units.setdefault(unit, {}).setdefault(field, {}).get(text) != v:
                    units[unit][field][text] = v
                    added += 1
    if added:
        doc = {'about': 'The case forms of the Ostali borci files (unit 122 and the census parts) that '
                        'data-extraction/places/resolved.json has keyed: the field as stored -> [GeoNames id, the field '
                        'with its village in the nominative, 1 if plainly a case]. build_ostali_borci.py writes those '
                        'files anew, and the gazetteer keys only what the files hold when it runs, so the forms are '
                        'kept here (scripts/resolved_places.py remember(), run by apply_corrections.py).',
               'units': {u: {f: dict(sorted(m.items())) for f, m in sorted(fs.items())} for u, fs in sorted(units.items())}}
        KEPT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding='utf-8')
        kept.cache_clear()
    return added


def _value(unit_file: str, field: str, text: str):
    text = (text or '').strip()
    v = load()['units'].get(unit_file, {}).get(field, {}).get(text)
    if v is None and unit_file.startswith(REBUILT):
        v = kept().get(unit_file, {}).get(field, {}).get(text)
    return v


def place_id(unit_file: str, field: str, text: str) -> int | None:
    v = _value(unit_file, field, text)
    return v[0] if isinstance(v, list) else v


def coords(gid: int) -> list | None:
    return load()['places'].get(str(gid))


def _texts(s: dict):
    yield s.get('additional_info') or ''
    for o in s.get('other_sources') or []:
        if not o.get('ref_book'):
            yield o.get('additional_info') or ''


def nominative(unit_file: str, field: str, s: dict) -> str | None:
    """the record's field with its village in the nominative, or None"""
    text = (s.get(field) or '').strip()
    v = _value(unit_file, field, text)
    if not isinstance(v, list):
        return None
    _, new, plain = v
    if not plain:
        village = re.split(r'\s*[,(]', text)[0]
        rx = re.compile(rf'(?<![\w]){PREP}\s+(?:s\.\s*|sel[ua]\s+)?{re.escape(village)}(?![\w])', re.I)
        if not any(rx.search(t) for t in _texts(s)):
            return None
    return new


def same_reading(read: str, field: str) -> bool:
    """the field as the table's record read it, or the same word put in another case since (the known places' vote
    reads "u Jarku" as Jarak since 2026-10-28, the table's "Jarku, Hrašćina Trgovišće" is Jarek): the same text after
    the first word, and the first word the same but for its last three letters"""
    if read == field:
        return True
    (a, rest_a), (b, rest_b) = (re.match(r'([^\s,]*)(.*)', x).groups() for x in (read, field))
    stem = min(len(a), len(b)) - 3
    return rest_a == rest_b and stem >= 2 and a[:stem] == b[:stem]


def apply(unit_file: str, soldiers: list[dict], manual: dict | None = None) -> Counter:
    """put each resolved village in the nominative in place; manual: soldier_id -> fields corrections set"""
    done = Counter()
    births = case_forms()['births']
    for s in soldiers:
        kept = (manual or {}).get(s.get('soldier_id'), ())
        for field in FIELDS:
            if field in kept or not s.get(field):
                continue
            # a birthplace whose form is a case in one record and a village's own name in another ("u Marini, Trogir"
            # is Marina, "u selu Marini, Prijedor" Marini): the table's record, while the field is as it was read
            own = births.get(s.get('soldier_id')) if field == 'birth_place' else None
            new = (own[1] if own and same_reading(own[0], s[field]) else None) or nominative(unit_file, field, s) \
                or case_nominative(s[field], s)
            if new and new != s[field]:
                s[field] = new
                done[field] += 1
    return done


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.path.insert(0, str(Path(__file__).parent))
    from name_utils import BRIGADE_CONFIGS          # noqa: E402
    from cleanup_text_fields import live_json_files  # noqa: E402
    import apply_corrections                         # noqa: E402

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--brigade', type=int)
    ap.add_argument('--sample', type=int, default=4)
    args = ap.parse_args()
    manual = {}
    for c in apply_corrections.load_corrections(ROOT / 'corrections.json'):
        got = (set(c.get('fields', {})) | set(c.get('record', {}))) & set(FIELDS)
        if got:
            manual.setdefault(c.get('new_id') or c['soldier_id'], set()).update(got)
    live, total = live_json_files(), Counter()
    for code, cfg in sorted(BRIGADE_CONFIGS.items()):
        if (args.brigade and code != args.brigade) or cfg['json_file'] not in live:
            continue
        path = ROOT / 'website' / 'public' / cfg['json_file']
        text = path.read_text(encoding='utf-8')
        soldiers = json.loads(text)
        before = {s['soldier_id']: (s.get('birth_place'), s.get('death_place')) for s in soldiers}
        done = apply(cfg['json_file'], soldiers, manual)
        if not done:
            continue
        total.update(done)
        print(f"{code:4} {cfg['json_file']}: {dict(done)}")
        shown = 0
        for s in soldiers:
            b, d = before[s['soldier_id']]
            if (b, d) != (s.get('birth_place'), s.get('death_place')) and shown < args.sample:
                print(f"       {s['soldier_id']} {b!r}->{s.get('birth_place')!r}  {d!r}->{s.get('death_place')!r}")
                shown += 1
        if args.apply:
            new_text = json.dumps(soldiers, ensure_ascii=False, indent=2)
            if new_text != text:
                path.write_text(new_text, encoding='utf-8')
    print(f'total {dict(total)}' + ('' if args.apply else ' (dry run)'))


if __name__ == '__main__':
    main()
