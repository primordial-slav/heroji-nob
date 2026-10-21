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
FIELDS = ('birth_place', 'death_place')
PREP = r'(?:u|iz|kod|na|pri|v|od|do|blizu|ispod|iznad|pod|nad|prema|kraj|oko)'


@lru_cache(maxsize=1)
def load() -> dict:
    try:
        return json.loads(RESOLVED.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return {'units': {}, 'places': {}}


def _value(unit_file: str, field: str, text: str):
    return load()['units'].get(unit_file, {}).get(field, {}).get((text or '').strip())


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


def apply(unit_file: str, soldiers: list[dict], manual: dict | None = None) -> Counter:
    """put each resolved village in the nominative in place; manual: soldier_id -> fields corrections set"""
    done = Counter()
    for s in soldiers:
        kept = (manual or {}).get(s.get('soldier_id'), ())
        for field in FIELDS:
            if field in kept or not s.get(field):
                continue
            new = nominative(unit_file, field, s)
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
