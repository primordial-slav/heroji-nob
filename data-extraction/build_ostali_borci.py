"""
Ostali borci (unit 122): every soldier of a book across units who has no record on the site.

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

Usage:
    python data-extraction/build_ostali_borci.py            # dry run: counts and samples
    python data-extraction/build_ostali_borci.py --write    # write website/public/ostali-borci.json
Then: python scripts/normalize_all_json.py --brigade 122 --apply; python scripts/apply_corrections.py --apply.
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

CODE = 122
IDS = ROOT / 'data-extraction' / 'ostali_borci_ids.json'
FIRST_NEW = 900001
OUT = ROOT / 'website' / 'public' / 'ostali-borci.json'     # not *soldiers.json, which the parsers' corpora read
# names a parser read wrong, by entry: the Zbornik's headings "DEMONJ A (NIKOLA)", "RAKOVAC J (OAKIM)" and one whose
# OCR took a line of the text for the name (Pal Šoti, born 19 January 1916 in Bečej, as Narodni heroji 1982 has him)
NAME_FIXES = {'9001000203': ('Demonja', 'Nikola', ''), '9001000908': ('Rakovac', 'Joakim', ''),
              '9001001039': ('Šoti', 'Pal', 'Pala')}
# given names an OCR slip spoiled (one letter added, lost or swapped); the entry's text keeps them as printed
GIVEN_FIXES = {'9010000849': 'Milan', '9013000684': 'Mihailo', '9010000551': 'Milorad', '9013002857': 'Velimir',
               '9009000207': 'Velimir', '9010000622': 'Petar', '9007000140': 'Nikola', '9005001914': 'Miodrag',
               '9010000363': 'Dmitar'}
SOURCE_FIELDS = ('source_url', 'source_page', 'pdf_file', 'pdf_page', 'pdf_x', 'pdf_y', 'pdf_x_end', 'pdf_y_end',
                 'pdf_x_left', 'pdf_rects')


def books() -> dict[str, list[dict]]:
    out = {}
    for d in ENTRY_DIRS:
        for p in sorted(d.glob('*-entries.json')):
            out[p.name[:-len('-entries.json')]] = json.loads(p.read_text(encoding='utf-8'))
    return out


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
        if len(sa) == len(sb) == 1:
            agree.add('death year')
    da, db = max(sa, default=None), max(sb, default=None)
    if (a.get('survived') and db and db <= 1945) or (b.get('survived') and da and da <= 1945):
        return False
    pa, pb = places(a), places(b)
    if pa and pb and any(x[:4] == y[:4] for x in pa for y in pb):
        agree.add('birthplace')
    if set(a.get('units') or ()) & set(b.get('units') or ()):
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
    from name_utils import BRIGADE_CONFIGS
    for code, cfg in BRIGADE_CONFIGS.items():
        path = ROOT / 'website' / 'public' / cfg['json_file']
        if code != CODE and path.exists():
            for r in json.loads(path.read_text(encoding='utf-8')):
                if r.get('first_name'):
                    _given[r['first_name']] += 1


def from_possessive(word: str) -> str:
    """The father's name from the possessive Trebinjci pali prints, -ov/-ev of a name without -a ("Mitrov" Mitar, "Vulov"
    Vule or Vulo), -in of a name in -a ("Lučin" Luka, "Savin" Sava): the form the site's given names know best; '' when
    none of them is a name"""
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
    taken = {c['ref_id'] for c in corrections if c['action'] == 'reference' and not c['soldier_id'].startswith(f'{CODE:04d}')}
    entries = []
    for book, es in books().items():
        for e in es:
            e = dict(e, _book=book, _hero=book in HERO_BOOKS or bool(re.search(r'narodn\w*\s*heroj', e['additional_info'], re.I)))
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
            rid = record_id(g)
            used.add(rid)
            for m in g:
                ids[m['soldier_id']] = rid
            rec = {'soldier_id': rid, 'last_name': first['last_name'],
                   'middle_name': father, 'first_name': first['first_name'],
                   'fathers_name': from_possessive(father) if first['_book'] == 'trebinjci-pali' else '',
                   'full_name': '', 'additional_info': text,
                   'birth_year': str(year(first, 'birth_year') or '')}
            rec.update({k: first[k] for k in SOURCE_FIELDS if first.get(k) not in (None, '')})
            if rest:
                rec['other_sources'] = [source_entry(m) for m in rest]
            records.append(rec)
            counts[f'{len(g)} book(s)'] += 1
            counts['from ' + first['_book']] += 1
    records.sort(key=lambda r: (fold(r['last_name']), fold(r['first_name']), fold(r['middle_name']), r['soldier_id']))
    n_ids = Counter(r['soldier_id'] for r in records)
    assert max(n_ids.values()) == 1, [i for i, n in n_ids.items() if n > 1][:5]
    print(f'{len(entries)} entries, {len(taken)} on records of units; {len(records)} records')
    print(f'{len(on_site)} more entries are the same man as an entry on the site and stay out')
    for k, v in sorted(counts.items()):
        print(f'  {k}: {v}')
    print(f'{sum(1 for r in records if int(r["soldier_id"][4:]) >= FIRST_NEW)} records with a new ID')
    if write:
        OUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
        IDS.write_text(json.dumps(dict(sorted(ids.items())), ensure_ascii=False, indent=0), encoding='utf-8')
        print('Written', OUT, 'and', IDS)
    else:
        import random
        random.seed(1)
        for r in random.sample([r for r in records if r.get('other_sources')], 5):
            print(json.dumps(r, ensure_ascii=False)[:500])


if __name__ == '__main__':
    main()
