"""What a soldier's books say together, for the rows of the record dialog and the memorial card (the user's decisions of
2026-10-27). apply_corrections.py runs it.

- `borrowed`: the fields a record took from the same man's record in another unit (a link) or from a book across units
  whose columns are clean (the census, `FILL_BOOKS`). They are put back on every run before the unit's own books are
  read (`put_back`), and taken again after the references and links, so a link or a reference taken off takes its
  fields along, and a field the record's own books come to give wins over them.
- The census and the column books fill the rows the unit's books and the linked records leave empty (`fill_from`): the
  birth year and place, the nationality, and the death; never the death of a man his own list has living, nor one
  whose year differs from the death the record gives.
- `birth_date`: the day of birth (or the month) where any of the record's entries prints it, its own first
  (extract_life_events.birth_day).
- `variants`: the birth years and the deaths the unit's other books, the same man's records in other units, and the
  census's and the column books' columns give otherwise, which the card shows after "ili" ("1915 ili 1918";
  "05.03.1943, kod Gornjeg Vakufa ili 06.1943, Sutjeska"; "10.09.1944, Žumberak ili 1944, Bosiljevo slove"): another
  year, month or day, or another place in the same year too (2026-11-19, the user's "use family report always and
  there should be also an option for alternative location if there's a mismatch"), where both places lie on the map
  further apart than NEAR_KM (same_place: a village and its town, a misspelling, the census's cut-off column, a region,
  or an area and a place inside it, "Kozara" and Bosanska Dubica, are no other place). A value a family's correction set stays first, and the record's own book shows after
  "ili" where it says otherwise (FAMILY_REASON). The other books across units only fill. Borci drugih jedinica has
  them from its own books (each one book among the others: the census's columns may have given its fields); the
  census's parts, one entry each, none.
"""
from __future__ import annotations

import math
import os
import re
import unicodedata
from functools import lru_cache

import extract_structured_fields as structured
from extract_life_events import birth_day, born_phrase, read_entry
from name_utils import BRIGADE_CONFIGS, OSTALI_CODES, extract_birth_info
from standardize_fields import date_form, standard

CENSUS_BOOK = 'zrtve-rata-1964-'
NOT_DEATHS = {'zarobljen', 'ranjen'}            # a fate that is no death (lib/deathDay.ts)
DEATH_FIELDS = ('death_type', 'death_date', 'death_place')
UNIT_NO_PLACE = re.compile(r'brig|\bdiv\b|\bdiv\.|diviz|odred|bataljon|korpus|pogrešan', re.I)


def put_back(soldiers: list[dict], manual: dict) -> int:
    """Take off the fields each record borrowed on the last run (a field corrections set stays); how many"""
    n = 0
    for s in soldiers:
        keys = s.pop('borrowed', None)
        for k in keys or ():
            if k not in manual.get(s.get('soldier_id'), ()):
                s.pop(k, None)
                n += 1
    return n


def borrow(s: dict, k: str, v) -> None:
    s[k] = v
    s['borrowed'] = sorted(set(s.get('borrowed', ())) | {k})


def borrowed(s: dict) -> set:
    return set(s.get('borrowed', ()))


def own_only(s: dict) -> dict:
    """The record as its unit's books give it, without what it borrowed: what the matchers compare, so that a birth
    year the census gave is no proof that the man is another book's entry too"""
    lent = s.get('borrowed')
    return {k: v for k, v in s.items() if k not in lent} if lent else s


# ── the census and the column books fill empty rows ─────────────────────────
def fill_books() -> set:
    import build_ostali_borci
    return build_ostali_borci.COLUMN_BOOKS


def reference_fields(book: str, e: dict) -> dict:
    """A census or column book's entry as the record's fields (as build_ostali_borci.py gives Ostali borci's)"""
    import build_ostali_borci as ob
    out = ob.census_fields(e) if book.startswith(CENSUS_BOOK) else ob.column_fields(e)
    # the unit the census's column names (a division, a brigade) is Ostali borci's sub-unit, never a unit's record's
    out.pop('unit_detail', None)
    if re.fullmatch(r'1[89]\d\d', str(e.get('birth_year') or '')):
        out['birth_year'] = str(e['birth_year'])
    if out.get('ethnicity'):
        out['ethnicity'] = standard('ethnicity', out['ethnicity'])            # the census's "Šiptar": Albanac
    if out.get('death_date'):
        out['death_date'] = date_form(out['death_date'])
    return out


