"""
Parser: Zapadnodolenjski odred (brigade code 68).

Source: Velimir Kraševec, "Zapadnodolenjski odred" (Knjižnica NOV in POS 30/4, 1985; znaci.org 00003/808.pdf)
        →  website/public/pdfs/zapadnodolenjski-odred.pdf (PDF pages 334-343 of the book):
    pp. 1-7     Seznam odredovcev   "Fabjan Milka-Olga, 1924, Podturn"
    pp. 8-10    Padli               "Ambrož Franc-Ašev, Velike Češnjice. 1906-1943"
Three columns, a hanging indent. Read by _slovene_lists.
"""
import re

from _parser_scaffold import repair_lj_ocr, run_parser
from _slovene_lists import OWN, Indent, columns_reader, parse

INDENT = Indent(padli_from=8, headings=re.compile(r'^(?:Seznam odredovcev|Padli)$'))
# the compilers' signatures under each list: "Zbrala in sestavila: Ivanka in Jože Lukšič, Ljubljana, maja 1984"
SIGNED = {7: 400, 10: 310}


def keep(ln: dict) -> bool:
    if ln['page'] in SIGNED and ln['x'] > 200 and ln['y'] >= SIGNED[ln['page']]:
        return False
    return INDENT(ln)


if __name__ == '__main__':
    OWN['file'] = 'zapadnodolenjski-odred-soldiers.json'
    run_parser(
        pdf_path='website/public/pdfs/zapadnodolenjski-odred.pdf',
        brigade_code=68,
        output_path='website/public/zapadnodolenjski-odred-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        extract_fn=columns_reader(3),
        script='latin',
        entry_start_re=re.compile(r'^§[sp]§'),
        parse_entry_fn=parse,
        prepare_fn=INDENT.prepare,
        line_filter=keep,
        post_fn=repair_lj_ocr,
    )
