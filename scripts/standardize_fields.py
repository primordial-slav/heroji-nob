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


def after_war(s: dict) -> dict | None:
    if AFTER_WAR.fullmatch((s.get('death_date') or '').strip()):
        return {'death_date': None, 'death_after_war': True}
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


def death_date(s: dict) -> dict | None:
    v = s.get('death_date')
    if not v:
        return None
    new = date_form(v)
    return {'death_date': new} if new != v else None


# ── albanian: the census's word ─────────────────────────────────────────────
ETHNICITY = {'Šiptar': 'Albanac', 'Šiptarka': 'Albanka', 'šiptar': 'Albanac', 'šiptarka': 'Albanka',
             'Siptar': 'Albanac', 'Siptarka': 'Albanka'}


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
                           r'nepoznato[-\s]\w+|nepoznata \w+|nije poznato|nn\.?)$', re.I)


# a Cyrillic list's scan read Љ as "l," (the Spomenica crnogorskim antifašistima, Prilog u krvi): the places it spoiled so
LJ_SCAN = {'Bol,anići': 'Boljanići', 'Pol,a, Mojkovac': 'Polja, Mojkovac', 'Pl,evlja': 'Pljevlja', 'Pol,ska': 'Poljska',
           'Šl,ivovica': 'Šljivovica', 'Gornje G1ol,e': 'Gornje Polje'}
LJ_SCAN_RE = re.compile('|'.join(re.escape(k) for k in sorted(LJ_SCAN, key=len, reverse=True)))
# "Šid, godine", "u Dubrovniku iste godine", "na Prozor .^godine": the bio's "godine" after the place
YEAR_WORD_TAIL = re.compile(r"[\s,.^'?!-]*(?:iste\s+)?godine\.?$")
# the Slovene census's part of a town: "Maribor (del), Maribor-Center", "Vrhe (del), Trbovlje"
PART_OF = re.compile(r'\s*\((?:del|dio|deo)\)')


def birth_place_form(value: str) -> str:
    return LJ_SCAN_RE.sub(lambda m: LJ_SCAN[m.group(0)], PART_OF.sub('', value)).strip()


def birth_place_forms(s: dict) -> dict | None:
    value = s.get('birth_place')
    new = birth_place_form(value) if value else value
    return {'birth_place': new} if new != value else None


def place_form(value: str) -> str | None:
    v = re.sub('­\\s*', '', value).strip()
    v = LJ_SCAN_RE.sub(lambda m: LJ_SCAN[m.group(0)], v)
    v = YEAR_WORD_TAIL.sub('', v).strip(' ,.')
    if UNKNOWN_PLACE.match(v) or not v:
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


RULES = [
    ('captured', captured),
    ('after_war', after_war),
    ('death_date', death_date),
    ('albanian', albanian),
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
             'trade_gender', 'birth_place_form'}


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