def column_values(book: str, e: dict) -> dict:
    """A census or column book's entry as the fields it lends, in the site's forms"""
    vals = reference_fields(book, e)
    # the census's column of the place of death often holds his unit, no place ("Cankarjeva brigada", "1 brigada 1
    # divizija", "11.brigada 26.div.", "Pogrešan od 9.1944"): nothing to lend (2026-10-30, check_fields.py's list)
    from standardize_fields import UNIT_COLUMN
    if UNIT_NO_PLACE.search(vals.get('death_place') or '') or UNIT_COLUMN.match(vals.get('death_place') or ''):
        vals.pop('death_place')
    elif vals.get('death_place'):
        # written as the site writes the census's places ("Otok-srem" Otok, Srem; standardize_fields.py runs before this)
        from standardize_fields import place_form
        vals['death_place'] = place_form(vals['death_place']) or ''
    if vals.get('birth_place'):
        from standardize_fields import birth_place_form            # "Maribor (del), Maribor-Center"
        vals['birth_place'] = birth_place_form(vals['birth_place'])
    return vals


def no_death_lent(s: dict) -> bool:
    """A man his own list has living, or whose death the record puts after the war, or a fate that is no death: no
    book's death is lent to him, nor shown after "ili\""""
    import find_source_duplicates as fsd
    return fsd.fate(s) == 'lived' or bool(s.get('death_after_war')) or s.get('death_type') in NOT_DEATHS


def fill_from(s: dict, book: str, e: dict) -> list[str]:
    """Fill s's empty fields from a reference of a census or column book; the fields filled"""
    if not (book.startswith(CENSUS_BOOK) or book in fill_books()):
        # any other book: only where he is from, as its parser read it (2026-11-03)
        if s.get('birth_place') or not e.get('born_in'):
            return []
        place = structured.born_in_form(e['born_in'], e.get('additional_info') or '')
        if not place:
            return []
        borrow(s, 'birth_place', place)
        return ['birth_place']
    vals = column_values(book, e)
    year = re.search(r'1[89]\d\d', s.get('death_date') or '')
    other = re.search(r'1[89]\d\d', vals.get('death_date') or '')
    if no_death_lent(s) or (year and other and year.group(0) != other.group(0)):
        # (a death of another year is shown after "ili", variants())
        vals = {k: v for k, v in vals.items() if k not in DEATH_FIELDS}
    taken =[k for k, v in vals.items() if v and not s.get(k)]
    for k in taken:
        borrow(s, k, vals[k])
    return taken


# the census's line, as parse_zrtve_rata_1964.py writes it after the birth: "Srbin, poginuo 1944. u NOBu, Bosiljevo
# slove", "Hrvat, poginuo od ustaša 1942. u NOBu, Glina", "Srbin, umro 1945. kao zarobljenik prip. NOV i POJ, Jasenovac"
CENSUS_LINE = re.compile(r'(?P<year>1[89]\d\d)\.\s+(?:u NOBu|u NORu|kao zarobljenik prip\. NOV i POJ)(?:,\s*(?P<place>.*))?$')


def census_entry(e: dict) -> dict:
    """A census entry another record holds (its text only) as the census's columns: the year and place of death"""
    text = e.get('additional_info') or ''
    m = CENSUS_LINE.search(text)
    return {'additional_info': text, 'death_year': m['year'], 'death_place': (m['place'] or '').strip()} if m else {}


_COLUMN_ENTRIES: dict = {}


def column_entry(sid: str, book: str = '') -> tuple[str, dict]:
    """A column book's entry by its id, from the book's entries file (loaded once): (book, entry), or ('', {})"""
    if not _COLUMN_ENTRIES:
        from match_references import entries_path
        for name in sorted(fill_books()):
            path = entries_path(name)
            if path.exists():
                import json
                for x in json.loads(path.read_text(encoding='utf-8')):
                    _COLUMN_ENTRIES[x['soldier_id']] = (name, x)
        _COLUMN_ENTRIES.setdefault('', ('', {}))
    got = _COLUMN_ENTRIES.get(sid, ('', {}))
    return got if not book or got[0] == book else ('', {})


