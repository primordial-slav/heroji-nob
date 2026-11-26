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
A place of death told otherwise is no other death where both give the same day, or where the two places lie near
each other (GeoNames, through the local places tool: "Šćepan Polje" and "Zlatni Bor, Foča", "Čusto Brdo" and "Novi
Šeher"; 2026-11-01, after the user found the review queue's top pairs of that kind all one man). One man linked across
units is one pairing, not rivals: an entry that fits his records in two units goes to each.
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
from itertools import combinations
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import find_source_duplicates as F  # noqa: E402
import match_references as M  # noqa: E402
from extract_life_events import iso, parse_when  # noqa: E402
from name_utils import OSTALI_CODES  # noqa: E402

FACTS = {'birth year', 'birthplace', 'death year', 'death place'}
HAND ={'vis-spomenica-1941', 'vis-zrtve-nob', 'moste-polje-spomenica-1941', 'xxxi-divizija-stabi', '15-brigada-stabi',
        '15-divizija-stabi', 'jb-odred-stabi', 'banijski-odredi-kadar', 'letalci-prekomorci-kader', 'susak-rijeka-spomenica', 'korosko-zdravstvo',
        'dolomiti-v-nob-3', 'artileristi-prekomorci', 'virovitica-spomenica-1941', 'sanitetska-sluzba-lekari',
        'krizani-v-boju-za-svobodo', 'vinodolska-selca', 'zene-vi-korpus-poginule', 'pali-za-lepsa-svitanja',
        'moslavina-spomenica-1941', 'kremna', 'komani', 'binovce', 'gornja-jablanica', '2-korpus-stabovi',
        'klanjscek-komandni-sastav'}
STOP = {'kod', 'blizu', 'selu', 'selo', 'grad', 'gradu', 'kraj', 'pod', 'iznad', 'okolini', 'okolina', 'reke', 'reka',
        'planini', 'planina'}
# the words a place's name shares with other places' ("Gornji Lapac" is not Gornji Vakuf, "Bosanski Novi" not
# Bosanski Petrovac)
SHARED = re.compile(r'(?:gornj|donj|velik|mal|nov|star|sredn|bosansk|slavonsk|lick|sremsk|hrvatsk|srpsk|svet|crn|'
                    r'bel|bijel|zelen|sirok|dug)\w{0,3}|polj[aeiu]|brd[aeou]|varos\w?|most[au]?|brod[au]?|luk[aeiu]|'
                    r'gor[aeiu]|vod[aeiu]|dolin[aeiu]|glav[aeiu]|potok[au]?|kamen[au]?|vrh[au]?|jezer[aoui]?')
# a republic or a region named for the place ("u Bosni", "Dalmacija", "Sremski front"): the GeoNames countries it
# is, or the box (south, north, west, east) it lies in, roughly
REGIONS = [(r'bosn\w{0,3}', {'BA'}), (r'crn\w{1,2} gor\w{1,2}', {'ME'}), (r'slovenij\w{0,2}', {'SI'}),
           (r'hrvatsk\w{0,3}', {'HR'}), (r'srbij\w{0,2}', {'RS'}), (r'makedonij\w{0,2}', {'MK'}),
           (r'kosov\w{0,2}|metohij\w{0,2}', {'XK'}),
           (r'(?:srem|srijem|sremsk)\w{0,4}(?: front\w{0,2})?', (44.65, 45.30, 18.7, 20.45)),
           (r'dalmacij\w{0,2}', (42.4, 44.5, 15.0, 18.6)), (r'lik[aeiu]|lici', (44.2, 45.1, 14.9, 16.0)),
           (r'kordun\w{0,2}', (44.9, 45.5, 15.3, 16.0)), (r'banij\w{0,2}', (45.0, 45.5, 15.8, 16.6)),
           (r'slavonij\w{0,2}', (45.0, 45.95, 16.8, 19.45)), (r'hercegovin\w{0,2}', (42.55, 43.85, 17.2, 18.9)),
           (r'krajin\w{0,2}', (44.3, 45.3, 15.7, 17.6)), (r'sandzak\w{0,2}', (42.8, 43.6, 19.2, 20.6)),
           (r'banat\w{0,2}', (44.7, 46.2, 20.2, 21.6)), (r'backa|backoj|backu|backe', (45.2, 46.2, 18.8, 20.4)),
           (r'vojvodin\w{0,2}', (44.6, 46.2, 18.8, 21.6)), (r'istr\w{0,2}', (44.75, 45.6, 13.45, 14.35)),
           (r'sumadij\w{0,2}', (43.8, 44.6, 20.2, 21.2)), (r'macv\w{0,2}', (44.5, 45.0, 19.2, 19.9)),
           (r'romanij\w{0,2}', (43.7, 44.1, 18.5, 19.0)), (r'bok[aeiu]', (42.35, 42.55, 18.45, 18.8))]
REGIONS = [(re.compile(rf'\b(?:{rx})\b'), where) for rx, where in REGIONS]
QUARTER = re.compile(r'(?:central|istocn|zapad|sjever|sever|juzn|srednj|dalmatinsk|bosansk|hrvatsk|kotorsk|posavin)\w*')
SPELLED = 0.7           # two names this alike are one place told in another case or spelling ("Ozlju", "Ozalj")
NEAR_KM = 60            # two places of death this near are one death told two ways
NEAR_SEVERAL_KM = 30    # ... where a name is several places, the nearest of them this near
VILLAGE_SPELLED = 0.8   # a birthplace's village told otherwise, a stricter measure ("Zapužani", "Zapužane")
TWO_VILLAGES_KM = 40    # one name this far apart, each with its municipality, is two villages
FRONT_BOOKS = {'sremski-front-poginuli', 'u-rovovima-srema-poginuli'}
# a roster of a unit formed that month: a man who fell before it is another man of the name
ROSTER_FROM = {'1-bokeljska-spisak.pdf': '1944-10'}
try:                # the local places tool and its GeoNames cache (not in git): without them, the names alone
    sys.path.insert(0, str(ROOT / 'quality' / 'places'))
    import gazetteer as G  # noqa: E402
except ImportError:
    G = None
_GEO = {}
BEARERS = Counter()


def match(book: str, index: dict) -> list[dict]:
    """match_references.main's matching and its two clean-ups, for one book."""
    refs = json.loads(M.entries_path(book).read_text(encoding='utf-8'))
    if book in M.HERO_BOOKS:
        for r in refs:
            r['hero'] = True
    found = []
    for ref in refs:
        lasts = {M.fold(ref['last_name'])} | {M.fold(x) for x in ref.get('also', ())}
        for s, variant in M.candidates(index, ref, lasts):       # with another form of the given name (rule 3)
            agree, clash = M.evidence(ref, s)
            if variant:
                clash.append('given?')
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


def linked_men(corr: list[dict]) -> dict[str, str]:
    """record -> the first record of the man it is linked to across units (itself where it has no link)"""
    up = {}

    def find(x):
        while up.get(x, x) != x:
            x = up[x]
        return x
    for c in corr:
        if c['action'] == 'link':
            a, b = find(c['soldier_id']), find(c['link_id'])
            if a != b:
                up[max(a, b)] = min(a, b)
    return {x: find(x) for x in list(up)}


def two_facts_unique(found: list[dict], need: str | None = None, man=None) -> list[tuple]:
    man = man or {}
    by_ref, by_rec = defaultdict(set), defaultdict(set)
    for m in found:
        by_ref[m['ref']].add(man.get(m['record'], m['record']))
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


def choose(book: str, found: list[dict], out: Path, man=None) -> list[tuple]:
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
        return two_facts_unique(found, need='death place', man=man)
    return two_facts_unique(found, man=man)


def folded(place: str) -> str:
    """M.fold, with a hyphen or a stop between words kept as a space ("Kotor-Varoši", "Bučuca-banija")."""
    return M.fold(re.sub(r'[-–—/.,;:()]+', ' ', place or ''))


def names(place: str) -> list[str]:
    """A place's words that name it (not "kod", not "Gornji"), of four letters or more."""
    return [w for w in re.findall(r'[a-z]{4,}', folded(place)) if w not in STOP and not SHARED.fullmatch(w)]


def words(place: str) -> set[str]:
    return {w[:5] for w in names(place)}


def spelled_alike(a: str, b: str, at: float = SPELLED) -> bool:
    """One place in another case or spelling: "Ozlju" and "Ozalj", "Ličkoj Jasenici" and "Lička Jesenica", "Crnom
    Vrhu" and "Crni vrh", "Drutlićima" and "Druglići", the scan's "u JTivnu" for Livno."""
    from difflib import SequenceMatcher

    def forms(p):
        first = re.sub(r'^(?:u|na|kod|pri|v|blizu|iznad|s|sela|selu|selo)\s+', '', folded(p.split(',')[0]).strip())
        return [w for w in names(p) if len(w) >= 5] + ([first] if len(first) >= 6 else [])
    return any(SequenceMatcher(None, x, y).ratio() >= at for x in forms(a) for y in forms(b))


def points(place: str) -> list[tuple]:
    """The GeoNames places a printed place of death can be, (lat, lon, country): the places tool's reading, else its
    nominatives (the books' "Novom Šeheru", "Spreči"), else its municipality's ("na Savinu Laktu, Prijepolje"). A
    region names no point ("Bosni", "Sremu")."""
    if G is None or not place:
        return []
    if place not in _GEO:
        if 'index' not in _GEO:
            _GEO['index'] = G.load_geonames()[0]
        found = ()
        muni = place.split(',', 1)[1].strip() if ',' in place else ''
        for text in (place, 'u ' + place) + ((muni,) if muni else ()):
            r = G.resolve(_GEO['index'], text, True)
            if 'lat' in r and r.get('kind') not in ('L', 'A'):
                found = ((r['lat'], r['lon'], r['cc']),)
            elif r.get('_hits'):
                found = tuple((e['lat'], e['lon'], e['cc']) for e in r['_hits'] if e['cls'] not in ('L', 'A'))
            if found:
                break
        _GEO[place] = found
    return list(_GEO[place])


def in_region(place: str, other: list[tuple]) -> bool:
    """A republic or a region printed for one place, and a place of the other's in it ("u Bosni" and "Paklen, Konjic",
    "Dalmacija" and Knin, "Sremski front" and Tovarnik)."""
    f = re.sub(r'\b(?:u|na|v|iz|po|kod)\b', ' ', folded(place))
    for rx, where in REGIONS:
        rest = rx.sub(' ', f)
        if rest == f or any(not QUARTER.fullmatch(w) and w not in STOP for w in re.findall(r'[a-z]{3,}', rest)):
            continue
        if isinstance(where, set):
            return any(x[2] in where for x in other)
        s, n, w, e = where
        return any(s <= x[0] <= n and w <= x[1] <= e for x in other)
    return False


def near(a: str, b: str) -> bool | None:
    """Whether two places of death lie near each other (or one is a region the other lies in); None where GeoNames
    can't tell: one of them is nowhere, or a name of several places none of which is near."""
    pa, pb = points(a), points(b)
    if in_region(a, pb) or in_region(b, pa):
        return True
    if not pa or not pb:
        return None
    d = min(G.km({'lat': x[0], 'lon': x[1]}, {'lat': y[0], 'lon': y[1]}) for x in pa for y in pb)
    if len(pa) == len(pb) == 1:
        return d <= NEAR_KM
    return True if d <= NEAR_SEVERAL_KM else None


def when(date: str | None) -> str | None:
    """A death date as YYYY, YYYY-MM or YYYY-MM-DD: the entries store it so, the records as printed ("01.03.1945")."""
    if not date:
        return None
    if re.fullmatch(r'\d{4}(?:-\d\d){0,2}', date.strip()):
        return date.strip()
    found = parse_when(date)
    return iso(found[0]) if found else None


def against(entry: dict, rec: dict) -> list[str]:
    """What in the record says another death than the entry's: the place (none of its names in the record's place
    or bio, nor near it, nor, where GeoNames can't tell, spelled alike; unless both give the same day) or the month."""
    out = []
    ed, rd = when(entry.get('death_date')), when(rec.get('death_date'))
    ep, rp = entry.get('death_place') or '', rec.get('death_place') or ''
    if ep and rp and not (words(ep) & words(rp)) and not (words(ep) & words(rec.get('additional_info'))) \
            and not (ed and len(ed) == 10 and ed == rd):
        close = near(ep, rp)
        if not (close or (close is None and spelled_alike(ep, rp))):
            out.append(f'place {ep!r} / {rp!r}')
    if ed and rd and len(ed) >= 7 and len(rd) >= 7 and ed[:7] != rd[:7]:
        out.append(f'date {ed} / {rd}')
    return out


def same_village(a: str, b: str) -> bool | None:
    """Whether two birthplaces name one village: the printed village's own name (not the municipality after it: "Drinić,
    Bosanski Petrovac" is not "Bravski Vaganac, Bos. Petrovac"), in any spelling or case. Velika is not Mala, and two
    villages of one name far apart are two ("Kamenica, Drvar", "Kamenica, Cazin"). None where one gives none, or gives
    the town alone and the other a village of its municipality ("Omiš", "Borak, Omiš")."""
    a, b = a or '', b or ''
    va, vb = a.split(',')[0], b.split(',')[0]
    if not folded(va).strip() or not folded(vb).strip():
        return None
    if not (words(va) & words(vb) or folded(va).strip() == folded(vb).strip() or spelled_alike(va, vb, VILLAGE_SPELLED)):
        if (',' in a) != (',' in b):
            town, other = (b, a) if ',' in a else (a, b)
            if words(town) & words(other.split(',', 1)[1]):
                return None
        return False
    qa, qb = F.village(a)[0], F.village(b)[0]
    if qa and qb and qa != qb:
        return False
    if ',' in a and ',' in b:
        pa, pb = points(a), points(b)
        d = min((G.km({'lat': x[0], 'lon': x[1]}, {'lat': y[0], 'lon': y[1]}) for x in pa for y in pb), default=None)
        return not (d is not None and d > TWO_VILLAGES_KM)
    return True


def nickname(x: dict) -> str:
    m = re.match(r'\s*zvan[ia] ([^;]{3,30});', x.get('additional_info') or '')
    return M.fold(x.get('nick') or (m.group(1) if m else ''))


def fathers(a: dict, b: dict) -> str | None:
    """'full' (the same name, in any case or a letter misread), 'initial', 'clash', or None where one gives no father."""
    fa = {M.fold(a.get('fathers_name')), M.fold(a.get('middle_name'))} - {''}
    fb = {M.fold(b.get('fathers_name')), M.fold(b.get('middle_name'))} - {''}
    if not fa or not fb:
        return None
    if any(len(x) <= 2 for x in fa | fb):
        return 'initial' if any(M.initial_of(x, y) for x in fa for y in fb) else 'clash'
    if fa & fb or any(M.same_father(x, y) or (min(len(x), len(y)) >= 4 and F.one_letter_apart(x, y))    # not Svetozar, Svetolik
                      for x in fa for y in fb):
        return 'full'
    return 'clash'


def fell_when(x: dict) -> tuple[str, str]:
    """The death's date as far as it is known, and its year (an entry's field, or its words)."""
    d = when(x.get('death_date')) or ''
    if d:
        return d, d[:4]
    y = str(x.get('death_year') or '')[:4]
    if not y:
        death = M.DEATH.search(x.get('additional_info') or '')
        y = death.group(1) if death else ''
    return '', y


def fate_of(x: dict) -> str:
    if x.get('survived') or re.search(r'\bDanas\b', x.get('additional_info') or ''):
        return 'lived'
    # F.fate reads the verbs in small letters; the lists print "Poginuo" as well
    return F.fate(x) or ('fell' if fell_when(x)[1] or re.search(r'\b(?:po\w?gin|umr|strelj|strijelj|nesta)', x.get('additional_info') or '', re.I) else '')


def count_bearers(index: dict) -> None:
    """How many men on the site and in the books bear each name (a name's records, and every book's entries)."""
    if BEARERS:
        return
    BEARERS.update({name: len(rs) for name, rs in index.items()})
    for d in M.ENTRY_DIRS:
        for p in d.glob('*-entries.json'):
            for e in json.loads(p.read_text(encoding='utf-8')):
                BEARERS[(M.fold(e.get('last_name')), M.fold(e.get('first_name')))] += 1


def bearers(x: dict) -> int:
    return BEARERS[(M.fold(x.get('last_name')), M.fold(x.get('first_name')))]


def facts(a: dict, b: dict) -> dict:
    """What two entries of one name give alike and otherwise, for same_man()."""
    ya, yb = (re.search(r'1[89]\d\d', x.get('birth_year') or '') for x in (a, b))
    da, ydeath_a = fell_when(a)
    db, ydeath_b = fell_when(b)
    pa, pb = a.get('death_place') or '', b.get('death_place') or ''
    na, nb = nickname(a), nickname(b)
    fa, fb = fate_of(a), fate_of(b)
    months = abs((int(da[:4]) - int(db[:4])) * 12 + int(da[5:7]) - int(db[5:7])) if len(da) >= 7 and len(db) >= 7 else None
    return {'father': fathers(a, b),
            'born': abs(int(ya.group(0)) - int(yb.group(0))) if ya and yb else None,
            'village': same_village(a.get('birth_place') or a.get('born_in') or '', b.get('birth_place') or b.get('born_in') or ''),
            'dead': abs(int(ydeath_a) - int(ydeath_b)) if ydeath_a and ydeath_b else None,
            'months': months,
            # the day and month a year off is the same day misprinted ("12. 4. 1945", "12. 4. 1944")
            'day': len(da) == 10 and len(db) == 10 and da[5:] == db[5:] and abs(int(da[:4]) - int(db[:4])) <= 1,
            'place': (bool(words(pa) & words(pb)) or bool(near(pa, pb)) or spelled_alike(pa, pb)) if pa and pb else None,
            'nick': bool(na and nb and na[:5] == nb[:5]),
            # the unit an entry of a book names is the other's (the entry's "units", the record's id)
            'unit': any(int(y.get('soldier_id', '0')[:4]) in (x.get('units') or ()) for x, y in ((a, b), (b, a))),
            'lived': bool(fa and fb and fa != fb)}


def same_man(a: dict, b: dict) -> str | None:
    """Two entries of one name that no one needs to read: what makes them one man, or None. Measured on every answer
    given (identity_decisions.json, 2026-11-01, after the user found the queue "way too obvious"; the counts are answers
    same/different/unsure). Another father, another fate or a death two years off part them, and a birth year off by
    more than three unless the father, the village and the death agree; the rest stay for a person. Another Slovene
    form of the given name (Jože, Jožef) is not one name here: such a pair needs the strict grade."""
    if M.slovene_form_only(a, b):
        return None
    for x, y in ((a, b), (b, a)):
        since = ROSTER_FROM.get(x.get('pdf_file'))
        if since:
            d, yr = fell_when(y)
            if yr and (yr < since[:4] or (len(d) >= 7 and d[:7] < since)):
                return None
    f = facts(a, b)
    if f['father'] == 'clash' or f['lived'] or (f['dead'] or 0) > 1:
        return None
    full, father, born, village, dead, place = f['father'] == 'full', f['father'], f['born'], f['village'], f['dead'], f['place']
    close = born is not None and born <= 1
    # two villages and two places, on a day many fell: two men of a common name and father (Jovanović Stanka Dragoljub,
    # Surdulica and the Srem front, Boljevac and Doboj, both 12 April 1945: the rule below had linked them, 2026-11-04)
    if f['day'] and village is False and place is False and not f['nick']:
        return None
    # on a day many fell (12 April 1945 on the Srem front) a name and the day aren't enough: two villages need the father
    # or the birth year, and without a village the place of death tells nothing unless the name is rare
    if f['day'] and (full or close or (village is not False and (father or born == 2 or village or bearers(a) <= 5))):
        return 'the same day of death'
    if (f['months'] or 0) > 1:
        return None
    if full and village and dead == 0 and place:                 # 67/0/1: a birth year the scan misread
        return 'the father, the village and the death'
    if (born or 0) > 3:
        return None
    if f['nick'] and (full or close or village):
        return 'what he was called'
    if (born or 0) > 2:
        return None
    if village and close and dead == 0:
        return 'the village, the birth year and the year of death'
    if full and village and (born or 0) <= 1 and place is not False and (dead != 1 or born is not None):
        return 'the father and the village'
    if close and dead == 0 and place and (village is not False or full):   # 40/0/3; two villages need the father
        return 'the birth year and the death'
    if full and close and not dead and place is not False and village is None:
        return 'the father and the birth year'
    if village and dead == 0 and place:
        return 'the village and the death'
    if f['unit'] and (father or close or village) and not dead:  # the book names his brigade
        return 'the unit he fought in'
    n = bearers(a)
    if village and dead == 0 and n <= 9:                         # 101/0/14: the place of death told otherwise or not at all
        return 'a rare name, the village and the year of death'
    if not dead and place is not False:
        if village and n <= 3:                                   # 49/1/5
            return 'a rare name and the village'
        if full and village is None and n <= 2:                  # 50/0/4
            return 'a rare name and the father'
        if dead == 0 and place and n <= 5 and village is not False:   # 22/0/2
            return 'a rare name and the death'
    return None


def thin(f: dict, carrying: int) -> bool:
    """A pair with so little to go on that no one can tell (the answers on such pairs, 2026-11-01): the father's initial
    alone, of 3 men or more of the name (14 same, 80 different, 46 unsure), or the father alone or nothing at all, of 16
    or more (32 same, 42 different, 15 unsure). Never offered."""
    if (f['born'] is not None and f['born'] <= 1) or f['village'] or f['dead'] == 0 or f['place'] or f['nick']:
        return False
    return carrying >= (3 if f['father'] == 'initial' else 16)


def front_pairs(entries, index: dict) -> list[tuple]:
    """The Srem front's lists name each man's brigade: the name and the brigade are enough where the brigade's records
    hold one man of the name and its list one entry of it (the user's decision of 2026-11-01), unless his record says
    otherwise: another father, a man who lived, a death in another year."""
    def name_of(x):
        return M.fold(x.get('last_name')), M.fold(x.get('first_name'))
    in_list = Counter((name_of(e), unit) for e in entries for unit in e.get('units') or ())
    out = []
    for e in entries:
        name = name_of(e)
        if not all(name):
            continue
        for unit in e.get('units') or ():
            ones = [s for s in index.get(name, ()) if int(s['soldier_id'][:4]) == unit]
            if in_list[(name, unit)] != 1 or len(ones) != 1:
                continue
            f = facts(e, ones[0])
            year = fell_when(ones[0])[1]
            if f['father'] != 'clash' and not f['lived'] and not (year and e.get('death_years') and year not in e['death_years']):
                out.append((ones[0]['soldier_id'], e['soldier_id'], 'the name and the brigade, the only one of the name in each'))
    return out


def rivals(rec: str, ref: str, found: list[dict], held: set, recs: dict) -> str:
    """For the review page: the other records the entry fits, and those that hold it already ("also fits Alempijević
    Selimira Dragan, Užički NOP odred, sure"): the same man in a unit whose record isn't linked to this one, as often
    as not."""
    from name_utils import BRIGADE_CONFIGS
    seen, out = {rec}, []
    for i, how in [(i, 'holds the entry') for i in sorted(held)] + \
                  [(f['record'], f['grade']) for f in found if f['ref'] == ref]:
        if i in seen or i not in recs:
            continue
        seen.add(i)
        unit = BRIGADE_CONFIGS.get(int(i[:4]), {}).get('name', i[:4])
        out.append(f"{recs[i].get('full_name')}, {unit}, {how}")
    return f"; also fits {'; '.join(out[:3])}" + (f' and {len(out) - 3} more' if len(out) > 3 else '') if out else ''


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
    have, ref_units, rec_books, holders = defaultdict(set), defaultdict(set), defaultdict(set), defaultdict(set)
    for c in corr:
        if c['action'] == 'reference':
            have[c['ref_book']].add((c['soldier_id'], c['ref_id']))
            ref_units[(c['ref_book'], c['ref_id'])].add(c['soldier_id'][:4])
            rec_books[(c['ref_book'], c['soldier_id'])].add(c['ref_id'])
            holders[(c['ref_book'], c['ref_id'])].add(c['soldier_id'])
    man = linked_men(corr)
    new, left, review = [], [], []
    count_bearers(index)
    for book in books:
        found = [f for f in match(book, index) if (book, f['record'], f['ref']) not in blocked]
        by_pair = {(f['record'], f['ref']): f for f in found}
        entries = {e['soldier_id']: e for e in json.loads(M.entries_path(book).read_text(encoding='utf-8'))}
        took, why_not, seen, mine, chosen = 0, Counter(), set(), [], set()
        # the pairs no one needs to read (same_man), where the entry fits one man and the record one entry so
        strong = {(f['record'], f['ref']): same_man(entries[f['ref']], recs[f['record']]) for f in found}
        strong = {k: why for k, why in strong.items() if why}
        men, held_by = defaultdict(set), defaultdict(set)
        for rec, ref in strong:
            men[ref].add(man.get(rec, rec))
            held_by[rec].add(ref)
        one_man = {ref for ref, ms in men.items() if len(ms) > 1 and all(
            same_man(recs[x], recs[y]) for x, y in combinations([r for r, e in strong if e == ref], 2) if x[:4] != y[:4])}
        strong = {(rec, ref): why for (rec, ref), why in strong.items()
                  if (len(men[ref]) == 1 or ref in one_man) and len(held_by[rec]) == 1}
        picks = choose(book, found, out, man)
        have_pick = {(rec, ref) for rec, ref, _ in picks}
        picks += [(rec, ref, why) for (rec, ref), why in strong.items() if (rec, ref) not in have_pick]
        if book in FRONT_BOOKS:
            picks += [p for p in front_pairs(entries.values(), index) if p[:2] not in have_pick and p[:2] not in strong]
        for rec, ref, why in picks:
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
            if flags and (rec, ref) in strong:
                flags, why = [], (f'{why}; ' if why and why != strong[(rec, ref)] else '') + strong[(rec, ref)] + ', the place of death told otherwise'
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
                # on the Srem lists the entry gives a name and an initial: no one can tell which of two men he is
                if (p['ref'], p['record'][:4]) in twice and book not in FRONT_BOOKS:
                    review.append({'grade': '', 'agree': p['agree'], **by_pair.get((p['record'], p['ref']), {}),
                                   'record': p['record'], 'ref': p['ref'], 'book': book, 'clash': [],
                                   'note': 'two records of one unit fit the entry'})
            mine = [p for p in mine if (p['ref'], p['record'][:4]) not in twice]
            why_not['two records of one unit'] += sum(per_unit[k] for k in twice)
            took -= sum(per_unit[k] for k in twice)
        new += mine
        # a likely pair the book's rule leaves
        by_ref, by_rec = defaultdict(set), Counter(f['record'] for f in found)
        for f in found:
            by_ref[f['ref']].add(f['record'])          # records, not men: one fact for a man in two units is still one
        for f in found:
            rec, ref = f['record'], f['ref']
            if f['grade'] != 'likely' or (rec, ref) in chosen or (rec, ref) in have[book] \
                    or rec[:4] in ref_units[(book, ref)] or rec_books[(book, rec)] \
                    or thin(facts(entries[ref], recs[rec]), bearers(recs[rec])):
                continue
            strong = set(f['agree']) & {'father', 'birthplace', 'death place', 'death day'}
            alone = len(by_ref[ref]) == 1 and by_rec[rec] == 1
            if len(set(f['agree']) - {'hero on the site'}) >= 2 or (strong and alone):
                review.append({**f, 'book': book, 'clash': [], 'note': 'likely' + ('' if alone else ', other pairings too')
                               + rivals(rec, ref, found, holders[(book, ref)], recs)})
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
