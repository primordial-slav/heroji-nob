"""
Match every book across units again against the units on the site today, and write the references its first
matching could not make: a unit or second book added since, a name mended since, a rule of the matcher grown since.

Each book's pairs are chosen by the rule it was first matched with:
    the census (zrtve-rata-1964-*), and the regional lists: sure pairs, and likely ones where two of birth year,
        birthplace, year and place of death agree and the pairing is the only one both ways
        (select_census_references.py's rule);
    the Karlovac volumes and Sjeničak: scripts/select_place_references.py;
    Tmušić's Sremski front: scripts/select_front_references.py;
    Gončin's U rovovima Srema: sure pairs, and likely ones whose place of death agrees, unique both ways;
    the hero books and the lists whose pairs were chosen by hand (staff lists, spomenica lists by name, ...): sure only.
Never an entry that a record of the same unit already holds, nor a record that already holds an entry of the book;
and never a pair whose record dies elsewhere (the entry's place of death and the record's share no name) or in
another month than the entry says: the matcher doesn't weigh these, and the first matchings dropped such pairs by hand.
scripts/find_identities.py runs the same (rematch()) with the other kinds of pair, and puts the pairs left out here
on its review queue.

Usage:
    python scripts/rematch_references.py out_dir                 # dry run: per book, the new pairs and the ones left out
    python scripts/rematch_references.py out_dir --write START   # append them as reference corrections from id START
Then rebuild Ostali borci (build_ostali_borci.py --write, normalize 122 and 131-138, fields and life events of 122)
and run apply_corrections.py --apply. The units are loaded once (match_references.py loads them for each book).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import match_references as M  # noqa: E402
from extract_life_events import iso, parse_when  # noqa: E402
from name_utils import OSTALI_CODES  # noqa: E402

FACTS = {'birth year', 'birthplace', 'death year', 'death place'}
HAND = {'vis-spomenica-1941', 'vis-zrtve-nob', 'moste-polje-spomenica-1941', 'xxxi-divizija-stabi', '15-brigada-stabi',
        '15-divizija-stabi', 'jb-odred-stabi', 'banijski-odredi-kadar', 'letalci-prekomorci-kader', 'susak-rijeka-spomenica', 'korosko-zdravstvo',
        'dolomiti-v-nob-3', 'artileristi-prekomorci', 'virovitica-spomenica-1941', 'sanitetska-sluzba-lekari',
        'krizani-v-boju-za-svobodo', 'vinodolska-selca', 'zene-vi-korpus-poginule', 'pali-za-lepsa-svitanja',
        'moslavina-spomenica-1941', 'kremna', 'komani', 'binovce', 'gornja-jablanica', '2-korpus-stabovi',
        'klanjscek-komandni-sastav'}
STOP = {'kod', 'blizu', 'selu', 'selo', 'grad', 'gradu', 'kraj', 'pod', 'iznad', 'okolini', 'okolina', 'reke', 'reka',
        'planini', 'planina'}


def match(book: str, index: dict) -> list[dict]:
    """match_references.main's matching and its two clean-ups, for one book."""
    refs = json.loads(M.entries_path(book).read_text(encoding='utf-8'))
    if book in M.HERO_BOOKS:
        for r in refs:
            r['hero'] = True
    found = []
    for ref in refs:
        names = {M.fold(ref['first_name'])} | ({M.fold(ref['nick'])} if ref.get('nick') else set())
        lasts = {M.fold(ref['last_name'])} | {M.fold(x) for x in ref.get('also', ())}
        for s in (s for l in lasts for n in names for s in index.get((l, n), [])):
            agree, clash = M.evidence(ref, s)
            g = M.grade(agree, clash)
            if g:                                          # as match_references --json writes it (the selectors read it)
                found.append({'grade': g, 'agree': agree, 'record': s['soldier_id'], 'record_name': s.get('full_name'),
                              'ref': ref['soldier_id'], 'ref_name': ref['name'], 'ref_info': ref['additional_info'][:160],
                              'record_info': (s.get('additional_info') or '')[:160]})
    refs = {r['soldier_id']: r for r in refs}
    by_record = defaultdict(list)
    for f in found:
        by_record[f['record']].append(f)

    def one_man(a, b):
        fa, fb = M.fold(a['fathers_name']), M.fold(b['fathers_name'])
        ya, yb = (re.search(r'1[89]\d\d', x.get('birth_year') or '') for x in (a, b))
        return not (fa and fb and fa != fb and not M.same_father(fa, fb)) and not (
            ya and yb and abs(int(ya.group(0)) - int(yb.group(0))) > 1)
    for fs in by_record.values():
        if len({f['ref'] for f in fs}) > 1 and not all(one_man(refs[a['ref']], refs[b['ref']]) for a in fs for b in fs):
            for f in fs:
                f['grade'] = None
    by_unit = defaultdict(list)
    for f in found:
        if f['grade']:
            by_unit[(f['ref'], f['record'][:4])].append(f)
    for fs in by_unit.values():
        if any('father' in f['agree'] for f in fs):
            for f in fs:
                if 'father' not in f['agree'] and 'hero on the site' not in f['agree']:
                    f['grade'] = None
    return [f for f in found if f['grade']]


