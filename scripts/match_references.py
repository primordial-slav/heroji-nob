"""
Find the records a reference book's entries belong to: the soldiers of the site's units that a book across units
(a hero's portrait in the Zbornik narodnih heroja, ...) describes. The book's entries are read by its parser into
data-extraction/poreklo/<book>-entries.json; each match becomes a `reference` correction, which apply_corrections.py
turns into an entry in the record's other_sources (the book's text, its page in the library), as a merge would.

A match needs the same surname and given name (letters folded) and more that agrees, with nothing that disagrees:
    sure     the father's name and one of: birth year (within a year), birthplace, year of death; or birth year and
             birthplace; or the record already calls him a narodni heroj and one of father, birth year, birthplace
    likely   one of father, birth year, birthplace, year of death
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

ROOT = Path(__file__).resolve().parent.parent
CORRECTIONS = ROOT / 'corrections.json'
FOLD = str.maketrans('ČĆŽŠĐčćžšđ', 'CCZSDcczsd')
HERO = re.compile(r'narodn\w*\s*heroj(?!i)', re.I)
DEATH = re.compile(r'\b(?:Poginu[oa]|Pogin|Streljan[a]?|Strelian|Obešen[a]?|Umr[oe]|Umrla|Ubijen[a]?|Ubio se|Ubila se|'
                   r'Umoren[a]?|Zaklan[a]?|Nestao|Nestala|Spaljen|Podlegao|Podlegla)\b[^.]*?\b(19[34]\d)\b')


def fold(text: str) -> str:
    return re.sub(r'[^a-z ]', '', (text or '').translate(FOLD).lower().replace('dj', 'd')).strip()


def stem(word: str) -> str:
    w = fold(word).replace(' ', '')
    return w[:5] if len(w) >= 5 else w


def evidence(ref: dict, s: dict) -> tuple[list[str], list[str]]:
    agree, clash = [], []
    rf, sf = fold(ref['fathers_name']), fold(s.get('middle_name') or '')
    if rf and sf:
        # a book that gives the father as a possessive (Trebinjci pali: "Muharemov", "Jovičin") against the site's
        # genitive ("Muharema", "Jovice"): the same name once both endings are off
        pos = re.match(r'^(.{3,}?)(?:ov|ev|in|ova|eva|ina)$', rf)
        if rf == sf or (len(rf) == 1 and sf.startswith(rf)) or (len(sf) == 1 and rf.startswith(sf)) or (
                pos and len(sf) >= 3 and pos.group(1) == re.sub(r'[aeiou]$', '', sf)):
            agree.append('father')
        elif not (min(len(rf), len(sf)) >= 4 and rf[:3] == sf[:3]):      # "Jurja" and "Juraj" are one father
            clash.append('father')
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
        elif s.get('birth_place') and not HERO.search(texts):
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
    elif alive and record_death:
        clash.append('alive after the war')                # the book has him alive, the record killed in the war
    if HERO.search(texts):
        agree.append('hero on the site')
    return agree, clash


def grade(agree: list[str], clash: list[str]) -> str | None:
    if clash:
        return None
    a = set(agree)
    core = a & {'birth year', 'birthplace', 'death year'}
    if 'father' in a and core:
        return 'sure'
    if {'birth year', 'birthplace'} <= a:
        return 'sure'
    if 'hero on the site' in a and (a & {'father', 'birth year', 'birthplace'}):
        return 'sure'
    if a - {'hero on the site'}:
        return 'likely'
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('book', help='the entries file: data-extraction/poreklo/<book>-entries.json')
    ap.add_argument('--json', help='write every match here, for review')
    ap.add_argument('--write', help='grades to append as reference corrections, e.g. "sure"')
    ap.add_argument('--only', help='file of "record_id ref_id" lines: append exactly these (reviewed) matches')
    args = ap.parse_args()

    refs = json.loads((ROOT / 'data-extraction' / 'poreklo' / f'{args.book}-entries.json').read_text(encoding='utf-8'))
    index = defaultdict(list)
    for code, (_, soldiers) in structured.load_live().items():
        for s in soldiers:
            index[(fold(s.get('last_name')), fold(s.get('first_name')))].append(s)
    found, grades, every = [], Counter(), {}
    for ref in refs:
        names = {fold(ref['first_name'])} | ({fold(ref['nick'])} if ref.get('nick') else set())
        cands = [s for n in names for s in index.get((fold(ref['last_name']), n), [])]
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
    heroes = {f['ref'] for f in found if f['grade'] == 'sure'}
    print(f'{len(refs)} entries; matches {dict(grades)}; heroes with a sure match: {len(heroes)}')
    for f in found[:0]:
        print(f)
    if args.json:
        Path(args.json).write_text(json.dumps(found, ensure_ascii=False, indent=1), encoding='utf-8')
    chosen = [f for f in found if args.write and f['grade'] in set(args.write.split(','))]
    if args.only:
        pairs = {tuple(ln.split()[:2]) for ln in Path(args.only).read_text(encoding='utf-8').splitlines() if ln.strip()}
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
        start = max(c['id'] for c in corr) + 1
        new = [{'id': 0, 'action': 'reference', 'soldier_id': f['record'], 'ref_book': args.book, 'ref_id': f['ref'],
                'ref_name': f['ref_name'], 'reason': f"{f['record_name']} is the {f['ref_name']} of the book; same "
                                                     f"{', '.join(f['agree'])}"
                                                     + ('; checked by hand' if f['grade'] in ('likely', 'reviewed') else '')}
               for f in chosen if (f['record'], f['ref']) not in have]
        for i, c in enumerate(new):
            c['id'] = start + i
        tmp = CORRECTIONS.with_suffix('.json.tmp')
        tmp.write_text(json.dumps(corr + new, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(tmp, CORRECTIONS)
        print(f'Appended {len(new)} reference corrections from id {start}')


if __name__ == '__main__':
    main()
