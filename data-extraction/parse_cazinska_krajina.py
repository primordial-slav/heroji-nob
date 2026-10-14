"""
Dušan D. Miljković, *Stradanja u Cazinskoj krajini i antifašistička borba (1941-1945)* (znaci.org 00003/587, the whole
book's PDF pp. 428-461: "B) Spisak palih boraca u Cazinskoj krajini") → website/public/pdfs/cazinska-krajina-pali-borci.pdf:
a book across units. The book's list A, the Serbian civilian victims, stays out; list B is the fallen fighters only, by
opština (Bihać, Bosanska Krupa, Cazin, Velika Kladuša: each a heading across both columns at the top of a page) and
village, numbered within the village, two columns, a line each:
    "1. Abdihodžić Abdo Ibrahim 1905/44" (surname, the father in the nominative, given name, born/fell; "1914/?" too)
A line too long for the column puts its years on the next line ("1924/44" alone); a village's name may run over two
lines ("TODOROVSKA" / "SLAPNICA").
Output: data-extraction/znaci/cazinska-krajina-pali-borci-entries.json, IDs 9040xxxxxx, each with its box.
Usage: python data-extraction/parse_cazinska_krajina.py [--sample N]
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import fitz
import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import _karlovac_lists as kl  # noqa: E402
import entry_boxes  # noqa: E402
import parse_ofanziva_1942 as ofz  # noqa: E402

BOOK = 'cazinska-krajina-pali-borci'
PDF = HERE.parent / 'website' / 'public' / 'pdfs' / f'{BOOK}.pdf'
OUT = HERE / 'znaci' / f'{BOOK}-entries.json'
PREFIX = '9040'
TITLE = 'Spisak palih boraca u Cazinskoj krajini'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
# born/fell at the line's end, as printed: "1905/44", "1927-1943" (Perna), "1914/?", "1923/", "192/41", "/43", "?//44", "1928/45 ."; the book
# sets a second pair after some ("Saljić Osman Husein 1925/44 1888/43", the line before's years): the first is his
YEARS = re.compile(r'(\d{3,4}|\?)?\s*[/-]+\s*(\d{2,4}|\?)?')
ENTRY = re.compile(rf'^(?:(\d{{1,3}})\s?\.\s*)?([{U}][{L}]+(?:-[{U}][{L}]+)?\s.+?)\s*([\d?/.\s-]*)$')
# the opština a page's heading opens (set across both columns above the lists: "OPŠTINA" | "BIHAĆ"; the OCR lost Velika)
OPSTINA = {1: 'Bihać', 7: 'Bosanska Krupa', 16: 'Cazin', 25: 'Velika Kladuša'}
HEAD_BELOW = 345                      # the title and the opština's heading stand above this on those pages
VILLAGES = {'BAG - BORCI': 'Bag', 'BOS. BOJNA': 'Bosanska Bojna', 'MEDJUDRAŽJE': 'Međudražje', 'TODORVO': 'Todorovo',
            'KUDICI': 'Kudići', 'GORNJI SUMATAC': 'Gornji Šumatac', 'ŠTURL1ĆKA PLATNICA': 'Šturlićka Platnica'}
SLIPS = {'Pastuvlvan': 'Pastuv Ivan', 'I.ukić': 'Lukić', 'Mirkol925': 'Mirko 1925', '.192243': '1922/43',
         'Haj rulahović': 'Hajrulahović', 'Tin tor': 'Tintor'}         # the text layer (and znaci's re-typeset page)


def build_pdf() -> None:
    if not PDF.exists():
        src, out = fitz.open(HERE / '.cache' / 'znaci_library' / 'chapters' / '00003_587.pdf'), fitz.open()
        out.insert_pdf(src, from_page=427, to_page=460)
        out.save(PDF, garbage=4, deflate=True)


def place(t: str) -> str:
    return VILLAGES.get(t) or ' '.join(w.capitalize() if w.isupper() else w for w in t.split())


def read() -> list[dict]:
    out, opstina, village, heading = [], '', '', []
    with pdfplumber.open(PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            data = entry_boxes.read_page(page, columns=2)
            for col in data['columns']:
                for ln in col:
                    t = ln['text'].strip()
                    if pno in OPSTINA and ln['top'] < HEAD_BELOW:
                        opstina = OPSTINA[pno]
                        continue
                    if re.fullmatch(r'[\d\W]{1,4}', t):
                        continue
                    if re.fullmatch(rf'[{U}][{U}\d\s\-.]+', t) and len(t) < 40:
                        heading.append(t)                      # a village; one over two lines comes in two
                        village = place(' '.join(heading))
                        continue
                    heading = []
                    for slip, read_as in SLIPS.items():
                        t = t.replace(slip, read_as)
                    t = re.sub(rf'(?<=[{L}])(?=[{U}])', ' ', t)          # "MujkićMeho"
                    if re.fullmatch(r'[\d?/.\s-]+', t) and re.search(r'\d[/-]|[/-]\d', t):
                        if out and not out[-1]['tail']:        # the years of the line before
                            out[-1]['tail'] = t
                        continue
                    e = ENTRY.match(t)
                    if e:
                        # a number the OCR lost ("Zorić Stevan Spaso 1925/45" after "9. Zorić Milan Đuro")
                        no = int(e.group(1)) if e.group(1) else out[-1]['no'] + 1
                        out.append({'no': no, 'name': e.group(2), 'tail': e.group(3).strip(),
                                    'pdf_page': pno, 'pdf_x': round(ln['x0'], 1), 'pdf_y': round(ln['top'], 1),
                                    'opstina': opstina, 'village': village, 'text': t})
                    else:
                        print(f'  p{pno} not read: {t!r}')
    return out


def year(y: str | None) -> str:
    if not y or y == '?' or len(y) == 3:
        return ''
    return y if len(y) == 4 else '19' + y


def parse(e: dict, n: int) -> dict:
    words = e['name'].split()
    also = words.pop(1) if len(words) == 4 else ''       # two surnames ("Uzelac Savić Risto Jovanka")
    last = words[0] if words else ''
    father, given = (words[1], ' '.join(words[2:])) if len(words) >= 3 else ('', ' '.join(words[1:]))
    first, nick = (given.split('-', 1) + [''])[:2] if '-' in given else (given, '')
    last = '-'.join(kl.spelled(p.upper(), 'last') for p in last.split('-') if p)
    y = YEARS.search(e['tail'])
    by, dy = (year(y.group(1)), year(y.group(2))) if y else ('', '')
    where = ', '.join(x for x in (e['village'], f"opština {e['opstina']}" if e['opstina'] else '') if x)
    rec = {'soldier_id': f'{PREFIX}{n:06d}', 'name': e['name'], 'last_name': last, 'also': [also] if also else [], 'first_name': first,
           'nick': nick, 'fathers_name': father.rstrip('.') + ('.' if father.endswith('.') else ''),
           'birth_year': by, 'born_in': e['village'] if e['village'] == e['opstina'] else ', '.join(x for x in (e['village'], e['opstina']) if x),
           'death_year': dy, 'no': e['no'],
           'additional_info': f"{TITLE}, {where}: {e['name']}" + (f", {by or '?'}–{dy or '?'}" if by or dy else ''),
           'list': TITLE, 'pdf_file': PDF.name, 'pdf_page': e['pdf_page'], 'pdf_x': e['pdf_x'], 'pdf_y': e['pdf_y']}
    return rec


def main() -> None:
    build_pdf()
    ofz.corpus()
    raw = read()
    recs = [parse(e, i) for i, e in enumerate(raw, 1)]
    stats = entry_boxes.fill_boxes(recs)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(recs)} fallen fighters -> {OUT.relative_to(HERE.parent)}; {dict(Counter(e["opstina"] for e in raw))}')
    print(f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    gaps, prev = [], None
    for e in raw:
        key = (e['opstina'], e['village'])
        if prev and prev[0] == key and e['no'] != prev[1] + 1:
            gaps.append(f"{e['village']} {prev[1]}->{e['no']} (p{e['pdf_page']})")
        prev = (key, e['no'])
    print(f'number gaps: {len(gaps)}', gaps[:20])
    print(f"father: {sum(bool(r['fathers_name']) for r in recs)}, birth year: {sum(bool(r['birth_year']) for r in recs)}, "
          f"death year: {sum(bool(r['death_year']) for r in recs)}")
    if '--sample' in sys.argv:
        random.seed(5)
        for r in random.sample(recs, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  {r['last_name']}|{r['fathers_name']}|{r['first_name']} [{r['born_in']}] {r['birth_year']}-{r['death_year']}")


if __name__ == '__main__':
    main()
