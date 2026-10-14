"""
Ostali borci (unit 122, and 131-138 for the 1964 census): every soldier of a book across units who has no record on
the site.

The books across units (the hero books, Trebinjci pali, the village chronicles, the Karlovac archive's volumes,
Ofanziva 1942, ...) are read by their parsers into data-extraction/{poreklo,znaci}/<book>-entries.json, and
scripts/match_references.py adds each entry that belongs to a record of a unit to that record (a `reference`
correction). The entries no record took are the soldiers whose unit is not on the site yet, or whom the books name
without one: they become records of their own here, so that their names and what the books say of them are on the
site and can be found.

One man printed in several of these books is one record: entries of the same name from different books that agree
(the father and one of birth year, birthplace, year of death; or birth year and birthplace; for two hero books the
father or the birth year; for the books that give little more than the name, a unit or the place of death together
with the year of death or each other), with nothing that disagrees, are merged, the richest entry first (a page on the
site's scans before the library's, then the longest text) and the others in `other_sources`. An entry of the same man
as an entry already on the site (a record took one of his entries) is left out: he has his record.

Record IDs are kept in data-extraction/ostali_borci_ids.json (entry ID -> record ID), so a record keeps its ID however
its entries change: a man whose entries had an ID keeps it (the first entry's, if two records of before become one), a
new man gets the next free one (0122900001 on; the first records took 0122 + the book's two digits + the entry's
number). A re-run after new references only drops the records whose men have found their unit.

The 1964 census of the war's dead (Žrtve rata 1941-1945, data-extraction/zrtve-rata/, one volume a republic or
province) names 180,000 fallen partisans, most with no other book: a man only the census names is a record of his
volume's part of Ostali borci (131-138, CENSUS_VOLUMES; 160,000 men would make one unit too big for a search part or
a file in git), with the ID of his census entry under the part's code (9021004235 -> 0132004235), so the registry
doesn't hold him; a man the census and another book name is a record of 122. Two census entries are never one man:
the volumes list each of the dead once, and one name, father and year in two republics are as a rule two men. The
census gives its columns as fields (born_in, ethnicity, death_year, death_place), which become the record's fields.

Usage:
    python data-extraction/build_ostali_borci.py            # dry run: counts and samples
    python data-extraction/build_ostali_borci.py --write    # write website/public/ostali-borci*.json
Then: python scripts/normalize_all_json.py --brigade 122 --apply (and 131-138); python scripts/apply_corrections.py --apply.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from match_references import ENTRY_DIRS, HERO_BOOKS, fold, same_father, stem  # noqa: E402
from extract_structured_fields import NAME_LISTS  # noqa: E402
from name_utils import BRIGADE_CONFIGS, CENSUS_VOLUMES, OSTALI_CODES  # noqa: E402

CODE = 122
IDS = ROOT / 'data-extraction' / 'ostali_borci_ids.json'
FIRST_NEW = 900001
OUT = ROOT / 'website' / 'public' / 'ostali-borci.json'     # not *soldiers.json, which the parsers' corpora read
CENSUS = 'zrtve-rata-1964'                                  # the census's volumes: zrtve-rata-1964-<vol>
# names a parser read wrong, by entry: the Zbornik's headings "DEMONJ A (NIKOLA)", "RAKOVAC J (OAKIM)" and one whose
# OCR took a line of the text for the name (Pal Šoti, born 19 January 1916 in Bečej, as Narodni heroji 1982 has him)
NAME_FIXES = {'9001000203': ('Demonja', 'Nikola', ''), '9001000908': ('Rakovac', 'Joakim', ''),
              '9001001039': ('Šoti', 'Pal', 'Pala')}
# given names an OCR slip spoiled (one letter added, lost or swapped); the entry's text keeps them as printed
GIVEN_FIXES = {'9010000849': 'Milan', '9013000684': 'Mihailo', '9010000551': 'Milorad', '9013002857': 'Velimir',
               '9009000207': 'Velimir', '9010000622': 'Petar', '9007000140': 'Nikola', '9005001914': 'Miodrag',
               '9010000363': 'Dmitar'}
# books that print the father in the nominative, as the census does: his name goes to fathers_name, not middle_name
NOMINATIVE_FATHERS = {'tuzla-spomen-knjiga'}
# books that print him as a possessive ("Mitrov", "Jovanova"): fathers_name is the nominative the site's names know
POSSESSIVE_FATHERS = {'trebinjci-pali', 'spomenica-crnogorskim-antifasistima'}
# books used only as references for men who have a unit record: their unmatched entries make no records; taking a book
# out of this set adds its unmatched men to Ostali borci (the Spomenica crnogorskim antifašistima was here until the
# user decided, on 2026-10-14, that every man it names counts as a partisan)
REFERENCE_ONLY: set = set()
# books printed as a table of columns, whose columns are the record's fields (as the census's are); every man of the
# Spomenica counts as a partisan who fell (the user's decision), so his death is "poginuo"
COLUMN_BOOKS = {'spomenica-crnogorskim-antifasistima'}


def column_fields(e: dict) -> dict:
    out = {'birth_place': e.get('born_in') or '', 'death_type': 'poginuo', 'death_date': e.get('death_year') or '',
           'death_place': e.get('death_place') or ''}
    return {k: v for k, v in out.items() if v}
SOURCE_FIELDS = ('source_url', 'source_page', 'pdf_file', 'pdf_page', 'pdf_x', 'pdf_y', 'pdf_x_end', 'pdf_y_end',
                 'pdf_x_left', 'pdf_rects')


def books() -> dict[str, list[dict]]:
    out = {}
    for d in ENTRY_DIRS:
        for p in sorted(d.glob('*-entries.json')):
            name = p.name[:-len('-entries.json')]
            if name not in REFERENCE_ONLY:
                out[name] = json.loads(p.read_text(encoding='utf-8'))
    return out


def census_fields(e: dict) -> dict:
    """A census entry's columns as the record's fields: "rođen 1888, Arbnež (Bar). Crnogorac, poginuo 1942. u NOBu, Zec
    Planina" (born_in "Arbnež, Bar", ethnicity, death_year, death_place; "Nepoznato" is no place)"""
    # its wordings: poginuo/poginula (157,000), umro/umrla (10,700, "od bolesti", "od ranjavanja"), ubijen (4,400),
    # nestao, streljan, obešen
    m = re.search(r'\b(poginu|umr|ubijen|nesta|streljan|obešen)', e['additional_info'])
    kind = ({'poginu': 'poginuo', 'umr': 'umro', 'nesta': 'nestao', 'obešen': 'ubijen'}.get(m.group(1), m.group(1))
            if m else 'poginuo')                       # the site's types: poginuo, umro, nestao, streljan, ubijen
    out = {'birth_place': e.get('born_in') or '', 'ethnicity': e.get('ethnicity') or '', 'death_type': kind,
           'death_date': e.get('death_year') or '', 'death_place': e.get('death_place') or ''}
    return {k: v for k, v in out.items() if v}


