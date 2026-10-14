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
NAME_FIXES = {'9061000128': ('Albahari', 'Nisim', 'Abrahama'),   # Romano's "Avrama": the hero books' Abraham
              '9035011823': ('Jelovac', 'Milan', 'Vučetin'), '9035011826': ('Jelovac', 'Strainj', 'Vučetin'),  # "Vučegin"
              '9001000203': ('Demonja', 'Nikola', ''), '9001000908': ('Rakovac', 'Joakim', ''),
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
# Spomenica counts as a partisan who fell (the user's decision), so his death is "poginuo"; and lists of the fallen
# whose entries give only the years ("1905/44" in the Cazin region's, "1920-1942" in Iskra in plamen's) or a name, a
# birth year and a village under the battle they fell in (Ludbreg's)
COLUMN_BOOKS = {'spomenica-crnogorskim-antifasistima', 'cazinska-krajina-pali-borci', 'iskra-in-plamen-padli',
                'ludbreg-poginuli'}
# books that print one man in more than one of their chapters: the Spomenica lists the dead by municipality, and a man
# born in one and living or killed in another can stand in two or three ("Ivović Momčilo" under Bar, Pljevlja and
# Podgorica); its entries of one name are one man when they agree as printed_twice says (the census never: each volume
# lists its dead once, and two of its entries of one name and village are as often two cousins)
PRINTS_TWICE = {'spomenica-crnogorskim-antifasistima'}
# entries checked by hand to be one man, where an OCR slip in the father hides it from same_man, or where the Spomenica
# prints him in two chapters with two villages
ONE_MAN = [
    ('9060000001', '9035011183', 'Adilović Hilmo, Kovačevići 1918, fell 1943; the Spomenica\'s "Recov" is Redžov'),
    ('9060000096', '9035011488', 'Gerina Muharem, Šumani 1928, fell 1943; the Spomenica\'s "Radišin" is Rašidov'),
    ('9060000387', '9035012663', 'Popović Gruban, Kakmuži 1927 (the Spomenica\'s "Kukmuži"); "Neđelžov" is Neđeljkov'),
    ('9060000432', '9035012899', 'Soković Živan, Bobovo 1911; the father Jovo to Prilog u krvi, Jovan to the Spomenica'),
    ('9060000475', '9035013044', 'Tomašević Novica, Mataruge 1915, fell 1944; the Spomenica\'s "Ć." is Đ. (Đerosim)'),
    ('9035007827', '9035012049', 'Kontić Radoje, Andrija\'s son, fell 1943: the Spomenica\'s chapters of Nikšić '
                                 '(Pješivci, 1920) and Pljevlja (Tikava, 1919), as his brother Radoš'),
    ('9035007830', '9035012050', 'Kontić Radoš, Andrija\'s son, fell 1943: Nikšić (Pješivci, 1922) and Pljevlja '
                                 '(Tikava, 1921)'),
    ('9035017001', '9035012349', 'Maričević Radmila, born in Prijepolje 1900 or 1901, fell at the Sutjeska 1943: the '
                                 'chapters of Šavnik ("N.") and Pljevlja ("D.", Prilog u krvi\'s Danila)'),
]
ONE_MAN_PAIRS = {frozenset(p[:2]) for p in ONE_MAN}


def column_fields(e: dict) -> dict:
    day = re.fullmatch(r'(\d{4})-(\d\d)-(\d\d)', e.get('death_date') or '')     # the Ludbreg lists give the battle's day
    out = {'birth_place': e.get('born_in') or '', 'death_type': 'poginuo',
           'death_date': f'{int(day[3])}. {int(day[2])}. {day[1]}.' if day else e.get('death_year') or '',
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


def father_forms(e: dict) -> set[str]:
    """the father as printed and, for a possessive ("Vukadinov", "Mićov"), in the nominative the site's names know, so
    that it meets another book's genitive ("Vukadina", "Mića")"""
    father = e.get('fathers_name') or ''
    forms = {fold(father)}
    if e.get('_book') in POSSESSIVE_FATHERS and len(father) > 2:
        forms.add(fold(from_possessive(father)))
    return {f for f in forms if f}


def one_slip(x: str, y: str) -> bool:
    """two fathers a letter apart once their endings are cut ("pegrov"/"petra", "colov"/"dola", "jusufof"/"jusufa")"""
    cut = lambda s: re.sub(r'(?:ov|ev|of|in|a|e|o|u)$', '', s)
    x, y = cut(x), cut(y)
    if min(len(x), len(y)) < 3 or abs(len(x) - len(y)) > 1:
        return False
    if len(x) == len(y):
        return sum(c != d for c, d in zip(x, y)) <= 1
    short, long_ = sorted((x, y), key=len)
    return any(long_[:i] + long_[i + 1:] == short for i in range(len(long_)))


def fathers_agree(x: str, y: str) -> bool:
    return x == y or (len(x) <= 2 and y.startswith(x)) or (len(y) <= 2 and x.startswith(y)) or same_father(x, y)   # "Lj"


def village(e: dict) -> set[str]:
    """The village alone, without the municipality after it ("Kosanica, Pljevlja": the Spomenica's chapter and the
    Pljevlja lists name the municipality in every entry, so it tells no two men apart)"""
    first = (e.get('born_in') or '').split(',')[0]
    return {stem(w) for w in fold(first).split() if len(w) >= 4} - {'selu', 'opst', 'opsti', 'kotar', 'srez', 'okrug', 'kod'}


def overlap(x: set[str], y: set[str]) -> bool:
    return any(p[:4] == q[:4] for p in x for q in y)


def agreement(a: dict, b: dict) -> set[str] | None:
    """What two entries of different books agree on when they are one man (see the module's note), else None"""
    if frozenset((a['soldier_id'], b['soldier_id'])) in ONE_MAN_PAIRS:
        return {'checked by hand'}
    agree = set()
    fa, fb = father_forms(a), father_forms(b)
    ya, yb = year(a, 'birth_year'), year(b, 'birth_year')
    if fa and fb:
        if any(fathers_agree(x, y) for x in fa for y in fb):
            agree.add('father')
        elif not ((a.get('_book') in POSSESSIVE_FATHERS) != (b.get('_book') in POSSESSIVE_FATHERS) and
                  any(one_slip(x, y) for x in fa for y in fb) and ya and ya == yb and overlap(places(a), places(b))):
            return None
        else:
            agree.add('father')              # an OCR slip in a possessive father ("Pegrov" Petrov, "Jueov" Jusov), where
            #                                  the birth year and the village agree as well
    if ya and yb:
        if abs(ya - yb) > 1:
            return None
        agree.add('birth year')
    sa, sb = death_years(a), death_years(b)
    qa, qb = death_places(a), death_places(b)
    if sa and sb:
        if not sa & sb:
            # the books often disagree on the year he fell: no clash where the father, the exact birth year and the
            # village agree ("Joknić Mihailo" of Jugovo, 1908: 1943 and 1945), or they and the place he fell, a year
            # apart ("Markišić Aleksa", 1908: Soko Banja, 1941 and 1942)
            same = 'father' in agree and ya and ya == yb
            if not (same and (overlap(village(a), village(b)) or
                              (overlap(qa, qb) and min(abs(x - y) for x in sa for y in sb) == 1))):
                return None
            agree.add('death year differs')
        elif len(sa) == len(sb) == 1 or sa == sb:
            agree.add('death year')                        # or the same front's years (Gončin's and Tmušić's Srem)
    da, db = max(sa, default=None), max(sb, default=None)
    if (a.get('survived') and db and db <= 1945) or (b.get('survived') and da and da <= 1945):
        return None
    if overlap(places(a), places(b)):
        agree.add('birthplace')
    if set(a.get('units') or ()) & set(b.get('units') or ()) or (
            not a.get('units') and not b.get('units') and unit_key(a) and unit_key(a) == unit_key(b)):
        agree.add('unit')
    if overlap(qa, qb):
        agree.add('death place')
    core = agree & {'birth year', 'birthplace', 'death year'}
    if 'father' in agree and core:
        return agree
    if {'birth year', 'birthplace'} <= agree:
        return agree
    # the lists that give a name, a brigade and where he fell (Gončin's Srem): the unit or the place of his death,
    # with the year of it or with each other
    if ('unit' in agree or 'death place' in agree) and len(agree & {'unit', 'death place', 'death year'}) >= 2:
        return agree
    # a narodni heroj and an entry that names no father (a spomenica list's "Maček Ivan, 1908", Romano's "Albahari Nisim"):
    # the hero's name and his birth year
    if bool(a.get('_hero')) != bool(b.get('_hero')) and 'birth year' in agree and not (father_of(a) and father_of(b)):
        return agree
    return agree if a.get('_hero') and b.get('_hero') and agree & {'father', 'birth year'} else None


def same_man(a: dict, b: dict) -> bool:
    return agreement(a, b) is not None


def closeness(a: dict, b: dict) -> tuple[int, int]:
    """How much two entries that are one man agree on, to choose between two of a book's entries that both fit: a pair
    whose years of death differ comes after every pair whose don't, then the more they agree on, an exact birth year
    counting once more"""
    agree = agreement(a, b)
    if agree is None:
        return (-1, 0)
    if 'checked by hand' in agree:
        return (2, 0)
    exact = bool(year(a, 'birth_year') and year(a, 'birth_year') == year(b, 'birth_year'))
    return (0 if 'death year differs' in agree else 1, len(agree - {'death year differs'}) + exact)


def printed_twice(a: dict, b: dict) -> bool:
    """Two entries of one book that prints a man in more than one chapter (PRINTS_TWICE), or that ONE_MAN ties: the same
    father (an initial, an OCR slip: "Risga" and "Ristov"), birth year and year of death, and the same place of death
    or village ("Minić Milisav", 1926, Perišin and Nerišin, fell at Polja in 1944; "Ivović Momčilo", 1923, born in
    Podgorica, in the chapters of Bar, Pljevlja and Podgorica)"""
    if a['_book'] != b['_book']:
        return False
    if frozenset((a['soldier_id'], b['soldier_id'])) in ONE_MAN_PAIRS:
        return True
    if a['_book'] not in PRINTS_TWICE:
        return False
    fa, fb = father_forms(a), father_forms(b)
    if not (fa and fb and any(fathers_agree(x, y) or one_slip(x, y) for x in fa for y in fb)):
        return False
    ya, yb, sa, sb = year(a, 'birth_year'), year(b, 'birth_year'), death_years(a), death_years(b)
    if not (ya and yb and sa and sa == sb and
            (overlap(death_places(a), death_places(b)) or overlap(village(a), village(b)))):
        return False
    if ya == yb:
        return True
    # born a year apart: only under two municipalities (one chapter's two of a name are as likely two cousins), and
    # the father in full, not a letter off ("Burić Stanko", Đuro's son, 1912 under Danilovgrad and 1911 under Šavnik,
    # fell at Pljevlja in 1941; not "Jovanović Veselin", Marko's or Mirko's)
    return (abs(ya - yb) == 1 and a.get('opstina') != b.get('opstina') and
            any(fathers_agree(x, y) for x in fa for y in fb))


def tied(members: list[dict]) -> list[list[dict]]:
    """A cluster's entries with each book's entries of one man (printed_twice) together, and a narodni heroj's entries
    of the hero books ("Rolović Niko": the Zbornik's of 1910 and Narodni heroji's of 1909, whom the Spomenica and the
    census each print twice)"""
    parent = {m['soldier_id']: m['soldier_id'] for m in members}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x
    for i, a in enumerate(members):
        for b in members[i + 1:]:
            if printed_twice(a, b) or (a['_book'] != b['_book'] and a['_book'] in HERO_BOOKS and
                                       b['_book'] in HERO_BOOKS and same_man(a, b)):
                parent[find(a['soldier_id'])] = find(b['soldier_id'])
    out = defaultdict(list)
    for m in members:
        out[find(m['soldier_id'])].append(m)
    return list(out.values())


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
        cands = [base + 'a', soft + 'a'] + ([base[:-1] + 'ca'] if base.endswith('č') else [])   # Jovičin: Jovica;
        #                                                       not Milijin: Milica, Perišin: Perica (Milija, Periša)
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
                if (a['_book'] != b['_book'] and same_man(a, b)) or printed_twice(a, b):
                    parent[find(a['soldier_id'])] = find(b['soldier_id'])
    for x, y, _ in ONE_MAN:
        if x in parent and y in parent:
            parent[find(x)] = find(y)
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
        # a cluster that took two entries of one book (not one man it prints twice) is two men: the entries of that
        # book stay apart, and an entry of another book joins the one it agrees with, or the one it agrees with best
        # ("Vujošević Stanko": the census's two of Mataguži, 1910 and 1911, and the Spomenica's of 1910); one that
        # agrees with two alike (or with neither) joins the other books' entries it is one man with ("Tešović
        # Neđeljko": the census prints him twice, the Spomenica crnogorska and Prilog u krvi once each), else stays alone
        units = tied(members)
        books_of = lambda g: {x['_book'] for x in g}
        per_book = Counter(b for u in units for b in books_of(u))
        if max(per_book.values()) > 1:
            book = per_book.most_common(1)[0][0]
            groups = [list(u) for u in units if book in books_of(u)]
            loose, left = [], []
            # the entry that fits the fewest groups first, each scored against all a group holds by then ("Burić
            # Stanko": the Spomenica's, which fits only the census's 1919, before the hero books', which then follow
            # it there rather than to the census's 1920)
            pending = [u for u in units if book not in books_of(u)]
            while pending:
                scored = []
                for u in pending:
                    score = [max(closeness(x, y) for x in g for y in u)
                             if not books_of(u) & books_of(g) else (-1, 0) for g in groups]
                    scored.append((sum(s[0] >= 0 for s in score), u, score))
                fits, u, score = min(scored, key=lambda t: (t[0] if t[0] else 99, [-x for x in max(t[2])]))
                pending.remove(u)
                best = max(score)
                if best[0] >= 0 and score.count(best) == 1:
                    groups[score.index(best)].extend(u)
                    continue
                # a man printed twice who fits two of the doubled book's entries alike, each of his entries best
                # another, is as likely two men that book prints too ("Martinović Ljubica", Marko's, of 1923 and 1924
                # in the Spomenica and in the census): each entry goes to its own
                picks = []
                for m in (u if len(u) > 1 and best[0] >= 0 else ()):
                    s = [max(closeness(x, m) for x in g) if m['_book'] not in books_of(g) else (-1, 0) for g in groups]
                    picks.append(s.index(max(s)) if max(s)[0] >= 0 and s.count(max(s)) == 1 else None)
                if picks and None not in picks and len(set(picks)) == len(picks):
                    for m, i in zip(u, picks):
                        groups[i].append(m)
                else:
                    left.append(u)
            for u in left:
                fit = lambda g: not books_of(u) & books_of(g) and all(same_man(x, y) for x in g for y in u)
                joins = [g for g in loose if fit(g)]          # another book's entry left over as well
                if joins:
                    joins[0].extend(u)
                    continue
                # else the one group of most books it agrees with whole, if that already joined another book's entry to
                # the doubled book's ("Anđelić Vukoman": the census man who took Prilog u krvi's entry, and the
                # Spomenica's)
                cands = [g for g in groups if fit(g)]
                best = max((len(books_of(g)) for g in cands), default=0)
                top = [g for g in cands if len(books_of(g)) == best]
                if best > 1 and len(top) == 1:
                    top[0].extend(u)
                else:
                    loose.append(list(u))
            groups += loose
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
            # the father as the lead entry gives him, else (it names none, or only an initial) as the first entry that
            # gives him in full ("Bukovec Franc": Dolomiti's scanned entry leads, the hero books name Franc his father),
            # read as that entry's book prints him (nominative, possessive or genitive)
            given = lambda m, n: len(re.sub(r'\W', '', m.get('fathers_name') or '')) > n
            fsrc = first if given(first, 2) else next((m for m in g if given(m, 2)), None)
            fsrc = fsrc or (first if given(first, 0) else next((m for m in g if given(m, 0)), first))
            father = fsrc.get('fathers_name') or ''
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
            nominative = fsrc['_vol'] or fsrc['_book'] in NOMINATIVE_FATHERS
            rec = {'soldier_id': rid, 'last_name': first['last_name'],
                   'middle_name': '' if nominative and code == CODE else father, 'first_name': first['first_name'],
                   'fathers_name': (from_possessive(father) if fsrc['_book'] in POSSESSIVE_FATHERS else
                                    father if nominative else ''),
                   'full_name': '', 'additional_info': text,
                   'birth_year': str(year(first, 'birth_year') or '')}
            if fsrc is not first and given(first, 0) and (nominative or fsrc['_book'] in POSSESSIVE_FATHERS):
                rec['middle_name'] = first['fathers_name']     # the lead's initial stays in the name ("Zec B. Drago"),
                #                                                his father in full from the census beside it (Bojan)
            rec.update({k: first[k] for k in SOURCE_FIELDS if first.get(k) not in (None, '')})
            # a names-only list of the fallen (Gončin's and Tmušić's Srem, Oborovo) holds no bio for the field
            # extractor: the death from its entries' fields, the village he fell at and the day where it gives them (not
            # a names-only list of survivors: the Vis spomenica's holders)
            listed = [m for m in g if m.get('pdf_file') in NAME_LISTS and not m.get('survived')]
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