def two_facts_unique(found: list[dict], need: str | None = None) -> list[tuple]:
    by_ref, by_rec = defaultdict(set), defaultdict(set)
    for m in found:
        by_ref[m['ref']].add(m['record'])
        by_rec[m['record']].add(m['ref'])
    sure_refs = {m['ref'] for m in found if m['grade'] == 'sure'}
    out = []
    for m in found:
        if m['grade'] == 'sure':
            out.append((m['record'], m['ref'], ''))
        elif m['ref'] not in sure_refs and len(by_ref[m['ref']]) == 1 and len(by_rec[m['record']]) == 1:
            facts = FACTS & set(m['agree'])
            if (need and need in m['agree']) or (not need and len(facts) >= 2):
                out.append((m['record'], m['ref'], 'likely, unique both ways'))
    return out


def script_pairs(cmd: list[str], path: Path) -> list[tuple]:
    subprocess.run(cmd, check=True, capture_output=True, cwd=ROOT)
    return [tuple((ln.split(maxsplit=2) + [''])[:3]) for ln in path.read_text(encoding='utf-8').splitlines() if ln.strip()]


def choose(book: str, found: list[dict], out: Path) -> list[tuple]:
    if book in HAND or book in M.HERO_BOOKS:
        return [(m['record'], m['ref'], '') for m in found if m['grade'] == 'sure']
    if book.startswith('hak-') or book == 'sjenicak':
        mj = out / f'{book}.json'
        mj.write_text(json.dumps(found, ensure_ascii=False), encoding='utf-8')
        return script_pairs([sys.executable, 'scripts/select_place_references.py', str(mj), book, str(out / f'{book}.pairs')],
                            out / f'{book}.pairs')
    if book == 'sremski-front-poginuli':
        return script_pairs([sys.executable, 'scripts/select_front_references.py', book, str(out / f'{book}.pairs')],
                            out / f'{book}.pairs')
    if book == 'u-rovovima-srema-poginuli':
        return two_facts_unique(found, need='death place')
    return two_facts_unique(found)


def words(place: str) -> set[str]:
    return {w[:5] for w in re.findall(r'[a-z]{4,}', M.fold(place or '')) if w not in STOP}


def against(entry: dict, rec: dict) -> list[str]:
    """What in the record says another death than the entry's: the place (none of its names in the record's place
    or bio) or the month."""
    out = []
    ep, rp = entry.get('death_place') or '', rec.get('death_place') or ''
    if ep and rp and not (words(ep) & words(rp)) and not (words(ep) & words(rec.get('additional_info'))):
        out.append(f'place {ep!r} / {rp!r}')
    try:
        ed = iso(parse_when(entry['death_date'])) if entry.get('death_date') else None
        rd = iso(parse_when(rec['death_date'])) if rec.get('death_date') else None
    except Exception:                                                       # noqa: BLE001
        ed = rd = None
    if ed and rd and len(ed) >= 7 and len(rd) >= 7 and ed[:7] != rd[:7]:
        out.append(f'date {ed} / {rd}')
    return out


def load_units() -> tuple[dict, dict]:
    """The units' records (not Ostali borci's) by folded name, and by id."""
    from record_sources import own_only
    index, recs = defaultdict(list), {}
    for code, (_, soldiers) in M.structured.load_live().items():
        if code in OSTALI_CODES:
            continue
        for s in soldiers:
            s = own_only(s)                       # not what the record borrowed (scripts/record_sources.py)
            index[(M.fold(s.get('last_name')), M.fold(s.get('first_name')))].append(s)
            recs[s['soldier_id']] = s
    return index, recs