def year(e: dict, key: str) -> int | None:
    m = re.search(r'1[89]\d\d', str(e.get(key) or ''))
    return int(m.group(0)) if m else None


def places(e: dict) -> set[str]:
    return {stem(w) for w in fold(e.get('born_in') or '').split() if len(w) >= 4} - {'selu', 'opst', 'opsti', 'kotar', 'srez', 'okrug', 'kod'}


def father_of(e: dict) -> str:
    return fold(e.get('fathers_name') or '')


def same_man(a: dict, b: dict) -> bool:
    """Two entries of different books that are one man (see the module's note)"""
    agree = set()
    fa, fb = father_of(a), father_of(b)
    if fa and fb:
        if fa == fb or (len(fa) == 1 and fb.startswith(fa)) or (len(fb) == 1 and fa.startswith(fb)) or same_father(fa, fb):
            agree.add('father')
        else:
            return False
    ya, yb = year(a, 'birth_year'), year(b, 'birth_year')
    if ya and yb:
        if abs(ya - yb) > 1:
            return False
        agree.add('birth year')
    sa, sb = death_years(a), death_years(b)
    if sa and sb:
        if not sa & sb:
            return False
        if len(sa) == len(sb) == 1 or sa == sb:
            agree.add('death year')                        # or the same front's years (Gončin's and Tmušić's Srem)
    da, db = max(sa, default=None), max(sb, default=None)
    if (a.get('survived') and db and db <= 1945) or (b.get('survived') and da and da <= 1945):
        return False
    pa, pb = places(a), places(b)
    if pa and pb and any(x[:4] == y[:4] for x in pa for y in pb):
        agree.add('birthplace')
    if set(a.get('units') or ()) & set(b.get('units') or ()) or (
            not a.get('units') and not b.get('units') and unit_key(a) and unit_key(a) == unit_key(b)):
        agree.add('unit')
    qa, qb = death_places(a), death_places(b)
    if qa and qb and any(x[:4] == y[:4] for x in qa for y in qb):
        agree.add('death place')
    core = agree & {'birth year', 'birthplace', 'death year'}
    if 'father' in agree and core:
        return True
    if {'birth year', 'birthplace'} <= agree:
        return True
    # the lists that give a name, a brigade and where he fell (Gončin's Srem): the unit or the place of his death,
    # with the year of it or with each other
    if ('unit' in agree or 'death place' in agree) and len(agree & {'unit', 'death place', 'death year'}) >= 2:
        return True
    return bool(a.get('_hero') and b.get('_hero') and agree & {'father', 'birth year'})


