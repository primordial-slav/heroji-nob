"""
Parser: Deveta brigada, IX. SNOUB "Kočevska" (brigade code 167).

Source: Velimir Kraševec-Igor, "Deveta brigada" II (Knjižnica NOV in POS, 1991; znaci.org 00003/2850.pdf)
        →  website/public/pdfs/deveta.pdf (book pp. 425-446): "Seznam borcev IX. SNOB Kočevske", three columns, a
        hanging indent, no commas; the year after the name, the place on the line below, and for the fallen "p." with
        the year and where:
            Batinica Angela 1927
                Kočevje, p. 1944 Suhorje
The first page's text layer has a few lines printed twice over each other ("A Ap p l a e n n a c - S J e a n n k e o
z"); those names stay as the layer reads them.
Read by _slovene_lists (columns_reader(3), a comma put after each entry's first line).
"""
import re

from _parser_scaffold import repair_lj_ocr, run_parser
from _slovene_lists import OWN, Indent, columns_reader, parse_roster

INDENT = Indent(padli_from=None, comma_after_first_line=True,
                headings=re.compile(r'^(?:SEZNAM|BORCEV IX)\b'))


def clean(text: str) -> str:
    """The scan's marks in names: '~' for the dash before a partisan name, '!' for l, '?' for o, a stray dot or
    middle dot, two words run together ("BakJosip")."""
    text = re.split(r'\s(?:zavedamo|Zavedamo)\b', text)[0]                  # the editors' note after the last entry
    head, sep, rest = text.partition(',')
    head = head.replace('~', '-').replace('•', '-').replace('[', 'I').replace('!', 'l').replace('?', 'o').replace('·', '').replace('E>', 'e')
    head = re.sub(r'(?<=\w)[.:"]+(?=\w|\s|$)', '', head)
    head = re.sub(r'(?<=[a-zčšž])(?=[A-ZČŠŽ][a-zčšž])', ' ', head)
    return head + sep + rest


def parse(text: str) -> dict:
    rec = parse_roster(clean(text))
    fell = re.search(r'\bp\.\*?\s*(19\d\d)?\s*,?\s*([^,;]*)', rec['additional_info'])
    if fell:
        rec['death_type'] = 'poginuo'
        if fell.group(1):
            rec['death_date'] = fell.group(1)
        where = fell.group(2).strip(' .')
        if where and not re.search(r'\d', where):
            rec['death_place'] = where
        before = rec['additional_info'][:fell.start()].strip(' ,;')
        place = re.sub(r'^(?:[^;]*;\s*)?(?:1[89]\d\d,?\s*)?', '', before).strip(' ,')
        if place and not re.search(r'\d', place):
            rec['birth_place'] = place
    return rec


if __name__ == '__main__':
    OWN['file'] = 'deveta-soldiers.json'
    run_parser(
        pdf_path='website/public/pdfs/deveta.pdf',
        brigade_code=167,
        output_path='website/public/deveta-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        extract_fn=columns_reader(3),
        script='latin',
        entry_start_re=re.compile(r'^§[sp]§'),
        parse_entry_fn=parse,
        prepare_fn=INDENT.prepare,
        line_filter=INDENT,
        post_fn=repair_lj_ocr,
    )
