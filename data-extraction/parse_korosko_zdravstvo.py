"""
Anton Ikovic, Marijan Linasi, *Koroško partizansko zdravstvo* (Partizanska knjiga, Ljubljana 1985; znaci.org
00003/756.pdf, PDF pp. 282-355 = book pp. 282-355) → website/public/pdfs/korosko-zdravstvo.pdf: "Seznami pacientov in
osebja z osnovnimi podatki", a book across units. Four numbered lists, one column, a short bio under each name:
    I.   the wounded and sick fighters and activists in Carinthia and the Solčava area to February 1944 (35)
    II.  the patients of the Carinthian partisan hospitals and the Carinthian units' fighters treated in others (227)
    III. "Koroški borci" treated outside the hospitals after February 1944, at farms, in bunkers, in the units
    IV.  the medical staff who worked in Carinthia or were tied to its partisan medicine
         "6. KASTELIC Franjo-Džon / Rojen 1. 9. 1921 v Trbovljah. / V NOV 28. 7. 1941 v Revirsko četo, ..."
List III is titled as the fighters' and goes in whole; of the others only those the bio puts in the army (NOV, a unit,
a duty in it or in an army hospital), by the rule for mixed lists: political workers in the field, doctors who sent
medicines to the partisans, helpers stay out. A man in two lists ("natančnejši opis v seznamu II") is one entry with
both texts. One whose name the book doesn't know ("JANKO (priimek in ime neznana)", "ALEKS") is `unnamed`. Slovene
surnames keep their -ič; the OCR's 1 for I in capitals and its spaced names are read back.
Output: data-extraction/znaci/korosko-zdravstvo-entries.json, IDs 9058xxxxxx in the book's order, each with its box.
Usage: python data-extraction/parse_korosko_zdravstvo.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz
import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import entry_boxes  # noqa: E402
import parse_mosorski_odred_2 as mos  # noqa: E402
import parse_ofanziva_1942 as ofz  # noqa: E402
import _karlovac_lists as kl  # noqa: E402

BOOK = 'korosko-zdravstvo'
PDF = HERE.parent / 'website' / 'public' / 'pdfs' / f'{BOOK}.pdf'
SOURCE = HERE / '.cache' / 'korosko' / '756.pdf'                    # znaci.org/00003/756.pdf
OUT = HERE / 'znaci' / f'{BOOK}-entries.json'
PREFIX = '9058'
FIRST_PAGE = 282                                                   # the site PDF's page 1 is the book's p. 282
U, L = 'A-ZČĆŽŠĐÖÜ', 'a-zčćžšđöü'
HEADINGS = [(re.compile(r'^I\.\s+RANJENI IN BOLNI'), 'I', 'Ranjeni in bolni borci in aktivisti na Koroškem in '
             'Solčavskem od začetka NOV do februarja 1944'),
            (re.compile(r'^RANJENCI IN BOLNIKI, KI SO SE ZDRAVILI'), 'II', 'Ranjenci in bolniki koroških in solčavskih '
             'partizanskih bolnišnic ter borci koroških enot, ki so se zdravili v drugih bolnišnicah'),
            (re.compile(r'^(?:III\.\s+)?KOROŠKI BORCI, KI SO SE PO FEBRUARJU'), 'III', 'Koroški borci, ki so se po februarju 1944 '
             'zdravili izven koroških partizanskih bolnišnic'),
            (re.compile(r'^IV\.\s+SANITETNO OSEBJE'), 'IV', 'Sanitetno osebje, ki je delovalo na Koroškem in Solčavskem '
             'ali bilo povezano s koroškim partizanskim zdravstvom')]
# in the army: NOV, a unit, a duty in it or in an army hospital (not "partizan" alone: "pošiljal partizanom zdravila")
ARMY_WORDS = re.compile(r'bore[ck]|bork[aeio]|bataljon|brigad|odred|\bčet[aeio]\b|divizij|\bcon[ae]\b|komandir|komandant'
                        r'|namestnik|kurir|intendant|bolničar|obveščeval|vodnik|desetar|politkomisar|komisar|referent'
                        r'|sanitet\w* odsek|ekonom|član\w* osebja|delovne ekipe', re.I)   # a partisan hospital's staff
ARMY_ABBR = re.compile(r'\bV NOV\b|\bNOV\b|\bNOVJ\b|\bVKO\b|\bZKO\b|\bKO\b|K\.\s?O\.|\bVOS\b|\bVPB\b|SVPB')


def army(text: str) -> bool:
    return bool(ARMY_WORDS.search(text) or ARMY_ABBR.search(text))


# Read again on 2026-10-19, when the user had the mixed lists' activists added, marked: a patient whom his comrades
# carried ("Soborci so ga ...") is a fighter; the movement's people the entry names (SKOJ, the party's political
# workers, the illegal printing shop "Netopir") are activists, and so is everyone in list IV, the medical service's
# helpers (the doctors and nurses in the towns who sent the partisans medicines, the leaders of the field ambulances),
# whose entry says what they did; a patient of whom nothing more is known stays out
SOBOREC = re.compile(r'\bsoborc\w*', re.I)


def later(person: dict, p: dict, text: str) -> str:
    if SOBOREC.search(text):
        return 'fighter'
    if mos.activist({'additional_info': text}):
        return 'activist'
    if 'IV' in person['kinds'] and len(p['text'].split()) > 4:
        return 'activist'
    return ''
UNITS = [(r'Šercerjev', 141), (r'Tomšičev', 70), (r'Zidanškov', 65), (r'Bračičev', 69), (r'Gradnikov', 64),
         (r'Cankarjev\w* brigad', 61), (r'Gubčev', 62), (r'Kosovelov', 142), (r'Kozjansk\w* odred', 164),
         (r'Kokršk\w* odred', 171), (r'Zapadnodolenjsk\w* odred', 68), (r'Ljubljansk\w* brigad', 4),
         (r'Dvanajst\w* brigad|XII\. brigad', 63)]
FIXES = {'TOM AZI N': 'TOMAZIN', 'SLEjyiENIK': 'SLEMENIK', 'KMET _Janez': 'KMET Janez'}


def build_pdf() -> None:
    if not PDF.exists():
        out = fitz.open()
        out.insert_pdf(fitz.open(SOURCE), from_page=FIRST_PAGE - 1, to_page=354)
        out.save(PDF, garbage=4, deflate=True)


def lines() -> list[dict]:
    out = []
    with pdfplumber.open(PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            for ln in entry_boxes.read_page(page, columns=1)['columns'][0]:
                t = re.sub(r'\s+', ' ', ln['text']).strip()
                if re.fullmatch(r'\d{3}', t):
                    continue
                out.append({'text': t, 'page': pno, 'x0': ln['x0'], 'top': ln['top'], 'x1': ln['x1'],
                            'bottom': ln['bottom']})
    return out


def read() -> list[dict]:
    """The entries of the four lists in the book's order: an entry starts at the next number of its list"""
    entries, kind, title, last_no, pending, prev_x = [], None, '', 0, None, None
    for ln in lines():
        t = ln['text']
        for k, v in FIXES.items():
            t = t.replace(k, v)
        head = next(((k, ti) for rx, k, ti in HEADINGS if rx.match(t)), None)
        if head:
            kind, title = head
            last_no, pending = 0, None
            continue
        if not kind:
            continue
        if t.startswith('Imen in priimkov ter drugih podatkov'):              # the note closing list I
            continue
        m = re.match(r'^(\d{1,3})\s?\.\s*(.*)$', t)
        # the list's next number, or one or two further on where the text layer lost a number, before a name in
        # capitals ("9. B1L1NA Marija" after 7.: no 8. on the page)
        name = m and re.match(rf'^(?:Dr\.\s*)?[{U}][{U}1]{{2,}}', m.group(2))
        if m and (int(m.group(1)) == last_no + 1 and (not m.group(2) or name or re.match(rf'^[{U}][{L}]', m.group(2)))
                  or last_no + 1 < int(m.group(1)) <= last_no + 5 and name):
            if int(m.group(1)) != last_no + 1:
                print(f'  {kind}: no number {last_no + 1} before {t[:40]!r}')
            last_no = int(m.group(1))
            entries.append({'kind': kind, 'title': title, 'no': last_no, 'lines': [m.group(2)] if m.group(2) else [],
                            'page': ln['page'], 'x0': ln['x0'], 'top': ln['top']})
            prev_x = None                                              # the name's own line: no bio yet to compare
            continue
        # a number the OCR garbled ("]9 BUGA Ivan") at the margin the entries start at: the next number
        g = re.match(rf'^[^\w\s]{{1,2}}\d?\s+((?:Dr\.\s*)?[{U}][{U}1]{{2,}}\s[{U}][{L}]+.*)$', t)
        if g and entries and entries[-1]['kind'] == kind and abs(ln['x0'] - entries[-1]['x0']) < 8:
            last_no += 1
            print(f'  {kind}: {last_no}. read from a garbled number: {t[:40]!r}')
            entries.append({'kind': kind, 'title': title, 'no': last_no, 'lines': [g.group(1)], 'page': ln['page'],
                            'x0': ln['x0'], 'top': ln['top'], 'guessed': True})
            prev_x = None
            continue
        # a name alone on its line, right of the bio before it: its number is lost in the text layer ("BÖHM Janez",
        # "Dr. DRŽAJ Peter, šef sanitetnega odseka ...", "CVETKO")
        if entries and entries[-1]['kind'] == kind and prev_x is not None and ln['x0'] > prev_x + 10 and re.match(
                rf'^(?:Dr\.\s*)?[{U}][{U}1]{{2,}}(?:\s\([^)]*\))?(?:\s[{U}][{L}]+(?:-[{U}][{L}]+)?(?:,.*)?)?$', t) \
                and not re.match(r'^(?:VPB|SVPB|VKO|ZKO|KO|PE|OF|KPS|SZC)\b', t):
            last_no += 1
            print(f'  {kind}: {last_no}. read from a name alone: {t[:40]!r}')
            entries.append({'kind': kind, 'title': title, 'no': last_no, 'lines': [t], 'page': ln['page'],
                            'x0': ln['x0'], 'top': ln['top'], 'guessed': True})
            prev_x = ln['x0']
            continue
        if entries and entries[-1]['kind'] == kind:
            entries[-1]['lines'].append(t)
        prev_x = ln['x0']
    return entries