ORDINALS = [('jedanaest', 11), ('dvanaest', 12), ('trinaest', 13), ('cetrnaest', 14), ('petnaest', 15),
            ('sesnaest', 16), ('sedamnaest', 17), ('osamnaest', 18), ('devetnaest', 19), ('prv', 1), ('drug', 2),
            ('trec', 3), ('cetvrt', 4), ('pet', 5), ('sest', 6), ('sedm', 7), ('osm', 8), ('devet', 9), ('deset', 10)]
ADJECTIVES = ('proletersk', 'krajisk', 'lick', 'srpsk', 'vojvodansk', 'crnogorsk', 'makedonsk', 'majevick',
              'istocnobosansk', 'konjick', 'kordunask', 'banijsk', 'dalmatinsk', 'slavonsk', 'hercegovack')
_keys: dict[str, str] = {}


def unit_key(e: dict) -> str:
    """A brigade not on the site, as two lists of one front name it ("Trideset prva srpska udarna brigada" and "Trideset
    prve srpske narodnooslobodilačke brigade": "31 srpsk"; an artillery brigade or the staff units of a division:
    "art 5 krajisk"; the brigade formed in the USSR, "Prva jugoslovenska" to Gončin): '' when the entry names none"""
    label = e.get('unit') or ''
    if label not in _keys:
        words = fold(label).split()
        key = ''
        if 'sssr' in words or 'jugoslovenska' in words:
            key = 'novj sssr'
        else:
            for i, w in enumerate(words):
                n = next((v for s, v in ORDINALS if w.startswith(s)), None)
                if w in ('dvadeset', 'trideset', 'cetrdeset', 'pedeset') and i + 1 < len(words):
                    n = {'dvadeset': 20, 'trideset': 30, 'cetrdeset': 40, 'pedeset': 50}[w] + next(
                        (v for s, v in ORDINALS if words[i + 1].startswith(s)), 0)
                    i += 1
                if n:
                    adj = next((a for x in words[i + 1:i + 4] for a in ADJECTIVES if x.startswith(a)), None)
                    if adj:
                        kind = ('art ' if any(x.startswith('artiljerij') for x in words) else
                                'stab ' if any(x.startswith('pristap') for x in words) else '')
                        key = f'{kind}{n} {adj}'
                    break
        _keys[label] = key
    return _keys[label]


