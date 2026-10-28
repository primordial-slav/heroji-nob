"""
Find the records a reference book's entries belong to: the soldiers of the site's units that a book across units
(a hero's portrait in the Zbornik narodnih heroja, ...) describes. The book's entries are read by its parser into
data-extraction/poreklo/<book>-entries.json (a book of the Poreklo library) or data-extraction/znaci/<book>-entries.json
(a znaci.org book whose PDF is on the site); each match becomes a `reference` correction, which apply_corrections.py
turns into an entry in the record's other_sources (the book's text, its page in the library or the PDF's page and the
entry's box), as a merge would.

A match needs the same surname and given name (letters folded) and more that agrees, with nothing that disagrees:
    sure     the father's name and one of: birth year (within a year), birthplace, year of death; or birth year and
             birthplace; or the record already calls him a narodni heroj and one of father, birth year, birthplace;
             or, in a book that lists soldiers by unit, a record of that unit and one of father, birth year,
             birthplace, the day of death
    likely   one of father, birth year, birthplace, year of death, day of death
A father's name printed differently (not an initial of it, nor the same name in another case), birth years more than a
year apart, a different year of death, a hero who lived past the war against a record of the fallen, or (where the record
doesn't call him a hero) a birthplace that shares no place name with the book's, rule a pair out.

Usage:
    python scripts/match_references.py zbornik-heroja-1957                   # dry run: grades and samples
    python scripts/match_references.py zbornik-heroja-1957 --json out.json   # every match, for review
    python scripts/match_references.py zbornik-heroja-1957 --write sure      # append reference corrections
    python scripts/match_references.py zbornik-heroja-1957 --only pairs.txt  # exactly these "record_id ref_id" pairs
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent))
import extract_structured_fields as structured  # noqa: E402
from name_utils import OSTALI_CODES  # noqa: E402
from extract_life_events import iso, parse_when  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CORRECTIONS = ROOT / 'corrections.json'
# the books' entries: the Poreklo library's (no scan on the site) and znaci.org's (the PDF on the site)
ENTRY_DIRS = (ROOT / 'data-extraction' / 'poreklo', ROOT / 'data-extraction' / 'znaci',
              ROOT / 'data-extraction' / 'zrtve-rata',      # the 1964 census of the war's dead, a volume a republic
              ROOT / 'data-extraction' / 'porodica')        # what families sent from their papers (no book prints them)


def entries_path(book: str) -> Path:
    paths = [d / f'{book}-entries.json' for d in ENTRY_DIRS]
    return next((p for p in paths if p.exists()), paths[0])
FOLD = str.maketrans('ČĆŽŠĐčćžšđ', 'CCZSDcczsd')
HERO = re.compile(r'narodn\w*\s*heroj(?!i)', re.I)
HERO_BOOKS = {'zbornik-heroja-1957', 'narodni-heroji-1982'}
DEATH = re.compile(r'\b(?:Poginu[oa]|Pogin|Streljan[a]?|Strelian|Obešen[a]?|Umr[oe]|Umrla|Ubijen[a]?|Ubio se|Ubila se|'
                   r'Umoren[a]?|Zaklan[a]?|Nestao|Nestala|Spaljen|Podlegao|Podlegla)\b[^.]*?\b(19[34]\d)\b')


def fold(text: str) -> str:
    return re.sub(r'[^a-z ]', '', (text or '').translate(FOLD).lower().replace('dj', 'd')).strip()


def stem(word: str) -> str:
    w = fold(word).replace(' ', '')
    return w[:5] if len(w) >= 5 else w


def same_father(a: str, b: str) -> bool:
    """Two spellings of one father's name in different cases or forms: "Jurja" and "Juraj", "Petra" and "Petar",
    "Pavla" and "Pavao", "Mile" and "Mileta", "Jove" and "Jovana"; not "Mile" and "Miloša" (folded, lower case)"""
    if min(len(a), len(b)) < 4 or a[:3] != b[:3]:
        return False
    def bases(x):
        x = re.sub(r'ao$', 'l', x)                                              # Pavao/Pavla
        x = re.sub(r'(?:ov|ev|in|ova|eva|ina|[aeiou])$', '', x)
        return {x, re.sub(r'a(?=[^aeiou]$)', '', x)}                            # Juraj/Jurja, Petar/Petra
    ba, bb = bases(a), bases(b)
    if ba & bb:
        return True
    return any(y.startswith(x) and y[len(x):] in ('et', 'ot', 'an', 'o', 'ij', 'k')     # Mile/Mileta, Jove/Jovana
               for p, q in ((ba, bb), (bb, ba)) for x in p for y in q)


FOLD_BUT_DJ = str.maketrans('ČĆŽŠčćžš', 'CCZScczs')


def initial_of(a: str, b: str) -> bool:
    """One father is the other's initial: "M." for Milan, "Lj." for Ljubo, "Dž." for Džemal, "Đ." (or "Dj.") for Đura
    or Djura but not Dušan; "D." for Đura too (a stroke the print or the OCR lost). From the printed names, since
    fold() writes Đ as D and leaves Lj, Nj, Dž two letters."""
    def letters(x):
        return re.sub(r'[^a-zđ]', '', (x or '').translate(FOLD_BUT_DJ).lower().replace('dj', 'đ'))
    short, long = sorted((letters(a), letters(b)), key=len)
    if not short:
        return False
    if len(short) == 1:
        return long[0] == short or (short == 'd' and long[0] == 'đ')
    return short in ('lj', 'nj', 'dz') and long.startswith(short)


def evidence(ref: dict, s: dict) -> tuple[list[str], list[str]]:
    agree, clash = [], []
    # a record that calls him a narodni heroj counts only for an entry that does too: a village book's Živković Živko of
    # Makce is not the hero Živković Radosava Živko of Buče because both were born in 1912
    hero = bool(HERO.search(ref['additional_info'])) or bool(ref.get('hero'))
    rf, sf = fold(ref['fathers_name']), fold(s.get('middle_name') or '')
    if rf and sf:
        # a book that gives the father as a possessive (Trebinjci pali: "Muharemov", "Jovičin") against the site's
        # genitive ("Muharema", "Jovice"): the same name once both endings are off
        def possessive(p, g):                                   # either side may give the possessive ("Lazin")
            m = re.match(r'^(.{3,}?)(?:ov|ev|in|ova|eva|ina)$', p)
            return bool(m) and len(g) >= 3 and m.group(1) == re.sub(r'[aeiou]$', '', g)
        # (and the same name in another case: the census's nominative "Mašan" against the site's genitive "Mašana")
        if rf == sf or initial_of(ref['fathers_name'], s.get('middle_name')) or (
                possessive(rf, sf) or possessive(sf, rf)) or same_father(rf, sf):
            agree.append('father')
        else:
            # a father whose name begins the same but is not clearly the same name ("Mile" and "Miloša", or an OCR
            # slip, "Mustave" for Mustafe) weighs against the pair without ruling it out (see grade)
            clash.append('father?' if min(len(rf), len(sf)) >= 4 and rf[:3] == sf[:3] else 'father')
    ry, sy = ref.get('birth_year'), re.search(r'1[89]\d\d', s.get('birth_year') or '')
    if ry and sy:
        if abs(int(ry) - int(sy.group(0))) <= 1:
            agree.append('birth year')
        else:
            clash.append('birth year')
    texts = ' '.join([s.get('birth_place') or '', s.get('additional_info') or ''] +
                     [o.get('additional_info') or '' for o in s.get('other_sources', ())])
    words = set(fold(texts).split())
    village = (ref.get('born_in') or '').split(',')[0].strip()
    if village:
        v = stem(village.split()[-1] if len(village.split()) > 1 and len(village.split()[-1]) > 3 else village.split()[0])
        if len(v) >= 4 and any(w.startswith(v) for w in words):
            agree.append('birthplace')
        elif s.get('birth_place') and not (hero and HERO.search(texts)):
            # a record that doesn't call him a hero, whose birthplace shares no place name with the book's village and
            # district, is another man of the same name (Kukić Nikole Milan of Gorička, Dvor, is not the hero born in
            # Baljci, Bileća); a record that does is the hero, his village printed in another case ("u Stocu", Stolac)
            places = {stem(w) for w in fold(ref['born_in']).split() if len(w) >= 4} - {'selu', 'opst', 'opsti', 'kotar', 'srez', 'okrug'}
            record = {stem(w) for w in fold(s['birth_place']).split() if len(w) >= 4}
            if places and record and not any(a[:3] == b[:3] for a in places for b in record):
                clash.append('birthplace')
    # a book whose entries keep only part of the biography gives the year he fell and whether he lived past the war
    # as fields of their own (Narodni heroji Jugoslavije, 1982); the Zbornik's summary says it in its words
    death = DEATH.search(ref['additional_info']) if 'death_year' not in ref else None
    dy = death.group(1) if death else ref.get('death_year') or ''
    alive = bool(re.search(r'\bDanas\s*:', ref['additional_info'])) or bool(ref.get('survived'))
    record_death = re.search(r'19[34]\d', s.get('death_date') or '') if s.get('death_type') in ('poginuo', 'streljan', 'ubijen', 'nestao') else None
    if dy:
        if dy in (s.get('death_date') or '') or re.search(rf'\b(?:pogin|strelj|umr|ubijen|obe[sš]en)\w*[^.;]{{0,60}}\b{dy}\b', texts, re.I):
            agree.append('death year')
        elif record_death and record_death.group(0) != dy:
            clash.append('death year')                     # Kostić Blagoje "Crni Marko" fell in 1943, the other in 1944
        if re.search(r'\bŽivi\b', s.get('additional_info') or ''):
            clash.append('alive on the site')              # the book has him fallen, the record alive (Ilić Mile Sava)
    elif alive and record_death:
        clash.append('alive after the war')                # the book has him alive, the record killed in the war
    if hero and HERO.search(texts):
        agree.append('hero on the site')
    # a book that lists the soldiers by unit (Ofanziva 1942: the fallen of four brigades) gives the site's unit codes,
    # and the day he fell when it prints one
    if int(s['soldier_id'][:4]) in ref.get('units', ()):
        agree.append('unit')
    if re.fullmatch(r'\d{4}-\d\d-\d\d', ref.get('death_date') or '') and s.get('death_date'):
        when = parse_when(s['death_date'])
        if when and when[0][2] and iso(when[0]) == ref['death_date']:
            agree.append('death day')
    # a book that names only where he fell (U rovovima Srema: the villages of the Srem front under each brigade) gives
    # that place, and the years its fighting lasted: a record that has him fall in another year is another man
    if ref.get('death_place'):
        place = ref['death_place'].split()
        p = stem(place[-1] if len(place) > 1 and len(place[-1]) > 3 else place[0])
        died = fold(' '.join([s.get('death_place') or '', s.get('additional_info') or ''] +
                             [o.get('additional_info') or '' for o in s.get('other_sources', ())])).split()
        if len(p) >= 4 and any(w.startswith(p) for w in died):
            agree.append('death place')
    if ref.get('death_years') and record_death and record_death.group(0) not in ref['death_years']:
        clash.append('death year')
    return agree, clash


def grade(agree: list[str], clash: list[str]) -> str | None:
    if [c for c in clash if c != 'father?']:
        return None
    a = set(agree)
    core = a & {'birth year', 'birthplace', 'death year'}
    if 'father?' in clash:
        # a father not clearly the same: sure only with all three of birth year, birthplace and death, or a hero on
        # the site and one more (Ilić Miloša Nikola, alive, is not the Ilić Mile Nikola who fell near Gračac)
        if len(core) == 3 or ('hero on the site' in a and core):
            return 'sure'
        return 'likely' if core else None
    if 'father' in a and core:
        return 'sure'
    if {'birth year', 'birthplace'} <= a:
        return 'sure'
    if 'hero on the site' in a and (a & {'father', 'birth year', 'birthplace'}):
        return 'sure'
    if 'unit' in a and (a & {'father', 'birth year', 'birthplace', 'death day', 'death place'}):
        return 'sure'
    if a - {'hero on the site', 'unit'}:
        return 'likely'
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('book', help='the entries file: data-extraction/{poreklo,znaci}/<book>-entries.json')
    ap.add_argument('--json', help='write every match here, for review')
    ap.add_argument('--write', help='grades to append as reference corrections, e.g. "sure"')
    ap.add_argument('--only', help='file of "record_id ref_id [why]" lines: append exactly these (reviewed) matches')
    ap.add_argument('--start', type=int, help="the first correction id to give (a session's own range)")
    args = ap.parse_args()

    refs = json.loads(entries_path(args.book).read_text(encoding='utf-8'))
    if args.book in HERO_BOOKS:
        for r in refs:
            r['hero'] = True                               # every entry of these books is a narodni heroj
    from record_sources import own_only
    index = defaultdict(list)
    for code, (_, soldiers) in structured.load_live().items():
        if code in OSTALI_CODES:                           # Ostali borci: made of the entries no unit's record took
            continue
        for s in soldiers:
            # not what the record borrowed from another unit or the census (scripts/record_sources.py)
            index[(fold(s.get('last_name')), fold(s.get('first_name')))].append(own_only(s))
    found, grades, every = [], Counter(), {}
    for ref in refs:
        names = {fold(ref['first_name'])} | ({fold(ref['nick'])} if ref.get('nick') else set())
        # a woman the book gives two surnames (married, maiden) may be on the site under either
        lasts = {fold(ref['last_name'])} | {fold(x) for x in ref.get('also', ())}
        cands = [s for l in lasts for n in names for s in index.get((l, n), [])]
        for s in cands:
            agree, clash = evidence(ref, s)
            g = grade(agree, clash)
            pair = {'grade': g, 'agree': agree, 'record': s['soldier_id'], 'record_name': s.get('full_name'),
                    'ref': ref['soldier_id'], 'ref_name': ref['name'], 'ref_info': ref['additional_info'][:160],
                    'record_info': (s.get('additional_info') or '')[:160]}
            every[(s['soldier_id'], ref['soldier_id'])] = pair
            if g:
                grades[g] += 1
                found.append(pair)
    # two entries of the book that are not one man (another father, birth years apart) matched to one record: which of
    # them it is, the record doesn't say (Đaković Dane Nikola and Đaković Mile Nikola, both of 1914, of Mogorić)
    refs = {r['soldier_id']: r for r in refs}
    by_record = defaultdict(list)
    for f in found:
        by_record[f['record']].append(f)

    def one_man(a, b):
        fa, fb = fold(a['fathers_name']), fold(b['fathers_name'])
        ya, yb = (re.search(r'1[89]\d\d', x.get('birth_year') or '') for x in (a, b))
        return not (fa and fb and fa != fb and not same_father(fa, fb)) and not (
            ya and yb and abs(int(ya.group(0)) - int(yb.group(0))) > 1)
    for fs in by_record.values():
        if len({f['ref'] for f in fs}) > 1 and not all(one_man(refs[a['ref']], refs[b['ref']]) for a in fs for b in fs):
            for f in fs:
                f['grade'] = None
    # an entry matched to two records of one unit, one with its father and one without: two men of the name in that
    # unit, and the entry is the one with the father (Bokan Milana Dušan, not Bokan Mile Dušan of the same village);
    # unless the other record calls him a narodni heroj too (a hero the unit's second book prints without his father)
    by_unit = defaultdict(list)
    for f in found:
        if f['grade']:
            by_unit[(f['ref'], f['record'][:4])].append(f)
    for fs in by_unit.values():
        if any('father' in f['agree'] for f in fs):
            for f in fs:
                if 'father' not in f['agree'] and 'hero on the site' not in f['agree']:
                    f['grade'] = None
    grades = Counter(f['grade'] for f in found if f['grade'])
    found = [f for f in found if f['grade']]
    heroes = {f['ref'] for f in found if f['grade'] == 'sure'}
    print(f'{len(refs)} entries; matches {dict(grades)}; heroes with a sure match: {len(heroes)}')
    for f in found[:0]:
        print(f)
    if args.json:
        Path(args.json).write_text(json.dumps(found, ensure_ascii=False, indent=1), encoding='utf-8')
    chosen = [f for f in found if args.write and f['grade'] in set(args.write.split(','))]
    why = {}
    if args.only:
        # a third column says why a script chose the pair (select_front_references.py: "front:months+place")
        lines = [ln.split() for ln in Path(args.only).read_text(encoding='utf-8').splitlines() if ln.strip()]
        why = {tuple(x[:2]): ' '.join(x[2:]) for x in lines if len(x) > 2}
        pairs = {tuple(x[:2]) for x in lines}
        # a reviewed pair of the same name is taken whatever its grade: a clash that the book's text explains (a
        # death a month off, a village printed in another case) was read and judged
        missing = sorted(p for p in pairs if p not in every)
        if missing:
            sys.exit(f'--only: no record and entry of the same name for {missing}')
        chosen += [dict(every[p], grade=every[p]['grade'] or 'reviewed') for p in sorted(pairs)
                   if not any((f['record'], f['ref']) == p for f in chosen)]
    if chosen:
        corr = json.loads(CORRECTIONS.read_text(encoding='utf-8'))
        have = {(c['soldier_id'], c.get('ref_id')) for c in corr if c['action'] == 'reference'}
        start = args.start or max(c['id'] for c in corr) + 1
        new = [{'id': 0, 'action': 'reference', 'soldier_id': f['record'], 'ref_book': args.book, 'ref_id': f['ref'],
                'ref_name': f['ref_name'], 'reason': f"{f['record_name']} is the {f['ref_name']} of the book; same "
                                                     f"{', '.join(f['agree'])}"
                                                     + (f"; {why[f['record'], f['ref']]}" if (f['record'], f['ref']) in why
                                                        else '; checked by hand' if f['grade'] in ('likely', 'reviewed')
                                                        else '')}
               for f in chosen if (f['record'], f['ref']) not in have]
        for i, c in enumerate(new):
            c['id'] = start + i
        taken = {c['id'] for c in corr}
        if any(c['id'] in taken for c in new):
            sys.exit(f'--start {start}: ids from there are taken')
        tmp = CORRECTIONS.with_suffix('.json.tmp')
        tmp.write_text(json.dumps(corr + new, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(tmp, CORRECTIONS)
        print(f'Appended {len(new)} reference corrections from id {start}')


if __name__ == '__main__':
    main()
