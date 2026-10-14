"""
Radule Butorović, *Sušak i Rijeka u NOB* (znaci.org 00003/799, PDF pp. 627-628, book pp. 548-549: "Nosioci
»Partizanske spomenice 1941«") → website/public/pdfs/susak-rijeka-spomenica.pdf: the holders of the Partizanska
spomenica 1941 from the Rijeka municipality, as the local SUBNOR board had them from the fighters' statements, a book
across units. Two columns, a name and a place a line: "Babić Bogoljub •— Jušići", "Marčelja Josip Antonov — Marčelji"
(the father's possessive or a nickname after the given name tells men of one name apart), "Benaš Milan** — Klići" (the
book sets in bold those who died after the war: the two stars of the footnote mark one the text layer kept).
The book's lists before it, the members of the KPJ and SKOJ of 1941 who fell in the NOB, give a name and a village and
nothing that tells a fighter from an activist killed in the underground, so they stay out by the rule for mixed lists,
as do the Spanish volunteers (another war).
Output: data-extraction/znaci/susak-rijeka-spomenica-entries.json, IDs 9053xxxxxx, each with its box.
Usage: python data-extraction/parse_susak_rijeka_spomenica.py
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

BOOK = 'susak-rijeka-spomenica'
PDF = HERE.parent / 'website' / 'public' / 'pdfs' / f'{BOOK}.pdf'
OUT = HERE / 'znaci' / f'{BOOK}-entries.json'
PREFIX = '9053'
TITLE = 'Nosioci »Partizanske spomenice 1941« (Sušak i Rijeka u NOB)'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
LINE = re.compile(rf'^([{U}][{L}]+(?:-[{U}][{L}]+)?)\s+([{U}][{L}]+)((?:\s+[{U}][{L}]+)*?)\s*(\**)\s*[•·]?\s*[—–-]\s*(.*)$')


def build_pdf() -> None:
    if not PDF.exists():
        src, out = fitz.open(HERE / '.cache' / 'znaci_library' / 'chapters' / '00003_799.pdf'), fitz.open()
        out.insert_pdf(src, from_page=626, to_page=627)
        out.save(PDF, garbage=4, deflate=True)


def main() -> None:
    build_pdf()
    out, missed = [], []
    with pdfplumber.open(PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            for col in entry_boxes.read_page(page, columns=2)['columns']:
                for ln in col:
                    t = re.sub(r'\s+', ' ', ln['text']).strip()
                    if re.fullmatch(r'\d{3}|NOSIOCI »PARTIZANSKE|SPOMENICE 1941«\*', t) or t.startswith(('*', 'Imena', 'odbor', 'mo sve')):
                        continue
                    # the OCR's slips: a small first letter ("čulinović"), a name broken apart ("Dami i an"); a
                    # title before the given name ("Kučić dr Zdravko") stays in the text only
                    name = (t[:1].upper() + t[1:]).replace('Dami i an', 'Damijan')
                    m = LINE.match(re.sub(r'\s+dr\.?\s+', ' ', name, count=1))
                    if not m:
                        missed.append(t)
                        continue
                    last, first, more, stars, place = m.groups()
                    n = len(out) + 1
                    out.append({'soldier_id': f'{PREFIX}{n:06d}', 'name': f'{last} {first}', 'last_name': last, 'also': [],
                                'first_name': first, 'nick': more.strip(), 'fathers_name': '', 'birth_year': '',
                                'born_in': place.strip(), 'additional_info': f'{TITLE}: {t}', 'list': TITLE,
                                'survived': True, 'pdf_file': PDF.name, 'pdf_page': pno, 'pdf_x': round(ln['x0'], 1),
                                'pdf_y': round(ln['top'], 1)})
    stats = entry_boxes.fill_boxes(out)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(out)} holders -> {OUT.relative_to(HERE.parent)}; boxes: {entry_boxes.describe(stats, stats["boxed"])}')
    print('not read:', missed)


if __name__ == '__main__':
    main()