def death_years(e: dict) -> set[int]:
    """The years he can have died in: the year the entry gives, or the span a list gives (`death_years`)"""
    ys = {int(y) for y in e.get('death_years') or () if re.fullmatch(r'19[34]\d', str(y))}
    y = year(e, 'death_year') or year(e, 'death_date')
    return {y} if y else ys


def death_places(e: dict) -> set[str]:
    return {stem(w) for w in fold(e.get('death_place') or '').split() if len(w) >= 4} - {'selu', 'kod', 'blizu'}


_given: Counter = Counter()


def given_names() -> None:
    """The site's given names, for a father the book gives as a possessive"""
    for code, cfg in BRIGADE_CONFIGS.items():
        path = ROOT / 'website' / 'public' / cfg['json_file']
        if code not in OSTALI_CODES and path.exists():
            for r in json.loads(path.read_text(encoding='utf-8')):
                if r.get('first_name'):
                    _given[r['first_name']] += 1


def from_possessive(word: str) -> str:
    """The father's name from the possessive Trebinjci pali prints, -ov/-ev of a name without -a ("Mitrov" Mitar, "Vulov"
    Vule or Vulo), -in of a name in -a ("Lučin" Luka, "Savin" Sava): the form the site's given names know best; '' when
    none of them is a name"""
    word = re.sub(r'(ov|ev|in)a$', r'\1', word)          # a daughter's: "Đokova", "Lučina"
    m = re.match(r'^(.+?)(ov|ev|in)$', word)
    if not m:
        return ''
    base, end = m.groups()
    if end in ('ov', 'ev'):
        cands = [base, base + 'o', base + 'e', re.sub(r'([^aeiou])([rl])$', r'\1a\2', base)]
    else:
        soft = base[:-1] + {'č': 'k', 'ž': 'g', 'š': 'h'}.get(base[-1], base[-1])      # Lučin: Luka
        cands = [base + 'a', soft + 'a', base[:-1] + 'ca']                              # Jovičin: Jovica
    best = max(cands, key=lambda c: _given[c])
    return best if _given[best] else ''


def registry() -> dict[str, str]:
    """Entry ID -> record ID; started from the file the first records were written to (0122 + the book's two digits +
    the entry's number, and the record's other entries)"""
    if IDS.exists():
        return json.loads(IDS.read_text(encoding='utf-8'))
    out = {}
    if OUT.exists():
        for r in json.loads(OUT.read_text(encoding='utf-8')):
            for o in r.get('other_sources') or ():
                if re.fullmatch(r'90\d{8}', o.get('soldier_id') or ''):
                    out[o['soldier_id']] = r['soldier_id']
            out.setdefault(f"90{r['soldier_id'][4:6]}00{r['soldier_id'][6:]}", r['soldier_id'])
    return out


def source_entry(e: dict) -> dict:
    out = {'soldier_id': e['soldier_id'], 'name': e['name'], 'additional_info': e['additional_info']}
    out.update({k: e[k] for k in SOURCE_FIELDS if e.get(k) not in (None, '')})
    return out


