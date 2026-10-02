"""
Parser: Cankarjeva brigada, 5. SNOUB "Ivan Cankar" (brigade code 61).

Source: Lado Ambrožič-Novljan, "Cankarjeva brigada" (Knjižnica NOV in POS, 1975; znaci.org 00003/767.pdf)
        →  website/public/pdfs/cankarjeva.pdf (PDF pages 818-864 of the book):
    pp. 1-32    Seznam cankarjevcev   "Adam Jože-Ciril, 1920, Sodražica"
    pp. 33-47   Padli                 "Afal Jože-Branko, Stružnica 1922—1944"
Read by _slovene_lists; a soldier in both lists is merged (find_source_duplicates LISTS).
"""
import re

from _parser_scaffold import repair_lj_ocr, run_parser
from _slovene_lists import OWN, Indent, parse

INDENT = Indent(padli_from=33, headings=re.compile(r'^(?:SEZNAM C|ANKARJEVCEV|PADLI)\b'))

if __name__ == '__main__':
    OWN['file'] = 'cankarjeva-soldiers.json'
    run_parser(
        pdf_path='website/public/pdfs/cankarjeva.pdf',
        brigade_code=61,
        output_path='website/public/cankarjeva-soldiers.json',
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
