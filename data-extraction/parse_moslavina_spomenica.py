"""
Vukašin Karanović, *Moslavački partizanski odred* (znaci.org 00001/290, its part III's chapter 290_8.pdf, PDF pp.
138-141 → website/public/pdfs/moslavina-spomenica-1941.pdf, book pp. 629-632): "Pregled nosilaca Partizanske
spomenice 1941. s područja Moslavine", a book across units. One column, the surname and the given name in capitals,
a nickname after a hyphen, a mark after some: "ALTIĆ IVAN-JOVO*,". The note under the list: the holders living and
dead who were born in Moslavina or lived there long, the leaders of the KP, SKOJ, AFŽ and the NOO among them, since
they all worked for the odred's units; "*" marks those who died after the liberation, who lived through the war
(`survived`); the others the note leaves open (Tuđman Stjepan, unmarked, was killed in 1943). The re-typeset page
sets a second mark, '"', which the note does not explain: it stays in the text, as printed. The odred is not on the
site.

Output: data-extraction/znaci/moslavina-spomenica-1941-entries.json (IDs 9102xxxxxx, in the list's order).
Usage: python data-extraction/parse_moslavina_spomenica.py
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
import _karlovac_lists as kl  # noqa: E402
import parse_ofanziva_1942 as ofz  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

PDF = 'moslavina-spomenica-1941.pdf'
OUT = HERE / 'znaci' / 'moslavina-spomenica-1941-entries.json'
PREFIX = '9102'
TITLE = 'Pregled nosilaca Partizanske spomenice 1941. s područja Moslavine'
U = 'A-ZČĆŽŠĐ'
# the re-typeset page's slips: "1VANOVIĆ", "ĐURAN1Ć", "M1LOŠ-M1MA", "ŠP1RO", "VUKAŠ1N", "BALTIC" (Baltić?), "JAG A"
SLIPS = [('1', 'I'), ('JAG A', 'JAGA'), ('OGULI NAC', 'OGULINAC'), ('KVEŠTEK MATO', 'KVEŠTEK MATO')]


def read() -> list[dict]:
    out = []
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            words = viewer_words(page)
            rows = {}
            for w in words:
                rows.setdefault(round(w['top'] / 3), []).append(w)
            for key in sorted(rows):
                ws = sorted(rows[key], key=lambda w: w['x0'])
                text = ' '.join(w['text'] for w in ws).strip()
                if not text or text.startswith(('NAPOMENA', 'živi i umrli', 'tu duže', 'ušli i', 'radili na', '* Umrli')):
                    if text.startswith('NAPOMENA'):
                        return out
                    continue
                if re.fullmatch(r'\d{3}|[PREGLD ]+|NOSILACA PARTIZANSKE SPOMENICE 1941\.|S PODRUČJA MOSLAVINE', text):
                    continue
                if out and not text.rstrip().endswith(',') and not re.match(rf'[{U}]{{2,}}\s', text) and out[-1]['open']:
                    out[-1]['text'] += ' ' + text
                    out[-1]['open'] = not text.rstrip().endswith(',')
                    continue
                out.append({'text': text, 'open': not text.rstrip().endswith(','), 'pdf_page': pno,
                            'pdf_x': round(ws[0]['x0'], 1), 'pdf_y': round(ws[0]['top'], 1)})
    return out


def main():
    ofz.corpus()
    found = read()
    recs = []
    for no, e in enumerate(found, 1):
        printed = e['text'].rstrip(', ')
        t = printed
        for a, b in SLIPS:
            t = t.replace(a, b)
        mark = ''.join(re.findall(r'[*"]', t))
        t = re.sub(r'[*"]', '', t).strip()
        words = t.split()
        last = '-'.join(kl.spelled(w, 'last') for w in words[0].split('-'))
        given = words[1] if len(words) > 1 else ''
        nick = ''
        if '-' in given:
            given, nick = given.split('-', 1)
        first = kl.spelled(given, 'first') if given else ''
        nick = kl.title(nick) if nick else ''
        recs.append({'soldier_id': f'{PREFIX}{no:06d}', 'name': f'{last} {first}' + (f' — {nick}' if nick else ''),
                     'last_name': last, 'first_name': first, 'also': [], 'nick': nick, 'fathers_name': '',
                     'birth_year': '', 'born_in': '', 'death_year': '', 'survived': '*' in mark, 'units': [],
                     'no': no, 'list': TITLE, 'additional_info': f'{TITLE}: {printed}' + (
                         '. (* umro poslije oslobođenja)' if '*' in mark else ''),
                     'pdf_file': PDF, 'pdf_page': e['pdf_page'], 'pdf_x': e['pdf_x'], 'pdf_y': e['pdf_y']})
    stats = entry_boxes.fill_boxes(recs)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(recs)} entries -> {OUT.relative_to(HERE.parent)}')
    print(f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    print([r['name'] for r in recs])


if __name__ == '__main__':
    main()