def main():
    write = '--write' in sys.argv
    given_names()
    corrections = json.loads((ROOT / 'corrections.json').read_text(encoding='utf-8'))
    # an entry a record of a unit took (not one of this unit's: those come and go with this script)
    ostali = {f'{c:04d}' for c in OSTALI_CODES}
    taken = {c['ref_id'] for c in corrections if c['action'] == 'reference' and c['soldier_id'][:4] not in ostali}
    entries = []
    for book, es in books().items():
        # the census's volumes are one book, its volume kept for the part of Ostali borci its men go to
        vol = book[len(CENSUS) + 1:] if book.startswith(CENSUS + '-') else ''
        for e in es:
            e = dict(e, _book=CENSUS if vol else book, _vol=vol,
                     _hero=book in HERO_BOOKS or bool(re.search(r'narodn\w*\s*heroj', e['additional_info'], re.I)))
            if e['soldier_id'] in NAME_FIXES:
                e['last_name'], e['first_name'], e['fathers_name'] = NAME_FIXES[e['soldier_id']]
                e['name'] = f"{e['last_name']} {e['first_name']}"
            if e['soldier_id'] in GIVEN_FIXES:
                e['first_name'] = GIVEN_FIXES[e['soldier_id']]
                e['name'] = f"{e['last_name']} {e['first_name']}"
            # a man the book could not name ("Nepoznati borac") is no one a search can find
            if e.get('last_name') and e.get('first_name') and not e.get('unnamed'):
                entries.append(e)
    by_name = defaultdict(list)
    for e in entries:
        by_name[(fold(e['last_name']), fold(e['first_name']))].append(e)

    # one man across books: the entries of a name joined pair by pair (never two entries of one book)
    parent = {e['soldier_id']: e['soldier_id'] for e in entries}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for group in by_name.values():
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                if a['_book'] != b['_book'] and same_man(a, b):
                    parent[find(a['soldier_id'])] = find(b['soldier_id'])
    clusters = defaultdict(list)
    for e in entries:
        clusters[find(e['soldier_id'])].append(e)

    ids = registry()
    next_number = max([int(v[4:]) for v in ids.values() if int(v[4:]) >= FIRST_NEW], default=FIRST_NEW - 1) + 1
    used = set()

    def record_id(group: list[dict]) -> str:
        """The ID the group's man had (its first entry's, if two records of before become one), else a new one"""
        nonlocal next_number
        for m in group:
            rid = ids.get(m['soldier_id'])
            if rid and rid not in used:
                return rid
        rid = f'{CODE:04d}{next_number:06d}'
        next_number += 1
        return rid

    records, counts, on_site = [], Counter(), []
    for members in clusters.values():
        # a cluster that took two entries of one book is two men (or the book's one man printed twice): the entries of
        # that book stay apart, and an entry of another book joins the one it agrees with, or stays alone if it agrees
        # with both
        if len({m['_book'] for m in members}) < len(members):
            book = Counter(m['_book'] for m in members).most_common(1)[0][0]
            groups = [[m] for m in members if m['_book'] == book]
            for m in members:
                if m['_book'] == book:
                    continue
                fits = [g for g in groups if same_man(g[0], m) and m['_book'] not in {x['_book'] for x in g}]
                if len(fits) == 1:
                    fits[0].append(m)
                else:
                    groups.append([m])
            counts['clusters split (two entries of one book)'] += 1
        else:
            groups = [members]
        for g in groups:
            if any(m['soldier_id'] in taken for m in g):
                on_site += [m for m in g if m['soldier_id'] not in taken]
                continue
            g.sort(key=lambda m: (not m.get('pdf_file'), -len(m['additional_info']), m['soldier_id']))
            first, rest = g[0], g[1:]
            text = first['additional_info'].strip()
            if first.get('nick') and first['nick'] not in text:
                text = f"zvani {first['nick']}; {text}"
            father = first.get('fathers_name') or ''
            census = [m for m in g if m['_vol']]
            if census and len(census) == len(g):
                # only the census names him: his volume's part, his census entry's number (no registry)
                code = CENSUS_VOLUMES[first['_vol']]
                rid = f"{code:04d}{first['soldier_id'][4:]}"
            else:
                code = CODE
                rid = record_id(g)
                for m in g:
                    ids[m['soldier_id']] = rid
            used.add(rid)
            # the census prints the father in the nominative ("Marković (Rade) Tomo"): as printed in its parts (their
            # config says nominative), only as fathers_name in 122, whose normalization reads a middle name as genitive
            # (and so does the Tuzla memorial book: "AJDASLIĆ, MUJO (Avdo i Fatima)")
            nominative = first['_vol'] or first['_book'] in NOMINATIVE_FATHERS
            rec = {'soldier_id': rid, 'last_name': first['last_name'],
                   'middle_name': '' if nominative and code == CODE else father, 'first_name': first['first_name'],
                   'fathers_name': (from_possessive(father) if first['_book'] in POSSESSIVE_FATHERS else
                                    father if nominative else ''),
                   'full_name': '', 'additional_info': text,
                   'birth_year': str(year(first, 'birth_year') or '')}
            rec.update({k: first[k] for k in SOURCE_FIELDS if first.get(k) not in (None, '')})
            # a names-only list of the fallen (Gončin's and Tmušić's Srem, Oborovo) holds no bio for the field
            # extractor: the death from its entries' fields, the village he fell at and the day where it gives them
            listed = [m for m in g if m.get('pdf_file') in NAME_LISTS]
            if listed:
                rec['death_type'] = 'poginuo'
                place = next((m['death_place'] for m in listed if m.get('death_place')), '')
                day = next((m['death_date'] for m in listed if re.fullmatch(r'\d{4}-\d\d-\d\d', m.get('death_date') or '')), '')
                if place:
                    rec['death_place'] = place
                if day:
                    y, mo, d = day.split('-')
                    rec['death_date'] = f'{int(d)}. {int(mo)}. {y}.'
            if census:
                for k, v in census_fields(census[0]).items():
                    rec.setdefault(k, v)                     # the census's columns, where a list gave no death
            columns = [m for m in g if m['_book'] in COLUMN_BOOKS]
            if columns:
                for k, v in column_fields(columns[0]).items():
                    rec.setdefault(k, v)                     # the Spomenica's columns
            if rest:
                rec['other_sources'] = [source_entry(m) for m in rest]
            records.append(rec)
            counts[f'{len(g)} book(s)'] += 1
            counts['from ' + first['_book'] + (f" ({first['_vol']})" if first['_vol'] else '')] += 1
    n_ids = Counter(r['soldier_id'] for r in records)
    assert max(n_ids.values()) == 1, [i for i, n in n_ids.items() if n > 1][:5]
    parts = defaultdict(list)                                 # code -> its records
    for r in records:
        parts[int(r['soldier_id'][:4])].append(r)
    for recs in parts.values():
        recs.sort(key=lambda r: (fold(r['last_name']), fold(r['first_name']), fold(r['middle_name']), r['soldier_id']))
    print(f'{len(entries)} entries, {len(taken)} on records of units; {len(records)} records')
    print(f'{len(on_site)} more entries are the same man as an entry on the site and stay out')
    for k, v in sorted(counts.items()):
        print(f'  {k}: {v}')
    for code in sorted(parts):
        print(f"  {code}: {len(parts[code])} records")
    print(f'{sum(1 for r in parts[CODE] if int(r["soldier_id"][4:]) >= FIRST_NEW)} records of {CODE} with a new ID')
    if write:
        for code in [CODE, *CENSUS_VOLUMES.values()]:
            path = ROOT / 'website' / 'public' / BRIGADE_CONFIGS[code]['json_file']
            path.write_text(json.dumps(parts.get(code, []), ensure_ascii=False, indent=2), encoding='utf-8')
            print('Written', path)
        IDS.write_text(json.dumps(dict(sorted(ids.items())), ensure_ascii=False, indent=0), encoding='utf-8')
        print('Written', IDS)
    else:
        import random
        random.seed(1)
        for r in random.sample([r for r in records if r.get('other_sources')], 5):
            print(json.dumps(r, ensure_ascii=False)[:500])


if __name__ == '__main__':
    main()