def spell(word: str) -> str:
    """A surname in capitals in the site's spelling: the OCR's 1 for I, a caron the site's records agree it lost"""
    w = re.sub(rf'(?<=[{U}])1|1(?=[{U}])', 'I', word)
    c = ofz._spell['last'].get(w.upper().translate(ofz.FOLD), {})
    fits = [s for s, n in sorted(c.items(), key=lambda x: -x[1]) if n >= 3 and len(s) == len(w)
            and all(a == b or (a != 'Đ' and b in ofz.LOST.get(a, '')) for a, b in zip(w.upper(), s))]
    return kl.title(fits[0]) if fits else kl.title(w)


def parse(e: dict) -> dict | None:
    text = ' '.join(e['lines'])
    text = re.sub(r'(?<=[a-zčšž])[-\xad]\s(?=[a-zčšž])', '', text)
    text = re.sub(r'(?<=\d)\s(?=\d\s?\.)|(?<=\d)\s(?=\d)', '', text)      # "1 1 . 9 . 1944"
    m = re.match(rf'^(Dr\.\s*)?([{U}1][{U}1\'-]+(?:\s[{U}1]{{2,}})*)(\s\([^)]*\))?(?:\s+([{U}][{L}]+)'
                 rf'(?:-\s?([{U}][{L}]+))?)?,?\s*(.*)$', text)
    if not m:
        return {'unnamed': True, 'text': text}
    dr, last, maiden, given, nick, bio = m.groups()
    unnamed = not given or (maiden or '').startswith(' (priimek') or 'priimek in ime nezna' in text[:60]
    last = ' '.join(spell(p) for p in last.split()) if len(last.split()) == 1 else spell(last.replace(' ', ''))
    return {'unnamed': unnamed, 'last': last, 'given': given or '', 'nick': nick or '', 'maiden': (maiden or '').strip(' ()'),
            'dr': bool(dr), 'bio': bio, 'text': text}


