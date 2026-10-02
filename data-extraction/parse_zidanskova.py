"""
Parser: Zidanškova brigada (brigade code 65).

Source: Mirko Fajdiga, "Zidanškova brigada" (Knjižnica NOV in POS 15, 1975; znaci.org 00003/776.pdf)
        →  website/public/pdfs/zidanskova.pdf (PDF pages 732-752 of the book): "Seznam borcev", 1,160 names, the
book says, 228 of them fallen, "marked with the years of birth and death":
    Ačkun Stanko, 1912, Hrastnik
    Kvas Konrad, Koritno, Oplotnica, 1926—1944
Two columns, a hanging indent. Read by _slovene_lists.
"""
import re

from _parser_scaffold import repair_lj_ocr, run_parser
from _slovene_lists import OWN, Indent, columns_reader, parse_roster

INDENT = Indent(padli_from=None, headings=re.compile(r'^SEZNAM BORCEV\b'))
def keep(ln: dict) -> bool:
    """The editors' note follows the list on its last page (from y 440 down)."""
    return not (ln['page'] == 21 and ln['y'] > 440) and INDENT(ln)


FELL = re.compile(r'(?:,\s*|\s)(1[89]\d\d)?\s*[—–-]+\s*(19[34]\d)\s*$')


def parse(text: str) -> dict:
    """A roster entry; one that ends with the years of birth and death is a soldier who fell."""
    rec = parse_roster(text)
    info = rec['additional_info']
    m = FELL.search(info) or re.search(r',?\s*(1[89]\d\d)?\s*[—–-]+\s*padel', info) and None
    if m:
        rec['death_type'] = 'poginuo'
        rec['death_date'] = m.group(2)
        if m.group(1) and not rec.get('birth_year'):
            rec['birth_year'] = m.group(1)
    elif re.search(r'[—–-]\s*pad(?:el|la)\b', info):                       # "1922 — padel"
        rec['death_type'] = 'poginuo'
    return rec


if __name__ == '__main__':
    OWN['file'] = 'zidanskova-soldiers.json'
    run_parser(
        pdf_path='website/public/pdfs/zidanskova.pdf',
        brigade_code=65,
        output_path='website/public/zidanskova-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        extract_fn=columns_reader(2),
        script='latin',
        entry_start_re=re.compile(r'^§[sp]§'),
        parse_entry_fn=parse,
        prepare_fn=INDENT.prepare,
        line_filter=keep,
        post_fn=repair_lj_ocr,
    )
