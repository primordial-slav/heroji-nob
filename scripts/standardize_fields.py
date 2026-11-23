"""
The structured fields in one form, whatever book or reader they came from (2026-10-26). Each rule is a small function of
a record that returns the fields it changes, listed in RULES with its name; apply_corrections.py runs them on every
unit it writes, after the places step, so they hold on every run and for every new book. Alone:

    python scripts/standardize_fields.py                           # every rule, every unit: counts and samples
    python scripts/standardize_fields.py --rule death_date --sample 30
    python scripts/standardize_fields.py --brigade 70 --apply      # write (outside apply_corrections.py)

The rules (the user's decisions of 2026-10-26):
    captured     a fate "zarobljen" read again in the clause after the capture: "zarobljen ... i strijeljan" is streljan,
                 "ujet in obešen" ubijen, "umro u nemačkom logoru" umro, "i nestao" nestao; a man let go ("pušten kući")
                 has none; else a fate his entries name elsewhere (the extractor took "zarobljeni ustaša" for his);
                 only captured, it stays (the dialog says "Zarobljen")
    after_war    a survivor who has died since, with no year: "po osvoboditvi", "po vojni" (the Slovene rosters' "†")
                 leave the date and set death_after_war; the dialog says "Umro posle rata" in the page's language
    death_date   a date in numbers, DD.MM.YYYY: "14. februara 1941" is 14.02.1941, "15. VI 1943" 15.06.1943, "juna
                 1943" 06.1943, a night "4/5. decembra 1944" 04/05.12.1944; a date with words besides ("krajem 1942",
                 "proljeće 1944", "početkom februara 1943") stays as printed
    albanian     the census's "Šiptar" is Albanac (Šiptarka Albanka); the entries' text keeps the census's word
    unit_numbers a sub-unit's number in figures ("I bataljon" 1. bataljon; 2026-10-28)
The rules of 2026-10-30 (the user's "do all of it" after a survey of the cards' rows):
    unit_case   a sub-unit's common nouns small ("2. Četa", "Bataljon »Garibaldi«", "Štab brigade")
    trade        the reader's cuts read on ("poljopriv." poljoprivrednik, "trg. pomoćnik", "čl. KPJ" no trade), the
                 scans' spellings ("ćak", "zemlzoradnik"), no schooling or status ("izbeglica", "osnovna škola"); a
                 duty of the war ("politički radnik") to the duty where the record has none
    grk_village  the village Grk read as a nationality ("1926, Grk, bolničarka")
    ethnicity_gender  the nationality in the soldier's gender as the card shows it ("Rođena ... Hrvatica")
    death_place_form  the census's place of death as a place ("Otok-srem" Otok, Srem; "Istočna bosna"; "Trnovo,
                 sarajevo"; "Nepoznata jedinica" none)
    parents      a woman's name in fathers_name is the mother's (mothers_name, the card's "Majka"); a father the
                 converter left in the genitive ("Hajima" Hajim)
The books' own forms stay otherwise: ekavian and ijekavian duties as each book prints them (zamenik, zamjenik).

A rule changes a field's form, never what the entry says, and the entries' text is never touched. A field corrections
set is standardized too by a rule that only changes its form (FORM_ONLY); a rule that reads the text again leaves it.

To add a rule: write `def rule(s: dict) -> dict | None` returning {field: new value} (None removes the field), and list
it in RULES; `--rule NAME` shows what it would change before it runs with the pipeline.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_life_events import MONTH_OF, ROMAN_OF  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


# ── captured: the fate after a capture ──────────────────────────────────────
CAUGHT_RE = re.compile(r'(?:zarobljen[a]?|zarobili|ujet[a]?)\b(?P<after>.{0,160})', re.I | re.S)
# the first fate the clause after the capture names
AFTER_CAUGHT = [
    ('streljan', re.compile(r'\b(?:stri?jelja\w*|strelja\w*|ustreljen\w*)', re.I)),
    ('ubijen', re.compile(r'\b(?:ubi(?:jen|li|o)\w*|zaklan\w*|zaklali|obe[šs]en\w*|obje[šs]en\w*|likvidir\w*)', re.I)),
    ('umro', re.compile(r'\b(?:umro|umrla|umr[lj]\w*|podlega\w*\s+ranama|podlegao|podlegla)', re.I)),
    ('poginuo', re.compile(r'\b(?:poginu\w*|padel|padla)', re.I)),
    ('nestao', re.compile(r'\b(?:nesta[oli]\w*|nije se (?:živ\s+)?vratio|nije se vratila|sudbina nepoznata|'
                          r'više se nije ništa saznalo|ništa se ne zna)', re.I)),
]
# a man let go or exchanged lived through the capture: "posle dva meseca ... pušten kući", "razmijenjen"
RELEASED = re.compile(r'\b(?:pu[šs]ten\w*|razmenjen\w*|razmijenjen\w*|zamenjen\w*|zamijenjen\w*|pobegao|pobjegao|'
                      r'pobegla|pobjegla|uspeo da pobegne|uspio pobjeći|oslobođen\w*)', re.I)


def first_fate(text: str) -> tuple[int, str] | None:
    """Where the first fate the text names stands, and which"""
    hits = [(m.start(), fate) for fate, r in AFTER_CAUGHT for m in [r.search(text)] if m]
    return min(hits) if hits else None


def captured(s: dict) -> dict | None:
    """The fate after a capture, read from the man's entries (a linked unit's too: the field may have come from it):
    the fate the clause after the capture names; none if he was let go; else a fate his entries name elsewhere ("zarobljen
    7. mj 1944, Knin" in one book, "streljan u Kninu od četnika" in the other), or the extractor's "zarobljen" read from
    someone else's capture ("ranio ga je zarobljeni ustaša", "pobegao iz nemačkog zarobljeništva")"""
    if s.get('death_type') != 'zarobljen':
        return None
    texts = [s.get('additional_info') or ''] + [o.get('additional_info') or '' for o in s.get('other_sources') or []
                                                 if not o.get('ref_book')]
    released = False
    for text in texts:
        for m in CAUGHT_RE.finditer(text):
            after = m.group('after')
            fate, free = first_fate(after), RELEASED.search(after)
            if fate and not (free and free.start() < fate[0]):
                return {'death_type': fate[1]}
            released = released or bool(free)
    if released:
        return {'death_type': None}
    for text in texts:
        fate = first_fate(text)
        if fate:
            return {'death_type': fate[1]}
    return None


# ── after_war: a survivor who has died since ────────────────────────────────
AFTER_WAR = re.compile(r'(?:po\s+osvoboditvi|po\s+vojni|posle\s+rata|poslije\s+rata|nakon\s+rata|po\s+vojnoj)\.?', re.I)


# the death's own sentence says so where no date is given: "Umro u Zagrebu posle rata", "poginuo na Golniku posle
# oslobođenja" (2026-10-31: the place of death keeps the place alone, tidy_death_place)
AFTER_WAR_DEATH = re.compile(r'\b(?:umro|umrla|poginuo|poginula|stradao|stradala)\b[^.;]{0,60}?\b(?:neposredno\s+)?'
                             r'(?:posle|poslije|nakon)\s+(?:rata|oslobođenja|oslobođenju)\b', re.I)


def after_war(s: dict) -> dict | None:
    if AFTER_WAR.fullmatch((s.get('death_date') or '').strip()):
        return {'death_date': None, 'death_after_war': True}
    if not s.get('death_date') and not s.get('death_after_war') and s.get('death_type') \
            and any(AFTER_WAR_DEATH.search(t) for t in texts_of(s)):
        return {'death_after_war': True}
    return None


# ── death_date: a date in numbers ───────────────────────────────────────────
MONTH = '|'.join(sorted(MONTH_OF, key=len, reverse=True))
ROMAN = '(?-i:XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I)'          # in capitals only: the Slovene "v" is a word
DAYS = r'(?P<day>\d{1,2}(?:\s?[/–—-]\s?\d{1,2})?)'
YEAR = r'(?P<year>1[89]\d\d|20\d\d)'
DATE_FORMS = [
    # 14. 2. 1941 / 14.02.1941 / 14. II 1941 / 14. II. 1941 / 4/5. 12. 1944
    re.compile(rf'{DAYS}\s*[.,]\s*(?P<month>\d{{1,2}}|{ROMAN})\s*[.,]?\s*{YEAR}', re.I),
    # 14. februara 1941 / 14 avgusta 1942 / 4/5. decembra 1944 / 15. juna mjeseca 1943
    re.compile(rf'{DAYS}\s*\.?\s*(?P<word>{MONTH})\s+(?:mjeseca\s+|meseca\s+)?{YEAR}', re.I),
    # juna 1943 / u junu 1943 / VI 1943 / VI. 1943 / 06.1943
    re.compile(rf'(?:u\s+)?(?P<word>{MONTH})\s+(?:mjeseca\s+|meseca\s+)?{YEAR}', re.I),
    re.compile(rf'(?P<month>{ROMAN}|\d{{1,2}})\s*\.\s*{YEAR}', re.I),
    re.compile(rf'(?P<month>{ROMAN})\s+{YEAR}', re.I),
    re.compile(YEAR),
]
DAYS_IN = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def date_form(value: str) -> str:
    """'14. februara 1941' -> '14.02.1941', 'juna 1943' -> '06.1943', '1943. god.' -> '1943'; a date with other words
    ('krajem 1942', 'proljeće 1944') or one no rule reads ('9.11944', '6. 2. 45') stays as printed"""
    v = re.sub(r'\s+', ' ', value.strip())
    v = re.sub(r'\.?\s*god(?:ine|\.|\b)\.?$', '', v).strip().rstrip('.').strip()
    for form in DATE_FORMS:
        m = form.fullmatch(v)
        if not m:
            continue
        g = m.groupdict()
        year = g['year']
        month = None
        if g.get('word'):
            month = MONTH_OF[g['word'].lower()]
        elif g.get('month'):
            month = ROMAN_OF.get(g['month']) or int(g['month'])
        if month is not None and not 1 <= month <= 12:
            return value
        if month is None:
            return year
        days = g.get('day')
        if not days:
            return f'{month:02d}.{year}'
        parts = re.split(r'\s?([/–—-])\s?', days)
        nums = parts[::2]
        if any(not 0 <= int(d) <= DAYS_IN[month - 1] for d in nums):
            return value                            # "31. 4.": a misprint, as printed
        if all(int(d) == 0 for d in nums):
            return f'{month:02d}.{year}'            # "00. 03. 1944": the day isn't known
        sep = '/' if '/' in days else '-'
        return f"{sep.join(f'{int(d):02d}' for d in nums)}.{month:02d}.{year}"
    return value


# a date with a word stuck to it or a slip of the scan, read so (2026-11-03): a day or a month no calendar has goes, the rest of the date stays
DATE_READ = {
    'poginuo 27. 3. 1945': '27.03.1945', 'poginuo 24. 10. 1944': '24.10.1944', 'poginuo 6. 4. 1945': '06.04.1945', 'poginuo 24. 3. 1945': '24.03.1945',
    'podlegao zadobijenim ranama 3. 4. 1945': '03.04.1945', 'Plana (Bileća) 1. 11. 1944': '01.11.1944', 'zarobljen od četnika jula 1944': '07.1944', '3. VIII 1944. |': '03.08.1944',
    '6. :XII 1944': '06.12.1944', '5. :XII 1944': '05.12.1944', '22. juliia 1944': '22.07.1944', '11. aiprila 1944': '11.04.1944', '3. oitotobra 1944': '03.10.1944',
    '95. 04. 1945': '04.1945', '65. 04. 1945': '04.1945', '93 juna 1943': '06.1943', '65 septembra 1943': '09.1943', '38 novembra 1944': '11.1944', '70. decembra 1941': '12.1941', '38. XII 1943': '12.1943', '9. mj. 1943': '09.1943',
    '00. 00. 1942': '1942', '15. 98. 1941': '1941', '3. 45. 1945': '1945', '31. 21. 1944': '1944', '24. 13. 1944': '1944', '22. 17. 1941': '1941', '4. XIII 1943': '1943', '8. XIII 1944': '1944',
    'Proljeće 1944': 'proljeće 1944', 'Proljeće 1943': 'proljeće 1943',
}


def death_date(s: dict) -> dict | None:
    v = s.get('death_date')
    if not v:
        return None
    new = date_form(DATE_READ.get(v, v))
    return {'death_date': new} if new != v else None


# ── albanian: the census's word, and one word for the Jews (Jevrej 258, Jevrejin 132: the user's decision of
# 2026-11-04; the regional pairs, Talijan and Italijan, Nemac and Nijemac, stay as each book prints them) ────
ETHNICITY = {'Šiptar': 'Albanac', 'Šiptarka': 'Albanka', 'šiptar': 'Albanac', 'šiptarka': 'Albanka',
             'Siptar': 'Albanac', 'Siptarka': 'Albanka', 'Jevrejin': 'Jevrej'}


def albanian(s: dict) -> dict | None:
    new = ETHNICITY.get(s.get('ethnicity') or '')
    return {'ethnicity': new} if new else None


# ── unit_numbers: a sub-unit's number in figures ────────────────────────────
# The books number their companies and battalions in Roman numerals or in figures; the site writes figures ("I
# bataljon" is 1. bataljon, "XV. divizije" 15. divizije), the scan's small letters too ("iV bataljon", "Vi bataljon",
# "i. četa"). A small "i" or "v" without its dot is a word ("i", "and"; the Slovene "v"), never read as a number here:
# check_fields.py lists such a value, which the reader no longer gives (2026-10-28)
UNIT_WORDS = r'(?i:čet[aeiu]|vod[au]?|bataljon\w*|desetin\w*|brigad\w*|divizij\w*|divizion\w*|baterij\w*|korpus\w*|eskadril\w*|odred\w*)'
UNIT_ROMAN_RE = re.compile(r'(?<![\w.])(?:([IVX]{1,6}|[IVX][IVXivx]{1,5}|[ivx]{1,4}[IVX][IVXivx]{0,3})\.?|([ivx]{1,4})\.)'
                           r'\s?(?=' + UNIT_WORDS + r'\b)')


def roman_value(text: str) -> int | None:
    """a Roman numeral's value, None where it is not written as one ("IIII", "VX")"""
    values = {'I': 1, 'V': 5, 'X': 10}
    total, prev = 0, 0
    for ch in reversed(text):
        v = values[ch]
        total = total - v if v < prev else total + v
        prev = max(prev, v)
    tens, units = divmod(total, 10)
    written = 'X' * tens + ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX'][units]
    return total if 0 < total < 40 and written == text else None


def unit_number_form(value: str) -> str:
    def figures(m: re.Match) -> str:
        n = roman_value((m.group(1) or m.group(2)).upper())
        return f'{n}. ' if n else m.group(0)
    return UNIT_ROMAN_RE.sub(figures, value)


def unit_numbers(s: dict) -> dict | None:
    value = s.get('unit_detail')
    new = unit_number_form(value) if value else value
    return {'unit_detail': new} if new != value else None


# ── unit_case: a sub-unit's common nouns in small letters ───────────────────
# Books and readers set "2. Četa", "5. Bataljon", "Mitraljeski Vod", "Prištapske jedinice", "Bataljon »Garibaldi«"
# beside "2. četa", "prištapske jedinice": the site writes the common noun small, as the books mostly do ("brigada
# »Braća Radić«"); a name stays as printed ("Muslimanska brigada", "Štab IV POS-a" keeps POS) (2026-10-30)
COMMON_FIRST = re.compile(
    r'^(\d+\.\s+)?(Četa|Čete|Bataljon|Vod|Desetina|Baterija|Štab|Prištapske|Prištapska|Prateća|Prateći|Samostalne|'
    r'Samostalna|Samostalni|Intendantura|Brigada|Divizion|Eskadron|Odeljenje|Odjeljenje|Sanitet|Komanda|Izviđačka|'
    r'Mitraljeska|Minobacačka|Protivavionska|Protivtenkovska|Protivoklopna|Inžinjerijska|Pionirska|Tehnička|Kurirska|'
    r'Zaštitna|Udarna|Omladinska|Omladinski|Politodjel|Politodel|Prva|Prvi|Druga|Drugi|Treća|Treći|Četvrta|Četvrti|'
    r'Peta|Peti|Šesta|Šesti|Mitraljeski|Izviđački|Minobacački|Protivavionski|Protivtenkovski|Inžinjerijski|Pionirski|'
    r'Kurirski|Zaštitni|Tehnički|Sanitetski|Pozadinski)\b')
COMMON_INSIDE = re.compile(r'(?<=[a-zčćžšđ.] )(Čet[aeiu]|Bataljon[a-z]*|Vod[au]?|Desetin[aeiu]|Baterij[aeiu]|Brigad[aeiu])\b')


def unit_case_form(value: str) -> str:
    parts = []
    for part in value.split(', '):
        part = COMMON_FIRST.sub(lambda m: (m.group(1) or '') + m.group(2).lower(), part)
        parts.append(COMMON_INSIDE.sub(lambda m: m.group(1).lower(), part))
    return ', '.join(parts)


def unit_case(s: dict) -> dict | None:
    value = s.get('unit_detail')
    new = unit_case_form(value) if value else value
    return {'unit_detail': new} if new != value else None


# ── trade: the reader's cuts, the scans' spellings, what is no trade ────────
# The reader stops a trade at a full stop, so an abbreviation lost its second word ("poljopriv. tehničar" was
# "poljopriv", "trg. pomoćnik" "trg", "čl. KPJ" "čl"): the words after it in the entry tell the trade. A schooling,
# a status or a word of the war is no trade ("izbeglica", "osnovna škola", "politički radnik"); a duty of the war
# goes to the duty where the record has none, in a unit (2026-10-30, the user's "do all of it" after the cards' survey)
TRADE_AFTER = {
    'poljopriv': [(r'tehn', 'poljoprivredni tehničar'), ('', 'poljoprivrednik')],
    'polj': [(r'tehn', 'poljoprivredni tehničar')],
    'trg': [(r'pom', 'trgovački pomoćnik'), (r'akad', 'učenik trgovačke akademije'), (r'put', 'trgovački putnik')],
    'trgov': [(r'pom', 'trgovački pomoćnik'), (r'akad', 'učenik trgovačke akademije')],
    'trg. pomoćnik': [('', 'trgovački pomoćnik')],
    'maturant trg': [('', 'maturant trgovačke akademije')],
    'maturant trg. akadem.': [('', 'maturant trgovačke akademije')],
    'dipl': [(r'vet', 'diplomirani veterinar'), (r'prav', 'diplomirani pravnik'), (r'ing', 'diplomirani inženjer'),
             (r'ekon', 'diplomirani ekonomista'), (r'agr', 'diplomirani agronom')],
    'dipi': [(r'vet', 'diplomirani veterinar'), (r'prav', 'diplomirani pravnik'), (r'ing', 'diplomirani inženjer')],
    'ing': [(r'(šumarstva|arhitekture|rudarstva|agronomije|elektrotehnike|mašinstva|građevinarstva|hemije|kemije)',
             'inženjer {}'), ('', 'inženjer')],
    'sez': [(r'rad', 'sezonski radnik')],
    'tvor': [(r'rad', 'tvornički radnik')],
    'građev': [(r'rad', 'građevinski radnik'), (r'teh', 'građevinski tehničar')],
    'grad. tehničar': [('', 'građevinski tehničar')],
    'građev. poslovođa': [('', 'građevinski poslovođa')],
    'podof': [('', 'podoficir')], 'podofic': [('', 'podoficir')],
    'učen': [(r'gimn', 'učenik gimnazije')],
    'učenik tehn': [('', 'učenik tehničke škole')],
    'zemlj': [('', 'zemljoradnik')],
    'mesarski': [(r'rad', 'mesarski radnik')],
    'trgovačka akademija': [('', 'učenik trgovačke akademije')],
    'pravni sćakultet': [('', 'student prava')],
}
TRADE_SPELLING = {
    'ćak': 'đak', 'dak': 'đak', 'dij ak': 'dijak', 'ćak gimnazije': 'đak gimnazije', 'kmećki sin': 'kmečki sin',
    'zemlzoradnik': 'zemljoradnik', 'zeljoradnik': 'zemljoradnik', 'zemjoradnik': 'zemljoradnik',
    'zemljroadnik': 'zemljoradnik', 'zemljoradni': 'zemljoradnik', 'zemljoradiik': 'zemljoradnik',
    'zemljorandik': 'zemljoradnik', 'zemljoradeik': 'zemljoradnik', 'zemljoradoik': 'zemljoradnik',
    'zemljoradvik': 'zemljoradnik', 'zemljoradaik': 'zemljoradnik', 'vemljoradnik': 'zemljoradnik',
    'zemljoradnika': 'zemljoradnik', 'zemgoradnik-rudar': 'zemljoradnik-rudar',
    'zemljoradeik i vodeničar': 'zemljoradnik i vodeničar', 'zemljoradnik-nadničao': 'zemljoradnik-nadničar',
    'graćevinski radnik': 'građevinski radnik', 'građevnnski radnik': 'građevinski radnik',
    'trađevinski radnik': 'građevinski radnik',
    'domađica': 'domaćica', 'domoćica': 'domaćica', 'domaćrgca': 'domaćica',
    'kljućavnićar': 'ključavničar', 'najamn raddnik': 'najamni radnik', 'iajamni radnik': 'najamni radnik',
    'radnmk': 'radnik', 'kroj ač': 'krojač', 'radnik čl': 'radnik', 'radnica čl': 'radnica', 'radiš-kovač': 'radnik-kovač',
    'stolaroki radnik': 'stolarski radnik', 'etolarski radnik': 'stolarski radnik',
    'obućaroki radnik': 'obućarski radnik', 'opančaroki radnik': 'opančarski radnik',
    'apančarski radnik': 'opančarski radnik', 'olančarski radnik': 'opančarski radnik',
    'opaičarski radnik': 'opančarski radnik', 'opančaski radnik': 'opančarski radnik',
    'obaleki radnik': 'obalski radnik', 'električareki radnik': 'električarski radnik',
    'qrafički radnik': 'grafički radnik', 'trogovački radnik': 'trgovački radnik', 'trogvački radnik': 'trgovački radnik',
    'abacijski radnik': 'abadžijski radnik', 'abadžitski radnik': 'abadžijski radnik',
    'učenik gimnazi je': 'učenik gimnazije', 'mašiznbravarski pomoćnik': 'mašinbravarski pomoćnik',
    'poelužitelj u opštini': 'poslužitelj u opštini', 'tršvac': 'trgovac', 'vookar': 'voskar', 'naničar': 'nadničar',
    'delavec ___________': 'delavec', 'VII. 1944 delavec': 'delavec', 'pozadinski-radnik': 'pozadinski radnik',
}
NOT_TRADE = {
    'čl', 'izbeglica', 'izbeg lica', 'izbegica', 'omladinka', 'dečak', 'porodica', 'u činovničkoj porodici',
    'otac pekar', 'nepismen', 'nepizmen', 'nepiemen', 'poginuo', 'borac u četi', 'bez zanimanja', '!', '__',
    'osnovna', 'osnov', 'osnovna škola', 'osnovna nžola', 'osnovna pžola', 'osnovnaško la', 'zanatska škola',
    'prava', 'venac', 'trgovska',
}
# a duty of the war, no trade: the record's duty where it has none (a unit's record; in Borci drugih jedinica it goes)
DUTY_NOT_TRADE = {'politički radnik', 'terenski radnik', 'partijski radnik', 'pozadinski radnik', 'četna bolničarka'}
# the Mačvanski odred's "osnovna škola, zemljoradnik": the trade after the schooling
SCHOOL_THEN_TRADE = re.compile(r'(?:osnov\W{0,2}\s*na\W{0,2}\s*škola|zanatska škola|trgovačka škola)\s*,\s*'
                               r'([a-zčćžšđ]{4,}(?:\s+radnik)?)\b')
NOT_UNITS = ('0122', '0131', '0132', '0133', '0134', '0135', '0136', '0137', '0138')


def texts_of(s: dict) -> list[str]:
    return [s.get('additional_info') or ''] + [o.get('additional_info') or '' for o in s.get('other_sources') or []
                                                if not o.get('ref_book')]


def trade_form(value: str, s: dict | None = None) -> str | None:
    """the trade as the site writes it; None where it is no trade"""
    v = re.sub('­\\s*', '', value).strip()
    v = TRADE_SPELLING.get(v, v)
    if v in TRADE_AFTER:
        after = ''
        for text in texts_of(s or {}):
            m = re.search(r'(?<![\w])' + re.escape(v.rstrip('.')) + r'\.?\s*[.,;:]?\s*(.{0,40})', text, re.I)
            if m:
                after = m.group(1).lower()
                break
        for pattern, full in TRADE_AFTER[v]:
            m = re.match(pattern, after) if pattern else None
            if not pattern or m:
                return full.format(*m.groups()) if m and m.groups() else full
        return None
    if v in NOT_TRADE:
        for text in texts_of(s or {}):
            m = SCHOOL_THEN_TRADE.search(text)
            if m and m.group(1) not in NOT_TRADE and m.group(1) != 'porodica':
                return TRADE_SPELLING.get(m.group(1), m.group(1))
        return None
    return v


def trade(s: dict) -> dict | None:
    value = s.get('occupation')
    if not value:
        return None
    new = trade_form(value, s)
    out = {}
    if new in DUTY_NOT_TRADE:
        if not s['soldier_id'].startswith(NOT_UNITS) and not s.get('rank'):
            out['rank'] = new
        new = None
    if new == value:
        return None
    out['occupation'] = new
    return out


# ── trade_gender: a woman's trade in the feminine ───────────────────────────
# Books print a woman's trade in the masculine too ("Rođena 1924, ... zemljoradnik", "tekstilni radnik"): the card says
# it as the site says "Rođena" (the user's choice of 2026-10-31). The noun and the adjectives before it ("tekstilni
# radnik" tekstilna radnica); what follows stays ("učenik gimnazije" učenica gimnazije). Only nouns whose feminine is
# one word everywhere (not "đak", "profesor", "lekar")
TRADE_FEMININE = {
    'zemljoradnik': 'zemljoradnica', 'poljoprivrednik': 'poljoprivrednica', 'učenik': 'učenica',
    'službenik': 'službenica', 'radnik': 'radnica', 'seljak': 'seljanka', 'krojač': 'krojačica', 'učitelj': 'učiteljica',
    'student': 'studentkinja', 'kuvar': 'kuvarica', 'kuhar': 'kuharica', 'činovnik': 'činovnica',
    'nadničar': 'nadničarka', 'frizer': 'frizerka', 'delavec': 'delavka', 'kmet': 'kmetica', 'dijak': 'dijakinja',
    'študent': 'študentka', 'uradnik': 'uradnica', 'nameštenik': 'nameštenica', 'namještenik': 'namještenica',
    'pomoćnik': 'pomoćnica', 'pomočnik': 'pomočnica', 'trgovac': 'trgovkinja', 'zemljoradnik-radnik': 'zemljoradnica-radnica',
}
TRADE_HEAD = re.compile(r'^((?:[a-zčćžšđ]+i\s+)*)(' + '|'.join(sorted(TRADE_FEMININE, key=len, reverse=True)) + r')(?=$|\s)(.*)$')


def trade_feminine(value: str) -> str:
    m = TRADE_HEAD.match(value)
    if not m:
        return value
    adjectives = re.sub(r'i(?=\s)', 'a', m.group(1))       # "tekstilni ", "trgovački " -> "tekstilna ", "trgovačka "
    return adjectives + TRADE_FEMININE[m.group(2)] + m.group(3)


def trade_gender(s: dict) -> dict | None:
    global _genders
    value = s.get('occupation')
    if not value or not TRADE_HEAD.match(value):
        return None
    import feminine_alias
    if _genders is None:
        _genders = feminine_alias.site_genders(ROOT)
    if not feminine_alias.site_is_woman(s, _genders):
        return None
    new = trade_feminine(value)
    return {'occupation': new} if new != value else None


# ── ethnicity_gender: a nationality in the soldier's gender ────────────────
# Books print "Hrvat" for a woman (the Mosor odred, the 32. division: "Rođena 1926, ... domaćica, Hrvat"), and a
# man's field may hold "Srpkinja" read from another's entry: the form follows the site's "Rođena"/"Rođen"
# (feminine_alias.site_is_woman, as website/app/lib/standIn.ts decides it)
NATIONALITY_PAIRS = [
    ('Srbin', 'Srpkinja'), ('Hrvat', 'Hrvatica'), ('Crnogorac', 'Crnogorka'), ('Slovenac', 'Slovenka'),
    ('Slovenec', 'Slovenka'), ('Musliman', 'Muslimanka'), ('Makedonac', 'Makedonka'), ('Jevrej', 'Jevrejka'),
    ('Jevrejin', 'Jevrejka'), ('Židov', 'Židovka'), ('Mađar', 'Mađarica'), ('Slovak', 'Slovakinja'), ('Čeh', 'Čehinja'),
    ('Poljak', 'Poljakinja'), ('Rus', 'Ruskinja'), ('Rusin', 'Rusinka'), ('Ukrajinac', 'Ukrajinka'),
    ('Italijan', 'Italijanka'), ('Talijan', 'Talijanka'), ('Turčin', 'Turkinja'), ('Rumun', 'Rumunka'),
    ('Rom', 'Romkinja'), ('Albanac', 'Albanka'), ('Nemac', 'Nemica'), ('Nijemac', 'Njemica'), ('Bugarin', 'Bugarka'),
    ('Grk', 'Grkinja'), ('Austrijanac', 'Austrijanka'), ('Englez', 'Engleskinja'), ('Jugosloven', 'Jugoslovenka'),
    ('Jugoslaven', 'Jugoslavenka'),
]
FEMININE_OF = {m: f for m, f in NATIONALITY_PAIRS}
MASCULINE_OF = {f: m for m, f in NATIONALITY_PAIRS if m not in ('Slovenec', 'Jevrejin')}
_genders = None


# "1926, Grk, bolničarka", "rođen 1907, Grk, Bosanski Brod": the village Grk (Šid; Bosanski Brod) read as a nationality
GRK_VILLAGE = re.compile(r'\b1[89]\d\d\.?,?\s+Grk,\s*(?P<next>[A-ZČĆŽŠĐ][\w.]*(?:\s[A-ZČĆŽŠĐ][\w.]*)?)?')
NATIONALITY_IN_TEXT = re.compile(r'\b(Srbin|Srpkinja|Hrvat|Hrvatica|Crnogorac|Crnogorka|Musliman|Muslimanka|Slovak|'
                                 r'Mađar|Rusin)\b')


def grk_village(s: dict) -> dict | None:
    if s.get('ethnicity') != 'Grk':
        return None
    text = s.get('additional_info') or ''
    m = GRK_VILLAGE.search(text)
    if not m:
        return None
    other = NATIONALITY_IN_TEXT.search(text)
    out = {'ethnicity': other.group(1) if other else None}
    if not s.get('birth_place'):
        out['birth_place'] = 'Grk' + (f", {m.group('next')}" if m.group('next') else '')
    return out


def ethnicity_gender(s: dict) -> dict | None:
    global _genders
    value = s.get('ethnicity')
    if not value or (value not in FEMININE_OF and value not in MASCULINE_OF):
        return None
    import feminine_alias
    if _genders is None:
        _genders = feminine_alias.site_genders(ROOT)
    woman = feminine_alias.site_is_woman(s, _genders)
    new = FEMININE_OF.get(value, value) if woman else MASCULINE_OF.get(value, value)
    return {'ethnicity': new} if new != value else None


# ── place_form: the census's places of death written as places ─────────────
# The census's column writes the region small after a dash or a space and leaves out the space after a comma ("Otok-
# srem", "Gračanica-bosna", "Istočna bosna", "Trnovo,sarajevo"); a unit or "Nepoznata jedinica" there is no place
# (build_ostali_borci.py moves a unit to the sub-unit). The site writes "Otok, Srem", "Istočna Bosna", "Trnovo,
# Sarajevo"; the entry's text keeps the census's words
REGIONS = {
    'srem': 'Srem', 'sremu': 'Sremu', 'bosna': 'Bosna', 'bosni': 'Bosni', 'bih': 'BiH', 'srbija': 'Srbija',
    'srbiji': 'Srbiji', 'slavonija': 'Slavonija', 'slavoniji': 'Slavoniji', 'hrvatska': 'Hrvatska',
    'hrvatskoj': 'Hrvatskoj', 'lika': 'Lika', 'lici': 'Lici', 'liki': 'Lici', 'crna gora': 'Crna Gora',
    'c. gora': 'C. Gora', 'c. gori': 'C. Gori', 'crnoj gori': 'Crnoj Gori', 'makedonija': 'Makedonija',
    'makedoniji': 'Makedoniji', 'kosovo': 'Kosovo', 'kosovu': 'Kosovu', 'dalmacija': 'Dalmacija',
    'dalmaciji': 'Dalmaciji', 'banija': 'Banija', 'baniji': 'Baniji', 'kordun': 'Kordun', 'kordunu': 'Kordunu',
    'vojvodina': 'Vojvodina', 'slovenija': 'Slovenija', 'sloveniji': 'Sloveniji', 'hercegovina': 'Hercegovina',
    'hercegovini': 'Hercegovini', 'banat': 'Banat', 'banatu': 'Banatu', 'bačka': 'Bačka', 'bačkoj': 'Bačkoj',
    'sandžak': 'Sandžak', 'sandžaku': 'Sandžaku', 'istra': 'Istra', 'istri': 'Istri', 'slavoni': 'Slavoniji',
    'zagorje': 'Zagorje', 'zagorju': 'Zagorju', 'posavina': 'Posavina', 'podravina': 'Podravina',
    'moslavina': 'Moslavina', 'gorski kotar': 'Gorski Kotar', 'primorje': 'Primorje', 'kozara': 'Kozara',
    'kozari': 'Kozari', 'romanija': 'Romanija', 'majevica': 'Majevica', 'majevici': 'Majevici',
}
REGION_WORDS = '|'.join(sorted((re.escape(k) for k in REGIONS), key=len, reverse=True))
ADJECTIVE = r'(?:istočn\w*|zapadn\w*|centraln\w*|srednj\w*|severn\w*|sjevern\w*|južn\w*|skopsk\w*|skop\.|hrvatsk\w*|hrv\.|ravn\w*)'
# "Istočna bosna", "u istočnoj bosni", "Skopska crna gora": the region and, opening the value, its adjective
REGION_NAMED = re.compile(r'\b(' + ADJECTIVE + r') (' + REGION_WORDS + r')$', re.I)
REGION_AFTER = re.compile(r'^([A-ZČĆŽŠĐ][^,]*?[a-zčćžšđ.])(?:\s*-\s*|\s+)(' + REGION_WORDS + r')$')
IN_REGION = re.compile(r'\b((?i:u|na|po)) (' + REGION_WORDS + r')$')
# the census's "Trnovo,sarajevo": a comma without its space, the next word in small letters (not after an l, which
# a Cyrillic list's scan sets for Љ: "Bol,anići" is Boljanići)
COMMA_GLUED = re.compile(r'^([A-ZČĆŽŠĐ][\w .-]*?(?<![lL])),([a-zčćžšđ])([a-zčćžšđ]{3,}(?:[ -][a-zčćžšđ]+)?)$')
UNKNOWN_PLACE = re.compile(r'^(?:nepoznat[aoi]?|nepoznate|nepoznata jedin\w*\.?(?: \w+)?|nepoznate jedinice|'
                           r'nepoznato[-\s]\w+|nepoznata \w+|nije poznato|nn\.?|u nob-?u|u nov-?u|n\.\s?o\.\s?[vb]\.?|'
                           r'u jedinici n\.\s?o\.\s?v\.?-?a?|[A-ZČĆŽŠĐ]\.?)$', re.I)
# the census's column naming his unit where it names no brigade by the word ("6 lička", "2.dalmatinska", "17 majevička",
# "1.četa 2.bat."): no place (a unit's record lent it before the rule; in the census's parts build_ostali_borci makes it
# the record's sub-unit)
UNIT_COLUMN = re.compile(r'^\s*\d+\s*\.?\s*(?:prolet|dalm|lič|kraj|kraišk|majev|moslav|slavon|vojv|vovođ|banij|banin|kordun|udarn|'
                         r'primorsk|hercegov|bosan|crnog|sandž|srps|jugosl|goran|makedon|muslim|omlad|virovit|romanij|južnomor|'
                         r'srednjebos|srednjobos|armij|čet|bat\b|bat\.|batalj|voj\.)', re.I)
# what the scan left in a place (2026-11-03): a mark or a Cyrillic look-alike after it ("na Sutjesci .^", "u Zelengori . „да",
# "kod Pecke. _", "kod Suhe^ó"), a word's last letter cut off after a stray "i" or "u" of the bio ("kod Bakova i"), accents no
# name of these lands has ("Kalesijä", "Danìlovgrad", "kod Benderà"; foreign names keep theirs), letters spaced out ("Gaber j e",
# "G. Badanj a"), a stray mark for a comma ("Srba„ D. Lapac", "Pinosavi ~ Beograd"), a mark in a word ("Doljani· ma")
CYRILLIC_TAIL = re.compile(r'[\s.]+[^\s]*[Ѐ-ӿ][^\s]*$')
MARKS_TAIL = re.compile(r'(?:\s+[^\w\s()]+)+(?:\s*[^\W\d]?)$|\^\S{0,2}$')
STRAY_WORD = re.compile(r'\s+(?:[iuao]|[ÌÍ])$')
ACCENTS = str.maketrans('àèìòùäáéíüöÀÈÌÒÙÄÖÜ', 'aeiouaaeiuoAEIOUAOU')       # not ó, the scan's ć ("Suóuraj")
ACCENT_WORD = re.compile(r'\S*[àèìòùäáéíüöÀÈÌÒÙÄÖÜ]\S*')
# Љ and Њ a Cyrillic scan read so: "Pljevl>a", "Zren»anin", "A>uša" (Ljuša), "L>. nahija"
LJ_MARK = [(re.compile(r'(?<=[a-zčćžšđ])l[>»](?=[a-zčćžšđ])'), 'lj'), (re.compile(r'(?<=lj)[>»](?=[a-zčćžšđ])'), ''), (re.compile(r'(?<=[a-zčćžšđ])n[>»](?=[a-zčćžšđ])'), 'nj'),
           (re.compile(r'\bA[>»](?=[a-zčćžšđ])'), 'Lj'), (re.compile(r'\bL[>»](?=[.a-zčćžšđ])'), 'Lj'),
           (re.compile(r'(?<=[a-zčćžšđ])l[>»]$'), 'lj')]
# the bio's words the reader took along, what is left of them at a place's end
AFTER_PLACE = re.compile(r',?\s+(?:u kome je|u kojoj je|na čijem je groblju|gdje je|gde je|krajem|početkom|sredinom|polovinom|kod|u|na|tu)$')
# a place of death's other words: the grave, the wound, what he was, the month of the date (in small letters: "u Maju" is a village's)
DEATH_PHRASE = re.compile(r',?\s+(?:odnesen kući|tu je|prenijet|(?:na|u) (?:čijem|kome|kojoj|kojem) je\b.*|gdje je\b.*|gde je\b.*|\(teško ranjen\)|kao bombaš|kao sekretar\b.*|'
                          r'prilikom zloglasne\b.*|za vrijeme ofanzive\b.*|radi učešća\b.*|od muslimanskog\b.*|u bolma|'
                          r'(?:januar|februar|mart|april|jun|jul|avgust|septemb[a]?r|oktob[a]?r|novemb[a]?r|decemb[a]?r)a?\.?)$')
FOREIGN_ACCENTED = {'Lucerà', 'Köln', 'Schönau', 'Köflach', 'Nürnberg', 'Mörs', 'Römengrund', 'Hühnerkogel', 'Göns', 'Czurgö', 'Muhovë'}
# a word's end set apart by the scan: "Gaber j e", "Litij i", "Doboj a", "Austrij a", "Postoj na", "Liv na"
SPACED = [(re.compile(r'(?<=\w)\s+j\s+([aei])\b'), r'j\1'), (re.compile(r'(?<=[nl]j)\s+a\b'), 'a'),
          (re.compile(r'(?<=[oi]j)\s+([ai])$'), r'\1'), (re.compile(r'\b(Postoj|Liv|Bar) na$'), r'\1na'), (re.compile(r'\bPia na$'), 'Plana')]
# a place's end in the scan's "^" for a lost letter, a Cyrillic list's Љ read "l." (the census's "Sl.orahovica", "Vel.ivanec" are abbreviations)
CARET_WORDS = {'Kr^ljevo': 'Kraljevo', 'Kral^evo': 'Kraljevo', 'Koso^o': 'Kosovo', 'Valjev^': 'Valjevu', 'Grab^': 'Grabu',
               'Kl.uč': 'Ključ', 'Pol.ana': 'Poljana', 'Pol.a': 'Polja', 'Pljevl.a': 'Pljevlja', 'Sovl.ak': 'Sovljak', 'Trebal.evo': 'Trebaljevo', 'Pel.iešc': 'Pelješac', '1 [l.evl.a': 'Pljevlja'}
# a place's bracket the text ended before closing: a note ("(teško ranjen", "(nepoznato", "(man") goes, a place is closed
BRACKET_NOTE = re.compile(r'^(?:teško|javno|nepoznato|nije\b|man$|po kazivanjima|vjerovatno$|verovatno$|[A-Za-zČĆŽŠĐčćžšđ]$|$|[^A-Za-zČĆŽŠĐčćžšđ])', re.I)
# an abbreviation at a place's end keeps its full stop: "Lovrenc na Poh.", "Otočec pri N. m.", "Fužine Lj."
ABBREVIATED_END = re.compile(r'(?:\b(?:na|pri|ob) (?:Gor|Dol|Poh|Štaj|Kor|Kr|Pr)|\bpri N\. m|\bFužine Lj|, Rom|\bReggio C)$')
# the census's column, cut at its width: a region's name it lost the end of ("Durmitor crna g", "Kasuni-gorski k", "Soko b")
CUT_REGION = [(re.compile(p, re.I), r) for p, r in (
    (r'^skopska crna g\.?$', 'Skopska Crna Gora'),
    (r'[-\s,]+(?:crna g|c\.\s?g)\.?$', ', Crna Gora'), (r'^crna g\.?$', 'Crna Gora'),
    (r'[-\s,]+bi?\s?i?\s?h$', ', BiH'), (r'^b\s?i\s?h$', 'BiH'),
    (r'\bsoko b\.?$', 'Sokobanja'), (r'[-\s,.]+(?:banja l|b\.l)\.?$', ', Banja Luka'),
    (r'[-\s,]+gorski k\.?$', ', Gorski Kotar'), (r'\bvišnja g\.?$', 'Višnja Gora'), (r'\bkulen v\.?$', 'Kulen Vakuf'),
    (r'[-\s,]+sl\.\s?p\.?$', ', Slavonska Požega'), (r'[-\s,]+sl\.\s?b\.?$', ', Slavonski Brod'),
    (r'\bpetrovo s\.?$', 'Petrovo Selo'))]


def scan_marks(value: str, birth: bool = False) -> str:
    """a place of birth or death without what the scan left in it"""
    v = value
    for word, new in CARET_WORDS.items():
        v = v.replace(word, new)
    if re.search(r'[A-Za-z]', v):
        v = CYRILLIC_TAIL.sub('', v)
    v = MARKS_TAIL.sub('', v)
    v = re.sub(r',?\s+nosilac\b.*$', '', v)
    for pattern, new in LJ_MARK:
        v = pattern.sub(new, v)
    v = re.sub(r'(?<=[a-zčćžšđ])\\/?(?=[a-zčćžšđ])', 'u', v)                         # "Zem\\n", "V\\/kovar"
    v = re.sub(r'(?<=\w)-{2,}\s*(?=\w)', '-', v)                                      # "Krilo--Jesenice", "Han--Pijesak"
    v = re.sub(r'\bSI\.(?=\s*[A-ZČĆŽŠĐ])', 'Sl.', v)                                     # "SI. Brod", "SI. Požega": the scan's I for l
    # a word broken at a line's end with the scan's specks after the hyphen: "Ko-\" lašin", "Ra-! stuša", "Pu~ lac"
    v = re.sub(r'(?<=[a-zčćžšđ])[-–—~_]\s*[^\w\s()\-–—]+\s*(?=\w)', '', v)
    if birth or re.match(r'(?:kod|na|u|kraj|pri|s\.|sela|selu)\s', v, re.I):
        # a word broken at a line's end: "Trboü- nje", "Budin- šćina", "kod Ko- sovske Mitrovice" (the census's column names no preposition)
        v = re.sub(r'(?<=[a-zčćžšđ])[-–—~_]\s+(?=[a-zčćžšđ])', '', v)
    else:
        # the census's column: the place and its općina, "Račić- bihać", "Hum- buzet"
        v = re.sub(r'\bZelen-\s+gora\b', 'Zelengora', v)
        v = re.sub(r'\bIvan-\s+(planin|sedl)', r'Ivan-\1', v)
        v = re.sub(r'(?<=[a-zčćžšđ])-\s+(?!u\b|na\b|kod\b)([a-zčćžšđ])(?=[a-zčćžšđ]{2})', lambda m: ', ' + m.group(1).upper(), v)
    # a ship ("Brod \"Cetinje\"", "brod „Drava\"", the Cetinje of Boka's fallen): one form
    v = re.sub(r'''^[Bb]rod\s*[„"»]\s*(\w+)\s*[“”"'«\\]*$''', r'Brod »\1«', v)
    # a quote with no other side
    if sum(v.count(q) for q in '"“”„') == 1:
        v = re.sub('["“”„]', '', v)
    if v.count('»') != v.count('«'):
        v = v.replace('»', '').replace('«', '')
    v = re.sub(r'[*>_|]+$', '', v)
    v = re.sub(r'\s{2,}', ' ', v).strip()
    v = re.sub(r'\s+\)', ')', v)
    v = re.sub(r'(?<=\w)·\s*', '', v)
    v = re.sub(r'(?<=\w)„(?=\s)', ',', v)
    v = re.sub(r'\s+~\s+', ', ', v)
    v = re.sub(r'\b([A-ZČĆŽŠĐ])!\s', r'\1. ', v)
    for pattern, new in SPACED:
        v = pattern.sub(new, v)
    v = ACCENT_WORD.sub(lambda m: m.group(0) if m.group(0).strip(',.') in FOREIGN_ACCENTED else m.group(0).translate(ACCENTS), v)
    if not re.match(r'između\b', v, re.I):
        for _ in range(2):
            v = STRAY_WORD.sub('', v).strip(' ,;.!')
            v = AFTER_PLACE.sub('', v)
            if not birth:
                v = DEATH_PHRASE.sub('', v)
    v = v.strip(' ,;.!')
    if v.count('(') == v.count(')') + 1:
        head, _, inner = v.rpartition('(')
        inner = inner.strip(' \\,;.')
        v = head.rstrip(' ,;') if BRACKET_NOTE.match(inner) else f'{head.rstrip()} ({inner})'
    if ABBREVIATED_END.search(v):
        v += '.'
    if re.search(r'\bBiH$', v) and not re.search(r'[,-]\s*BIH$', v):
        return v
    v = re.sub(r'\bkod bih$', 'kod Bihaća', v)
    for pattern, new in CUT_REGION:
        v2 = pattern.sub(new, v)
        if v2 != v:
            v = v2
            break
    return v


# a Cyrillic list's scan read Љ as "l," (the Spomenica crnogorskim antifašistima, Prilog u krvi): the places it spoiled so
LJ_SCAN = {'Bol,anići': 'Boljanići', 'Pol,a, Mojkovac': 'Polja, Mojkovac', 'Pl,evlja': 'Pljevlja', 'Pol,ska': 'Poljska',
           'Šl,ivovica': 'Šljivovica', 'Gornje G1ol,e': 'Gornje Polje'}
LJ_SCAN_RE = re.compile('|'.join(re.escape(k) for k in sorted(LJ_SCAN, key=len, reverse=True)))
# "Šid, godine", "u Dubrovniku iste godine", "na Prozor .^godine": the bio's "godine" after the place
YEAR_WORD_TAIL = re.compile(r"[\s,.^'?!-]*(?:iste\s+)?godine\.?$")
# the Slovene census's part of a town: "Maribor (del), Maribor-Center", "Vrhe (del), Trbovlje"
PART_OF = re.compile(r'\s*\((?:del|dio|deo)\)')


# places read from the page or the entry where no rule tells them (2026-11-03), as they stand after the rules or as printed; '' is no place
PLACE_READ = {
    # birth
    'Borovak pri Litij': 'Borovak pri Litiji', 'Gradec pri Litij': 'Gradec pri Litiji',
    'Matenja vas, Postoj': 'Matenja vas, Postojna', 'Rakitnik, Postoj': 'Rakitnik, Postojna', 'Trnje, Postoj': 'Trnje, Postojna',
    'V. Bar': 'V. Barna', 'Trnovče, Velika Pia': 'Trnovče, Velika Plana', 'Gor. Majur, Badlj evina, Pakrac': 'Gor. Majur, Badljevina, Pakrac',
    'Krilo-Jeseni ce, Omiš': 'Krilo-Jesenice, Omiš', 'Knlo-Jesenice, Omiš': 'Krilo-Jesenice, Omiš', 'Dežanovac, Trojef glava, Daruvar': 'Dežanovac, Trojeglava, Daruvar',
    'Hrat stovsko, Ludbreg': 'Hrastovsko, Ludbreg', 'Kaštei Novi, Split': 'Kaštel Novi, Split', 'Kotoi Varoš, Kotor-Varoš': 'Kotor-Varoš',
    'Botoš, Zre-njanin': 'Botoš, Zrenjanin', 'Ranilović, Aranđe-lovac': 'Ranilović, Aranđelovac', 'BravsJ-Bos. Petrovac': 'Bravsko, Bos. Petrovac',
    'Jadriei, Ribnik': 'Jadrići, Ribnik', 'Jasenica, Bosansea Krupa': 'Jasenica, Bosanska Krupa', 'Mrkotie, Tešanj, Doboj': 'Mrkotić, Tešanj, Doboj',
    'Kraljevoi, Ruma': 'Kraljevci, Ruma', 'Prvanselo, Perušić': 'Prvan Selo, Perušić', 'Doljani Žumbcracki Ozalj': 'Doljani Žumberački, Ozalj',
    'Stepojevac, Lazarcvac': 'Stepojevac, Lazarevac', 'Čibutkovica LaZarcvac': 'Čibutkovica, Lazarevac', 'Grčac, Smeđercvska Palanka': 'Grčac, Smederevska Palanka',
    'Bašin, Smeđerevska Palanka': 'Bašin, Smederevska Palanka', 'Schvage, Malme, Svcdska': 'Schvage, Malme, Švedska', 'Slope, Sczana': 'Slope, Sežana',
    'Gračanica, SRÉiH': 'Gračanica', 'Gračanica, SReiH': 'Gračanica', 'GDrugovac, Smederevo': 'Drugovac, Smederevo', 'Koceljevo, Vladimir': 'Koceljevo, Vladimirci',
    'Donji Vakuf, BiH, Musliman': 'Donji Vakuf, BiH', 'Konjščina, Zabok, Hrvatica': 'Konjščina, Zabok', 'Ašanja (nema drugih podataka)': 'Ašanja',
    'Hrvat': '', 'Srpkinja': '', 'Trbovlje Zakelj Alojz': 'Trbovlje', 'TrbovUe': 'Trbovlje', 'Trbov-. Ue': 'Trbovlje', 'Tuzla. u Beogradu od 1938': 'Tuzla', 'Rijeka, moler': 'Rijeka',
    'Dal': 'Dalj', 'Rosulje, Dvor na UHII': 'Rosulje, Dvor na Uni', 'Srpske Moravice, Del': 'Srpske Moravice, Delnice', 'Stanišićima %, De': 'Stanišići, Budva',
    'Ščedna, Trst. italij': 'Ščedna, Trst, Italija', 'Ščedna, Trst. italija': 'Ščedna, Trst, Italija', 'Sto-Borci Sutjeske lac': 'Stolac', 'Stankovci, Benkoac': 'Stankovci, Benkovac',
    'Stašeica, Ploče': 'Stašević, Ploče', 'Medenom Polju Bosanski Petrovac': 'Medeno Polje, Bosanski Petrovac', 'Donjoj Gorev-NICR': 'Donja Gorevnica', 'Gornjoj VrbavR': 'Gornja Vrbava',
    'Gornja s Kupinovica, Leskovac': 'Gornja Kupinovica, Leskovac', 'Progar, Zemuln': 'Progar, Zemun', 'Vitez g': 'Vitez', "Trnjaci, Bijeljina'": 'Trnjaci, Bijeljina',
    'Stanislav (SZ': 'Stanislav (SSSR?)', 'Stanislav (SZ)': 'Stanislav (SSSR?)', 'Stanislav (SZ ?)': 'Stanislav (SSSR?)', 'Čelebić (Liva': 'Čelebić (Livno?)', 'Čelebić (Liva)': 'Čelebić (Livno?)',
    'Čelebić (Liva. ..?)': 'Čelebić (Livno?)', 'Češnjice (na Dolenjskem': 'Češnjice (na Dolenjskem?)', 'Češnjice (na Dolenjskem)': 'Češnjice (na Dolenjskem?)', 'Češnjice (na Dolenjskem ?)': 'Češnjice (na Dolenjskem?)',
    'Srem-( ska Mitrovica': 'Sremska Mitrovica', 'Gornji (avoranj, Dvor': 'Gornji Javoranj, Dvor', 'Gornji (avoranj), Dvor': 'Gornji Javoranj, Dvor', 'Veliko Laole v(i!.:<xi': 'Veliko Laole', 'Veliko Laole v(i!.:<xi)': 'Veliko Laole',
    'Podgorici (TitogradJ': 'Podgorica (Titograd)', 'Podgorici (TitogradJ)': 'Podgorica (Titograd)', 'Naglušicama (BosnaJ': 'Naglušice (Bosna)', 'Naglušicama (BosnaJ)': 'Naglušice (Bosna)', 'Donja Gorica (Lješ': 'Donja Gorica', 'Donja Gorica (Lješ)': 'Donja Gorica',
    'LJupten': 'Ljupten', 'LSSOVAC': 'Lasovac, Bjelovar', 'Tppnipp': '', 'StjApana': 'Kozarevac, Nova Rača, Bjelovar', 'X3ahec,Travarsko': 'Kravarsko', 'Oratje-Krap': 'Oratje, Krapinske Toplice, Zabok',
    'Ldska-Kotlenice, Split': 'Kotlenice, Split', 'Prisloici': 'Prislonica', 'Ljuiću': 'Ljubić', 'Berčinovcu. zešoradnik': 'Berčinovac', 'Šipćonu, Rijeka Crpojsvića, Eta': 'Šipčanik, Rijeka Crnojevića',
    'Prvoj Čađavici, Bosanski Novi, Bosna iHercegovina': 'Prva Čađavica, Bosanski Novi', 'I vanji grad': 'Ivanji grad', 'I van j i grad': 'Ivanji grad',
    # places of birth and of death the scans garbled, read from the entry (2026-11-03)
    'OrjaLuka, Danilovgrad': 'Orja Luka, Danilovgrad', 'PoJBa, Mojkovac': 'Polja, Mojkovac', 'u selu JBubi, Ilok': 'u selu Ljubi, Ilok', 'kod JTipovca, Sremski front': 'kod Lipovca, Sremski front', 'u JTivnu': 'u Livnu',
    'Brančić, JBig': 'Brančić, Ljig', 'Liplje, JBig': 'Liplje, Ljig', 'Adaševci, JPid': 'Adaševci, Šid', 'u Ča/mi': 'u Čazmi', 'G. VranjiSka': 'G. Vranjska', 'Bijeljiii': 'Bijeljina', 'Đurđevik, Živiiice': 'Đurđevik, Živinice',
    'UbliKuči, Podgorica': 'Ubli Kuči, Podgorica', 'PrimoSten, Šibenik': 'Primošten, Šibenik', 'Sedlari.ma': 'Sedlarima', 'Komljinsk, SSSR. Pye': 'Komljinsk, SSSR', 'Široki brijeg m': 'Široki Brijeg', 'Krčedin, InđiJa': 'Krčedin, Inđija', 'Sjeničak l': 'Sjeničak',
    'Podturn pri DoL Toplicah': 'Podturn pri Dol. Toplicah', 'Dolenjske Toylice': 'Dolenjske Toplice', 'Čestelin kodVranja': 'Čestelin kod Vranja', 'pohodu 14. divizije na Štajersko': '', '4 ofanziva': '', '5 ofanziva': '', '7 ofanziva': '', 'U 5 ofanzivi': '', '5.ofanziva': '',
    'U bosni 5.ofanz': 'Bosna', '19div': '', '1dal.bri': '', 'X+': '', 'Crna gora 4.of': 'Crna Gora', 'Unska operat.grupa': '', 'Štajerska (2.UB.)': 'Štajerska', 'Rakovec (13.B.)': 'Rakovec',
    # the odd values read one by one against their entries (2026-11-04)
    'sremski front': 'Sremski front', 'štajerska': 'Štajerska', 'centralna bolnica (od Pive do Sutjeske)': 'Centralna bolnica (od Pive do Sutjeske)', 'strijeljana': '',
    'žiri': 'Žiri', 'delavec': '', 'pog. zadatku': '', 'nestao': '', 'kapelska pruga': 'Kapelska pruga', 'željeznička pruga': '',
    'kapelska pruga kod Javornika': 'Kapelska pruga kod Javornika', 'boiRudište': 'Rudište', 'Bistrica 21': 'Bistrica', 'iKatanići': 'Katanići',
    '4.jedinica u borbama': '', 'U 5. ofanzivi': '', 'b.polje': 'Bijelo Polje', 'borije kalinov': 'Borije, Kalinovik', 'osl,bileće': 'Bileća', 'Centarl 3. i 12. kor': '',
    'idrija-c.vrh': 'Idrija', 'boju 14. divizije': '', 'območju Zg. Vrtače —Borje nad Izlakami': 'Zg. Vrtače — Borje nad Izlakami', 'verjetno na pohodu proti Savi': '',
    'območju Kolovrata': 'Kolovrat', '/45 pri Dravograđu': 'pri Dravogradu', 'bolnišnici v Celju': 'Celje', '/45, Kot nad Oplotnico': 'Kot nad Oplotnico',
    '/45 na preboju iz sovražnikove ofenzive v Savinjski dolini': 'Savinjska dolina', 'goreči šoli v Šoštanju': 'Šoštanj',
    'poti iz bolnišnice Košuta na Pohorju': 'Pohorje', '/45 v okolici Dramelj': 'okolica Dramelj', 'pohodu 14. divizije na Štajerskem': 'Štajerska',
    '/45, Trojane': 'Trojane', 'območju Paški Kozjak —Pohorje na pohodu 14. divizije': 'Paški Kozjak — Pohorje', '/44; kraj ni ugotovljen': '',
    'Štajerskem v nemški ofenzivi proti 14. diviziji': 'Štajerska', 'ali 1945 na Štajerskem': 'Štajerska', 'g u kovje pri Slivnici, Šentjur': 'Slivnica, Šentjur',
    'ali januarja 1944 v Zgornji Savinjski dolini': 'Zgornja Savinjska dolina', '-1945, Kupusine (AOSJ, Beograd)': 'Kupusine',
    'hrib Srnjak pri Rakeku': 'Srnjak pri Rakeku', 'bolnišnici pri Solčavi': 'Solčava', '/45 na Konjiški gori': 'Konjiška gora', '/45 neznano kje': '',
    '— 1945 v Savinjski dolini': 'Savinjska dolina', '/45 v Savinjski dolini ali na Pohorju': 'Savinjska dolina',
    '/45, Zgomje Slemene, Dramlje': 'Zgornje Slemene, Dramlje', 'Nova Štifta 2': 'Nova Štifta', 'Lindek (13.B.)': 'Lindek',
    'Perkos pri Grahovem (2.UB.)': 'Perkos pri Grahovem', 'Štajerska (13.B.)': 'Štajerska', '2.č.1.bat.5.br.14.d': '',
    'prema Trebavirejon Gračanice': 'Trebava, Gračanica', 'Jast. 1944': 'Jastrebarsko', 'lvanska': 'Ivanska', 'U 5-oj ofanzivi': '', 'ncznanokjc': '', 'ncznanokje': '',
    'umro od batina': '', 'j Morinj': 'Morinj', '1944. Italija': 'Italija', 'izgorjela': '', 'mehanik': '', 'dijak': '', '2. k. v': '', 'poginuo': '', 'Poginuo': '',
    '11onikvice': 'Ponikvice', 'zdravnik': '', 'ustreljen od Nemcev': '', '1 Borča': 'Borča', 'šivilja': '', 'Bosn. b. 4 batebijeljina': 'Bijeljina', '1 Jrevina': '',
    'bijedići': 'Bijedići', 'ubijena': '', 'š.kula gospić': 'Široka Kula, Gospić', 'istok': 'Istok', '3 kralja klanje': '', 'prelazak preko Zete': 'Zeta',
    'Zelenika 1': 'Zelenika', 'ist. Bosna': 'Istočna Bosna', 'Strahovi D<': 'Strahov Do', '5. kozarska ofanziva': '', 'pogre šan': '', 'loznica': 'Loznica',
    'tromeđa S. C. G. B': '', '5ofanziva': '', 'frutak': 'Frutak', 'štatenber ška dolina pri Novem mestu': 'Štatenberška dolina pri Novem mestu',
    'umro u Buronjima': 'Buronji', 'saveznički brod': '', 'črni vrh': 'Črni Vrh', 'njemački logor': '', 'štatemberg': 'Štatenberg', '1 9 2 0 - 1 9 4 4': '',
    '5of. na sutjesci 2da': 'Sutjeska', 'aprilski rat': '', '1 9 2 4 - 1 9 4 4': '', 'pozadinski rad': '', 'đule': 'Đule', 'žabja vas': 'Žabja vas', 'koncen. logor': '',
    'Zuri J1. rijeka': '', '1': '', 'zak. "Crna ruka"': '', 'umro od mučenja': '', '1 9 2 5 - 1 94 5': '', '1 crn.knoj': '',
    'teško ranjen kod Šarengrada, preminuo u bolnici': 'Šarengrad', 'križišče Mala lažna—Mrzla rupa': 'Mala Lažna — Mrzla Rupa', 'goriški grad': 'Goriški grad',
    'goriška fronta': 'Goriška fronta', 'goriški fronti': 'Goriška fronta', 'štalcerji, Kočevje': 'Štalcerji, Kočevje', 'sv. Katarina, Reka': 'Sv. Katarina, Rijeka',
    'žab j ak, Livno': 'Žabljak, Livno', 'črna gora': 'Crna Gora', 'Sutjeska-5.ofan': 'Sutjeska', 'padel RCEV IX. SNOB KOČ': '', 'J5ri kota': '', 'Kao kurir nov': '',
    'od bombardovanja': '', 'za posledicami ran, dobljenih v boju': '', 'na Pelješc': 'Pelješac', 'na Sremskom frontu. kod Iloka': 'Sremski front, kod Iloka',
    'Crna gora': 'Crna Gora', 'Crna gora-': 'Crna Gora',
    # the census's place column as its table first wrote it (2026-11-03: a reader's value caught by the joined-parts rule)
    'Žljebova': 'Žljebovi', 'Kopito, Žljebova': 'Kopito, Žljebovi', 'Pljevlje': 'Pljevlja', 'Podromanije Sokolac': 'Podromanija, Sokolac', 'Dubovik, Bos. Kru': 'Dubovik, Bos. Krupa', 'Kamensko, D. Lapa': 'Kamensko, D. Lapac', 'Čadžavica, B. Nov': 'Čadžavica, B. Novi', 'Pirit- u bolnici': 'Pirit', 'Tounj-na Pruzi': 'Tounj', 'Šolta-na brodu': 'Šolta',
    'Nar.bol.pljevlj': 'Pljevlja', 'Nepoz.partizan.jed': '', 'Boln.u zagrebu': 'Zagreb', 'Darča.na.dravi': 'Darda na Dravi', 'Lon.kod kolašin': 'kod Kolašina', 'Okr.g.milanovac': 'G. Milanovac', 'Polja.radulo.kr': '', 'S.grliš.srez za': 'Grliš', 'St.sl.vi.kopriv': '',
    'Brdce, Ilir, Ska Bistrica': 'Brdce, Ilirska Bistrica', 'Dubrovčak, Ivanić, grad': 'Dubrovčak, Ivanić-Grad', 'Ovčarevo, Mlinište, Mrkonjić, grad': 'Ovčarevo, Mlinište, Mrkonjić-Grad', 'Beli Potok, širi rejon Knjaževca, Protiv bugarskih fašista': 'Beli Potok, širi rejon Knjaževca',
    'Doborovci, okolina Gračanice, Protiv Nemaca': 'Doborovci, okolina Gračanice', 'Drljača, Na pravcu prema Rogačici': 'Drljača', 'Topalovićiširi rejon Gračanice, Protiv četnika': 'Topalovići, širi rejon Gračanice', 'Boln. U zagrebu': 'Zagreb', 'Br. Braće radića': '', 'Darča. Na.dravi': 'Darda na Dravi', 'Kom. Mesta bihać': 'Bihać',
    'Lon. Kod kolašin': 'kod Kolašina', 'Nar. Bol.pljevlj': 'Pljevlja', 'Nepoz. Partizan.jed': '', 'Okol. Trsta istr': 'okolina Trsta, Istra', 'Okr. G.milanovac': 'G. Milanovac', 'Polja. Radulo.kr': '', 'S. Grliš.srez za': 'Grliš', 'St. Sl.vi.kopriv': '', 'Crkvice, Crna gora': 'Crkvice, Crna Gora', 'C. Gora sutjeska': 'Crna Gora, Sutjeska',
    'Kolov, Venecija italija': 'Kolov, Venecija, Italija', 'Trnovo Sarajevo': 'Trnovo, Sarajevo', 'Ckara. Mojkovac': 'Ckara, Mojkovac', 'Zag. Danilovgrad': 'Zagarač, Danilovgrad', 'Š. Polje no.mest': 'Š. Polje, Novo Mesto', 'Drljača-na pravcu prema Rogačici': 'Drljača',
    'Beli Potok, širi rejon Knjaževca-protiv bugarskih fašista': 'Beli Potok, širi rejon Knjaževca', 'Doborovci, okolina Gračanice-protiv Nemaca': 'Doborovci, okolina Gračanice', 'Topalovićiširi rejon Gračanice-protiv četnika': 'Topalovići, širi rejon Gračanice', 'Brdce, Ilir-ska Bistrica': 'Brdce, Ilirska Bistrica',
    'Dubrovčak, Ivanić-grad': 'Dubrovčak, Ivanić-Grad', 'Ovčarevo, Mlinište, Mrkonjić-grad': 'Ovčarevo, Mlinište, Mrkonjić-Grad',
    # death
    'Obješen u, Desinec': 'Desinec', 'u Istoku (?)': 'Istok (?)', 'u Badovincima (?)': 'Badovinci (?)', 'na -drumu (?)': 'na drumu (?)', 'Zelen gord': 'Zelengora',
    'u Zi vaji kod Sunje': 'u Živaji kod Sunje', 'u Zi va j i kod Sunje': 'u Živaji kod Sunje', 'kod Ko, Sovske Mitrovice': 'kod Kosovske Mitrovice', 'kod Jas, Trepca, Vlasotince': 'kod Jastrepca, Vlasotince', 'kod Li, Povca na Sremskom frontu': 'kod Lipovca na Sremskom frontu',
    'kod sela Čo, Kotina, Oruglica, Jablanica': 'kod sela Čokotina, Oruglica, Jablanica', 'Postoj': 'Postojna', 'kod Liv': 'kod Livna', 'kod Poloj': 'kod Poloja',
    'kod Vila Vrhovski kod Doboj': 'kod Vila Vrhovski kod Doboja', 'na Becnju kod Doboj': 'na Becnju kod Doboja', 'na Bender': 'na Benderu', 'u Novom Marof': 'u Novom Marofu', 'u Počitelj': 'u Počitelju',
    'u Staroj Krši j': 'u Staroj Kršlji', 'u Staroj Kršiji': 'u Staroj Kršlji', 'M athauzen-Austrij': 'Mauthausen, Austrija', 'M athauzen-Austrija': 'Mauthausen, Austrija',
    'TrnovecN abnežina': 'Trnovec, Nabrežina', 'Trnovec—<N abnežina': 'Trnovec, Nabrežina', 'Vraboe': 'Vrabče', 'Vraböe': 'Vrabče', 'u Beograeu': 'u Beogradu', 'u CerovR': 'u Cerovi', 'u s. Bujavica kod PakraCa': 'u s. Bujavica kod Pakraca',
    'kod Nove Kapc lc': 'kod Nove Kapele', 'kod PitOKLaCG': 'kod Pitomače', "kod RaKOB'a": 'kod Rakova', 'na Suisci': 'Sutjeska', 'Xisle bitke na Sutjesci': '', 'na Zelengori ia': 'na Zelengori',
    'na Neretvi februar— —- član SKOJ': 'na Neretvi', 'na Kozari u bolma': 'na Kozari', 'u Rošcima pecemboa': 'u Rošcima', 'u Prekornici N Ljubotinskoj Kao sekretar MjesHor komiteta KPJ Bar': 'u Prekornici Ljubotinskoj',
    'na Dučinskoj kooi Leska': 'na Dučinskoj kosi Leska', 'u Zelengorikod Foče': 'u Zelengori kod Foče', 'u Topčić-polju,centralna Bosna': 'u Topčić-polju, centralna Bosna',
    'Odreda negde u Slepčeviću (podaci iz Hronike Grušića)': 'Slepčević', 'u NOV. Mesto i vreme pogibije nepoznato (verovatno poginula)': '', 'u NOV. (nepoznato': '', 'u NOV. (nepoznato)': '', 'u NOV': '',
    'Tu je': '', 'Obješen': '', 'Centralne bolnice': '', 'V. korpusa': '', 'u Jajincima . gom/me': 'u Jajincima', 'u Istočnoj Bosni . na području Ireštenica - Banovići': 'u Istočnoj Bosni, na području Treštenica - Banovići',
    'u kanjonu Tare . kod sela Tepca': 'u kanjonu Tare, kod sela Tepca', 'Ugljevik, Biljeljina': 'Ugljevik, Bijeljina', 'Inkuša, Otrić Gracsc': 'Inkuša, Otrić, Gračac', 'D. Caglio': 'D. Čaglić',
    'kod Tovartnika': 'kod Tovarnika', 'Sremski front, kod lovarnika': 'Sremski front, kod Tovarnika', 'na Batinskoj Skeli, kod Beiog Manastira': 'na Batinskoj Skeli, kod Belog Manastira',
    'u Konjevićima (Cacak)': 'u Konjevićima (Čačak)', 'u Mojsinju (Cacak)': 'u Mojsinju (Čačak)', 'u Brzeću, na Kopaonihi (Brus)': 'u Brzeću, na Kopaoniku (Brus)', 'žužcmbc1k': 'Žužemberk', 'žužcmbc1·k': 'Žužemberk',
    'Gračanica, Tuzl': 'Gračanica, Tuzla', 'Miljakovac, Prijedor, puskomuraljezac': 'Miljakovac, Prijedor', 'Oštrelj, Bosanski Petrovac, komandu Voda': 'Oštrelj, Bosanski Petrovac',
    'Orežnik kod, BiH': 'Orežnik kod Bihaća', 'Zavalje kod, BiH': 'Zavalje kod Bihaća', 'Tromeđa bih, Crna Gora': 'Tromeđa BiH, Crna Gora', 'kod Sjetline, na pruzi Sarajevo-Višegrad, IS': 'kod Sjetline, na pruzi Sarajevo-Višegrad',
    'kod Šib( nika': 'kod Šibenika', 'kod Šib( nika)': 'kod Šibenika', 'Strahovi D(': 'Strahovi', 'Strahovi D': 'Strahovi', 'Gornjane bor(ru': 'Gornjane, Bor', 'Gornjane bor(ru)': 'Gornjane, Bor', 'Stričići, na Manjači (Klju': 'Stričići, na Manjači (Ključ)',
    'Stričići, na Manjači (Klju)': 'Stričići, na Manjači (Ključ)', 'Stričići, na Manjači (Klju^': 'Stričići, na Manjači (Ključ)', 'u Donjim Magnojevićima (Bij': 'u Donjim Magnojevićima (Bijeljina)', 'u Donjim Magnojevićima (Bij)': 'u Donjim Magnojevićima (Bijeljina)',
    "u Donjim Magnojevićima (Bij^'tó": 'u Donjim Magnojevićima (Bijeljina)', 'u Brčelima (Crmni': 'u Brčelima (Crmnica)', 'u Brčelima (Crmni)': 'u Brčelima (Crmnica)', 'u Celini (Sjetlini': 'u Celini (Sjetlini?)', 'u Celini (Sjetlini)': 'u Celini (Sjetlini?)',
    'u Celini (Sjetlini ?)': 'u Celini (Sjetlini?)', 'kod Vlasotinca. (Po kazivanjima njegovih seljana poginuo': 'kod Vlasotinca', 'kod Ratkovog potoka (nije moglo da se utvrdi': 'kod Ratkovog potoka', 'u Bosni (vjerovatno': 'u Bosni',
    'u Bosni (vjerovatno)': 'u Bosni', 'u Samoboru (javno strijeljan': 'u Samoboru', 'na Lupcu kod Zenice (teško ranjen i umro': 'na Lupcu kod Zenice', 'na Lupcu kod Zenice (teško ranjen i umro)': 'na Lupcu kod Zenice',
    # villages the readers' reports of 2026-11-22 put right, spread to every record that prints the same slip where it is the same
    # place (task 40, 2026-11-23; only the village changes, the municipality stays as printed: the user's rule after Ninković)
    'Zavode': 'Zavođe', 'Zavode, Gospić': 'Zavođe, Gospić', 'Veliki Badić': 'Veliki Radić', 'Veliki Badić, Bosanska Krupa': 'Veliki Radić, Bosanska Krupa',
    'Smiljani': 'Smiljan', 'Metak, Gospić': 'Medak, Gospić', 'Metak, Lika': 'Medak, Lika', 'Banjane, Ub': 'Banjani, Ub',
    'Vrhovina, Otočac': 'Vrhovine, Otočac', 'Neprićava': 'Nepričava',
    # the 5. srpska's "Sindija" (Panić Zlatomir, Pavlović Slobodan): Sirdija of Osečina, as the census prints them (a
    # reader's report of 2026-11-23 08:01)
    'Sindija': 'Sirdija',
    # the Spomenica crnogorska prints the men of Štitari (Cetinje) under its Šavnik heading: the Lovćenski odred's list and a
    # reader's report of 2026-11-23 ("Štitari, srez Cetinjski, opština Cetinje") put them under Cetinje (18 records)
    'Štitari, Šavnik': 'Štitari, Cetinje',
    # the 20. srpska's scan reads Ć as B: "Buprija" is Ćuprija (a family's form of 2026-11-23, Milosavljević Ilija); 36 records,
    # the villages as printed
    'Krnjicc, Bar': 'Krnjice, Bar',   # a reader's report of 2026-11-23 (Pekić Boža Špiro)
    'Buprija': 'Ćuprija', 'Krušar, Buprija': 'Krušar, Ćuprija', 'Batinac, Buprija': 'Batinac, Ćuprija', 'Senje, Buprija': 'Senje, Ćuprija', 'Poljane, Buprija': 'Poljane, Ćuprija', 'Poljana, Buprija': 'Poljana, Ćuprija', 'Paljina, Buprija': 'Paljina, Ćuprija', 'Pločnik, Buprija': 'Pločnik, Ćuprija', 'Baginac, Buprija': 'Baginac, Ćuprija', 'Bigrenica, Buprija': 'Bigrenica, Ćuprija', 'Virine, Buprija': 'Virine, Ćuprija',
}


# for birthplaces only, each read against its entry: a form in a case or a scan's slip that may be a place's own name in a place of death or in another book
BIRTH_READ = {
    # the odd values read one by one against their entries (2026-11-04)
    'diplomirani': 'Subotica', 'građevinski': '', 'Ranjen': '', 'Kao': '', '1926': '', 'Viškovci, Đakovo i<': 'Viškovci, Đakovo',
    'Majskim Poljanama {Glina': 'Majske Poljane, Glina', 'Plina >točna, Ploče': 'Plina Istočna, Ploče', 'Gradačcu..Musliman': 'Gradačac',
    'Bijeljini.. Jugos loven': 'Bijeljina', 'Zlato | polje': 'Zlato Polje', 'Pošćanski kraj 1, Žabljak': 'Pošćanski Kraj, Žabljak', 'Belom Potoku}': 'Beli Potok',
    'đogmilovići, Danilovgrad': 'Bogmilovići, Danilovgrad', 'Plevlja 3, Pljevlja': 'Pljevlja', 'anilovgrad, Danilovgrad': 'Danilovgrad',
    'zaostro, Bijelo Polje': 'Zaostro, Bijelo Polje', 'uice, Šavnik': 'Šavnik', '1 Parci Lj. nahija, Podgorica': 'Parci, Lješanska nahija, Podgorica',
    'bijedići, Pljevlja': 'Bijedići, Pljevlja', 'Pl>evlja, Pljevlja': 'Pljevlja', '11ol.ska, Pljevlja': 'Poljska, Pljevlja', 'Ora^, Plužine': 'Orah, Plužine',
    'Po raspadu jugoslovenske vojske odveden aprila 1941. u zarobljeništvo Nemačku kao rezervni': '', 'I .... Lučanu': '',
    'Gornje Pole 3, Nikšić': 'Gornje Polje, Nikšić', 'Gornjem 3uiiču': '', 'Priče– Buy= omladinac': '', 'Bučju3': 'Bučje', 'mokra Njiva': 'Mokra Njiva',
    'Čevo1945. Bar, Šavnik': 'Čevo, Šavnik', 'Lipi Grcka], Cetinje': 'Lipa, Cetinje', 'Kraljevom Selu 1920': 'Kraljevo Selo', 'Bogo]evićima': 'Bogojevići',
    'Slovensko] mi, Kocevje': 'Kočevje', 'Belanovu[Severovici), Ludbreg': 'Belanovo (Severovići), Ludbreg', 'Ča_ Jetini': 'Čajetina', 'grac, Pljevlja': 'Grac, Pljevlja',
    'Šetoi>e': 'Šetonje', 'Češd>eva Bara': 'Češljeva Bara', 'črnomelj': 'Črnomelj', '_ Loka pri Žusmu': 'Loka pri Žusmu', 'Struw~': '',
    'Sela pri Vrbcah, Se>mit': 'Sela pri Vrbcah, Semič', '_ Velike Brusnice': 'Velike Brusnice', 'županje njive pri Stahovici': 'Županje Njive pri Stahovici',
    'Duplica__pri Kamniku': 'Duplica pri Kamniku', 'črna pri Stahovici': 'Črna pri Stahovici', 'študa pri Domžalah': 'Študa pri Domžalah',
    'đinovići, Cetinje': 'Đinovići, Cetinje',
    # the birthplaces first read on 2026-11-03 ("iz Briševa", "u Medjeđem Brdu"): a case nothing else reads, or too garbled to read ('')
    'Medjeđem Brdu, Sanica': 'Međeđe Brdo, Sanica', 'Samaričkim Brđanima (Dvor na Uni)': 'Šamarički Brđani (Dvor na Uni)', 'Šamaričkim Brđanima (Dvor na Uni)': 'Šamarički Brđani (Dvor na Uni)',
    'Brdu Vilenskom (Dvor na Uni)': 'Brdo Vilensko (Dvor na Uni)', 'Kuljenovcima, Derventa': 'Kuljenovci, Derventa', 'Donjem Zirovcu (Dvor na Uni)': 'Donji Žirovac (Dvor na Uni)', 'Briševa': 'Briševo', 'Ujevca': 'Ujevac',
    'Parževića, Sokolac': 'Parževići, Sokolac', 'Parževića': 'Parževići', 'Sara jeva': 'Sarajevo', 'Saraieva': 'Sarajevo', 'Donjem Javorju (Dvor na Uni)': 'Donje Javorje (Dvor na Uni)', 'Donjem Javomju (Dvor na Uni)': 'Donje Javorje (Dvor na Uni)',
    'Gornjim Petrovićima, Bosanska Krupa': 'Gornji Petrovići, Bosanska Krupa', 'Kumanima, Veliko Gradište': 'Kumani, Veliko Gradište', 'Donjim Lukavicama, Živinice': 'Donje Lukavice, Živinice', 'Gornjim Lukavicama, Valjevo': 'Gornje Lukavice, Valjevo',
    'Zapreščića': 'Zaprešić', 'Grčkog Islama': 'Grčki Islam', 'Gornjeg Islama': 'Gornji Islam', 'Nadića, Sokolac': 'Nadići, Sokolac', 'Pobrataca, Sokolac': 'Pobratci, Sokolac', 'Remšeniku, Železna Kapla': 'Remšenik, Železna Kapla',
    'Šmartnem, Slovenj Gradec': 'Šmartno, Slovenj Gradec', 'Smartnem, Slovenj Gradec': 'Šmartno, Slovenj Gradec', 'Suhaca, Sanski Most': 'Suhača, Sanski Most', 'Crnogorcima, Kamenmost': 'Crnogorci, Kamenmost', 'Rasovcu, Dživar, Trebinje': 'Rasovac, Dživar, Trebinje',
    'Beloparici': 'Beloparica', 'Ribarici, Tutin': 'Ribariće, Tutin', 'Gomjoj Stupnici (Dvor na Uni)': 'Gornja Stupnica (Dvor na Uni)', 'Majskim Poljanama ili Roviškoj (Glina)': 'Majske Poljane ili Roviška (Glina)', 'Brdu Plavšića (Dvor na Uni)': 'Brdo Plavšića (Dvor na Uni)',
    'Velikom Dvorištu, Bosanska Dubiea': 'Veliko Dvorište, Bosanska Dubica', 'Smoluču, Lukavac': 'Smoluća, Lukavac', 'Donjim Garevcima, Prijedor': 'Donji Garevci, Prijedor', 'Donjim Garevcima': 'Donji Garevci', 'Prnjavoru Velikom, Doboj': 'Prnjavor Veliki, Doboj',
    'Gornjim Štrpcima, Prnjavor': 'Gornji Štrpci, Prnjavor', 'Bašisovcima, Živinice': 'Bašigovci, Živinice', 'Molunama, Tuzla': 'Moluhe, Tuzla', 'Sumama, Topola': 'Šume, Topola', 'Gornjoj Gorjevnici, Čačak': 'Gornja Gorevnica, Čačak', 'Trebeškom Polju, Goražde': 'Trebeško Polje, Goražde',
    'Beranama (sada Ivangrad) u Crnoj Gori': 'Berane (sada Ivangrad)', 'Radiljeva': 'Radiljevo', 'Djelekovca': 'Đelekovec', 'Plitvičkim Jezerima': 'Plitvička Jezera', 'Miolića, Karlovac': 'Miolići, Karlovac', 'Sinđelića': 'Sinđelić', 'Vračevca': 'Vračevac',
    'Maričića, Kuršumlija': 'Maričići, Kuršumlija', 'Markovića, Kuršumlija': 'Markovići, Kuršumlija', 'Velkih Radinaca, Sremska Mitrovica': 'Veliki Radinci, Sremska Mitrovica', 'Pudinaca (Srem)': 'Putinci (Srem)', 'Vlasini': 'Vlasina', 'Ljubošini, Gomirje': 'Ljubošina, Gomirje',
    'Tulima': 'Tuli', 'Tulima, Zubci, Trebinje': 'Tuli, Zubci, Trebinje', 'Kraquievcu': 'Kragujevac', 'Kragu]evca': 'Kragujevac', 'Endrića, Sokolac': 'Endrići, Sokolac', 'Žvabeku, Pliberk': 'Žvabek, Pliberk', 'Donjem Pazarištu': 'Donje Pazarište', 'Medojevića, Sokolac': 'Medojevići, Sokolac',
    'Kanalski dolini': 'Kanalska dolina', 'Sočavi': 'Sočava', 'Šempolaju, Nabrežina': 'Šempolaj, Nabrežina', 'Sevastopolu': 'Sevastopolj', 'Vrabaca, Sokolac': 'Vrapci, Sokolac', 'Ivazovića, Sokolac': 'Ivazovići, Sokolac', 'Zavodnjah nad Šoštanjem': 'Zavodnje nad Šoštanjem',
    'Jastrepcima, Kog, Ljutomer': 'Jastrebci, Kog, Ljutomer', 'Kremenčaku': 'Kremenčak', "Koturic'u, Pakrac": 'Koturić, Pakrac', 'Ettendorfa v Labotski dolini': 'Ettendorf v Labotski dolini', 'Lesnom Brdu': 'Lesno Brdo', 'Goselni vasi na Koroškem': 'Goselna vas na Koroškem',
    'Slovenjem Plajberku': 'Slovenji Plajberk', 'Frkovcima (Vinkovci)': 'Frkovci (Vinkovci)', 'Padovića, Sokolac': 'Padovići, Sokolac', 'Padeškem vrhu na Pohorju': 'Padeški vrh na Pohorju', 'Han Krama (Vlasenica)': 'Han Kram (Vlasenica)', 'Haniću, Mačkovac': 'Hanić, Mačkovac',
    'Zlatoličju, Ptuj': 'Zlatoličje, Ptuj', 'Kostanjenici': 'Kostanjenica', 'Lieškom Polju, Titograd (Podgorica)': 'Lješkopolje, Podgorica', 'Trnjavcima, Ub, Srbije': 'Trnjavci, Ub', 'Kaca': 'Kać', 'Strassburgu na Koroškem': 'Strassburg na Koroškem', 'Pribiniču, Teslić, Doboj': 'Pribinić, Teslić, Doboj',
    'Pribiniču, Teslič': 'Pribinić, Teslić', 'Jarušicama': 'Jarušice', 'Obirskem, Železna Kapla': 'Obirsko, Železna Kapla', 'Obirskem': 'Obirsko', 'Legnu, Slovenj Gradec': 'Legen, Slovenj Gradec', 'Bohorini, Slovenskih Konjicah': 'Bohorina, Slovenske Konjice', 'Širijevića, Sokolac': 'Širijevići, Sokolac',
    'Nikiforovu, Gostivar': 'Nikiforovo, Gostivar', 'Knežaku na Notranjskem': 'Knežak na Notranjskem', 'Budanici (Virovitica)': 'Budanica (Virovitica)', 'Crnomlju': 'Črnomelj', 'Novi Cerkvi': 'Nova Cerkev', 'K umanovu': 'Kumanovo', 'Rojanu': 'Rojan', 'Plaznici, Beljak': 'Plaznica, Beljak',
    'Sovici, Jablanica': 'Sovići, Jablanica', 'Matavuza kod Sarajeva': 'Matavuz kod Sarajeva', 'Hrastovca': 'Hrastovac', 'Starih Andrijevaca': 'Stari Andrijevci', 'Ražljeva, Brčko': 'Ražljevo, Brčko', 'Zburga pri Kopru': 'Zburg pri Kopru', 'L. Lešću, Ličko Lešce': 'Ličko Lešće', 'D. Dolu, Dugi Do': 'Dugi Do',
    'Kostet Bregu, Pregrada': 'Kostel Breg, Pregrada', 'Velikoj Hrvatskoj': 'Velika Hrvatska', 'Donjem Milagaovcu': 'Donji Milanovac', 'Donjem Porvanu, Banja Luka': 'Donji Porvan, Banja Luka', 'Donjem Obodniku, Kotor-Varoš': 'Donji Obodnik, Kotor-Varoš', 'Kukici, Gornje Dubrave': 'Kukača, Gornje Dubrave',
    'Stipanu, Vrginmosl': 'Stipan, Vrginmost', 'Priboiu, T uzla': 'Priboj, Tuzla', 'malom istarskorrr selu Zarečju (Pazin)': 'Zarečje (Pazin)', 'Žalaberu (Češka)': 'Žalaber (Češka)', 'D. Lupljanici, Derventa': 'D. Lupljanica, Derventa', 'Nemcima, Sokolac': 'Nemci, Sokolac', 'Mjestu Vilusima, Nikšić': 'Vilusi, Nikšić',
    'Lokvi-Rogoznici, Omiš': 'Lokva Rogoznica, Omiš', 'Martiničima, Danilovgrad': 'Martinići, Danilovgrad', 'Ferdinandoveu': 'Ferdinandovac', 'Omeragićima, Derventa': 'Omeragići, Derventa', 'Skopliu': 'Skoplje', 'Martiš Vasu, Pregrada, Krapina': 'Martiša Ves, Pregrada, Krapina', "' Trbovlju": 'Trbovlje',
    'Ssddarima, Popovo polje, Trebinje': 'Sedlari, Popovo polje, Trebinje', 'Višnjiku, Derventa': 'Višnjik, Derventa', 'V. Sočnaici, Derventa': 'V. Sočanica, Derventa', 'Ssdu Veličanima, Popovo polje, Trebinje': 'Veličani, Popovo polje, Trebinje', 'Babici, Šipovo': 'Babići, Šipovo',
    'Gunjevcima, Bosanka Dubica': 'Gunjevci, Bosanska Dubica', 'radničkoj porodici, na Grbinu kod Litije': 'Grbin kod Litije', 'Potočanima, Derventa': 'Potočani, Derventa', 'crnoj Travi, Vlasotinci': 'Crna Trava, Vlasotince', 'Bihovima, Dživar, Trebinje': 'Bihovo, Dživar, Trebinje', 'N. Lužanima, Derventa': 'N. Lužani, Derventa',
    'Suljetovićima, Kreka, Tuzla': 'Suljetovići, Kreka, Tuzla', 'Samaričkoj Dragi (Dvor na Uni)': 'Šamarička Draga (Dvor na Uni)', 'Smaričkoj Dragi (Dvor na Uni)': 'Šamarička Draga (Dvor na Uni)', 'Timočkog kraja': 'Timočki kraj', 'Valjevskog kraja': 'Valjevski kraj', 'Trsteničkog kraja': 'Trstenički kraj',
    'Gornjoj Slabinji, Bosanski Novi': 'Gornja Slabinja, Bosanski Novi', 'Vražićima Lopare': 'Vražići, Lopare', 'Gornjoj Maikić Japri, Sanski Most': 'Gornja Majkić-Japra, Sanski Most', 'Busnovima Prijedor': 'Busnovi, Prijedor', 'Rom iz Sokobanje': 'Sokobanja', 'Rodom iz sela Zavala (Piperi)': 'Zavala (Piperi)',
    'Ćrnoj Gori': 'Crna Gora', 'Novog Beograda': 'Novi Beograd', 'Novog Beogoada': 'Novi Beograd', 'Novog Grahova': 'Novo Grahovo', 'Novog Karlovia, Inćija': 'Novi Karlovci, Inđija', 'Velikih Lašč': 'Velike Lašče', 'Velikih Laščah': 'Velike Lašče', 'Velikog Iža': 'Veli Iž', 'Biovčevog Sela': 'Biovičino Selo',
    'Bačkog Petrovog sela': 'Bačko Petrovo Selo', 'Novog sela': 'Novo Selo', 'Ljubnem ob Savinji': 'Ljubno ob Savinji', 'Novog Sela Sokolac': 'Novo Selo, Sokolac', 'Novog Sa da': 'Novi Sad', 'Bugoj na': 'Bugojno', 'Ravnog sela': 'Ravno Selo', 'Bilećkog sreza': 'Bileća', 'Novoj Vasi': 'Nova Vas',
    'Mul-skom Središća, Čakovec': 'Mursko Središće, Čakovec', 'Dugom Polju kod': 'Dugo Polje', 'Velika Drenova, Trstenik (ili Velikom Drenovcu kod Aleksinca —j prim. red.)': 'Velika Drenova, Trstenik', 'Bačka Topola (nema drugih podataka)': 'Bačka Topola', 'Beli Potok (verovatno kod Leskovca)': 'Beli Potok (kod Leskovca)',
    'Ljubina (ili Grabovici) (Dvor na Uni)': 'Ljubina (Dvor na Uni)', 'Sarajevo (otac mu bio konzul u Sarajevu)': 'Sarajevo', 'Dobrotić (zaselak Selište), Prokuplje, Srbija': 'Dobrotić (zaselak Selište), Prokuplje', 'Sv. Rozaliji, Sv. Jurij, Celje (Šentjur)': 'Sv. Rozalija, Sv. Jurij, Celje (Šentjur)',
    'Dobji vasi, Guštanj (Ravne na Koroškem)': 'Dobja vas, Guštanj (Ravne na Koroškem)', 'Marina, Prijedor Bosna i Hercegovina': 'Marina, Prijedor', 'Orahovac, T rebinie, Bosna i Hercegovina': 'Orahovac, Trebinje', 'Bosansko Grahovo i Matočići, Bosansko Grahovo': 'Bosansko Grahovo i Matočići',
    'Podhajcu': '', 'Tivacima (nije pronađeno gde se to selo nalazi)': '', 'Lovca': '', 'Slovenije u Segovinu, Ludbreg': '', 'Vrujovaca': '', 'Labočaca': '', 'Sotomišića': '', 'Vikinića': '', 'Dobroseljaca': '', 'Primčića': '', 'Brajakovića': '', 'Piržaju': '', 'Dragosavi': '', 'Lušču': '', 'Ćesici': '', 'Guslanju': '', 'Božiću': '',
    'Budovcu': '', 'climnici': '', 'Vladu': '', 'rusnici, Pregrada': '', 'thrbovu, Trebinje': '', 'Straže vici, Pakrac': '', 'Donjoj': '', 'Botiču': '', 'Kunonu': '', 'Krasnosmolenskog kraja (SSSR)': '', 'Srpkinja„': '', 'Tp«pnipp': '', 'Pešnika (ne zna se mjesto pogibije)': '', 'Radnici drvarske livnice (Vojnotehnička radionica VŠ)': '',
    # the birthplaces the second look read and the record's other books print clean, or still in a case, read one by one (2026-11-04)
    'Bašigovci, Zivinice': 'Bašigovci, Živinice', 'Binoveu, Smederevo': 'Binovac, Smederevo', 'Bobovo, Pljevlje': 'Bobovo, Pljevlja', 'Brezičanima, Priiedor': 'Brezičani, Prijedor', 'Donja Lukavica, Zivinice': 'Donja Lukavica, Živinice', 'Donja Trepča, Cačak': 'Donja Trepča, Čačak',
    'Donjim Palačkovcima, Prnjavor': 'Donji Palačkovci, Prnjavor', 'podinarskom selu Biteliču': 'Bitelić, Sinj', 'G.Komren, Niš': 'G. Komren, Niš', 'Dubnice': 'Dubnica', 'Ervenlka': 'Ervenik',
    'Požeravca': 'Požarevac', 'Brvenika': 'Brvenik', 'Kamenice': 'Kamenica', 'Krimovicama': 'Krimovice', 'Blljana': 'Gornje Biljane, Benkovac',
    'Raljana': 'Gornje Biljane, Benkovac', 'Gornjim Stranjanima, Prijepolje': 'Gornji Stranjani, Prijepolje', 'Gornji Zirovac (Dvor na Uni)': 'Gornji Žirovac (Dvor na Uni)', 'Gornjoj Kusonji': 'Gornja Kusonja', 'Gradac, Pljevl': 'Gradac, Pljevlja', 'Goli Rid. Leskovac': 'Goli Rid, Leskovac',
    'Kosanica, Pl.evlja': 'Kosanica, Pljevlja', 'Jasikovo, Krepoljii, Žagubica': 'Jasikovo, Krepoljin, Žagubica', 'Lazovika': 'Lozovik', 'JVubotinju': 'Ljubotinj', 'Maoče, Pljemlja': 'Maoče, Pljevlja', 'Pušanski Do, Plevlja': 'Pušanski Do, Pljevlja',
    'Mašnica (An-drijevica)': 'Mašnica (Andrijevica)', 'Miljakov cima, Prijedor': 'Miljakovci, Prijedor', 'Mojsinje, Cačak': 'Mojsinje, Čačak', 'Mrćajevci, Cačak': 'Mrčajevci, Čačak', 'Mulu': 'Muo, Kotor', 'Notranja': 'Notranje Gorice, Ljubljana',
    'Ovsištu Topola': 'Ovsište, Topola', "Takoštam'ma. Makarska": 'Pakoštane, Zadar', "Perna, Vrgz'n Most": 'Perna, Vrginmost', 'Počitclja': 'Počitelj', 'Pušanjskom Dolu': 'Pušanjski Do', 'Rogozu': 'Rogolji, Bosanska Gradiška',
    'Samaričkim Brđanima. (Dvor na Uni)': 'Šamarički Brđani (Dvor na Uni)', 'Stupiice': 'Stupnica, Leskovac', 'Straosten, Despotovac, Svetozarevo': 'Strmosten, Despotovac, Svetozarevo', 'T rniniča Brijegu': 'Trninić-Brijeg, Drvar', 'Toplounja, Knina': 'Tepljuh, Drniš',
    'Ublnma': 'Ubli', 'Velika Plaia': 'Velika Plana', 'Vilsnica, Dečinu, Čehoslovačka': 'Vilsnica, Dečin, Čehoslovačka', 'Vodice, Šibeiik': 'Vodice, Šibenik', 'Vrhpoliu, Gorica': 'Vrhpolje, Gorica', 'Vrhovo, Raydeče, Krško': 'Vrhovo, Radeče, Krško',
    'Vrmca, Sokobanja': 'Vrmdža, Sokobanja', 'Brmdža, Sokobanja': 'Vrmdža, Sokobanja', 'Vrulja, Plevlja': 'Vrulja, Pljevlja', 'Devđeliii': 'Đevđelija', 'Đevrsaka': 'Đevrske', 'Šetonii': 'Šetonje',
    'Lozovića': 'Lozovići', 'Rodoljice': 'Rodaljice', 'Dobropo-Ija': 'Dobropoljci', 'Koiečera': 'Ljubač, Dubrovnik', 'Batovac, Požarevap': 'Batovac, Požarevac', 'Grljai': 'Grljan',
    'Reovci, Pirot': 'Rsovci, Pirot', 'Rsavci, Pirot': 'Rsovci, Pirot', 'Araga, Tutin': 'Draga, Tutin', 'Lađevac Okućani Nova Gradiška': 'Lađevac, Okučani, Nova Gradiška', 'Preićani, Pljevlja': 'Prenćani, Pljevlja', 'Prenćane, Pljevlja': 'Prenćani, Pljevlja',
    'Burćevića Tara, Pljevlja': 'Đurđevića Tara, Pljevlja', 'Srćevac, Bijelo Polje': 'Srđevac, Bijelo Polje', 'Sokolac, Ša hovići, Bijelo Polje': 'Sokolac, Šahovići, Bijelo Polje', 'Nošar, Pirot': 'Nišor, Pirot', 'Malče, Niš': 'Malča, Niš',
    'Dikla, Zadar': 'Diklo, Zadar', 'Hruševac (Zagreb)': 'Hruševec (Zagreb)', 'Igalo (Mađarska)': 'Igal (Mađarska)', 'Kamenica (Kragujevačkoj)': 'Kamenica (Kragujevac)', 'Zastupa, Prijepolje': 'Zastup, Prijepolje', 'Zastupa': 'Zastup',
    'Sedobra, Prijepolje': 'Sedobro, Prijepolje', 'Brezovi': 'Brezova, Ivanjica', 'Jelašinovac': 'Jelašinovci, Lušci Palanka', 'Nin (ne zna se mjesto pogibije)': 'Nin', 'Suvaje': 'Suvaja', 
    'G. Mikuljana': 'G. Mikuljane', 'G. Mikuljana, Kuršumlija': 'G. Mikuljane, Kuršumlija', 'Pažmana': 'Pašman', 'Jasika, Sokolac': 'Jasik, Sokolac', 'Medvede': 'Medviđa', 'Uskoka': 'Uskoci',
    'Alinca': 'Alinci', 'Azanje, Mladenovac': 'Azanja, Mladenovac', 'Bal-štita Odžaka, Sokolac': 'Bandin Odžak, Sokolac', 'Bandini Odžaka, Sokolac': 'Bandin Odžak, Sokolac', 'Bandnna Odžaka': 'Bandin Odžak, Sokolac', 'Begluka': 'Begluk',
    'Belune, Italija': 'Beluno, Italija', 'Beogiada': 'Beograd', 'Bešeiova, Sremska Mitrovica': 'Bešenovo, Sremska Mitrovica', 'Bitulja': 'Bitolj', 'Btiolja': 'Bitolj', 'Boropca Kaljina, Sokolac': 'Kaljina, Sokolac',
    'Brejakovt-tća, Sokolac': 'Brajakovići, Sokolac', 'Bridže, Sokobanja': 'Vrmdža, Sokobanja', 'Vridža, Sokobanja': 'Vrmdža, Sokobanja', 'Cara, Korčula': 'Čara, Korčula', 'Ceranja': 'Ceranje', 'Ciste Ma': 'Cista Mala',
    'Dalmacije': 'Dalmacija', 'Dikla': 'Diklo', 'Dmiža': 'Drniš', 'Donjeg Jelenja': 'Donje Jelenje', 'Donjega, Hrušica': 'Donja Hrušica',
    'Dubrovpika': 'Dubrovnik', 'Gazivoda, Sokolac': 'Gazivode, Sokolac', 'Grabarja kod Sl. Broda': 'Grabarje kod Sl. Broda', 'Inđše': 'Inđija', 'Kalne kod Pirota': 'Kalna kod Pirota', 'Kolana (Rab)': 'Kolan (Rab)',
    'Kočevskega rudnika': 'Kočevski rudnik', 'Krajišta': 'Krajište', 'Krapinej električar iz Zagreba': 'Krapina', 'Kuklica': 'Kukljica', 'Kučkova (kod Skoplja)': 'Kučkovo (kod Skoplja)', 'L ike': 'Lika',
    'Ljuljaka': 'Ljuljaci', 'Lobnika, Žel. Kapli': 'Lobnik, Železna Kapla', 'Lužana (Malino), Sl. Brod': 'Lužani (Malino), Sl. Brod', 'Maglenca': 'Meglenci', 'Meglenca': 'Meglenci', 'Marije Snežne (Slovenija)': 'Marija Snežna (Slovenija)',
    'Medoševca kraj Niša': 'Medoševac kod Niša', 'Međimurja': 'Međimurje', 'NOVOG Sada': 'Novi Sad', 'Nivičana': 'Nivičani', 'Ohia, SAD': 'Ohio, SAD', 'Opašca': 'Opašac',
    'Ozerkovnća, Sokolac': 'Ozerkovići, Sokolac', 'Paučja': 'Paučje', 'Pestiža, Prokuplje': 'Pestiš, Prokuplje', 'Petrovgra da (Zrenjanin)': 'Petrovgrad (Zrenjanin)', 'Podvirja, Sl. Brod': 'Podvinje, Sl. Brod', 'Privluke': 'Privlaka',
    'Ra va': 'Rava', 'Rudara, Kuršumlija': 'Rudare, Kuršumlija', 'SSSR-a': 'SSSR', 'Saraje va': 'Sarajevo', 'Sarajera': 'Sarajevo', 'Senokosa': 'Senokos',
    'Senteša (Mađarska)': 'Senteš (Mađarska)', 'Senteša (Szentes u Mađarskoj)': 'Senteš (Mađarska)', 'Slavonije': 'Slavonija', 'Sremeke Mitrovice': 'Sremska Mitrovica', 'Su botice': 'Subotica', 'Teherua': 'Teheran',
    'Tolminskega loma': 'Tolminski Lom', 'Toptice': 'Toplica', 'Trnca': 'Trnac', 'Trpaje, Vukovar': 'Trpinja, Vukovar', 'Trpinje kod Vukovara': 'Trpinja kod Vukovara', 'Trpnja sa Pelješca': 'Trpanj, Pelješac',
    'Virovitce': 'Virovitica', 'Viroviti ce': 'Virovitica', 'Višega': 'Višegrad', 'Vrbovljana': 'Vrbovljani', 'Zagerba': 'Zagreb', 'Zagieba': 'Zagreb',
    'Zenize': 'Zenica', 'Zlariua': 'Zlarin', 'Škobrnje': 'Škabrnja', 'Žednika kod Užica': 'Žednik kod Užica', 'Železne Kaple': 'Železna Kapla', 'Žitorađa, Vladičin Han': 'Žitorađe, Vladičin Han',
    'Žljebova, Sokolac': 'Žljebovi, Sokolac', 'Batuznice': '', 'Crveike, Sokolac': '', 'Dudve (Crna Gora)': '', 'Hermaža': '', 'Krivane': '',
    'Lalovođa': '', 'Mokrolače': '', 'Negrizije': '', 'Staveća': '', 'Svetišnice': '', 'TPuljma': '',
    'Zuvka': '', 'Življa': '', 'Borovljah': 'Borovlje', 'Jesenicah': 'Jesenice', 'Lučah ob Savinji': 'Luče ob Savinji', 'Podurljai': 'Podurljaj',
    'Trbovljah': 'Trbovlje', 'Tresibabi, Knjaževac': 'Tresibaba, Knjaževac', 'Brdicah, Nova Gorica': 'Brdice, Nova Gorica', 'Brdinjah, Guštanj (Ravnah)': 'Brdinje, Guštanj (Ravne)', 'Broćancti, Split': 'Broćanac, Split', 'Cadevici kod Biieljine': 'Čađavica kod Bijeljine',
    'Celiću Lopare': 'Čelić, Lopare', 'Donje Koniuvce': 'Donje Konjuvce', 'Fanovcu, Sl. Bistrica': 'Fanovec, Sl. Bistrica', 'Gage blizu Smoluče, Lukavac': 'Gage kod Smoluće, Lukavac', 'Gaine-D. Lapac': 'Gajine, D. Lapac', 'Gotovljah, Žalec': 'Gotovlje, Žalec',
    'Guč': 'Guča', 'Holovlja, Škoija Loka': 'Hotovlja, Škofja Loka', 'Idriii': 'Idrija', 'Ivanjgadi': 'Ivangrad', 'Ivanskoi, Bjelovar': 'Ivanska, Bjelovar', 'Kozarjah': 'Kozarje',
    "Kruščic'i. Bela Crkva": 'Kruščica, Bela Crkva', 'Lešah na Prevaljah': 'Leše na Prevaljah', 'Libučah, Pliberk': 'Libuče, Pliberk', 'Liiešani, Kolašin': 'Liješani, Kolašin', 'Lokvah, Trst': 'Lokve, Trst', 'Lomu nad Mežico': 'Lom nad Mežico',
    'Makolah, Maribor': 'Makole, Maribor', 'Nišu_ Maturirao': 'Niš', 'Opatiii': 'Opatija', "Oreovc'u. Prilep": 'Oreovec, Prilep', 'Orlovski oblasti': 'Orlovska oblast', 'Osoju blizu Dragunje, Tuzla': 'Osoje kod Dragunje, Tuzla',
    'Pišecah': 'Pišece', 'Podbrdn': 'Podbrdo', 'Predosljah (Grosuplje)': 'Predoslje (Grosuplje)', 'Radečah, Zidani most': 'Radeče, Zidani Most', 'Rosalnicah, Metlika': 'Rosalnice, Metlika', 'Rušah, Maribor': 'Ruše, Maribor',
    'Slivnicah, Rakek': 'Slivnica, Rakek', 'Stipovači, Kutina': 'Stipovača, Kutina', 'Sv. Jederri': 'Sv. Jedert', 'Svečah': 'Sveče', 'Topoli Topola': 'Topola', 'Veličanah': 'Veličani',
    'Vlaškovcima, Bosanska Dubica': 'Vlaškovci, Bosanska Dubica', 'Vrhah, Slovenj Gradec': 'Vrhe, Slovenj Gradec', 'Zagrebu Hrvatska': 'Zagreb', 'Zdolah': 'Zdole', 'Zg. Gorjah, Bled': 'Zg. Gorje, Bled', 'Šibeniku Hrvatska': 'Šibenik',
    'Štipn': 'Štip', 'Žigmanicah, Sodražica': 'Žigmarice, Sodražica', 'Beloševen': '', 'Budovcu': '', 'Celin': '', 'Trari, St': '',
}


# the census's place column in one form ("Doboj-tuzla" Doboj, Tuzla; "Banja luka" Banja Luka; "D.lapac" D. Lapac; a value cut at its 15 characters): make_census_forms.py
_forms_path = Path(__file__).resolve().parent.parent / 'data-extraction' / 'places' / 'census_forms.json'
CENSUS_FORMS = json.loads(_forms_path.read_text(encoding='utf-8')) if _forms_path.exists() else {}


# a capital pair at a word's start: "LJubija, Prijedor", "kod LJubovije"
LJ_CAPS = re.compile(r'\b(L|N)J(?=[a-zčćžšđ])')


def birth_place_form(value: str) -> str:
    v = LJ_CAPS.sub(lambda m: m.group(1) + 'j', PLACE_READ.get(value.strip(), value))
    v = BIRTH_READ.get(v, v)
    v = scan_marks(LJ_SCAN_RE.sub(lambda m: LJ_SCAN[m.group(0)], PART_OF.sub('', v)).strip(), birth=True)
    v = PLACE_READ.get(v, v)
    v = re.sub(r'^s\.\s+(?=[A-ZČĆŽŠĐ])', '', v)
    return BIRTH_READ.get(v, v)


def birth_place_forms(s: dict) -> dict | None:
    value = s.get('birth_place')
    new = birth_place_form(value) if value else value
    return {'birth_place': new} if new != value else None


OFFENSIVE_IN_PLACE = re.compile(r'[\s,_-]*(?:\b[Uu]\s+(?:toku\s+)?|\b[Zz]a\s+vreme\s+|\bu\s+borbi\s+)?\b\d\s*\.?\s*(?:-oj\s*)?(?:ne(?:pr\w*)?\.?\s*|n\.\s*)?'
                                r'(?:ofanz|ofenz|ofan|ofa|of\b|oranz)\w*\.?(?:-pog)?')
SMALL_WORDS = re.compile(r'^(?:u|na|kod|pri|v|pod|nad|med|ispod|iznad|za|oko|kraj|od|s|ali|pred|prema|dolina|bolnica|logor|šuma|pruga|centralna|okolina|selo|zbeg|zbjeg|'
                         r'ž|žel|kota|brdo|hrib|reka|rijeka|planina|grapa|teško|njemački|nemački|italijanski|talijanski|neprijateljski)\b', re.I)


def column_slips(v: str) -> str:
    """What the census's column and the scans leave beside a place: the offensive ("Zelengora 5 ofa", "U 4 ofanzivi"), a number
    run on ("Vranje3", "Tržič 1"), the digit for a letter ("Vrp0lje", "2itomislić"), a first letter small ("avala"; 2026-11-04)"""
    v = re.sub(r'(?<=[a-zčćžšđA-ZČĆŽŠĐ])0(?=[a-zčćžšđ]|\b)', 'o', v)
    v = re.sub(r'^2(?=[a-zčćžšđ]{4})', 'Ž', v)
    v = OFFENSIVE_IN_PLACE.sub('', v).strip(' ,.-_')
    if not re.match(r'(?:[Kk]ota|[Kk]\.)\s', v):
        v = re.sub(r'(?<=[a-zčćžšđ])\s*\d{1,2}$', '', v)
    v = re.sub(r'(?<=[a-zčćžšđ])_(?=[a-zčćžšđA-ZČĆŽŠĐ])', ', ', v)
    if v == 'usa':
        return 'SAD'
    # a place named by what it lies near keeps its small letter on the card: "Poginuo: 1943, između Drniša i Knina"
    if re.match(r'(?:Između|Ispred|Blizu|Iza|Pored|Iz)\s', v):
        return v[0].lower() + v[1:]
    if v and v[0].islower() and not re.match(r'(?:između|ispred|blizu|iza|pored|iz)\s', v) and not SMALL_WORDS.match(v):
        v = v[0].upper() + v[1:]
    return v


def place_form(value: str) -> str | None:
    """A place in the site's form, the steps below repeated until nothing changes: a later step can leave a form an
    earlier one reads (the census's "Crna gora-5 ofa": the offensive's cut leaves "Crna gora", which PLACE_READ writes
    "Crna Gora"), and a second run of apply_corrections.py must change nothing (2026-11-20: the census parts' "Crna
    gora" took two runs to become "Crna Gora")"""
    v = _place_form_once(value)
    for _ in range(3):
        if v is None:
            break
        again = _place_form_once(v)
        if again == v:
            break
        v = again
    return v


def _place_form_once(value: str) -> str | None:
    v = re.sub('­\\s*', '', value).strip()
    v = LJ_CAPS.sub(lambda m: m.group(1) + 'j', PLACE_READ.get(v, v))
    v = LJ_SCAN_RE.sub(lambda m: LJ_SCAN[m.group(0)], v)
    v = YEAR_WORD_TAIL.sub('', v).strip(' ,.')
    v = scan_marks(v)
    v = PLACE_READ.get(v, v)
    v = CENSUS_FORMS.get(v, v)
    v = PLACE_READ.get(v, v)
    v = column_slips(v)
    v = CENSUS_FORMS.get(v, v)
    v = re.sub(r'^s\.\s+(?=[A-ZČĆŽŠĐ])', '', v)
    if UNKNOWN_PLACE.match(v) or UNIT_COLUMN.match(v) or not v:
        return None
    m = COMMA_GLUED.match(v)
    if m:
        v = f'{m.group(1)}, {m.group(2).upper()}{m.group(3)}'
    m = REGION_NAMED.search(v)
    if m:
        adjective = m.group(1).capitalize() if m.start(1) == 0 else m.group(1)
        return v[:m.start(1)] + adjective + ' ' + REGIONS.get(m.group(2).lower(), m.group(2))
    m = IN_REGION.search(v)
    if m and m.group(2).islower():
        return v[:m.start(2)] + REGIONS[m.group(2)]
    m = REGION_AFTER.match(v)
    if m and m.group(2).islower() and not re.search(r'\b(?:kod|u|na|po|pri)$', m.group(1), re.I):
        region = {'slavoni': 'Slavonija'}.get(m.group(2), REGIONS[m.group(2)])
        # an abbreviated word before it is the region's own ("Pl. majevica", "Pod. moslavina")
        return f"{m.group(1)}{' ' if m.group(1).endswith('.') else ', '}{region}"
    return v


def death_place_form(s: dict) -> dict | None:
    value = s.get('death_place')
    if not value:
        return None
    new = place_form(value)
    return {'death_place': new} if new != value else None


# ── parents: the mother where the book names her, a father's genitive the converter left ─────────────────────
# The census and some books print the mother where the father is unknown ("Ajduk (Ruža) Joze", "ADŽIĆ Milica KRSTAN"):
# a woman's name in fathers_name is his mother's (mothers_name; the card's row "Majka", the user's choice of
# 2026-10-30). Only names that are no man's genitive or hypocoristic count (Joka, Draga, Ivana, Petra may be either and
# stay); the census, which prints the parent in the nominative, also its women's names that a man's genitive shares
# in the books (Milka, Savka, Živka). A father the converter left in the genitive ("Kabiljo Hajima Jakov") gets his
# nominative where the form is no one's given name and its stem a man's (FATHER_NOMINATIVE, read on 2026-10-30)
MOTHERS = {
    'Marija', 'Kata', 'Ana', 'Milica', 'Mara', 'Spasenija', 'Janja', 'Jela', 'Terezija', 'Frančiška', 'Marica',
    'Katarina', 'Julka', 'Ljubica', 'Ruža', 'Stana', 'Sofija', 'Mileva', 'Anka', 'Danica', 'Darinka', 'Katica',
    'Marta', 'Anđa', 'Dragica', 'Helena', 'Manda', 'Ružica', 'Bosiljka', 'Olga', 'Klara', 'Eva', 'Roza', 'Neža',
    'Jeka', 'Persa', 'Jovanka', 'Draginja', 'Vukica', 'Leposava', 'Mirjana', 'Nevenka', 'Agata', 'Magdalena',
    'Rozalija', 'Uršula',
}
# women's names in the nominative the census prints that a man's genitive shares in the books ("Milka" of Milko,
# "Milena" of Milen, "Antonija" of Antonije)
CENSUS_MOTHERS = MOTHERS | {'Milka', 'Zorka', 'Ivanka', 'Milena', 'Jelena', 'Milja', 'Zora', 'Antonija', 'Smilja',
                            'Savka', 'Ivka', 'Joka', 'Stanka', 'Živka', 'Radojka', 'Perka', 'Ane', 'Kate', 'Mare',
                            'File', 'Mande', 'Jele', 'Luce'}
CENSUS_PARTS = ('0131', '0132', '0133', '0134', '0135', '0136', '0137', '0138')
FATHER_NOMINATIVE = {
    'Morica': 'Moric', 'Hajima': 'Hajim', 'Arona': 'Aron', 'Nisima': 'Nisim', 'Mijata': 'Mijat', 'Smajila': 'Smajil',
    'Pilipa': 'Pilip', 'Artura': 'Artur', 'Dezidera': 'Dezider', 'Rikarda': 'Rikard', 'Dragutina': 'Dragutin',
    'Stevana': 'Stevan', 'Lavoslava': 'Lavoslav', 'Mihaila': 'Mihailo', 'Elijasa': 'Elijas', 'Izraela': 'Izrael',
    'Abrahama': 'Abraham',
    # a Cyrillic scan's Ђ read as Б ("Борђа" Đorđa), its Viđana as Viadana
    'Borđa': 'Đorđe', 'Borća': 'Đorđe', 'Borđija': 'Đorđija', 'Tođora': 'Tođor', 'Viđana': 'Viđan',
    'Viadana': 'Viđan',
}


def parents(s: dict) -> dict | None:
    father = (s.get('fathers_name') or '').strip()
    printed = (s.get('middle_name') or '').strip()
    if not father:
        return None
    # printed as he is named (the census, a book of nominative fathers), or a genitive the converter left
    as_printed = not printed or printed == father
    if as_printed and father in FATHER_NOMINATIVE:
        return {'fathers_name': FATHER_NOMINATIVE[father]}
    census = s['soldier_id'].startswith(CENSUS_PARTS) or (s['soldier_id'].startswith('0122') and not printed)
    # a mother: in a census part (or a 122 record whose father the builder took as printed) the census's women's
    # names, in a book her name as printed or from her genitive in -e ("Mare" Mara, "Mileve" Mileva)
    if (census and father in CENSUS_MOTHERS) or (father in MOTHERS and (as_printed or printed.endswith(('e', 'i')))):
        return {'mothers_name': father, 'fathers_name': None}
    return None


# a duty the reader took with its case or the scan's slip ("politički komesara čete", "bortac", "komandirvoda"), 2026-11-03
DUTY_SLIPS = [(re.compile(r'\b(zamjenik|zamenik|pomoćnik) politički komesara?\b'), r'\1 političkog komesara'),
              (re.compile(r'\bpolitički komesara\b'), 'politički komesar'), (re.compile(r'\b(?:bortac|borace)\b'), 'borac'),
              (re.compile(r'\bkomandirvoda\b'), 'komandir voda'), (re.compile(r'\bstriji vodnik\b'), 'stariji vodnik'),
              (re.compile(r'\bzam\. polit\. komesara\b'), 'zamjenik političkog komesara'), (re.compile(r'\bpomoćnik polit\. komesara\b'), 'pomoćnik političkog komesara'),
              (re.compile(r'\bzamjenik polit\. kom\.?(?=,|$)'), 'zamjenik političkog komesara'), (re.compile(r'\bpolit\. komesar\b'), 'politički komesar'),
              (re.compile(r'\bzam\. kom\. čete\b'), 'zamjenik komesara čete'), (re.compile(r'\bzam\. komandanta\b'), 'zamjenik komandanta'),
              (re.compile(r'\bvod\. delegat\b'), 'vodni delegat'), (re.compile(r'\bvod\. voda\b'), 'vodnik voda'), (re.compile(r'\bzastavnr\b'), 'zastavnik'),
              (re.compile(r'\bkapet(?=,|$)'), 'kapetan'), (re.compile(r'\bborac--(?=[a-zčćžšđ])'), 'borac, '), (re.compile(r'\bint\. bat\.'), 'intendant bataljona')]
# no duties: a title, a trade or the words of the sentence the reader took along
NOT_DUTY = {'heroj', 'mesar', 'janjač', 'mlađi brat Milidragović G. Koste', 'pomočnik OC', 'pomočnik Vidic', 'pomočnik do', 'pomočnik in', 'pomočnik četnega'}


def duty_slips(s: dict) -> dict | None:
    value = s.get('rank')
    if not value:
        return None
    new = value
    for pattern, right in DUTY_SLIPS:
        new = pattern.sub(right, new)
    if any(d in NOT_DUTY for d in new.split(', ')):
        new = ', '.join(d for d in new.split(', ') if d not in NOT_DUTY)
    return {'rank': new} if new != value else None


RULES = [
    ('captured', captured),
    ('after_war', after_war),
    ('death_date', death_date),
    ('albanian', albanian),
    ('duty_slips', duty_slips),
    ('unit_numbers', unit_numbers),
    ('unit_case', unit_case),
    ('trade', trade),
    ('trade_gender', trade_gender),
    ('grk_village', grk_village),
    ('ethnicity_gender', ethnicity_gender),
    ('death_place_form', death_place_form),
    ('birth_place_form', birth_place_forms),
    ('parents', parents),
]
# the rules that change only a field's form: they apply to a field corrections set too
FORM_ONLY = {'after_war', 'death_date', 'albanian', 'unit_numbers', 'unit_case', 'ethnicity_gender', 'death_place_form',
             'trade_gender', 'birth_place_form', 'duty_slips'}


def standard(field: str, value):
    """one field's value as the rules would leave it (extract_structured_fields.forget_stale compares by it)"""
    if field == 'death_date' and value:
        return None if AFTER_WAR.fullmatch(value.strip()) else date_form(value)
    if field == 'ethnicity' and value:
        return ETHNICITY.get(value, value)
    if field == 'unit_detail' and value:
        return unit_case_form(unit_number_form(value))
    if field == 'occupation' and value:
        return trade_form(value)
    if field == 'death_place' and value:
        return place_form(value)
    if field == 'birth_place' and value:
        return birth_place_form(value)
    return value


def apply(soldiers: list[dict], manual: dict | None = None, only: str | None = None, samples: dict | None = None) -> collections.Counter:
    """run the rules on a unit's records in place; manual: soldier_id -> the fields corrections set"""
    done = collections.Counter()
    for s in soldiers:
        kept = (manual or {}).get(s.get('soldier_id'), ())
        for name, rule in RULES:
            if only and name != only:
                continue
            change = rule(s)
            if not change or (name not in FORM_ONLY and set(change) & set(kept)):
                continue
            before = {k: s.get(k) for k in change}
            for k, v in change.items():
                if v is None:
                    s.pop(k, None)
                else:
                    s[k] = v
            done[name] += 1
            if samples is not None and len(samples.setdefault(name, [])) < samples.get('_n', 5):
                samples[name].append((s['soldier_id'], before, change))
    return done


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    from name_utils import BRIGADE_CONFIGS          # noqa: E402
    from cleanup_text_fields import live_json_files  # noqa: E402
    import apply_corrections                         # noqa: E402

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--brigade', type=int)
    ap.add_argument('--rule', choices=[n for n, _ in RULES])
    ap.add_argument('--sample', type=int, default=4)
    args = ap.parse_args()
    manual = {}
    for c in apply_corrections.load_corrections(ROOT / 'corrections.json'):
        got = set(c.get('fields', {})) | set(c.get('record', {}))
        if got:
            manual.setdefault(c.get('new_id') or c['soldier_id'], set()).update(got)
    live, total = live_json_files(), collections.Counter()
    samples: dict = {'_n': args.sample}
    for code, cfg in sorted(BRIGADE_CONFIGS.items()):
        if (args.brigade and code != args.brigade) or cfg['json_file'] not in live:
            continue
        path = ROOT / 'website' / 'public' / cfg['json_file']
        text = path.read_text(encoding='utf-8')
        soldiers = json.loads(text)
        done = apply(soldiers, manual, args.rule, samples)
        if not done:
            continue
        total.update(done)
        print(f"{code:4} {cfg['json_file']}: {dict(done)}")
        if args.apply:
            path.write_text(json.dumps(soldiers, ensure_ascii=False, indent=2), encoding='utf-8')
    for name, rows in samples.items():
        if name == '_n':
            continue
        print(f'\n{name}:')
        for sid, before, change in rows:
            print(f'   {sid}  {before} -> {change}')
    print(f'\ntotal {dict(total)}' + ('' if args.apply else ' (dry run)'))


if __name__ == '__main__':
    main()
