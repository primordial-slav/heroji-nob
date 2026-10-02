"""
Parser: 3. makedonska NOU brigada (brigade code 51) — "Spisak poginulih boraca".

Source: Kiril Mihailovski Grujica, "Treća makedonska brigada", the chapter "Odlikovanja, narodni heroji, spisak
        poginulih boraca" (znaci.org 00001/71_7.pdf)  →  website/public/pdfs/3-makedonska.pdf, pages 6-15
One column, Cyrillic (ekavica), numbered:
    1. Арсов Димитриев Славко из с. Никулине, рођен 1922. год., погинуо код Славонске Пожеге 20-IV-1945. год.
Surname, the father as a possessive (Dimitriev, Stojanov; a woman's "Miloševa"), the given name, a nickname in
quotes; "iz" the village, the birth year, where and when he fell. The scan reads the Roman months as letters and
digits ("20-1U-1945" = 20-IV, "13-U1" = VI, "15-H" = X, "5-UŠ" = VIII, "Z" for the digit 3): the death date is read
back from them; the entry stays as printed. Pages 2-5 are the brigade's narodni heroji, with long biographies.
"""
import glob
import json
import re
from collections import Counter

from _parser_scaffold import _record, run_parser
from scripts.name_utils import genitive_to_nominative

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
START = re.compile(r'^\d{1,3}\.\s+[A-ZČĆŽŠĐ]')
# Surname Father's Given [— "Nick"] — the name ends before "iz", a comma or "poginuo"
NAME = re.compile(rf'^\d{{1,3}}\.\s+([{U}][{L}A-Z]+(?:-[{U}][{L}]+)?)(?:\s+\(([{U}][{L}]+)\))?\s+(?:dr\s+)?'
                  rf'(?:([{U}][{L}]+|[{U}]\.)\s+)?([{U}][{L}]+)'
                  rf'(?:\s+[—–-]?\s*[„"»]([^"“”«]+)["“”«]|\s+\(([{U}][{L}]+)\)|\s+[—–]\s+([{U}][{L}]+)(?=,))?'
                  rf'(?:\s+[{U}][{L}]+)?(?=\s+iz\b|\s*,|\s+pogin|\s+umr|\s*$)')
# The villages the list names in the genitive ("iz s. Mladog Nagoričana"), in the nominative: the Macedonian
# villages of the brigade's Kumanovo, Kratovo and Lipkovo country. Towns are left to the field extractor, and a
# village not listed here stays as printed.
VILLAGES = {
    'Agino Sela': 'Agino Selo', 'Aginosela': 'Agino Selo', 'Arbanaškog': 'Arbanaško', 'Bajlovca': 'Bajlovce',
    'Bistrice': 'Bistrica', 'Brusnika': 'Brusnik', 'Dejlovca': 'Dejlovce', 'Dimanca': 'Dimance',
    'Dolno Dupeni': 'Dolno Dupeni', 'Dupeni': 'Dupeni', 'Dovezenaca': 'Dovezence', 'Gornjeg Konjara': 'Gornje Konjare',
    'Konjara': 'Konjare', 'Kiselice': 'Kiselica', 'Klečevca': 'Klečevce', 'Kokina': 'Kokino',
    'Ljubodraga': 'Ljubodrag', 'Lojana': 'Lojane', 'Makreša': 'Makreš', 'Malina': 'Malino', 'Malotina': 'Malotino',
    'Matejča': 'Matejče', 'Mladog Nagoričana': 'Mlado Nagoričane', 'Mlado Nagoričane': 'Mlado Nagoričane',
    'Murgaša': 'Murgaš', 'Nikuline': 'Nikuljane', 'Nikuljana': 'Nikuljane', 'Niže Polja': 'Niže Pole',
    'Pavlešenca': 'Pavlešence', 'Pelinca': 'Pelince', 'Proevca': 'Proevce', 'Pčinje': 'Pčinja', 'Ramna': 'Ramno',
    'Režanovca': 'Režanovce', 'Romanovca': 'Romanovce', 'Ruginca': 'Rugince', 'Sopsko Rudare': 'Šopsko Rudare',
    'Sopskog Rudara': 'Šopsko Rudare', 'Šopskog Rudara': 'Šopsko Rudare', 'Starog Nagoričana': 'Staro Nagoričane',
    'Stenja': 'Stenje', 'Stepanaca': 'Stepance', 'Stepanca': 'Stepance', 'Stracina': 'Stracin',
    'Strezovca': 'Strezovce', 'Strzovca': 'Strezovce', 'Strnovca': 'Strnovac', 'Suševa': 'Suševo',
    'Tabanovaca': 'Tabanovce', 'Tabanovca': 'Tabanovce', 'Umindola': 'Umin Dol', 'Vojnika': 'Vojnik',
    'Vratnice': 'Vratnica', 'Čelopeka': 'Čelopek', 'Četirci': 'Četirce', 'Žegljana': 'Žegljane',
}
FROM_VILLAGE = re.compile(r'^iz\s+s\.\s*([^,]+?)(?=,|\s+rođen|\s+\d{4}|\s+pogin|\s*$)')
DEATH_DATE = re.compile(r'(?:[pl]ogin\w+|umr\w+|strelj\w+|ubijen\w*).*?\b([\dZzIO]{1,3})[>»<\']?\s*-\s*([^-\s]{1,6})\s*-\s*'
                        r'([\dI(>)\'&<g]{4,7})')
