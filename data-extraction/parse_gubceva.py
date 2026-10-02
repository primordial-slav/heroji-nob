"""
Parser: Gubčeva brigada, SNOUB "Matija Gubec" (brigade code 62).

Source: Lado Ambrožič-Novljan, "Gubčeva brigada" (Knjižnica NOV in POS, 1972; znaci.org 00003/782.pdf)
        →  website/public/pdfs/gubceva.pdf (PDF pages 980-1028 of the book):
    pp. 1-37    Seznam gubčevcev   "Ambrožič Lado-Novljan, 1908, Čatež ob Savi"
    pp. 38-49   Padli              "Abunar Karel, Gabrovka, 1900—1944"
Read by _slovene_lists.
"""
import re

from _parser_scaffold import repair_lj_ocr, run_parser
from _slovene_lists import OWN, Indent, parse

INDENT = Indent(padli_from=38, headings=re.compile(r'^(?:SEZNAM GUB|GUBČEVCEV|PADLI)\b'))

if __name__ == '__main__':
    OWN['file'] = 'gubceva-soldiers.json'
    run_parser(
        pdf_path='website/public/pdfs/gubceva.pdf',
        brigade_code=62,
        output_path='website/public/gubceva-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        col_split_x='auto',
        script='latin',
        entry_start_re=re.compile(r'^§[sp]§'),
        parse_entry_fn=parse,
        prepare_fn=INDENT.prepare,
        line_filter=INDENT,
        post_fn=repair_lj_ocr,
    )