def rematch(index: dict, recs: dict, corr: list[dict], out: Path, blocked=frozenset(), log=print):
    """Each book's new pairs by its rule (new), the chosen pairs left out for another death (left), and the pairs
    worth a look that the rule doesn't take (review: those, an entry two records of one unit fit, and a likely pair
    the rule leaves where two things agree, or the father or village alone and no other pairing). blocked:
    (book, record, entry) triples answered 'different' (identity_decisions.json), never taken nor offered."""
    books = sorted(p.name[:-len('-entries.json')] for d in M.ENTRY_DIRS for p in d.glob('*-entries.json'))
    have, ref_units, rec_books = defaultdict(set), defaultdict(set), defaultdict(set)
    for c in corr:
        if c['action'] == 'reference':
            have[c['ref_book']].add((c['soldier_id'], c['ref_id']))
            ref_units[(c['ref_book'], c['ref_id'])].add(c['soldier_id'][:4])
            rec_books[(c['ref_book'], c['soldier_id'])].add(c['ref_id'])
    new, left, review = [], [], []
    for book in books:
        found = [f for f in match(book, index) if (book, f['record'], f['ref']) not in blocked]
        by_pair = {(f['record'], f['ref']): f for f in found}
        entries = {e['soldier_id']: e for e in json.loads(M.entries_path(book).read_text(encoding='utf-8'))}
        took, why_not, seen, mine, chosen = 0, Counter(), set(), [], set()
        for rec, ref, why in choose(book, found, out):
            chosen.add((rec, ref))
            if (rec, ref) in have[book] or (book, rec, ref) in blocked:
                continue
            if rec[:4] in ref_units[(book, ref)]:
                why_not['entry on a record of that unit'] += 1
                continue
            if rec_books[(book, rec)] or rec in seen:
                why_not['record holds an entry of the book'] += 1
                continue
            flags = against(entries[ref], recs[rec])
            if flags:
                why_not['another death'] += 1
                left.append({'book': book, 'record': rec, 'ref': ref, 'against': flags})
                review.append({'grade': '', 'agree': [], **by_pair.get((rec, ref), {'record': rec, 'ref': ref}),
                               'book': book, 'clash': flags, 'note': 'dies elsewhere or in another month'})
                continue
            seen.add(rec)
            took += 1
            mine.append({'book': book, 'record': rec, 'ref': ref, 'why': why,
                         'agree': by_pair.get((rec, ref), {}).get('agree', []),
                         'ref_name': entries[ref]['name'], 'record_name': recs[rec].get('full_name')})
        # an entry two records of one unit fit (the unit's two lists, never merged: the same man, or a cousin of the
        # name, father and village) goes to neither
        per_unit = Counter((p['ref'], p['record'][:4]) for p in mine)
        twice = {k for k, n in per_unit.items() if n > 1}
        if twice:
            for p in mine:
                if (p['ref'], p['record'][:4]) in twice:
                    review.append({'grade': '', 'agree': p['agree'], **by_pair.get((p['record'], p['ref']), {}),
                                   'record': p['record'], 'ref': p['ref'], 'book': book, 'clash': [],
                                   'note': 'two records of one unit fit the entry'})
            mine = [p for p in mine if (p['ref'], p['record'][:4]) not in twice]
            why_not['two records of one unit'] += sum(per_unit[k] for k in twice)
            took -= sum(per_unit[k] for k in twice)
        new += mine
        # a likely pair the book's rule leaves
        by_ref, by_rec = Counter(f['ref'] for f in found), Counter(f['record'] for f in found)
        for f in found:
            rec, ref = f['record'], f['ref']
            if f['grade'] != 'likely' or (rec, ref) in chosen or (rec, ref) in have[book] \
                    or rec[:4] in ref_units[(book, ref)] or rec_books[(book, rec)]:
                continue
            strong = set(f['agree']) & {'father', 'birthplace', 'death place', 'death day'}
            alone = by_ref[ref] == 1 and by_rec[rec] == 1
            if len(set(f['agree']) - {'hero on the site'}) >= 2 or (strong and alone):
                review.append({**f, 'book': book, 'clash': [], 'note': 'likely' + ('' if alone else ', other pairings too')})
        log(f'{book:40} new {took:4}  {dict(why_not)}')
    return new, left, review


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    start = int(sys.argv[sys.argv.index('--write') + 1]) if '--write' in sys.argv else None
    index, recs = load_units()
    corr = json.loads(M.CORRECTIONS.read_text(encoding='utf-8'))
    new, left, _ = rematch(index, recs, corr, out)
    (out / 'rematch_new.json').write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding='utf-8')
    (out / 'rematch_left_out.json').write_text(json.dumps(left, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(new)} new pairs, {len(left)} left out for another death (in {out})')
    if start is not None and new:
        taken = {c['id'] for c in corr}
        add = [{'id': start + i, 'action': 'reference', 'soldier_id': p['record'], 'ref_book': p['book'], 'ref_id': p['ref'],
                'ref_name': p['ref_name'],
                'reason': f"{p['record_name']} is the {p['ref_name']} of the book; same {', '.join(p['agree'])}"
                          + (f"; {p['why']}" if p['why'] else '') + '; matched again against the units of the day'}
               for i, p in enumerate(new)]
        if any(c['id'] in taken for c in add):
            sys.exit(f'--write {start}: ids from there are taken')
        M.CORRECTIONS.write_text(json.dumps(corr + add, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'Appended {len(add)} reference corrections from id {start}')


if __name__ == '__main__':
    main()
