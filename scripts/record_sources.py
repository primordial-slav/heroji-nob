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
- `variants`: the birth years and the deaths the unit's other books and the same man's records in other units give
  otherwise, which the card shows after "ili" ("1915 ili 1918"; "05.03.1943, kod Gornjeg Vakufa ili 06.1943,
  Sutjeska"). Books across units only fill; Ostali borci and the census's parts, all books across units, have none.
"""
from __future__ import annotations

import re
import unicodedata

import extract_structured_fields as structured
from extract_life_events import birth_day, born_phrase
from name_utils import OSTALI_CODES, extract_birth_info
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
    if re.fullmatch(r'1[89]\d\d', str(e.get('birth_year') or '')):
        out['birth_year'] = str(e['birth_year'])
    if out.get('ethnicity'):
        out['ethnicity'] = standard('ethnicity', out['ethnicity'])            # the census's "Šiptar": Albanac
    if out.get('death_date'):
        out['death_date'] = date_form(out['death_date'])
    return out


def fill_from(s: dict, book: str, e: dict) -> list[str]:
    """Fill s's empty fields from a reference of a census or column book; the fields filled"""
    if not (book.startswith(CENSUS_BOOK) or book in fill_books()):
        return []
    import find_source_duplicates as fsd
    vals = reference_fields(book, e)
    # the census's column of the place of death often holds his unit, no place ("Cankarjeva brigada", "1 brigada 1
    # divizija", "11.brigada 26.div.", "Pogrešan od 9.1944"): nothing to lend (2026-10-30, check_fields.py's list)
    if UNIT_NO_PLACE.search(vals.get('death_place') or ''):
        vals.pop('death_place')
    year = re.search(r'1[89]\d\d', s.get('death_date') or '')
    other = re.search(r'1[89]\d\d', vals.get('death_date') or '')
    if (fsd.fate(s) == 'lived' or s.get('death_after_war') or s.get('death_type') in NOT_DEATHS
            or (year and other and year.group(0) != other.group(0))):
        vals = {k: v for k, v in vals.items() if k not in DEATH_FIELDS}
    taken = [k for k, v in vals.items() if v and not s.get(k)]
    for k in taken:
        borrow(s, k, vals[k])
    return taken


# ── what the books say otherwise ────────────────────────────────────────────
def fold(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', (text or '').lower()) if not unicodedata.combining(c))


def same_place(a: str, b: str) -> bool:
    """Two places of death that name one place: a word of one is a word of the other, as far as their stems go
    ("Šid" and "Sid", "Crnac" and "u s. Crnac — Slavonija", "Šujica" and "Šujica, Livno")"""
    def stems(v):
        return {w[:5] for w in re.findall(r'\w+', fold(v)) if len(w) >= 3} - {'kod', 'selu', 'sela', 'okolini', 'blizu'}
    sa, sb = stems(a), stems(b)
    return bool(sa & sb) or not sa or not sb


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


def sources(s: dict, by_id: dict, ex) -> list[dict]:
    """The facts of each of the record's other entries: the unit's other books, the same man's records in other units
    and their books (not the books across units)"""
    out = []
    for o in s.get('other_sources', ()):
        if o.get('ref_book'):
            continue
        oid = o.get('soldier_id') or ''
        if o.get('unit_file') and oid in by_id:
            out.append(record_facts(by_id[oid][1]))
        else:
            out.append(entry_facts(o, int((oid or s['soldier_id'])[:4]), ex))
    return out


def plausible_birth(year: int, s: dict) -> bool:
    died = date_parts(s.get('death_date') or '')
    return 1850 <= year <= 1945 and not (died and year >= died[0])


def variants(s: dict, by_id: dict, ex) -> dict:
    """The birth years and the deaths the record's other books and linked records give otherwise"""
    if int(s['soldier_id'][:4]) in OSTALI_CODES:
        return {}
    facts = sources(s, by_id, ex)
    out = {}
    year = (s.get('birth_year') or '')[:4]
    born, seen = [], {year}
    for f in facts:
        y = (f.get('birth_year') or '')[:4]
        if y and y not in seen and year and plausible_birth(int(y), s):
            seen.add(y)
            born.append(f.get('birth_date') or y)
    if born:
        out['born'] = born
    mine = date_parts(s.get('death_date') or '')
    deaths = []
    for f in facts:
        theirs = date_parts(f.get('death_date') or '')
        if not dates_differ(mine, theirs):
            continue
        d = {'date': f['death_date']}
        place = f.get('death_place') or ''
        if place:
            # the record's own spelling where the two name one place, so the card can say it once
            d['place'] = s['death_place'] if s.get('death_place') and same_place(s['death_place'], place) else place
        # two books that agree with each other ("08.1944" and "10.08.1944"): one, the day where one gives it
        like = next((x for x in deaths if not dates_differ(date_parts(x['date']), theirs)), None)
        if like is None:
            deaths.append(d)
        elif precision(theirs) > precision(date_parts(like['date'])):
            like['date'] = d['date']
            if 'place' in d and 'place' not in like:
                like['place'] = d['place']
    if deaths:
        out['death'] = deaths
    return out


def apply(soldiers: list[dict], by_id: dict) -> dict:
    """Set each record's birth_date and variants (rebuilt on every run); counts"""
    ex = structured.get_extractor()
    counts = {'birth_date': 0, 'born': 0, 'death': 0}
    for s in soldiers:
        s.pop('birth_date', None)
        s.pop('variants', None)
        day = birth_day(s)
        if day:
            s['birth_date'] = day_form(day[3])
            counts['birth_date'] += 1
        v = variants(s, by_id, ex)
        if v:
            s['variants'] = v
            for k in v:
                counts[k] += 1
    return counts
