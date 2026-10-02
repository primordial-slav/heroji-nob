"""
Parser: Gradnikova (Goriška) brigada (brigade code 64).

Source: Stanko Petelin, "Gradnikova brigada" (Knjižnica NOV in POS 7, 2nd ed. 1983; znaci.org 00003/825.pdf)
        →  website/public/pdfs/gradnikova.pdf (PDF pages 839-877 of the book; page 1 is the editors' note):
    pp. 2-10    Seznam v Gradnikovi (Goriški) brigadi padlih borcev   (793 names, the note says)
    pp. 11-39   Seznam drugih borcev Gradnikove (Goriške) brigade   (2,837: those who survived the war or didn't
                fall while in the brigade)
Three columns, a hanging indent, no commas; the place on the line below the name:
    Bufolin Zdravko-Valentin
        1927 Šempeter
Read by _slovene_lists (columns_reader(3), a comma put after each entry's first line).
"""
import re

from _parser_scaffold import repair_lj_ocr, run_parser
from _slovene_lists import OWN, Indent, columns_reader, parse_roster

INDENT = Indent(padli_from=2, padli_to=10, comma_after_first_line=True,
                headings=re.compile(r'^(?:SEZNAM|BRIGADI PADLIH|ADI PADLIH|Adi Padlih|GRADNIKOVE|\(GORIŠKE\)|BORCEV)\b'))


def parse(text: str) -> dict:
    """Both lists print name, year and place alike; the first is the fallen."""
    rec = parse_roster(re.sub(r'^§p§', '§s§', text))
    if text.startswith('§p§'):
        rec['death_type'] = 'poginuo'
    return rec


if __name__ == '__main__':
    OWN['file'] = 'gradnikova-soldiers.json'
    run_parser(
        pdf_path='website/public/pdfs/gradnikova.pdf',
        brigade_code=64,
        output_path='website/public/gradnikova-soldiers.json',
        start_page=2,
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