ROMAN = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12}


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if ln['page'] == 6 and re.fullmatch(r'S P I S A K|POGINULIH BORACA', t):
        return False
    return not re.fullmatch(r'[\d\W]{1,5}', t)                           # page numbers


def month(token: str) -> int:
    """The scan's Roman month: У read as U (V), Х as H (X), I as 1 or G, Ш as Š (III), П as P (II)."""
    t = token.upper().replace('U', 'V').replace('H', 'X').replace('1', 'I').replace('G', 'I').replace('Š', 'III')
    t = t.replace('P', 'II').replace('Ш', 'III')
    t = re.sub(r'[^IVX]', '', t)
    return ROMAN.get(t, 0)


def death_date(info: str) -> str:
    m = DEATH_DATE.search(info)
    if not m:
        return ''
    day, mon, year = m.groups()
    day = day.replace('Z', '3').replace('z', '3').replace('O', '0').replace('I', '1')
    day = int(day) if day.isdigit() and len(day) <= 2 else 0                # "101-H1", "217-IV": unreadable
    mo = month(mon)
    digits = re.sub(r'\D', '', year.replace('I', '1'))
    if not (1 <= day <= 31 and mo and digits and digits[-1] in '12345'):
        return ''
    return f'{day}. {mo}. 194{digits[-1]}'


_first: Counter = Counter()


def corpus() -> None:
    for f in glob.glob('website/public/*soldiers.json'):
        if not f.replace('\\', '/').endswith('3-makedonska-soldiers.json'):
            for s in json.load(open(f, encoding='utf-8')):
                _first[s['first_name']] += 1


def nominative(father: str) -> str:
    """Stojanov → Stojan, Dimitriev → Dimitri(je), Ordev → Orde, Miloševa → Miloš: of the forms a possessive can
    come from, the one most common as a given name."""
    if not father or father.endswith('.'):
        return father
    f = re.sub(r'a$', '', father) if father.endswith(('ova', 'eva')) else father      # a woman's "Miloševa"
    m = re.match(r'^(.*?)([eo]v)$', f)
    if not m:
        if f.endswith('a') and _first[f[:-1]] >= 2:                          # a genitive: "Stojana", "Božidara"
            return f[:-1]
        if f.endswith('ija'):
            return f[:-1] + 'e'                                             # "Vasilija"
        return genitive_to_nominative(f) or f                               # "Ilije"
    stem, suffix = m.groups()
    bare = stem if len(stem) >= 4 else ''
    if suffix == 'ov':
        # Stojanov → Stojan, Petrov → Petar, Trajkov → Trajko
        inserted = stem[:-1] + 'a' + stem[-1] if len(stem) > 2 and stem[-1] in 'rl' and stem[-2] not in 'aeiou' else ''
        order = sorted([(bare, 2), (inserted, 2), (stem + 'o', 2)], key=lambda c: -_first[c[0]]) + [(stem + 'e', 2)]
        if stem[-1] in 'nmfl':
            order.insert(0, (bare, 2))                                      # Stefanov → Stefan, not Stefano
        # unknown names: Dimkov → Dimko, Dimov → Dimo, Dimitrov → Dimitar, Vangelov → Vangel
        fallback = stem + 'o' if stem[-1] == 'k' or len(stem) <= 4 else (inserted or stem)
    elif stem.endswith('i'):
        order = [(stem + 'ja', 2), (stem, 2), (stem + 'je', 2), (stem + 'j', 2)]  # Iliev → Ilija, Georgiev → Georgi
        fallback = father
    elif stem[-1] in 'aeiou':
        order, fallback = [], stem + 'j'                                    # Blagoev → Blagoj
    elif stem.endswith('j'):
        # Stanojev → Stanoje, Dositejev → Dositej
        order, fallback = [], stem if stem.endswith('ej') else stem + 'e'
    else:
        # Macedonian names in -e: Ordev → Orde, Micev → Mice, Spasev → Spase; Blažev → Blaž
        order = [(stem + 'e', 1), (bare, 3)]
        fallback = stem + 'e'                                               # Ančev → Anče, Conev → Cone
    for c, least in order:
        if c and _first[c] >= least:
            return c
    return fallback


def parse_entry(text: str) -> dict:
    m = NAME.match(text)
    if not m:
        num = re.match(r'^\d{1,3}\.\s+', text)
        toks = text[num.end():].split(',')[0].split() if num else text.split()
        last, given, father, nick = (toks[0] if toks else ''), (toks[-1] if len(toks) > 1 else ''), '', None
        rest = text
    else:
        last, other, father, given, nick, paren, dash = m.groups()
        nick = nick or paren or dash
        rest = text[m.end():]
    rest = rest.strip(' ,')
    info = ('zvani ' + nick.strip() + '; ' if nick else '') + rest
    if m and other:
        info = f'ili {other}; ' + info                                      # "Trajković (Dodić)": the other surname
    rec = _record(last, given, father or '', info)
    rec['fathers_name'] = nominative(father or '')
    vm = FROM_VILLAGE.match(rest)
    if vm and vm.group(1).strip() in VILLAGES:
        rec['birth_place'] = VILLAGES[vm.group(1).strip()]
    d = death_date(rest)
    if d:
        rec['death_date'] = d
    return rec


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/3-makedonska.pdf',
        brigade_code=51,
        output_path='website/public/3-makedonska-soldiers.json',
        start_page=6,
        end_page=15,
        layout='single',
        script='cyrillic',
        entry_start_re=START,
        parse_entry_fn=parse_entry,
        line_filter=keep,
    )
