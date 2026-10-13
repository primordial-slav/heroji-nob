"""
Bitka kod Oborova (Milan Brunović, Tomo Sović; znaci.org 00003/660, the whole book 660.pdf) →
website/public/pdfs/bitka-kod-oborova-poginuli.pdf: a book across units, its entries added to the records of the
soldiers it describes (see scripts/match_references.py).

"Imena palih boraca" (book pp. 158-160, the whole book's PDF pp. 159-161): the 128 fighters of the II. moslavačka
brigada and the Posavski partizanski odred killed at Oborovo on 29 March 1944, numbered, a name a line in two columns,
surname first, a nickname after a dash ("34. Gluhak Rudo — »Brko«"). The account of the burial before them and the
monument's note after them are not read. Neither unit is on the site, so an entry has the name, the day and the place
of death (death_date, death_place) for the matcher; its men without a record go to unit 122.

Output: data-extraction/znaci/bitka-kod-oborova-poginuli-entries.json (IDs 9015xxxxxx, in the book's order).
Usage: python data-extraction/parse_bitka_kod_oborova.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import entry_boxes  # noqa: E402

PDF = 'bitka-kod-oborova-poginuli.pdf'
OUT = HERE / 'znaci' / 'bitka-kod-oborova-poginuli-entries.json'
PREFIX = '9015'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'


def read() -> list[dict]:
    entries = []
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            for col in entry_boxes.read_page(page, 2)['columns']:
                start_x = None
                for ln in col:
                    t = ln['text'].strip()
                    m = re.match(r'^(\d{1,3})\.\s+(?=[' + U + '])', t)
                    if m:
                        start_x = ln['x0']
                        entries.append({'no': int(m.group(1)), 'text': t[m.end():], 'pdf_page': pno,
                                        'pdf_x': round(ln['x0'], 1), 'pdf_y': round(ln['top'], 1)})
                    elif entries and start_x is not None and ln['x0'] > start_x + 5 and len(t) < 30:
                        entries[-1]['text'] += ' ' + t                 # "»Brko«" under its name
                    else:
                        start_x = None                                 # prose: the burial's account, the monument
    # the burial's count before the list is numbered too ("1. Oborovo 81, 2. Trebovec 52 ..."): the list is what
    # follows its own number 1
    first = max(i for i, e in enumerate(entries) if e['no'] == 1)
    return entries[first:]


def parse(e: dict, n: int) -> dict:
    text = re.sub(r'\s+', ' ', e['text']).strip()
    nick = ''
    m = re.search(r'\s*[—–-]?\s*»\s*-?([^«]+)«\s*$', text)
    if m:                                                              # "Gluhak Rudo — »Brko«", "Sešić Ivan — »-Sosa«"
        nick, text = m.group(1).strip(), text[:m.start()].rstrip(' —–-')
    text = re.sub(r'\b(?:dr|inž)\.?\s+', '', text).strip()              # "Hercigonja dr inž. Marko", "Čmelić dr Marijan"
    text = re.sub(r'\s+\d{3}$', '', text)                               # the page number: "Sekelj Anđela 159"
    words = []
    for w in text.split():
        if w == '...':
            continue
        if words and re.fullmatch(rf'[{L}]{{1,3}}', w):
            words[-1] += w                                             # "Badanj ek", "Žirovi ć", "Mati ja"
        else:
            words.append(w)
    last = words[0] if words else ''
    given = ' '.join(words[1:])
    shown = ' '.join(x for x in (last, given) if x) + (f' — {nick}' if nick else '')
    rec = {'soldier_id': f'{PREFIX}{n:06d}', 'name': shown, 'last_name': last, 'first_name': given, 'nick': nick,
           'fathers_name': '', 'birth_year': '', 'born_in': '', 'death_year': '1944', 'death_date': '1944-03-29',
           'death_place': 'Oborovo', 'units': [], 'no': e['no'],
           'additional_info': f"Pali u bici kod Oborova 29. III 1944: {e['no']}. {re.sub(chr(32) + '+', ' ', e['text']).strip()}"}
    rec.update(pdf_file=PDF, pdf_page=e['pdf_page'], pdf_x=e['pdf_x'], pdf_y=e['pdf_y'])
    return rec


def main():
    raw = read()
    recs = [parse(e, i) for i, e in enumerate(raw, 1)]
    stats = entry_boxes.fill_boxes(recs)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    nos = sorted(r['no'] for r in recs)
    print(f'{len(recs)} entries -> {OUT.relative_to(HERE.parent)}; missing numbers: {sorted(set(range(1, 129)) - set(nos))}')
    print(f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    for r in recs:
        if not re.fullmatch(rf'[{U}][{L}]+(?:-[{U}][{L}]+)? [{U}][{L}]+(?: — .+)?', r['name']):
            print('  odd:', r['no'], r['name'], '|', r['additional_info'])


if __name__ == '__main__':
    main()
