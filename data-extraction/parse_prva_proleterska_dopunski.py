"""
Parser: Prva proleterska brigada (brigade code 1) — "Dopunski spisak", the supplement to its roster.

Source: "Prva proleterska brigada", knjiga 4, Spisak boraca (znaci.org 00001/97, chapter 97_4.pdf, book pp.
        1065-1071)  →  website/public/pdfs/prva-proleterska-dopunski.pdf. The 93 members the editors found between the
        end of March and the end of July 1991, after the roster (the unit's first list, its three PDFs) was set; in its
        format, one column, each entry hanging:
    BOŠKOVIĆ-ANTONOVIĆ Gojka KSENIJA, 1923 god. Glamoč, BiH, Srpkinja, učenica, čl. KPJ od 1942 god. ...
The footnote under the first page (why the list is apart) is dropped, and the man whose name the editors didn't know
("PREZIME I IME NEPOZNATI", who left the brigade in May 1942). A second name in capitals after the given name is a
nickname ("zvani X;"), as in the roster. These get IDs from 700001.
"""
import re
import sys

from _parser_scaffold import repair_lj_ocr, run_parser

PDF = 'website/public/pdfs/prva-proleterska-dopunski.pdf'
NOTE: dict = {}
# the text layer's slips, read from the page: spaced capitals, Đ and the OCR's U for IJ
WORDS = [('ELZ A,', 'ELZA,'), ('NEŠIĆ AB ID', 'NEŠIĆ ABID'), ('ĐORDIJE', 'ĐORĐIJE'), ('LUKU ANO VIĆ', 'LUKIJANOVIĆ'),
         ('MAS AL Stevana', 'MASAL Stevana'), ('IVAŠKIN, SSSR', 'IVAŠKIN, SSSR')]


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if t.startswith('* Od kraja marta') or NOTE.get(ln['page']):
        NOTE[ln['page']] = True                                              # the footnote, to the page's end
        return False
    for a, b in WORDS:
        t = t.replace(a, b)
    ln['text'] = t
    if re.fullmatch(r"'?\d{4}", t) or t.startswith('Dopunski spisak') or t in (
            'pripadnika Prve proleterske', 'narodnooslobodilačke udarne brigade') or t.startswith('od 21. XII'):
        return False
    return True


def post(soldiers: list[dict]) -> list[dict]:
    out = []
    for s in repair_lj_ocr(soldiers):
        if s['last_name'] == 'Prezime':                                     # "PREZIME I IME NEPOZNATI"
            continue
        if s['last_name'] == 'Ivaškin':                                     # "IVAŠKIN, SSSR, lekar-hirurg": no given name
            s['first_name'], s['additional_info'] = '', 'SSSR, ' + s['additional_info']
        if s['last_name'] == 'Popović-Marković' and s['middle_name'] == 'Olga':   # "OLGA POPADIJA": no father
            s['middle_name'], s['first_name'] = '', 'Olga Popadija'
        words = s['first_name'].split()
        if len(words) == 2:                                                 # "PETAR PERO", "ROSA CRNA"
            s['first_name'] = words[0]
            s['additional_info'] = f'zvani {words[1]}; ' + s['additional_info']
        s['full_name'] = ' '.join(x for x in (s['last_name'], s['middle_name'], s['first_name']) if x)
        out.append(s)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    run_parser(pdf_path=PDF, brigade_code=1, output_path='website/public/prva-proleterska-soldiers.json',
               line_filter=keep, post_fn=post, id_start=700001, keep_other_sources=True)
