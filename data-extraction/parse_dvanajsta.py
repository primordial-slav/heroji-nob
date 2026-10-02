"""
Parser: Dvanajsta brigada, XII. SNOUB (brigade code 63).

Source: Lado Ambrožič-Novljan, "Dvanajsta brigada" (Knjižnica NOV in POS 16, 1976; znaci.org 00003/814.pdf)
        →  website/public/pdfs/dvanajsta.pdf (PDF pages 608-647 of the book, at its end):
    pp. 1-4     XII. SNOUB — Seznam padlih   "Bavle Marjan, Gor. Podboršt, 1927—1945"
    pp. 5-40    Seznam borcev XII. SNOUB     "Ban Anton, 1925, Divača"
One column, one line to an entry. Read by _slovene_lists.
"""
import re

from _parser_scaffold import repair_lj_ocr, run_parser
from _slovene_lists import OWN, Indent, parse

INDENT = Indent(padli_from=1, padli_to=4, headings=re.compile(r'^(?:XII\. SNOUB|SEZNAM BORCEV)\b'))

if __name__ == '__main__':
    OWN['file'] = 'dvanajsta-soldiers.json'
    run_parser(
        pdf_path='website/public/pdfs/dvanajsta.pdf',
        brigade_code=63,
        output_path='website/public/dvanajsta-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§[sp]§'),
        parse_entry_fn=parse,
        prepare_fn=INDENT.prepare,
        line_filter=INDENT,
        post_fn=repair_lj_ocr,
    )
