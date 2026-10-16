"""
Parser: Osječka udarna brigada (brigade code 104) — its leaders, a third list.

Source: Zdravko B. Cvetković, "Osječka udarna brigada", V, "Spisak rukovodilaca Osječke brigade" (znaci.org
        00003/450.pdf, its pages 198-201, book pp. 203-206, just before the fallen on the site)  →
        website/public/pdfs/osjecka-rukovodioci.pdf.
Under each duty in capitals, a name a line in capitals, a nickname after it and a fate in brackets:
    KOMANDANTI BRIGADE:
    BABAC MILIVOJ Obilić (poginuo 13. 11. 1944. u s. Piškorevcima)
The commanders and commissars of the companies stand in one list. The OCR lost most carons and reads I as l
("DOTLlC"); names are put right from the spellings the other units print, as for the fallen and survivors
(parse_osjecka's helpers). A man in several posts is one record with each; his box is around his name at each post
on his first post's page. The fallen and survivors are the unit's first list (IDs from 1), the women of Žene Hrvatske
the second (10001); these get IDs from 20001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

import parse_8_kordunaska_divizija as k8
import parse_osjecka as osj
from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/osjecka-rukovodioci.pdf'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00003_450.pdf'   # znaci.org 00003/450.pdf
FIRST_PAGE, LAST_PAGE = 198, 201
TITLE = 'Spisak rukovodilaca Osječke brigade'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
LINES: dict = {}                                                             # (page, y, x) -> the line's box
# the text layer's slips, read from the list's order: "DULETA" between BRAZDA and BUZAĐŽIĆ, "NJGO VANO VIC"
WORDS = [('DULETA', 'BULETA'), ('NJGO VANO VIC', 'NJEGOVANOVIC'), ('BUZAĐZlC', 'BUZADŽIĆ')]


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


def read_lines(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    out = []
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages[start_page - 1:end_page], start_page):
            rows: list = []
            for w in sorted(viewer_words(page), key=lambda w: (w['top'], w['x0'])):
                row = next((r for r in rows if abs(r[0]['top'] - w['top']) <= 3), None)
                (rows.append([w]) if row is None else row.append(w))
            for r in sorted(rows, key=lambda r: r[0]['top']):
                r.sort(key=lambda w: w['x0'])
                ln = {'text': ' '.join(w['text'] for w in r), 'x': round(r[0]['x0'], 1), 'y': round(r[0]['top'], 1), 'page': n}
                LINES[(n, ln['y'], ln['x'])] = (ln['x'], ln['y'], round(max(w['x1'] for w in r), 1),
                                                round(max(w['bottom'] for w in r), 1))
                out.append(ln)
    return out


DUTY = {'d': ''}


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        t = ln['text'].strip()
        if re.fullmatch(r'[\d\W]{1,6}|V', t) or t in ('SPISAK RUKOVODILACA', 'OSJEČKE BRIGADE'):
            ln['drop'] = True
        elif t.endswith(':'):                                                # "KOMANDANTI BRIGADE:"
            DUTY['d'] = t.rstrip(':').replace('CETA', 'ČETA').capitalize().replace('brigade', 'brigade')
            ln['drop'] = True
        else:
            ln['text'] = f"§§{DUTY['d']}|{t}"


def keep(ln: dict) -> bool:
    return not ln.get('drop')


def parse(text: str) -> dict:
    duty, line = text[2:].split('|', 1)
    for a, b in WORDS:
        line = line.replace(a, b)
    fate = ''
    m = re.search(r'\(([^)]*)\)\s*$', line)
    if m:
        fate, line = m.group(1).strip(), line[:m.start()].strip()
    words = line.split()
    caps = [w for w in words if re.fullmatch(rf'[{U}][{U}l]+', w)]
    nick = [w for w in words if w not in caps]
    last = k8.join_parts([k8.caps_word(c) for c in caps[:-1]], 'last_name')
    given = k8.caps_word(caps[-1]).title() if len(caps) > 1 else ''
    rec = _record(last, given, '', '')
    rec['_duty'], rec['_nick'], rec['_fate'] = duty, ' '.join(nick), fate
    return rec


def men(soldiers: list[dict]) -> list[dict]:
    soldiers = k8.post(soldiers)                                             # the corpus's spellings
    out, seen = [], {}
    for s in soldiers:
        key = (s['last_name'], s['first_name'])
        man = seen.get(key)
        if man is None:
            man = seen[key] = s
            s['_duties'], s['_nicks'], s['_fates'], s['_rects'] = [], [], [], []
            out.append(s)
        if s['_duty'] not in man['_duties']:
            man['_duties'].append(s['_duty'])
        for k, v in (('_nicks', s['_nick']), ('_fates', s['_fate'])):
            if v and v not in man[k]:
                man[k].append(v)
        if s['pdf_page'] == man['pdf_page']:
            man['_rects'].append(list(LINES[(s['pdf_page'], s['pdf_y'], s['pdf_x'])]))
    for s in out:
        notes = [f"zvani {n}" for n in s['_nicks']]
        s['additional_info'] = '; '.join(notes + [f"{TITLE}: {'; '.join(d[:1].lower() + d[1:] for d in s['_duties'])}"]
                                         + s['_fates'])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        s['full_name'] = f"{s['last_name']} {s['first_name']}".strip()
        for k in ('_duty', '_nick', '_fate', '_duties', '_nicks', '_fates', '_rects'):
            s.pop(k, None)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    osj.corpus()
    run_parser(pdf_path=PDF, brigade_code=104, output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/osjecka-soldiers.json',
               extract_fn=read_lines, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, prepare_fn=prepare,
               line_filter=keep, post_fn=men, id_start=20001, keep_other_sources=True)