def main() -> None:
    build_pdf()
    ofz.corpus()
    raw = read()
    counts = {}
    for e in raw:
        counts[e['kind']] = counts.get(e['kind'], 0) + 1
    print('entries per list:', counts)
    people, order = {}, []                                              # one man in two lists is one entry
    for e in raw:
        p = parse(e)
        key = None if p['unnamed'] else (p['last'], p['given'])
        printed = f"{e['title']}: {'' if e.get('guessed') else str(e['no']) + '. '}{p['text']}"
        if key and key in people:
            people[key]['texts'].append(printed)
            people[key]['kinds'].add(e['kind'])
            continue
        person = {'e': e, 'p': p, 'texts': [printed], 'kinds': {e['kind']}}
        if key:
            people[key] = person
        order.append(person)
    out, left, added = [], [], []
    for person in order:
        e, p, all_text = person['e'], person['p'], ' '.join(person['texts'])
        new = ''
        if 'III' not in person['kinds'] and not army(all_text):
            new = later(person, p, all_text)
            if not new:
                left.append(f"{e['kind']} {e['no']}. {p['text'][:100]}")
                continue
        born = re.search(r'\bRoj(?:en|ena|\.)\b[^;]{0,25}?((?:18|19)\d\d)', all_text)
        died = re.search(r'\b(?:Padel|Padla|[Uu]mrl[a]?|[Uu]streljen\w*|[Pp]obit\w*)\b[^;]{0,40}?(194\d)', all_text)
        rec = {'soldier_id': '', 'name': ' '.join(x for x in (p.get('last'), p.get('given')) if x),
               'last_name': p.get('last', ''), 'first_name': p.get('given', ''), 'nick': p.get('nick', ''),
               'fathers_name': '', 'birth_year': born.group(1) if born else '', 'born_in': '',
               'death_year': died.group(1) if died else '',
               'units': sorted({c for pat, c in UNITS if re.search(pat, all_text)}), 'list': '+'.join(sorted(person['kinds'])),
               'additional_info': 'Koroško partizansko zdravstvo: ' + ' '.join(person['texts']),
               'source_page': FIRST_PAGE - 1 + e['page'],
               'pdf_file': PDF.name, 'pdf_page': e['page'], 'pdf_x': round(e['x0'], 1), 'pdf_y': round(e['top'], 1)}
        if p['unnamed']:
            rec['unnamed'] = True
        if new == 'activist':
            rec['role'] = 'activist'
        if new and rec['first_name'] in ('Zdravnik', 'Zdravnica', 'Učitelj', 'Učiteljica'):
            # "Dr. ARH Zdravnik na Ljubnem ob Savinji": the book gives the surname and the trade, no given name
            rec['first_name'], rec['name'] = '', rec['last_name']
        rec['_at'] = len(out) + len(added)
        (added if new else out).append(rec)
    for i, r in enumerate(out, 1):
        r['soldier_id'] = f'{PREFIX}{i:06d}'
    for i, r in enumerate(added, 1001):                      # after the first reading's, whose numbers stay put
        r['soldier_id'] = f'{PREFIX}{i:06d}'
    print(f"added on 2026-10-19: {sum(not r.get('role') for r in added)} fighters, "
          f"{sum(bool(r.get('role')) for r in added)} activists")
    out = sorted(out + added, key=lambda r: r.pop('_at'))
    stats = entry_boxes.fill_boxes(out)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(out)} entries -> {OUT.relative_to(HERE.parent)}; boxes: {entry_boxes.describe(stats, stats["boxed"])}')
    print(f'left out ({len(left)}):')
    for x in left:
        print('  ', x)


if __name__ == '__main__':
    main()
