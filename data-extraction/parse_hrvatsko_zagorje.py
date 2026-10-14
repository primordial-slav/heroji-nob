"""
*Hrvatsko zagorje u revoluciji* (grupa autora, 1981; znaci.org 00003/647, the chapter 647_1.pdf →
website/public/pdfs/hrvatsko-zagorje-1981.pdf): "Popis poginulih učesnika NOB-a 1941-1945. s područja općina Donja
Stubica, Ivanec, Klanjec, Krapina, Pregrada, Zabok, Zaprešić i Zlatar-Bistrica", a book across units.

One column, alphabetical, flush, a bio each:
    "ANTOLIĆ (Ignaca) EDUARD, rođen 1920. u Svedruži—Krapina, stupio u Kalnički odred 15. 2. 1942, poginuo 18. 5. 1944.
    u Dugoj Rijeci kao komesar bataljona."
The list mixes the fighters with the victims of fascist terror ("ubijena ... kao ŽFT"), sympathizers and party members
killed in camps; only the fighters go in (the user's decision of 2026-10-14; the rule of parse_mosorski_odred_2.FIGHTER:
borac, a military duty, or a unit of the army he joined or served in). An entry starts after a wider gap with a surname
in capitals; the OCR spaces letters out ("ADA M IĆ (Stjepana) FRA N JO", "M arkuš Bregu"), which are joined again, the
father in brackets parting surname from given name, else the corpus choosing where a run of capitals splits
("W IN TER A M A N D A" = Winter Amanda). The units the site has that an entry names go to `units`.

The book's 1959 edition (*Hrvatsko zagorje u NOB*, 00003/648_1) prints the same list in shorter form; it is not read.

Output: data-extraction/znaci/hrvatsko-zagorje-1981-entries.json, IDs 9036xxxxxx (by the entry's place among all the
list's entries, so they stay put whatever the fighter rule keeps).
Usage: python data-extraction/parse_hrvatsko_zagorje.py [--sample N] [--dropped N]
"""
from __future__ import annotations

import json
import math
import random
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import _karlovac_lists as kl  # noqa: E402
import entry_boxes  # noqa: E402
import parse_ofanziva_1942 as ofz  # noqa: E402
from extract_life_events import iso, parse_when  # noqa: E402
from parse_mosorski_odred_2 import CHETNIK, FIGHTER, REAR  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

BOOK = 'hrvatsko-zagorje-1981'
PDF = HERE.parent / 'website' / 'public' / 'pdfs' / f'{BOOK}.pdf'
OUT = HERE / 'znaci' / f'{BOOK}-entries.json'
PREFIX = '9036'
TITLE = 'Popis poginulih učesnika NOB-a 1941-1945. s područja Hrvatskog zagorja'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
NOT_A_NAME = r'(?:NOB|NOV|NOVJ|NOO|KPJ|KPH|SKOJ|SKH|ŽFT|AFŽ|KK|OK|MK|PK|CK|USAOH|JNA|NDH|SS)\b'
# the units of the site an entry names
UNITS = [(r'Kalničk\w*\s+(?:partizansk\w*\s+)?odred', 58), (r'Zagrebačk\w*\s+(?:partizansk\w*\s+)?odred', 147),
         (r'\b32\.\s*divizij|»?Braća Radić|brigad\w*\s+»?Matija Gubec|Zagorsk\w*\s+brigad', 35),
         (r'\b(?:I|1\.)\s*zagorsk', 105), (r'\b13\.\s*proletersk|Rade Končar', 6)]