def column_facts(o: dict) -> dict | None:
    """The death a census or column book's entry gives (its columns), or None where the entry is no such book's"""
    book = o.get('ref_book') or ''
    if book.startswith(CENSUS_BOOK) or structured.CENSUS in (o.get('source_url') or ''):
        e, book = census_entry(o), CENSUS_BOOK
        if not e:
            return {}
    else:
        # (a book across units' entries are numbered 9 + the book's number: a unit's own entry is never a column book's)
        if (book and book not in fill_books()) or not (o.get('soldier_id') or '').startswith('9'):
            return None
        book, e = column_entry(o['soldier_id'], book)
        if not e:
            return None
    vals = column_values(book, e)
    out = {k: vals[k] for k in ('death_date', 'death_place') if vals.get(k)}
    if out.get('death_place'):
        out['death_place'] = death_place_of(out['death_place'])
    # (marked: never lent to a man the record has living, no_death_lent)
    return {**out, 'columns': True} if out.get('death_date') or out.get('death_place') else {}


# ── what the books say otherwise ────────────────────────────────────────────
def fold(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', (text or '').lower()) if not unicodedata.combining(c))


# the words of a place that say nothing of which place it is: prepositions, the kind of place, "Gornji", "Novi"
PLACE_FILLER = {'kod', 'u', 'v', 'na', 'pri', 'iz', 'od', 'do', 'pod', 'nad', 'ispod', 'iznad', 'blizu', 'kraj', 'oko',
                'izmedu', 'ispred', 'preko', 'selo', 'selu', 'sela', 's', 'okolini', 'okolina', 'okolici', 'podrucju',
                'mesto', 'mjesto', 'mestu', 'mjestu', 'grad', 'gradu', 'gornji', 'gornja', 'gornje', 'gornjem', 'gornjoj',
                'gornjeg', 'donji', 'donja', 'donje', 'donjem', 'donjoj', 'donjeg', 'g', 'd', 'gor', 'gornj', 'donj',
                'veliki', 'velika', 'veliko', 'velikom', 'vel', 'mali', 'mala', 'malo', 'malom', 'novi', 'nova', 'novo',
                'novom', 'stari', 'stara', 'staro', 'starom', 'sveti', 'sveta', 'sv', 'i', 'ili', 'bolnica', 'bolnici',
                'logor', 'logoru', 'nob', 'nobu', 'nor', 'b', 'sl', 'bos', 'st', 'n', 'm', 'gr',
                'nepoz', 'nepoznato', 'nepoznat', 'nepoznata', 'negdje', 'negde'}      # ("Crna gora, Nepoz": a region)
# a region, a land or a country says where no place of it does otherwise ("Srem" beside "Ilinci", "Bosna" beside
# "Sutjeska"); the regions a man may fall in, not a mountain or a river's valley, which name a battle's place
REGIONS = {'srem', 'srijem', 'sremski front', 'bosna', 'lika', 'kordun', 'banija', 'slavonija', 'dalmacija',
           'hercegovina', 'crna gora', 'sandzak', 'srbija', 'hrvatska', 'slovenija', 'makedonija', 'kosovo', 'metohija',
           'kosovo metohija', 'vojvodina', 'istra', 'gorski kotar', 'zagorje', 'hrvatsko zagorje', 'primorje',
           'hrvatsko primorje', 'podravina', 'posavina', 'moslavina', 'backa', 'banat', 'baranja', 'sumadija', 'krajina',
           'bosanska krajina', 'istocna bosna', 'zapadna bosna', 'centralna bosna', 'srednja bosna', 'jugoslavija',
           'bih', 'bosna hercegovina', 'stajerska', 'stajerskem', 'koroska', 'gorenjska', 'dolenjska', 'notranjska',
           'primorska', 'lici', 'c gora', 'italija', 'nemacka', 'njemacka', 'austrija', 'madarska', 'albanija', 'bugarska', 'grcka'}
NEAR_KM = 30            # a village and the town it belongs to, or one battle's two places: no other version
# An area covers ground, so a place inside it is no other place (the user's correction of 2026-11-19: "one might be a
# region and the other could be a place within the region"): how far from its GeoNames point a place may lie and still
# be in it, by the feature's code (data-extraction/places/areas.json, scripts/area_places.py): a region, a mountain
# range ("Kozara" and Bosanska Dubica at its foot, 31 km), a plain, an island, a river along its course ("Neretva" and
# Jablanica, Konjic or Mostar), a single mountain, a valley; a hill, a peak or a spring hardly more than a village
AREA_KM = {'RGN': 50, 'ADM1': 60, 'ADM2': 60, 'ADM3': 30, 'MTS': 35, 'HLLS': 35, 'PLN': 30, 'PLAT': 30, 'AREA': 25,
           'ISL': 25, 'STM': 60, 'STMI': 15, 'MT': 20, 'VAL': 20, 'DPR': 20}
AREA_SMALL_KM = 10      # any other area: a hill, a peak, a ridge, a locality, a spring
# a river a hundred km long or more is no point ("na Drini": Foča, Višegrad, Zvornik): it covers LONG_RIVER_KM, still no
# place 400 km off ("Lim" is not Vinkovci; the Neretva is the battle's ground by Jablanica, NAMED_AREAS)
LONG_RIVER_KM = 100
LONG_RIVERS = {'Drina', 'Ibar', 'Južna Morava', 'Kupa', 'Lim', 'Una', 'Vrbas', 'Sana', 'Tara', 'Morača', 'Beli Drim',
               'Bregalnica', 'Sutla', 'Треска', 'Stara Drava'}
# the areas a place of death names that GeoNames places nowhere or as something else (a village of the name in Serbia,
# a peak of the name): their point and ground, so "Zelengora" or "Tjentište" beside "Sutjeska" is that battle's place
# and "Jablanica" beside it another battle's, and "Bosiljevo" lies outside Žumberak (37 km from its middle, 20 km
# past its southern edge)
NAMED_AREAS = {'sutjeska': (43.354, 18.692, 35), 'neretva': (43.660, 17.760, 60), 'romanija': (43.850, 18.700, 35),
               'igman': (43.750, 18.250, 20), 'piva': (43.250, 18.830, 35), 'zelengora': (43.370, 18.500, 35),
               'durmitor': (43.130, 19.030, 35), 'grmec': (44.750, 16.330, 35), 'kozara': (44.970, 17.090, 35),
               'vucevo': (43.300, 18.800, 20),      # (the Sutjeska's Vučevo, not the village of Pljevlja GeoNames gives)
               'zumberak': (45.730, 15.450, 25)}    # (the region, not the peak Žumberak GeoNames gives)


@lru_cache(maxsize=1)
def _areas() -> dict:
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parent.parent / 'data-extraction' / 'places' / 'areas.json'
    return json.loads(path.read_text(encoding='utf-8'))['areas'] if path.exists() else {}


def ground(gid) -> float:
    """How far from its point a place may lie inside the resolved place gid: 0 for a settlement"""
    a = _areas().get(str(gid))
    if not a:
        return 0
    if a[1] in ('PCLI', 'PCL'):
        return 500
    return LONG_RIVER_KM if a[2] in LONG_RIVERS else AREA_KM.get(a[1], AREA_SMALL_KM)


def place_words(v: str) -> list[str]:
    return [w for w in re.findall(r'[a-z]+', fold(v)) if w not in PLACE_FILLER]


def same_word(a: str, b: str, spelling: bool = True) -> bool:
    """One word of a place in two cases or two spellings: "Žumberak" and "Žumberku", "Dvor" and "Dvora", "Čačak" and
    "Čačku", "Bosiljevo" and "Bosiljevu"; not "Bar" and "Barilović". spelling: a misspelling too (not "Sutjeska" for
    the region "Štajerska")"""
    if a == b:
        return True
    if min(len(a), len(b)) >= 4 and (a.startswith(b) or b.startswith(a)):
        return True                 # the census cuts its column at 15 letters: "Negdje u zeleng", "MiljevinaBosna"
    if min(len(a), len(b)) < 3 or abs(len(a) - len(b)) > 3:
        return False
    common = len(os.path.commonprefix([a, b]))
    if common >= max(3, min(len(a), len(b)) - 2):
        return True
    import difflib
    return spelling and min(len(a), len(b)) >= 5 and difflib.SequenceMatcher(None, a, b).ratio() >= 0.8


def region(words: list[str]) -> bool:
    return any(len(r.split()) == len(words) and all(same_word(x, y, False) for x, y in zip(r.split(), words))
               for r in REGIONS)


@lru_cache(maxsize=1)
def _resolved() -> tuple[dict, dict]:
    """The resolved places (data-extraction/places/resolved.json): by unit file and folded text, the GeoNames ids; and
    by folded text, how many units' fields resolved it to each place"""
    import resolved_places
    from collections import Counter
    units, votes = {}, {}
    for unit, fields in resolved_places.load()['units'].items():
        d = units.setdefault(unit, {})
        for field in ('death_place', 'birth_place'):
            for text, v in fields.get(field, {}).items():
                gid = v[0] if isinstance(v, list) else v
                d.setdefault(fold(text).strip(), set()).add(gid)
                votes.setdefault(fold(text).strip(), Counter())[gid] += 1
    return units, votes


def _points(text: str, unit: str) -> list[tuple]:
    """Where a place may lie: as the record's own unit's places resolved it (its region decides a name of several
    places), else where most units' places put the name (two fields or more, two in three of them: "Bosiljevo" is by
    Karlovac for four fields and by Ivanić-Grad for two); nothing for a name the units read as several places. The
    resolved places have their slips (Opčine by Trieste put in Montenegro), so two places are told apart only where
    every reading of each lies far from the other's (same_place). Each point is (lat, lon, the ground it covers)"""
    import resolved_places
    key = fold(text).strip()
    if key in NAMED_AREAS:
        return [NAMED_AREAS[key]]
    units, votes = _resolved()
    gids = units.get(unit, {}).get(key)
    if not gids:
        vote = votes.get(key)
        # (not a case after a preposition, which the census's parts resolved as they could: "Kod zagreba" far off)
        if not vote or sum(vote.values()) < 2 or re.match(r'(?:kod|u|na|pri|blizu|iznad|ispod|pod)\s', key):
            return []
        gid, n = vote.most_common(1)[0]
        if n * 3 < sum(vote.values()) * 2:
            return []
        gids = {gid}
    points = [(*p[:2], ground(g)) for g, p in ((g, resolved_places.coords(g)) for g in sorted(gids)) if p]
    # (a unit whose birthplaces and places of death read one name as two places: neither)
    return [] if any(km(points[0], p) > 5 for p in points[1:]) else points


def points_of(v: str, unit: str = '') -> list[tuple]:
    """Where a place may lie (_points): the place as written, in the nominative, a part of it from the last, its
    municipality ("Ozren, Tjentište" is by Tjentište, not on the Ozren of Doboj; not a region's point: "Lipovac
    (Srem)"), or its first words where the rest is the scan's or cut off ("Bosiljevo slove")"""
    parts = [p.strip() for p in re.split(r'[,()]', v or '') if p.strip()]
    words = parts[0].split() if parts else []
    heads = [' '.join(words[:n]) for n in range(len(words) - 1, 0, -1)
             if place_words(words[n - 1]) and words[n - 1][0].isupper()]
    parts = [p for p in reversed(parts) if not region(place_words(p))]
    for text in [v, death_place_of(v)] + parts + heads:
        got = text and _points(text, unit)
        if got:
            return got
    return []


def nearest(a: str, b: str, unit: str = '') -> float | None:
    """How far apart two places lie at the nearest of their readings; None where one can't be put on the map"""
    pa, pb = points_of(a, unit), points_of(b, unit)
    return min(km(x, y) for x in pa for y in pb) if pa and pb else None


def beyond(a: str, b: str, unit: str = '') -> float | None:
    """How far two places lie apart beyond what one place may span, at the nearest of their readings: the distance less
    NEAR_KM or the ground the larger of them covers (an area, ground()); 0 or less where one may lie in the other or
    beside it; None where one can't be put on the map"""
    pa, pb = points_of(a, unit), points_of(b, unit)
    if not (pa and pb):
        return None
    return min(km(x, y) - max(NEAR_KM, x[2], y[2]) for x in pa for y in pb)


def km(a, b) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def words_match(wa: list, wb: list) -> bool:
    import difflib                  # (and "Bela Krajina" and "Belokrajina", "Zelen gora" and "Zelengora")
    return bool(wa and wb and (any(same_word(x, y) for x in wa for y in wb)
                               or difflib.SequenceMatcher(None, ''.join(wa), ''.join(wb)).ratio() >= 0.85))


def one_place(a: str, b: str, unit: str = '') -> bool:
    """Two places of death that name one place: a word of one is a word of the other in another case or spelling ("Šid"
    and "Sid", "Crnac" and "u s. Crnac — Slavonija", "Šujica" and "Šujica, Livno", "Žumberak" and "u Žumberku"), or a
    village and its town a few km apart (the resolved places, NEAR_KM); not an area and a place in it, which the card
    names each in its own words ("Kozara" is not Bosanska Dubica)"""
    if words_match(place_words(a), place_words(b)):
        return True
    pa, pb = points_of(a, unit), points_of(b, unit)
    return any(km(x, y) <= NEAR_KM for x in pa for y in pb if not x[2] and not y[2])


def same_place(a: str, b: str, unit: str = '') -> bool:
    """Two places of death that don't say otherwise: unless both lie where the resolved places put them, further apart
    than NEAR_KM and than the ground an area among them covers (beyond: "Kozara" and Bosanska Dubica at its foot,
    "Neretva" and Konjic, "Sutjeska" and Miljevina say the same), and no word of one is a word of the other, and neither
    is a region or a land ("Srem" beside "Ilinci"). A place the site can't put on the map says nothing against another:
    the census's column, cut at 15 letters and often misspelt ("Podrav slatina", "Lukovo kod bolj"), or a village of a
    name several bear. "Žumberak" and "Bosiljevo slove" are two places (Bosiljevo lies 37 km from Žumberak's middle);
    so are "Neretva" and "Sutjeska", two battles 80 km apart"""
    wa, wb = place_words(a), place_words(b)
    if not wa or not wb or region(wa) or region(wb) or words_match(wa, wb):
        return True
    d = beyond(a, b, unit)
    return d is None or d <= 0


def date_parts(v: str):
    """(year, month, (first day, last day)) of a date in the stored form ("05.03.1943", "03-08.06.1943", "06.1943",
    "1943"); a date printed otherwise ("krajem 1942") gives its year alone; None without a year"""
    v = (v or '').strip()
    m = re.fullmatch(r'(?:(\d\d)(?:[-/](\d\d))?\.)?(\d\d)\.(\d{4})', v)
    if m:
        days = (int(m[1]), int(m[2] or m[1])) if m[1] else None
        return int(m[4]), int(m[3]), days
    m = re.search(r'(?<!\d)(1[89]\d\d)(?!\d)', v)
    return (int(m[1]), None, None) if m else None


def precision(d) -> int:
    return 0 if not d else 3 if d[2] else 2 if d[1] else 1


def dates_differ(a, b) -> bool:
    if not a or not b:
        return False
    if a[0] != b[0]:
        return True
    if a[1] and b[1] and a[1] != b[1]:
        return True
    return bool(a[2] and b[2] and (a[2][1] < b[2][0] or b[2][1] < a[2][0]))


def since_in_unit(s: dict) -> str:
    """When a record's entries say he came to the unit ("u brigadi od juna 1943": "1943-06"), for the card's order of his units"""
    entries = [s] + [o for o in s.get('other_sources', ()) if not o.get('unit_file') and not o.get('ref_book')]
    for e in entries:
        for step in read_entry(e.get('additional_info') or ''):
            if step.get('k') == 'unit' and step.get('d'):
                return step['d']
    return ''


def misprinted_year(a, b) -> bool:
    """The same day and month, one in the war and the other long after it: the misprint "poginuo 4. 6. 1963", no other death"""
    return bool(a and b and a[1:] == b[1:] and a[2] and min(a[0], b[0]) <= 1945 and max(a[0], b[0]) > 1950)


def death_place_of(v: str) -> str:
    if not v:
        return ''
    import resolved_places
    v = structured.tidy_death_place(structured.fix_place(v))
    return resolved_places.case_nominative(v) or v


def entry_facts(e: dict, code: int, ex) -> dict:
    """An entry's birth year and day and its death, read from its text by the unit's rules"""
    if e.get('pdf_file') in structured.NAME_LISTS | structured.ROSTERS or structured.CENSUS in (e.get('source_url') or ''):
        return {}
    text = e.get('additional_info') or ''
    if structured.PARTIZANKE in (e.get('source_url') or ''):
        text = structured.her_own_deaths(text)
    out = {}
    year = extract_birth_info(text)[1]
    if year:
        out['birth_year'] = year
        b = born_phrase(text, year)
        if b and b[2][1]:
            out['birth_date'] = day_form(b[2])
    got = ex.extract(text, code, read=not structured.parser_set(code, e)) if text else {}
    if got.get('death_date'):
        out['death_date'] = date_form(got['death_date'])
        out['death_place'] = death_place_of(got.get('death_place') or '')
    return out


def record_facts(rec: dict) -> dict:
    """A linked record's own fields (not those it borrowed, perhaps from this very record)"""
    lent = borrowed(rec)
    out = {}
    if rec.get('birth_year') and 'birth_year' not in lent:
        out['birth_year'] = rec['birth_year'][:4]
        if rec.get('birth_date'):
            out['birth_date'] = rec['birth_date']
    if rec.get('death_date') and 'death_date' not in lent:
        out['death_date'] = rec['death_date']
        out['death_place'] = rec.get('death_place') if 'death_place' not in lent else ''
    return out


def day_form(d: tuple) -> str:
    y, m, day = d
    return f'{day:02d}.{m:02d}.{y}' if m and day else f'{m:02d}.{y}' if m else str(y)


_OWN_IDS: dict = {}


def own_entry_ids(sid: str) -> set:
    """A record of Borci drugih jedinica's entries by their books' ids (data-extraction/ostali_borci_ids.json)"""
    if not _OWN_IDS:
        import json
        from pathlib import Path
        path = Path(__file__).resolve().parent.parent / 'data-extraction' / 'ostali_borci_ids.json'
        for entry, rec in json.loads(path.read_text(encoding='utf-8')).items():
            _OWN_IDS.setdefault(rec, set()).add(entry)
        _OWN_IDS.setdefault('', set())
    return _OWN_IDS.get(sid, set())


def facts_of(e: dict, code: int, ex) -> dict:
    """An entry's facts: a census or column book's columns, else its text read by the unit's rules"""
    col = column_facts(e)
    return entry_facts(e, code, ex) if col is None else col


def own_facts(s: dict, code: int, ex) -> dict:
    """The record's own entry's facts; in Borci drugih jedinica its entry may be a column book's, whose id the record
    doesn't carry"""
    if code in OSTALI_CODES and structured.CENSUS not in (s.get('source_url') or ''):
        merged = {o.get('soldier_id') for o in s.get('other_sources', ())}
        for eid in sorted(own_entry_ids(s['soldier_id']) - merged):
            if column_entry(eid)[1]:
                return column_facts({'soldier_id': eid}) or {}
    return facts_of({k: s.get(k) for k in ('soldier_id', 'additional_info', 'pdf_file', 'source_url')}, code, ex)


def sources(s: dict, by_id: dict, ex, own: bool = False) -> list[dict]:
    """The facts of each of the record's other entries: the unit's other books, the same man's records in other units
    and their books, and the census's and the column books' columns (their death; not the other books across units);
    own: the record's own entry first"""
    code = int(s['soldier_id'][:4])
    out = [own_facts(s, code, ex)] if own else []
    for o in s.get('other_sources', ()):
        oid = o.get('soldier_id') or ''
        if o.get('ref_book'):
            col = column_facts(o)
            if col:
                out.append(col)
        elif o.get('unit_file') and oid in by_id:
            out.append(record_facts(by_id[oid][1]))
        else:
            # an entry by its own unit's rules (a linked record's merged entry, 0001200318 in the Druga proleterska's
            # record, is the Prva proleterska's: the Druga proleterska's parser sets its fields and reads none); in Borci
            # drugih jedinica every entry is a book across units', read by 122's rules as its fields are
            out.append(facts_of(o, code if code in OSTALI_CODES else int((oid or s['soldier_id'])[:4]), ex))
    return out


def plausible_birth(year: int, s: dict) -> bool:
    died = date_parts(s.get('death_date') or '')
    # 1936: the youngest the entries print (a child with her family in the 5. proleterska); "u NOB od ;1941" read as a birth is none
    return 1850 <= year <= 1936 and not (died and year >= died[0])


# a correction that gives a family's report ("Family (B. Batalo, 2026-11-19) names him ...", "Form 2026-11-19 (a
# great-nephew ...)", "Visitor form", "the family (B. Batalo)"): its values win on the card, and what the record's own
# book says otherwise shows after "ili" (the user's rule of 2026-11-19); a correction that mends a reading doesn't make
# the misreading another version
FAMILY_REASON = re.compile(r"\bfamil(?:y|ies)(?:'s)?\s*(?:\(|biography|report|letter|papers|says|said|sent|wrote|names)|"
                           r'\b(?:visitor\s+)?form\s+20\d\d-\d\d-\d\d|\bvisitor\s+form\b|'
                           r'\bgrand(?:son|daughter|child)\b|\bgreat-(?:nephew|niece|grand\w+)\b', re.I)
# (not "the Zakrajšek family above it", "a Livno family", "the family nickname": a book's words, no family's report)


def variants(s: dict, by_id: dict, ex, family: set = frozenset(), fixed: set = frozenset()) -> dict:
    """The birth years and the deaths the record's other books, linked records, the census and the column books give
    otherwise. family: the fields a family's correction set on the record; fixed: those other corrections set. The
    record's own entry is one book among the others in Borci drugih jedinica (the census's columns may have given its
    fields), and in a unit's record where a family's correction set the field"""
    code = int(s['soldier_id'][:4])
    if code in OSTALI_CODES and code != 122:
        return {}                   # the census's parts: one entry each, its columns the fields
    own_death = (code == 122 or bool(family & set(DEATH_FIELDS))) and not (fixed - family) & set(DEATH_FIELDS)
    own_birth = (code == 122 or 'birth_year' in family) and 'birth_year' not in fixed - family
    facts = sources(s, by_id, ex, own=own_death or own_birth)
    own = facts[0] if own_death or own_birth else {}
    out = {}
    year = (s.get('birth_year') or '')[:4]
    born, seen = [], {year}
    for f in facts:
        if f is own and not own_birth:
            continue
        y = (f.get('birth_year') or '')[:4]
        if y and y not in seen and year and plausible_birth(int(y), s):
            seen.add(y)
            born.append(f.get('birth_date') or y)
    if born:
        out['born'] = born
    deaths = []
    unit = BRIGADE_CONFIGS[code]['json_file'] if code in BRIGADE_CONFIGS else ''
    mine = date_parts(s.get('death_date') or '')
    here = s.get('death_place') or ''
    lent = not no_death_lent(s)
    for f in facts:
        if (f is own and not own_death) or (f.get('columns') and not lent):
            continue
        theirs = date_parts(f.get('death_date') or '')
        place = f.get('death_place') or ''
        other_day = dates_differ(mine, theirs) and not misprinted_year(mine, theirs)
        # another place, in the same year too (the user's rule of 2026-11-19): where the record names a place
        other_place = bool(place and here and not same_place(here, place, unit))
        if not (other_day or other_place):
            continue
        d = {'date': f['death_date']} if f.get('death_date') else {}
        if place:
            # the record's own spelling where the two name one place, so the card can say it once
            d['place'] = here if here and one_place(here, place, unit) else place
        # two books that agree with each other ("08.1944" and "10.08.1944", "Bosiljevo" and "u Bosiljevu"): one, the
        # day where one gives it
        like = next((x for x in deaths if not dates_differ(date_parts(x.get('date', '')), theirs)
                     and same_place(x.get('place', ''), place, unit)), None)
        if like is None:
            deaths.append(d)
            continue
        if precision(theirs) > precision(date_parts(like.get('date', ''))):
            like['date'] = d['date']
        if 'place' in d and 'place' not in like:
            like['place'] = d['place']
    if deaths:
        out['death'] = deaths
    return out


def apply(soldiers: list[dict], by_id: dict, manual: dict | None = None, family: dict | None = None) -> dict:
    """Set each record's birth_date and variants (rebuilt on every run); counts. manual: soldier_id -> the fields
    corrections set; family: those a family's correction set (FAMILY_REASON)"""
    ex = structured.get_extractor()
    manual, family = manual or {}, family or {}
    counts = {'birth_date': 0, 'born': 0, 'death': 0}
    for s in soldiers:
        s.pop('birth_date', None)
        s.pop('variants', None)
        day = birth_day(s)
        if day:
            s['birth_date'] = day_form(day[3])
            counts['birth_date'] += 1
        sid = s['soldier_id']
        v = variants(s, by_id, ex, set(family.get(sid, ())), set(manual.get(sid, ())))
        if v:
            s['variants'] = v
            for k in v:
                counts[k] += 1
    return counts