def lines() -> list[dict]:
    out = []
    with pdfplumber.open(PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            ws = sorted(viewer_words(page, keep_blank_chars=False), key=lambda w: (round(w['top']), w['x0']))
            rows = []
            for w in ws:
                if rows and abs(w['top'] - rows[-1]['top']) < 3:
                    rows[-1]['words'].append(w)
                else:
                    rows.append({'top': w['top'], 'words': [w]})
            for r in rows:
                r['words'].sort(key=lambda w: w['x0'])
                out.append({'text': ' '.join(w['text'] for w in r['words']), 'page': pno, 'top': r['top'],
                            'bottom': max(w['bottom'] for w in r['words']), 'x0': r['words'][0]['x0'],
                            'x1': max(w['x1'] for w in r['words'])})
    return out


def unspace(text: str) -> str:
    """"M arkuš Bregu" -> "Markuš Bregu", "D ubrovčanu" -> "Dubrovčanu" (a capital the OCR set apart)"""
    return re.sub(rf'(?<![{U}{L}])([{U}]) (?=[{L}]{{2}})', r'\1', text)


def read() -> list[dict]:
    entries, prev = [], None
    for ln in lines():
        t = unspace(ln['text'].replace('\xad', '-').strip())
        if re.fullmatch(r'[\d\W]{1,5}|[A-ZČĆŽŠĐ]', t) or re.match(r'^(?:POPIS\b|poginulih učesnika|K\s?rapina, Pregrada)', t):
            prev = ln
            continue                                     # page numbers, the letter headings, the list's title
        gap = ln['top'] - prev['bottom'] if prev and prev['page'] == ln['page'] else 99
        caps = re.match(rf'^(?!{NOT_A_NAME})[{U}](?:[{U}\-]|\s(?=[{U}]))+(?:\s*\(|\s+[{U}]{{2}}|,)', t)
        if caps and (gap > 3.2 or not entries):
            entries.append({'lines': [t], 'pdf_page': ln['page'], 'pdf_x': round(ln['x0'], 1), 'pdf_y': round(ln['top'], 1),
                            'box': [ln['x0'], ln['top'], ln['x1'], ln['bottom']]})
        elif entries:
            e = entries[-1]
            e['lines'].append(t)
            if ln['page'] == e['pdf_page']:
                b = e['box']
                e['box'] = [min(b[0], ln['x0']), b[1], max(b[2], ln['x1']), max(b[3], ln['bottom'])]
        prev = ln
    return entries


def join_lines(ls: list[str]) -> str:
    text = ''
    for ln in ls:
        if text.endswith('-') and re.match(rf'[{L}]', ln):
            text = text[:-1] + ln
        else:
            text += (' ' if text else '') + ln
    return re.sub(r'\s+', ' ', text).strip()


def score(word: str, part: str) -> float:
    n = ofz.known(word, part)[0]
    return math.log(1 + n) if n else -1.0


def split_caps(run: str) -> tuple[str, str]:
    """A run of capitals without the father's bracket, its letters spaced at random: the split into surname and given
    name the corpus knows best ("WIN TER A M A N D A" -> WINTER, AMANDA)"""
    parts = run.split()
    if len(parts) == 2 and all(len(p) > 2 for p in parts):
        return parts[0], parts[1]
    joined = ''.join(parts)
    cuts = sorted({sum(len(p) for p in parts[:i]) for i in range(1, len(parts))})
    best = max(cuts, key=lambda c: score(joined[:c], 'last') + score(joined[c:], 'first'), default=None)
    if best is None:
        return joined, ''
    return joined[:best], joined[best:]


def parse(e: dict, n: int) -> dict:
    text = join_lines(e['lines'])
    text = text.translate(kl.OCR).translate(str.maketrans('ÒÓÀÁÈÉÙÚ', 'OOAAEEUU'))       # "ANDRÒ"
    text = re.sub(rf'(?<=[{U}])1(?=[{U}])', 'I', text)                                 # "GABR1JELA"
    text = re.sub(rf'(?<=[{U}])\.I(?=[{U}])', 'J', text)                               # "MI.IO" = MIJO
    m = re.match(rf'^(.*?)\s*\(\s*([^)]+?)\s*\)\s*([{U}][{U}\s\-]*?)\s*(?=[,.]|$)', text)   # "IVAN. rođen"
    if m and ',' not in m.group(1):
        surname, father, given = re.sub(r'\s*-\s*', '-', m.group(1)).replace(' ', ''), m.group(2).replace(' ', ''), m.group(3)
        rest = text[m.end():]
        given_parts = given.split()
        # a given name spaced out ("FRA N JO") is one word; two long ones are a name and what he was called
        if len(given_parts) > 1 and any(len(p) <= 2 for p in given_parts):
            given = ''.join(given_parts)
    else:
        head = re.match(rf'^([{U}\s\-]+?)\s*(?=[,.]|$)', text)
        run = re.sub(r'\s*-\s*', '-', head.group(1)) if head else text.split(',')[0]
        surname, given = split_caps(run)
        father, rest = '', text[head.end():] if head else text[len(text.split(',')[0]):]
    rest = rest.lstrip(' ,.')
    given_words = given.split()
    first = kl.spelled(given_words[0], 'first') if given_words else ''
    nick = ' '.join(kl.title(w) for w in given_words[1:])
    last = '-'.join(kl.spelled(p, 'last') for p in surname.split('-') if p)
    rec = {'soldier_id': f'{PREFIX}{n:06d}',
           'name': ' '.join(x for x in (last, f'({father})' if father else '', first, nick) if x),
           'last_name': last, 'also': [], 'first_name': first, 'nick': nick, 'fathers_name': father}
    born = re.search(r'\bro[đd]en[a]?\s+(?:[\d.\s]*?(1[89]\d\d)\.?\s*(?:god\.?\s*|godine\s*)?)?(?:u\s+([^,]+))?', rest)
    rec['birth_year'] = (born.group(1) or '') if born else ''
    place = (born.group(2) if born and born.group(2) else
             (re.search(r'\biz\s+([^,]+)', rest).group(1) if re.search(r'\biz\s+([^,]+)', rest) else ''))
    place = re.split(r'\s+(?:poginu|strijelj|ubijen|umr|nesta|stupi|radnik|zemljoradn)', place)[0]   # "Jesenju Gornjem poginula"
    rec['born_in'] = re.sub(r'\s*[—–-]+\s*', ', ', place.strip(' .')) if place else ''
    death = list(re.finditer(r'\b(?:poginu[oa]|strijeljan[a]?|ubijen[a]?|umro|umrla|nesta[oa]|nestala|obješen[a]?|ubil[ei])\b', rest, re.I))
    after = rest[death[0].start():] if death else ''
    y = re.search(r'\b(19[34]\d)\b', after[:120])
    rec['death_year'] = y.group(1) if y else ''
    when = re.search(r'\b\d{1,2}\.\s?\d{1,2}\.\s?19[34]\d', after[:120])
    parsed = parse_when(when.group(0)) if when else None
    rec['death_date'] = iso(parsed[0]) if parsed and parsed[0][2] else ''
    rec['units'] = sorted({code for pat, code in UNITS if re.search(pat, rest, re.I)})
    rec['additional_info'] = rest
    rec['list'] = TITLE
    b = e['box']
    rec.update(pdf_file=PDF.name, pdf_page=e['pdf_page'], pdf_x=e['pdf_x'], pdf_y=e['pdf_y'],
               pdf_x_end=round(b[2], 1), pdf_y_end=round(b[3], 1))
    return rec


def fighter(rec: dict) -> bool:
    info = REAR.sub('', rec['additional_info'])
    if re.search(r'\bŽFT\b|simpatizer|suradnik|saradnik', info) and not re.search(r'\bbor(?:ac|kinja)\b', info):
        return False
    return bool(FIGHTER.search(info)) and not CHETNIK.search(info)


def main() -> None:
    if not PDF.exists():
        shutil.copy(HERE / '.cache' / 'znaci_library' / 'chapters' / '00003_647_1.pdf', PDF)
    ofz.corpus()
    raw = read()
    recs = [parse(e, i) for i, e in enumerate(raw, 1)]
    kept = [r for r in recs if fighter(r)]
    OUT.write_text(json.dumps(kept, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(recs)} entries read, {len(kept)} fighters -> {OUT.relative_to(HERE.parent)}')
    print(f"no given: {sum(not r['first_name'] for r in kept)}, father: {sum(bool(r['fathers_name']) for r in kept)}, "
          f"birth year: {sum(bool(r['birth_year']) for r in kept)}, death year: {sum(bool(r['death_year']) for r in kept)}, "
          f"units: {Counter(u for r in kept for u in r['units'])}")
    random.seed(4)
    if '--sample' in sys.argv:
        for r in random.sample(kept, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  IN  {r['name']!r} [{r['born_in']}] {r['birth_year']} d{r['death_year']} {r['units']} | {r['additional_info'][:110]}")
    if '--dropped' in sys.argv:
        out = [r for r in recs if r not in kept]
        for r in random.sample(out, int(sys.argv[sys.argv.index('--dropped') + 1])):
            print(f"  OUT {r['name']!r} | {r['additional_info'][:130]}")


if __name__ == '__main__':
    main()
